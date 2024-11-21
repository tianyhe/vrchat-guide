import os

from loguru import logger
from suql import suql_execute
from suql.agent import postprocess_suql

from worksheets.llm.basic import llm_generate

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


def suql_runner(query, *args, **kwargs):
    processed_query = postprocess_suql(query)
    processed_query = query.replace("\\'", "''")
    results, column_names, _ = suql_execute(
        processed_query,
        {
            "courses": "course_id",
            "ratings": "rating_id",
            "offerings": "course_id",
            "programs": "program_id",
        },
        "course_assistant",
        llm_model_name="gpt-4o",
        embedding_server_address="http://127.0.0.1:8509",
        source_file_mapping={
            "course_assistant_general_info.txt": os.path.join(
                CURRENT_DIR, "course_assistant_general_info.txt"
            )
        },
    )

    results = [dict(zip(column_names, result)) for result in results]
    return results[:5]


async def suql_prompt_selector(query):
    # Determine which tables are needed to answer the query.
    tables = await llm_generate(
        "table_classification.prompt",
        prompt_inputs={"query": query},
        prompt_dir=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "prompts",
        ),
        model_name="gpt-4o",
        temperature=0.0,
    ).lower()

    logger.info("User Query: {}", query)
    logger.info("Tables Selected: {}", tables)

    template_name = ""

    # Add the enums to the parsing template string
    if "programs" in tables:
        template_name += "p_parser.prompt"
    elif "ratings" in tables and "offerings" in tables:
        template_name += "cro_parser.prompt"
    elif "ratings" in tables:
        template_name += "cr_parser.prompt"
    elif "offerings" in tables:
        template_name += "co_parser.prompt"
    else:
        template_name += "c_parser.prompt"

    logger.info("Template Name: {}", template_name)

    return template_name
