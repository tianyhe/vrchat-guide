import os

current_dir = os.path.dirname(os.path.realpath(__file__))
prompt_dir = os.path.join(current_dir, "prompts")

botname = "Doctor Follow-up bot"
starting_prompt = "Hello! I am a bot that helps you get followup instructions from your doctor."
description = "You are a bot that helps patients get follow-up instructions from their doctors."
