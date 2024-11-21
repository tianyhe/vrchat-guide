import random
from uuid import UUID, uuid4


def doctor_followup_instructions(*args, **kwargs):
    outputs = [
        "You must take your medicine 2 times a day before meals.",
        "Take your medicine before you go to sleep. If you experience nausea, please contact your doctor immediately.",
    ]

    return {"message": random.choice(outputs)}
