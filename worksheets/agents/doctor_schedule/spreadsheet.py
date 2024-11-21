from worksheets.agents.doctor_schedule import api
from worksheets.agents.doctor_schedule.common import (
    botname,
    description,
    prompt_dir,
    starting_prompt,
)
from worksheets.agents.doctor_schedule.custom_suql import suql_runner
from worksheets.from_spreadsheet import gsheet_to_genie

gsheet_id_default = "1GXiL_irt_gR1wk4RiJ36nKS6EveyXnH_4O4C9DxFahA"
suql_prompt_selector = None
