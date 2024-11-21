from worksheets.agents.hotel_service_request import api
from worksheets.agents.hotel_service_request.common import (
    botname,
    description,
    prompt_dir,
    starting_prompt,
)
from worksheets.agents.hotel_service_request.custom_suql import suql_runner
from worksheets.from_spreadsheet import gsheet_to_genie

gsheet_id_default = "1oDhGvfcukeIa1gggXma4Fz1NTtnPJYtw1uolO1d5Fg0"
suql_prompt_selector = None
