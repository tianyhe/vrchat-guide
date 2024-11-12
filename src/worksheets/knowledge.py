import os
from datetime import datetime, timedelta
from typing import Callable, List, Optional

from chainlite import write_prompt_logs_to_file
from kraken.agent import PartToWholeParser
from kraken.utils import DialogueTurn
from loguru import logger
from pydantic import BaseModel
from suql import suql_execute
from suql.agent import DialogueTurn as SUQLDialogueTurn

from worksheets.environment import Answer, GenieRuntime
from worksheets.llm import llm_generate
from worksheets.modules import CurrentDialogueTurn
from worksheets.utils import extract_code_block_from_output

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


class SUQLKnowledgeBase(BaseModel):
    """Knowledge base for SUQL queries"""

    # Name of the LLM model to use for the queries
    llm_model_name: str

    # Tables with primary keys as values for the queries.
    # TODO: This should be automatically generated from the database schema
    tables_with_primary_keys: Optional[dict] = None

    # Name of the database to run the queries on
    database_name: Optional[str] = None

    # Address of the embedding server to use for the queries on free-text data
    embedding_server_address: Optional[str] = None

    # Mapping of free-text files to their paths for free-text data
    source_file_mapping: Optional[dict] = None

    # Function to run on the generated SUQL query
    postprocessing_fn: Callable

    # Function to run on the result from execution of the SUQL query
    result_postprocessing_fn: Optional[Callable] = None

    # Maximum number of rows to return in the result
    max_rows: int = 3

    # Username for the database
    db_username: Optional[str] = None

    # Password for the database
    db_password: Optional[str] = None

    # db host
    db_host: str = "127.0.0.1"

    # db port
    db_port: str = "5432"

    # Additional parameters for Azure
    api_base: Optional[str] = None

    api_version: Optional[str] = None

    # def run(self, query, *args, **kwargs):
    #     """Run the SUQL query and return the result."""

    #     if self.postprocessing_fn:
    #         query = self.postprocessing_fn(query)

    #     query = query.strip().replace("\\'", "'")

    #     results, column_names, _ = suql_execute(
    #         query,
    #         table_w_ids=self.tables_with_primary_keys,
    #         database=self.database_name,
    #         llm_model_name=self.llm_model_name,
    #         embedding_server_address=self.embedding_server_address,
    #         source_file_mapping=self.source_file_mapping,
    #         db_username=self.db_username,
    #         db_password=self.db_password,
    #         db_host=self.db_host,
    #         db_port=self.db_port,
    #         api_base=self.api_base,
    #         api_version=self.api_version,
    #     )

    #     # Convert the results to a list of dictionaries for genie worksheets
    #     results = [dict(zip(column_names, result)) for result in results]

    #     if self.result_postprocessing_fn:
    #         results = self.result_postprocessing_fn(results, column_names)

    #     return results[: self.max_rows]

    def run(self, query, *args, **kwargs):
        """Run the SUQL query and return the result."""
        try:
            if self.postprocessing_fn:
                query = self.postprocessing_fn(query)

            query = query.strip().replace("\\'", "'")

            # Create database connection string
            db_url = f"postgresql://{self.db_username}:{self.db_password}@{self.db_host}:{self.db_port}/{self.database_name}"

            # Execute query with proper parameters
            results, column_names, _ = suql_execute(
                query,
                table_w_ids=self.tables_with_primary_keys,
                database=self.database_name,
                llm_model_name=self.llm_model_name,
                embedding_server_address=self.embedding_server_address,
                source_file_mapping=self.source_file_mapping,
                select_username=self.db_username,
                select_userpswd=self.db_password,
                host=self.db_host,
                port=self.db_port,
            )

            # Convert the results to a list of dictionaries for genie worksheets
            results = [dict(zip(column_names, result)) for result in results]

            if self.result_postprocessing_fn:
                results = self.result_postprocessing_fn(results, column_names)

            return results[: self.max_rows]

        except Exception as e:
            logger.error(f"Error in SUQL execution: {str(e)}")
            return []

class BaseSUQLParser(BaseModel):
    """Base class for SUQL parsers"""

    # Name of the LLM model to use for the queries
    llm_model_name: str

    async def parse(self, dlg_history: List[CurrentDialogueTurn], query: str):
        raise NotImplementedError

    def convert_dlg_turn_to_suql_dlg_turn(self, dlg_history, turn, db_results):
        # Convert the dialog history to the expected format for SUQL
        suql_dlg_history = []
        for i, turn in enumerate(dlg_history):
            user_target = turn.user_target_suql
            agent_utterance = turn.system_response
            user_utterance = turn.user_utterance

            if db_results is None:
                db_result = [
                    obj.result
                    for obj in turn.context.context.values()
                    if isinstance(obj, Answer)
                    and obj.query.value == turn.user_target_suql
                ]
            else:
                db_result = db_results[i]

            suql_dlg_history.append(
                SUQLDialogueTurn(
                    user_utterance=user_utterance,
                    db_results=db_result,
                    user_target=user_target,
                    agent_utterance=agent_utterance,
                )
            )

        return suql_dlg_history


