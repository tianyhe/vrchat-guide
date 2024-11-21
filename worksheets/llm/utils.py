from typing import Tuple

INSTRUCTION_START = "<|startofinstruction|>"
INSTRUCTION_END = "<|endofinstruction|>"
PROMPT_START = "<|startofinput|>"
PROMPT_END = "<|endofinput|>"


def load_prompt(prompt_file: str) -> Tuple[str, str]:
    with open(prompt_file, "r") as f:
        text = f.read()
        system_prompt = (
            text.split(INSTRUCTION_START)[1].split(INSTRUCTION_END)[0].strip()
        )
        prompt = text.split(PROMPT_START)[1].split(PROMPT_END)[0].strip()

    return system_prompt, prompt
