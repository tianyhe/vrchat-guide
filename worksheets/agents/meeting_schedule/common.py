import os

current_dir = os.path.dirname(os.path.realpath(__file__))
prompt_dir = os.path.join(current_dir, "prompts")

botname = "Meeting Scheduling Bot"
starting_prompt = "Hello! I am a bot will help you schedule a meeting."
description = "You are a bot that helps users schedule meetings with a guest."
