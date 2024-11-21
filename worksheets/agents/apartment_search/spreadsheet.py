from worksheets.agents.apartment_search import api
from worksheets.agents.apartment_search.common import (
    botname,
    description,
    prompt_dir,
    starting_prompt,
)
from worksheets.agents.apartment_search.custom_suql import suql_runner
from worksheets.from_spreadsheet import gsheet_to_genie

gsheet_id_default = "1-j9c6Bg7hz3EglpR0WE6Lip8qSz8y_TsXe_evJTHsIo"
suql_prompt_selector = None
