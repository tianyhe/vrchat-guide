import random
from uuid import UUID, uuid4


def plane_search(
    departure_city: str,
    arrival_city: str,
    date: str,
    airline: str,
    seat_class: str,
    price: str,
    duration: str,
):
    if airline is None:
        random.choice(["American", "United", "Delta", "Virgin"])
    if seat_class is None:
        random.choice(["Economy", "Business", "First"])
    if price is None:
        random.randint(100, 1000)
    else:
        price = int(price)
        if price < 100 or price > 1000:
            return {
                "message": "Couldn't find any flights with the given price range. Please try again.",
            }
    if duration is None:
        random.randint(1, 8)
    else:
        duration = int(duration)
        if duration < 1 or duration > 8:
            return {
                "message": "Couldn't find any flights with the given duration. Please try again.",
            }

    return {
        "found": True,
        "departure_city": departure_city,
        "arrival_city": arrival_city,
        "date": date,
        "airline": airline,
        "seat_class": seat_class,
        "price": price,
        "duration": duration,
    }
