from worksheets.agents.meeting_schedule import api
from worksheets.agents.meeting_schedule.common import (
    botname,
    description,
    prompt_dir,
    starting_prompt,
)
from worksheets.agents.meeting_schedule.custom_suql import suql_runner
from worksheets.from_spreadsheet import gsheet_to_genie

gsheet_id_default = "1SzqoyVoB0XF3pYf_KHvJihAzR2Cu4bTMuoDYgO1GJwA"
suql_prompt_selector = None
