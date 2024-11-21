from worksheets.agents.bank_fraud import api
from worksheets.agents.bank_fraud.common import (
    botname,
    description,
    prompt_dir,
    starting_prompt,
)
from worksheets.agents.bank_fraud.custom_suql import suql_runner
from worksheets.from_spreadsheet import gsheet_to_genie

gsheet_id_default = "1Ia-IQJhNYUsTbob8eaVd7vwdZfHDLXzvWuogthPa8gA"
suql_prompt_selector = None
