import random
from uuid import UUID, uuid4


def apartment_search_result(
    num_bedrooms: int,
    min_price: int,
    max_price: int,
    min_floor_level: int,
    max_floor_level: int,
    min_floor_area: int,
    max_floor_area: int,
    has_balcony: bool,
    balcony_side: str,
    has_elevator: bool,
    nearby_point_of_interest: str,
):
    num_bedrooms = int(num_bedrooms)
    if min_price == "NA":
        min_price = 0
    min_price = int(min_price)

    if max_price == "NA":
        max_price = 10000000
    max_price = int(max_price)

    if min_floor_level == "NA":
        min_floor_level = 0
    min_floor_level = int(min_floor_level)

    if max_floor_level == "NA":
        max_floor_level = 15
    max_floor_level = int(max_floor_level)

    if min_floor_area == "NA":
        min_floor_area = 0
    min_floor_area = int(min_floor_area)

    if max_floor_area == "NA":
        max_floor_area = 10000000
    max_floor_area = int(max_floor_area)

    min_floor_area_available = num_bedrooms * 10
    max_floor_area_available = num_bedrooms * 50

    min_price_available = num_bedrooms * 300
    max_price_available = num_bedrooms * 800

    near_by_pois_available = random.sample(
        [
            "School",
            "TrainStation",
            "Park",
            "Museum",
            "University",
            "Club",
            "User's office",
            "User's gym",
        ],
        2,
    )
    min_floor_level_available = 0
    max_floor_level_available = 15

    if max_price < min_price_available:
        return {"status": "No matching apartments found."}
    if min_floor_level > max_floor_level_available:
        return {"status": "No matching apartments found."}
    if min_floor_area > max_floor_area_available:
        return {"status": "No matching apartments found."}
    if max_floor_area < min_floor_area_available:
        return {"status": "No matching apartments found."}
    if min_price > max_price_available:
        return {"status": "No matching apartments found."}
    if has_balcony != "NA" and has_balcony and balcony_side == "":
        return {"status": "No matching apartments found."}
    if has_elevator != "NA" and has_elevator and min_floor_level > 0:
        return {"status": "No matching apartments found."}
    if (
        nearby_point_of_interest != "NA"
        and nearby_point_of_interest not in near_by_pois_available
    ):
        return {"status": "No matching apartments found."}

    apartment_name = [
        "One on Center Apartments",
        "Shadyside Apartments",
        "North Hill Apartments",
    ]
    return {
        "status": "Apartment found.",
        "apartment": {
            "id": str(uuid4()),
            "name": random.choice(apartment_name),
            "num_bedrooms": num_bedrooms,
            "floor_area": random.randint(min_floor_area, max_floor_area),
            "floor_level": random.randint(min_floor_level, max_floor_level),
            "price": random.randint(min_price, max_price),
            "balcony": (
                random.choice([True, False]) if has_balcony == "NA" else has_balcony
            ),
            "balcony_side": (
                random.choice(["North", "South", "East", "West"])
                if balcony_side == "NA"
                else balcony_side
            ),
            "elevator": (
                random.choice([True, False]) if has_elevator == "NA" else has_elevator
            ),
            "nearby_point_of_interest": (
                random.choice(near_by_pois_available)
                if nearby_point_of_interest == "NA"
                else nearby_point_of_interest
            ),
        },
    }
