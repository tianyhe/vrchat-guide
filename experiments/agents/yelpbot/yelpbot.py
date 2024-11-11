import asyncio
import datetime
import json
import os
from decimal import Decimal
from uuid import uuid4

from loguru import logger
from suql.agent import postprocess_suql

from worksheets.agent import Agent
from worksheets.interface_utils import conversation_loop
from worksheets.knowledge import SUQLKnowledgeBase, SUQLParser
from worksheets.utils import num_tokens_from_string

# Define your APIs


def book_restaurant_yelp(
    restaurant: str,
    date: datetime.date,
    time: datetime.time,
    number_of_people: int,
    special_request_info: str,
    **kwargs,
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


# Define path to the prompts

current_dir = os.path.dirname(os.path.realpath(__file__))
prompt_dir = os.path.join(current_dir, "prompts")


# Define Knowledge Base
def clean_up_response(results, column_names, required_restaurant_columns=None):
    """
    Custom function to define what to include in the final response prompt.
    This function should be customized to your database.

    This function currently is used for the restuarants domain, with some processing code
    to deal with:
    (1) `rating` (a float issue) and;
    (2) `opening_hours` (represented as a dictionary)

    It also cuts out too long DB results at the end.
    """

    def if_usable_restaurants(field: str):
        """
        Custom function to define what fields to not show to users.
        """
        NOT_USABLE_FIELDS = [
            # reviews are too long
            "reviews",
            # location related fields
            "_location",
            "longitude",
            "latitude",
        ]

        USABLE_FIELDS = ["_id", "id"]

        if (
            field in required_restaurant_columns or field in USABLE_FIELDS
        ) and field not in NOT_USABLE_FIELDS:
            return True

        return False

    def handle_opening_hours(input_dict):
        """
        Custom function to convert opening hours into LLM-readable formats.
        """
        order = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        def get_order_index(x):
            try:
                return order.index(x["day_of_the_week"])
            except ValueError:
                return len(order)  # or any default value

        res = []
        input_dict = sorted(input_dict, key=lambda x: get_order_index(x))
        for i in input_dict:
            res.append(
                f'open from {i["open_time"]} to {i["close_time"]} on {i["day_of_the_week"]}'
            )
        return res

    final_res = []
    for res in results:
        temp = dict(
            (column_name, result)
            for column_name, result in zip(column_names, res)
            if if_usable_restaurants(column_name)
        )
        for i in temp:
            if isinstance(temp[i], Decimal):
                temp[i] = float(temp[i])

        if "opening_hours" in temp:
            temp["opening_hours"] = handle_opening_hours(temp["opening_hours"])

        if "_id" in temp:
            temp["id"] = temp["_id"]
            del temp["_id"]

        # here is some simple heuristics to deal with too long DB results,
        # thus cutting it at some point
        if (
            num_tokens_from_string(
                json.dumps(final_res + [temp], indent=4), "gpt-3.5-turbo"
            )
            > 3500
        ):
            logger.info("Cutting off the response due to too long DB results")
            break

        final_res.append(temp)
    return final_res


def clean_up_response_restaurant(
    results, column_names, required_restaurant_columns=None
):
    final_res = clean_up_response(results, column_names, required_restaurant_columns)

    return final_res


suql_knowledge = SUQLKnowledgeBase(
    # llm_model_name="azure/gpt-4o",
    llm_model_name="gpt-4o",
    tables_with_primary_keys={"restaurants": "_id"},
    database_name="restaurants",
    embedding_server_address="http://127.0.0.1:8509",
    source_file_mapping={
        "yelp_general_info": os.path.join(current_dir, "yelp_general_info.txt")
    },
    postprocessing_fn=postprocess_suql,
    result_postprocessing_fn=clean_up_response_restaurant,
    # api_base="https://ovaloairesourceworksheet.openai.azure.com/",
    # api_version="2024-08-01-preview",
)

# Define the SUQL React Parser
suql_parser = SUQLParser(
    llm_model_name="gpt-4o",
    # llm_model_name="gpt-4",
)

# Define the agent
yelpbot = Agent(
    botname="YelpBot",
    description="You an assistant at Yelp and help users with all their queries related to booking a restaurant. You can search for restaurants, ask me anything about the restaurant and book a table.",
    prompt_dir=prompt_dir,
    starting_prompt="""Hello! I'm YelpBot. I'm here to help you find and book restaurants in four bay area cities **San Francisco, Palo Alto, Sunnyvale, and Cupertino**. What would you like to do?""",
    args={},
    api=[book_restaurant_yelp],
    knowledge_base=suql_knowledge,
    knowledge_parser=suql_parser,
).load_from_gsheet(
    gsheet_id="1pVcD0GBCkEYLCFxck77Nu8s_nvlFLijmTNxyl_Kf968",
)


if __name__ == "__main__":
    # Run the conversation loop
    asyncio.run(conversation_loop(yelpbot, "yelp_bot.json"))
