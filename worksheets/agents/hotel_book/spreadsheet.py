from worksheets.agents.hotel_book import api
from worksheets.agents.hotel_book.common import (
    botname,
    description,
    prompt_dir,
    starting_prompt,
)
from worksheets.agents.hotel_book.custom_suql import suql_runner
from worksheets.from_spreadsheet import gsheet_to_genie

gsheet_id_default = "11yI3uFOw1tGCLZWvofvdTyforQZsKDArjWt_DkNt0DM"
suql_prompt_selector = None
