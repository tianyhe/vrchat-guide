import os

current_dir = os.path.dirname(os.path.realpath(__file__))
prompt_dir = os.path.join(current_dir, "prompts")

botname = "Trivia Bot"
starting_prompt = "Hello! I am a trivia bot. I will ask you a series of questions. Which question number do you want to start from?"
description = "You are a trivia bot. You ask questions and the user answers them. You inform the user if they are correct or not and ask them if they want to continue playing."
