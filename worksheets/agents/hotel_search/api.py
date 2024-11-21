import random
from uuid import UUID, uuid4


def hotel_search(
    hotel_name: str,
    location: str,
    cost: str,
    min_rating: str,
    max_rating: str,
):
    min_rating = int(min_rating)
    max_rating = int(max_rating)

    min_rating_limit = 0
    max_rating_limit = 5

    if min_rating < min_rating_limit or min_rating > max_rating_limit:
        return {
            "message": "Couldn't find any hotels with the given rating range. Please try again.",
        }

    return {
        "hotel_name": hotel_name,
        "location": location,
        "cost": cost,
        "rating": random.randint(min_rating, max_rating),
    }
