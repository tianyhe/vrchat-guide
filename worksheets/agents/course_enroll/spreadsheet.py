from worksheets.agents.course_enroll import api
from worksheets.agents.course_enroll.common import (
    botname,
    description,
    prompt_dir,
    starting_prompt,
)
from worksheets.agents.course_enroll.custom_suql import (
    suql_prompt_selector,
    suql_runner,
)
from worksheets.from_spreadsheet import gsheet_to_genie

gsheet_id_default = "1ejyFlZUrUZiBmFP3dLcVNcKqzAAfw292-LmyHXSFsTE"
