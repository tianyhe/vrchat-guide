import datetime
from uuid import UUID, uuid4


def book_restaurant_yelp(
    restaurant: str,
    date: datetime.date,
    time: datetime.time,
    number_of_people: int,
    special_request_info: str,
    **kwargs
):
    outcome = {
        "status": "success",
        "params": {
            "restaurant_id": restaurant.value.id.value,
            "date": date.value,
            "time": time.value,
            "number_of_people": number_of_people.value,
            "special_request_info": special_request_info.value,
        },
        "response": {
            "booking_id": uuid4(),
            "transaction_date": datetime.date.today(),
            "transaction_time": datetime.datetime.now().time(),
        },
    }
    return outcome


def modify_booking_yelp(
    booking_id: UUID,
    date: datetime.date,
    time: datetime.time,
    party_size: int,
    special_request: str,
):
    return {
        "status": "success",
        "params": {
            "booking_id": booking_id,
            "date": date,
            "time": time,
            "party_size": party_size,
            "special_request": special_request,
        },
        "response": {
            "transaction_id": uuid4(),
        },
    }


def cancel_booking_yelp(booking_id: UUID):
    return {
        "status": "success",
        "params": {
            "booking_id": booking_id,
        },
        "response": {
            "transaction_id": uuid4(),
        },
    }
