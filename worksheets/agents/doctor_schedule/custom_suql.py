import os

from loguru import logger
from suql import suql_execute
from suql.agent import postprocess_suql

from worksheets.llm.basic import llm_generate


def suql_runner(query, *args, **kwargs):
    return []
