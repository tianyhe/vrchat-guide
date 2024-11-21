from worksheets.agents.tripbot import api
from worksheets.agents.tripbot.common import (
    botname,
    description,
    prompt_dir,
    starting_prompt,
)
from worksheets.agents.tripbot.custom_suql import suql_runner
from worksheets.from_spreadsheet import gsheet_to_genie

gsheet_id_default = "12dVJdhCFuIi020r1zgQplfA8He5OxYOzCRWelgCyc0c"
suql_prompt_selector = None
