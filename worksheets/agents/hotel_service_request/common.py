import os

current_dir = os.path.dirname(os.path.realpath(__file__))
prompt_dir = os.path.join(current_dir, "prompts")

botname = "Hotel Service Request Bot"
starting_prompt = "Hello! I am a bot will help you request a hotel service."
description = "You are a bot that helps users request hotel services."
