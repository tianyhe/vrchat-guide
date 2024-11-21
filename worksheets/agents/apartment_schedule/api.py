import random
from uuid import UUID, uuid4


def check_availability(
    customer_name,
    apartment_name,
    day_of_visit,
    start_time,
    application_fee_paid,
    special_request_from_customer,
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


def book_apartment_visit(
    customer_name,
    apartment_name,
    day_of_visit,
    start_time,
    application_fee_paid,
    special_request_from_customer,
):
    return {
        "status": "success",
        "booking_id": str(uuid4()),
    }
