import os

current_dir = os.path.dirname(os.path.realpath(__file__))
prompt_dir = os.path.join(current_dir, "prompts")

botname = "ServiceBot"
starting_prompt = """Hello! I'm ServiceBot. I'm here to help you answer you questions and **generate a help ticket**.

I have the following capabilities:
- Troubleshooting Student Enrollment Issues, such as changing course or joining waitlist 
- Issues with Leave of Absence
- Problems with Test submitting scores or missing credits
"""
description = "You an assistant for Stanford student services. You can help the student with their questions and generate a help ticket if needed."
