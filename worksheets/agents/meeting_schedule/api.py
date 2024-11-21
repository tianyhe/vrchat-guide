import random
from uuid import UUID, uuid4


def check_availability(
    user_name: str,
    meeting_guest_name: str,
    day: str,
    start_time: str,
    end_time: str,
    meeting_reason: str,
):
    available = random.choice([True, False])

    if not available:
        return {
            "message": "Sorry, the time slot is not available. Please try again.",
            "booking_available": False,
        }
    else:
        return {
            "user_name": user_name,
            "meeting_guest_name": meeting_guest_name,
            "day": day,
            "start_time": start_time,
            "end_time": end_time,
            "meeting_reason": meeting_reason,
            "booking_available": True,
        }
