from worksheets.agents.apartment_schedule import api
from worksheets.agents.apartment_schedule.common import (
    botname,
    description,
    prompt_dir,
    starting_prompt,
)
from worksheets.agents.apartment_schedule.custom_suql import suql_runner
from worksheets.from_spreadsheet import gsheet_to_genie

gsheet_id_default = "1y4zrxCaDy-YAf8y8Csp9otiWX4lRLzAIVcLbAxRvJtc"
suql_prompt_selector = None
