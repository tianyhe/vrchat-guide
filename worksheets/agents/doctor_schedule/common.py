import os

current_dir = os.path.dirname(os.path.realpath(__file__))
prompt_dir = os.path.join(current_dir, "prompts")

botname = "Doctor Visit Booking Bot"
starting_prompt = (
    "Hello! I am a bot that helps you book an appointment to visit a doctor. "
)
description = "You are a bot that helps customers book an appointment to visit a doctor. You need to check the availability of the doctor and book the appointment if available."
