import datetime
from enum import Enum

from worksheets.agents.yelpbot.common import (
    api_list,
    botname,
    prompt_dir,
    starting_prompt,
)
from worksheets.agents.yelpbot.db import booking_db, restaurant_db
from worksheets.environment import (
    Action,
    GenieDB,
    GenieField,
    GenieRuntime,
    GenieType,
    GenieWorksheet,
)

try:
    from worksheets.agents.yelpbot.custom_suql import run_suql_query
except ImportError:
    print("Import Error: SUQL is not installed, database queries will not work")

bot = GenieRuntime(
    botname,
    prompt_dir=prompt_dir,
    starting_prompt=starting_prompt,
    apis=api_list,
)


class UserTask(str, Enum):
    book_restaurant = "book_restaurant"
    modify_booking = "modify_booking"
    cancel_booking = "cancel_booking"
    other = "other"


class Price(str, Enum):
    cheap = "cheap"
    moderate = "moderate"
    expensive = "expensive"
    luxury = "luxury"


@bot.geniews()
class YelpBot(GenieWorksheet):
    user_task = GenieField(
        UserTask, "user_task", description="The intent or the task the user wants to do"
    )
    user_full_name = GenieField(
        str, "user_full_name", description="The full name of the user"
    )
    user_email_address = GenieField(
        str, "user_email_address", description="The email address of the user"
    )
    user_phone_number = GenieField(
        str,
        "user_phone_number",
        description="The phone number of the user",
        actions=Action(
            '>say("either email id or phone number is required"), ask(user_email_id) if user_email_id == "refused_to_answer" and user_phone_number == "refused_answer"'
        ),
    )


@bot.geniews(
    actions=Action(
        '>genie_propose(BookRestaurant, {"restaurant": self}) if user_intent != "book_restaurant"'
    )
)
class Restaurant(GenieType):
    restuarant_id = GenieField(
        str, "restaurant_id", description="The id of the restaurant", primary_key=True
    )
    name = GenieField(str, "name", description="The name of the restaurant")
    cuisines = GenieField(
        list[str], "cuisines", description="The cuisines the restaurant serves"
    )
    price = GenieField(
        Price,
        "price",
        description="The price range of the restaurant.",
    )
    rating = GenieField(float, "rating", description="The rating of the restaurant")
    num_reviews = GenieField(
        int, "num_reviews", description="The number of reviews the restaurant has"
    )
    address = GenieField(str, "address", description="The address of the restaurant")
    popular_dishes = GenieField(
        list[str], "popular_dishes", description="The popular dishes of the restaurant"
    )
    phone_number = GenieField(
        str, "phone_number", description="The phone number of the restaurant"
    )
    location = GenieField(str, "location", description="The location of the restaurant")
    opening_hours = GenieField(
        list[str], "opening_hours", description="The opening hours of the restaurant"
    )
    summary = GenieField(
        str, "summary", description="The summary of reviews for the restaurant"
    )


@bot.geniews(
    actions=Action(
        ">genie_propose(ModifyBooking, {'booking': self}) if user_intent != 'modify_booking'; >genie_propose(CancelBooking, {'booking': self}) if user_intent != 'cancel_booking'"
    )
)
class Booking(GenieType):
    booking_id = GenieField(str, "booking_id", description="The id of the booking")
    restaurant_id = GenieField(
        str, "restaurant_id", description="The id of the restaurant"
    )
    date = GenieField(datetime.date, "date", description="The date of the booking")
    time = GenieField(datetime.time, "time", description="The time of the booking")
    party_size = GenieField(
        int, "party_size", description="The number of people for the booking"
    )
    special_request = GenieField(
        str,
        "special_request",
        description="Any special requests for the booking",
        optional=True,
    )


@bot.geniews(
    predicates=["user_intent == 'book_restaurant'"],
    requires_confirmation=True,
    actions=Action(
        '@book_restaurant("self.restaurant.id", "self.date", "self.time", "self.party_size", "self.special_request")'
    ),
)
class BookRestaurant(GenieWorksheet):
    restaurant = GenieField(
        Restaurant,
        "restaurant",
        description="The restaurant the user wants to book",
        requires_confirmation=True,
    )
    date = GenieField(
        datetime.date,
        "date",
        description="The date the user wants to book the restaurant for",
    )
    time = GenieField(
        datetime.time,
        "time",
        description="The time the user wants to book the restaurant for",
    )
    party_size = GenieField(
        int, "party_size", description="The number of people the user wants to book for"
    )
    special_request = GenieField(
        str,
        "special_request",
        description="Any special requests the user has for the restaurant",
        optional=True,
    )


@bot.geniews(
    predicates=["user_intent == 'modify_booking'"],
    requires_confirmation=True,
    actions=Action(
        "@modify_booking(self.booking.booking_id, self.date, self.time, self.party_size, self.special_request)"
    ),
)
class ModifyBooking(GenieWorksheet):
    booking = GenieField(
        Booking, "booking", description="The id of the booking the user wants to modify"
    )
    date = GenieField(
        datetime.date,
        "date",
        description="The date the user wants to modify the booking for",
        optional=True,
    )
    time = GenieField(
        datetime.time,
        "time",
        description="The time the user wants to modify the booking for",
        optional=True,
    )
    party_size = GenieField(
        int,
        "party_size",
        description="The number of people the user wants to modify the booking for",
        optional=True,
    )
    special_request = GenieField(
        str,
        "special_request",
        description="Any special requests the user has for the restaurant",
        optional=True,
    )


@bot.geniews(
    predicates=["user_intent == 'cancel_booking'"],
    requires_confirmation=True,
    actions=Action("@cancel_booking(self.booking.booking_id)"),
)
class CancelBooking(GenieWorksheet):
    booking = GenieField(
        Booking, "booking", description="The id of the booking the user wants to cancel"
    )
    reason = GenieField(
        str,
        "reason",
        description="The reason the user wants to cancel the booking",
        optional=True,
    )


@bot.genie_sql(
    db_schema=restaurant_db,
    outputs=[Restaurant],
    actions=Action("@execute_restaurant_query(self.query, yelpbot)"),
)
class RestaurantDB(GenieDB):
    location = GenieField(str, "location", description="The location of the restaurant")
    query = GenieField(
        str,
        "query",
        description="The SQL query for finding information about a restaurant",
        internal=True,
    )


@bot.genie_sql(
    db_schema=booking_db,
    outputs=[Booking],
    actions=Action("@execute_restaurant_query(self.query, yelpbot)"),
)
class BookingsDB(GenieDB):
    query = GenieField(
        str,
        "query",
        description="The SQL query to get information about bookings",
        internal=True,
    )
