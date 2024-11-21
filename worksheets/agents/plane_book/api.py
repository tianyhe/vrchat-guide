import random
from uuid import UUID, uuid4


def check_availability(user_name: str, flight_id: str):
    if random.random() > 0.5:
        return {
            "status": "success",
            "booking_available": True,
        }
    else:
        return {
            "status": "success",
            "booking_available": False,
        }


def book_hotel_visit(user_name: str, hotel_id: str):
    return {
        "status": "success",
        "booking_id": str(uuid4()),
    }
