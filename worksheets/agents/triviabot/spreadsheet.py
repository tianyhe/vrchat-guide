from worksheets.agents.triviabot import api
from worksheets.agents.triviabot.common import (
    botname,
    description,
    prompt_dir,
    starting_prompt,
)
from worksheets.agents.triviabot.custom_suql import suql_runner
from worksheets.from_spreadsheet import gsheet_to_genie

gsheet_id_default = "1oo7tasfwNDKQp6HO2BSsXKBKikrX7ubw6qEyzT9bMuM"
suql_prompt_selector = None
