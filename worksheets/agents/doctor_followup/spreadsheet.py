from worksheets.agents.doctor_followup import api
from worksheets.agents.doctor_followup.common import (
    botname,
    description,
    prompt_dir,
    starting_prompt,
)
from worksheets.agents.doctor_followup.custom_suql import suql_runner
from worksheets.from_spreadsheet import gsheet_to_genie

gsheet_id_default = "1Cb0JC2UtbLCIMRHxFtF8PZGTjANvkGS-wECubAASe64"
suql_prompt_selector = None
