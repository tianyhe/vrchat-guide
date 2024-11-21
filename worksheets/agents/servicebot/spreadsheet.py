from worksheets.agents.servicebot import api
from worksheets.agents.servicebot.common import (
    botname,
    description,
    prompt_dir,
    starting_prompt,
)
from worksheets.agents.servicebot.custom_suql import suql_runner
from worksheets.from_spreadsheet import gsheet_to_genie

gsheet_id_default = "1aNAG5xh1F_6EmtUAYTmoOBlJBdnpl7lgiZ9YhIW8UxA"

suql_prompt_selector = None
