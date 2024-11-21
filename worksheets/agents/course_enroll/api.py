import random
from uuid import UUID, uuid4

from worksheets.environment import GenieField, get_genie_fields_from_ws

course_is_full = {}


def course_detail_to_individual_params(course_detail):
    if course_detail.value is None:
        return {}
    course_detail = course_detail.value
    course_detail = {}
    for field in get_genie_fields_from_ws(course_detail):
        course_detail[field.name] = field.value

    return course_detail


# def courses_to_take_oval(
#     course_1_details,
#     course_2_details,
#     course_3_details,
#     course_4_details,
#     course_5_details,
#     course_6_details,
#     **kwargs
# ):
#     courses = {
#         "course_id_1": course_detail_to_individual_params(
#             course_1_details["course_id"]
#         ),
#         "course_id_2": course_detail_to_individual_params(
#             course_2_details["course_id"]
#         ),
#         "course_id_3": course_detail_to_individual_params(
#             course_3_details["course_id"]
#         ),
#         "course_id_4": course_detail_to_individual_params(
#             course_4_details["course_id"]
#         ),
#         "course_id_5": course_detail_to_individual_params(
#             course_5_details["course_id"]
#         ),
#         "course_id_6": course_detail_to_individual_params(
#             course_6_details["course_id"]
#         ),
#     }

#     return {
#         "params": courses,
#         "transaction_id": uuid4(),
#     }


def courses_to_take_oval(**kwargs):
    return {"success": True, "transaction_id": uuid4()}


def is_course_full(course_id, **kwargs):
    # randomly return True or False
    if course_id not in course_is_full:
        is_full = random.choice([True, False])
        course_is_full[course_id] = is_full

    return course_is_full[course_id]
