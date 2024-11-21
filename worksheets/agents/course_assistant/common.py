import os

current_dir = os.path.dirname(os.path.realpath(__file__))
prompt_dir = os.path.join(current_dir, "prompts")

botname = "Course Requirement Assistant"
starting_prompt = "Hello! I'm the Course Requirement Assistant. I can help you with filling submitting the course requirements form, you can ask me anything about the course requirements. What would you like to know?"
description = "You are a couse requirement assistant. You can help students with their course requirements."
