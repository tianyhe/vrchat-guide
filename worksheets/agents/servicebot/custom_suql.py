import os

from loguru import logger
from suql import suql_execute
from suql.agent import postprocess_suql

from worksheets.llm.basic import llm_generate

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


def suql_runner(query, *args, **kwargs):
    processed_query = postprocess_suql(query)
    results, column_names, _ = suql_execute(
        processed_query,
        {},
        "services_assistant",
        embedding_server_address="http://127.0.0.1:8509",
        source_file_mapping={
            "services_general_info": os.path.join(
                CURRENT_DIR, "services_general_info.txt"
            )
        },
    )

    return results
