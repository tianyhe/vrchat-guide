from worksheets.agents.course_assistant import api
from worksheets.agents.course_assistant.common import (
    botname,
    description,
    prompt_dir,
    starting_prompt,
)
from worksheets.agents.course_assistant.custom_suql import (
    suql_prompt_selector,
    suql_runner,
)
from worksheets.from_spreadsheet import gsheet_to_genie

gsheet_id_default = "1ejyFlZUrUZiBmFP3dLcVNcKqzAAfw292-LmyHXSFsTE"