class SUQLParser(BaseSUQLParser):
    """Parser for SUQL queries"""

    # Selector for the prompt to use for the queries
    prompt_selector: Optional[Callable] = None

    async def parse(
        self,
        dlg_history: List[CurrentDialogueTurn],
        query: str,
        bot: GenieRuntime,
        db_results: List[str] | None = None,
    ):
        """
        A SUQL conversational semantic parser, with a pre-set prompt file.
        The function convets the List[CurrentDialogueTurn] to the expected format
        in SUQL (suql.agent.DialogueTurn) and calls the prompt file.

        # Parameters:

        `dlg_history` (List[CurrentDialogueTurn]): a list of past dialog turns.

        `query` (str): the current query to be parsed.

        # Returns:

        `parsed_output` (str): a parsed SUQL output
        """

        suql_dlg_history = self.convert_dlg_turn_to_suql_dlg_turn(
            dlg_history, query, db_results
        )

        # Use the prompt selector if available
        if self.prompt_selector:
            prompt_file = await self.prompt_selector(bot, dlg_history, query)
        else:
            prompt_file = "suql_parser.prompt"

        # Generate the SUQL output
        parsed_output = await llm_generate(
            prompt_file,
            prompt_inputs={
                "dlg": suql_dlg_history,
                "query": query,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "day": datetime.now().strftime("%A"),
                "day_tmr": (datetime.now() + timedelta(days=1)).strftime("%A"),
            },
            prompt_dir=bot.prompt_dir,
            model_name=self.llm_model_name,
            temperature=0.0,
        )

        return extract_code_block_from_output(parsed_output, lang="sql")


class SUQLReActParser(BaseSUQLParser):
    """ReAct Parser for SUQL queries"""

    # Select examples for the queries
    example_path: str

    # Select instructions for the queries
    instruction_path: str

    # Select table schema for the queries
    table_schema_path: str

    # Knowledge base for the queries
    knowledge: SUQLKnowledgeBase

    # List of examples for the queries
    examples: Optional[List[str]] = None

    # List of instructions for the queries
    instructions: Optional[List[str]] = None

    # Table schema for the queries
    table_schema: Optional[str] = None

    # Conversation history for the queries
    conversation_history: List = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.examples is None:
            self.examples = []
            with open(self.example_path, "r") as f:
                text = f.read()

            for example in text.split("--"):
                if example.strip():
                    self.examples.append(example.strip())

        if self.instructions is None:
            with open(self.instruction_path, "r") as f:
                self.instructions = f.readlines()

        if self.table_schema is None:
            with open(self.table_schema_path, "r") as f:
                self.table_schema = f.read()

    async def parse(
        self,
        dlg_history: List[CurrentDialogueTurn],
        query: str,
        bot: GenieRuntime,
        db_results: List[str] | None = None,
    ):
        suql_dlg_history = self.convert_dlg_turn_to_suql_dlg_turn(
            dlg_history, query, db_results
        )

        self.conversation_history = suql_dlg_history

        output = await self.anext_turn(
            query,
            update_conversation_history=False,
            table_w_ids=self.knowledge.tables_with_primary_keys,
            database_name=self.knowledge.database_name,
            embedding_server_address=self.knowledge.embedding_server_address,
            source_file_mapping=self.knowledge.source_file_mapping,
        )

        # TODO: KeyError: 'final_sql'
        # happens when the action_counter limit is met without a final SQL being generated
        logger.info(f"SUQL output: {output}")
        try:
            final_output = output["final_sql"].sql
        except Exception as e:
            logger.error(f"Error in parsing output: {e}")
            final_output = None
        return final_output

    async def anext_turn(
        self,
        user_input: str,
        update_conversation_history: bool = False,
        table_w_ids: dict = None,
        database_name: str = None,
        embedding_server_address: str = None,
        source_file_mapping: dict = None,
    ):
        try:
            parser = PartToWholeParser()
            parser.initialize(
                engine=self.llm_model_name,
                table_w_ids=table_w_ids,
                database_name=database_name,
                suql_model_name=self.knowledge.llm_model_name,
                suql_api_base=self.knowledge.api_base,
                suql_api_version=self.knowledge.api_version,
                embedding_server_address=embedding_server_address,
                source_file_mapping=source_file_mapping,
                domain_instructions=self.instructions,
                examples=self.examples,
                table_schema=self.table_schema,
            )

            output = await parser.arun(
                {
                    "question": user_input,
                    "conversation_history": self.conversation_history,
                }
            )
        finally:
            write_prompt_logs_to_file(append=True, include_timestamp=True)

        if update_conversation_history:
            self.update_turn(self.conversation_history, output, response=None)

        return output

    def update_turn(self, conversation_history, output, response):
        turn = DialogueTurn(
            user_utterance=output["question"],
            agent_utterance=response,
            user_target=output["final_sql"].sql,
            db_results=output["final_sql"].execution_result,
        )

        conversation_history.append(turn)
