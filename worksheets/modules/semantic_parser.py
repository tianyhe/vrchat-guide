import datetime
import os
import re

from loguru import logger
from sql_metadata import Parser
from suql.sql_free_text_support.execute_free_text_sql import _check_required_params

from worksheets.annotation_utils import prepare_semantic_parser_input
from worksheets.environment import (
    GenieRuntime,
    count_number_of_vars,
    get_genie_fields_from_ws,
)
from worksheets.llm.basic import llm_generate
from worksheets.modules import CurrentDialogueTurn
from worksheets.modules.rewriter import rewrite_code_to_extract_funcs
from worksheets.utils import extract_code_block_from_output

current_dir = os.path.dirname(__file__)


async def semantic_parsing(current_dlg_turn, dlg_history, bot):
    # Reset the agent acts
    bot.context.reset_agent_acts()

    # Convert the user utterance to worksheet representation
    user_target, suql_target = await _nl_to_code(current_dlg_turn, dlg_history, bot)

    current_dlg_turn.user_target_sp = user_target
    current_dlg_turn.user_target_suql = "\n".join(suql_target)

    # Rewrite the code to extract function calls to variables
    genie_user_target = _rewrite_code(user_target, bot)

    current_dlg_turn.user_target = genie_user_target


def _rewrite_code(user_target, bot):
    """Use LLM to extract the function calls to variables"""

    # Use the AST to extract the function calls to variables
    valid_worksheets = [func.__name__ for func in bot.genie_worksheets]
    valid_dbs = [func.__name__ for func in bot.genie_db_models]

    valid_worksheets.append("Answer")
    valid_worksheets.append("MoreFieldInfo")

    var_counter = count_number_of_vars(bot.context.context)

    try:
        rewritten_user_target = rewrite_code_to_extract_funcs(
            user_target,
            valid_worksheets,
            valid_dbs,
            var_counter,
        )
    except SyntaxError as e:
        logger.info(f"SyntaxError: {e}")
        rewritten_user_target = None

    return rewritten_user_target


async def _nl_to_code(current_dlg_turn, dlg_history, bot: GenieRuntime, **kwargs):
    (
        state_schema,
        agent_acts,
        agent_utterance,
        available_worksheets_text,
        available_dbs_text,
    ) = prepare_semantic_parser_input(bot, dlg_history, current_dlg_turn)

    user_target = await user_utterance_to_user_target(
        bot,
        dlg_history,
        current_dlg_turn,
        state_schema,
        agent_acts,
        agent_utterance,
        available_worksheets_text,
        available_dbs_text,
    )

    # extract `answer("query")` where query is a string from user_target

    answer_queries, pattern_type = extract_answer(user_target)
    suql_queries = []
    for answer_query in answer_queries:
        logger.info(f"Answer query: {answer_query}")
        suql_query = await bot.suql_parser.parse(dlg_history, answer_query[1:-1], bot)

        if suql_query is None:
            logger.error(f"SUQL parsing failed for {answer_query}")
            suql_query = ""

        suql_query = suql_query.replace("\*", "*")

        if "SELECT" in suql_query:
            tables = Parser(suql_query).tables

            # Check for required parameters in the tables
            table_req_params = {}
            for table in tables:
                req_params, table_class = get_required_params_in_table(table, bot)
                table_req_params[table] = req_params

            _, unfilled_params = _check_required_params(suql_query, table_req_params)
        else:
            tables = []
            unfilled_params = {}

        suql_queries.append(suql_query)

        # If query has unfilled params, but the primary key is filled, then we don't need required params
        if len(unfilled_params) > 0:
            id_filled, _ = _check_required_params(
                suql_query, get_table_primary_keys(bot)
            )
            if id_filled:
                unfilled_params = {}

        # Semantic parser generates a new Answer object
        if pattern_type == "func":
            answer_str = f"Answer({repr(suql_query)}, {unfilled_params}, {tables}, {repr(answer_query[1:-1])})"

            user_target = user_target.replace(f"answer({answer_query})", answer_str)
        else:
            # We need Answer(query, unfilled_params, tables, query_str) from answer variables
            answer_var = re.search(r"answer_(\d+)", user_target).group(0)
            answer_str = f"{answer_var}.result = []\n"
            answer_str = f"{answer_var}.update(query={repr(suql_query)}, unfilled_params={unfilled_params}, tables={tables}, query_str={repr(answer_query[1:-1])})"
            user_target = user_target.replace(
                f"{answer_var}.query = {answer_query}", answer_str
            )
    return user_target.strip(), suql_queries


