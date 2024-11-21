from worksheets.agents.hotel_search import api
from worksheets.agents.hotel_search.common import (
    botname,
    description,
    prompt_dir,
    starting_prompt,
)
from worksheets.agents.hotel_search.custom_suql import suql_runner
from worksheets.from_spreadsheet import gsheet_to_genie

gsheet_id_default = "1TibrxFzni-qsVrw7Md7_gOegkV_Hx39-WxP23TyDS6A"
suql_prompt_selector = None
