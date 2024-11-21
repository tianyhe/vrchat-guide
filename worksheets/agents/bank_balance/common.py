import os

current_dir = os.path.dirname(os.path.realpath(__file__))
prompt_dir = os.path.join(current_dir, "prompts")

botname = "Bank Fraud Report Bot"
starting_prompt = (
    "Hello! I am a bot that helps you report fraud to the bank. What is your name?"
)
description = "You are a bank's fraud reporting app, you will first authenticate the user's information and then take a report of the fraud."