def get_table_primary_keys(bot):
    """Get the primary keys for all tables in the bot's database models.

    Args:
        bot (GenieRuntime): The bot instance containing the database models.

    Returns:
        dict: A dictionary mapping table names to their primary keys.
    """
    mapping = {}
    for db in bot.genie_db_models:
        for field in get_genie_fields_from_ws(db):
            if field.primary_key:
                mapping[db.__name__] = [field.name]

    return mapping


def get_required_params_in_table(table, bot: GenieRuntime):
    """Get the required parameters for a given table in the bot's database models.

    Args:
        table (str): The name of the table.
        bot (GenieRuntime): The bot instance containing the database models.

    Returns:
        tuple: A tuple containing a list of required parameters and the table class."""
    required_params = []
    table_class = None
    for db in bot.genie_db_models:
        if db.__name__ == table:
            table_class = db
            for field in get_genie_fields_from_ws(db):
                if not field.optional:
                    required_params.append(field.name)

    return required_params, table_class


def extract_answer(text):
    """Extracts answer queries from the provided text.

    Args:
        text (str): The input text containing answer queries.

    Returns:
        tuple: A list of extracted answer queries and the pattern type (either "func" or "attr").
    """
    pattern_type = "func"
    # Regex pattern to find answer() with a string argument inside, handling both single and double quotes
    pattern = r'answer\((?:("[^"]*")|(\'[^\']*\'))\)'

    matches = re.findall(pattern, text)

    # Each match is a tuple with the string in either the first or the second position, depending on the quote type
    # We extract non-None values from these tuples and return them as a list
    queries = [match[0] or match[1] for match in matches]
    if len(queries) == 0:
        pattern = r'answer_\d+\.query = (?:("[^"]*")|(\'[^\']*\'))'
        matches = re.findall(pattern, text)
        queries = [match[0] or match[1] for match in matches]
        pattern_type = "attr"

    return queries, pattern_type


async def user_utterance_to_user_target(
    bot: GenieRuntime,
    dlg_history: list[CurrentDialogueTurn],
    current_dlg_turn: CurrentDialogueTurn,
    state_schema: str | None,
    agent_acts: str | None,
    agent_utterance: str | None,
    available_worksheets_text: str,
    available_dbs_text: str,
):
    """Convert user utterance to user target using LLM.

    Args:
        bot (GenieRuntime): The bot instance.
        dlg_history (list[CurrentDialogueTurn]): The dialogue history.
        current_dlg_turn (CurrentDialogueTurn): The current dialogue turn.
        state_schema (str | None): The state schema.
        agent_acts (str | None): The agent actions.
        agent_utterance (str | None): The agent utterance.
        available_worksheets_text (str): Available worksheets text.
        available_dbs_text (str): Available databases text.

    Returns:
        str: The user target generated from the user utterance.
    """

    # Prepare the prompt file based on the state schema
    prompt_file = "semantic_parser.prompt"

    # Prepare the inputs for the prompt
    prompt_inputs = {
        "user_utterance": current_dlg_turn.user_utterance,
        "dlg_history": dlg_history,
        "bot": bot,
        "apis": available_worksheets_text,
        "dbs": available_dbs_text,
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "day": datetime.datetime.now().strftime("%A"),
        "date_tmr": (datetime.datetime.now() + datetime.timedelta(days=1)).strftime(
            "%Y-%m-%d"
        ),
        "yesterday_date": (
            datetime.datetime.now() - datetime.timedelta(days=1)
        ).strftime("%Y-%m-%d"),
        "state": state_schema,
        "agent_actions": agent_acts if agent_acts else "None",
        "agent_utterance": agent_utterance,
        "description": bot.description,
    }

    # Generate the user target using LLM
    parsed_output = await llm_generate(
        prompt_file,
        prompt_inputs=prompt_inputs,
        prompt_dir=bot.prompt_dir,
        model_name="gpt-4o",
        temperature=0.0,
        # **bot.args["semantic_parser"],
    )

    # Extract the code block from the parsed output
    user_target = extract_code_block_from_output(parsed_output, lang="python")

    return user_target
