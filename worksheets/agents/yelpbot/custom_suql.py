import json
import os
from decimal import Decimal

import tiktoken
from loguru import logger
from suql import suql_execute
from suql.agent import postprocess_suql

from worksheets.utils import num_tokens_from_string

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


def suql_runner(query, required_restaurant_columns=None, **kwargs):
    final_res = []

    processed_query = postprocess_suql(query)
    results, column_names, _ = suql_execute(
        processed_query,
        {"restaurants": "_id"},
        "restaurants",
        embedding_server_address="http://127.0.0.1:8509",
        source_file_mapping={
            "yelp_general_info": os.path.join(CURRENT_DIR, "yelp_general_info.txt")
        },
    )

    if column_names:
        # some custom processing code to clean-up results
        final_res = clean_up_response(
            results, column_names, required_restaurant_columns
        )

        return final_res
    return results


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
