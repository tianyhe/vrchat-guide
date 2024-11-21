import os

current_dir = os.path.dirname(os.path.realpath(__file__))
prompt_dir = os.path.join(current_dir, "prompts")

botname = "Hotel Booking Bot"
starting_prompt = "Hello! I am a bot that helps you book a hotel room."
description = "You are a bot that helps customers book a hotel room. You need to check the availability of the hotel room and book the room if available."
