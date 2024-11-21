import random
from uuid import UUID, uuid4


def check_availability(
    customer_name, hotel_name, start_date, end_date, customer_request
):
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


def book_hotel_visit(customer_name, hotel_name, start_date, end_date, customer_request):
    return {
        "status": "success",
        "booking_id": str(uuid4()),
    }
