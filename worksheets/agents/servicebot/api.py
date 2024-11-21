from uuid import UUID, uuid4


def submit_api(
    student_task,
    trouble_shoot_student_enrollment,
    leave_of_absence,
    external_test_credits,
    full_name,
    **kwargs,
):
    task = None
    if trouble_shoot_student_enrollment.value:
        task = trouble_shoot_student_enrollment.value
    elif leave_of_absence.value:
        task = leave_of_absence.value
    elif external_test_credits.value:
        task = external_test_credits.value

    return {
        "status": "success",
        "params": {
            "student_task": student_task.value,
            "task": task,
            "full_name": full_name.value,
        },
        "response": {
            "transaction_id": uuid4(),
        },
    }


def change_course_service(
    change_type: str,
    course_id: str,
    class_number: int,
    issue_description: str,
):
    outcome = {
        "status": "success",
        "params": {
            "change_type": change_type.value,
            "course_id": course_id.value,
            "class_number": class_number.value,
            "issue_description": issue_description.value,
        },
        "response": {
            "transaction_id": uuid4(),
        },
    }
    return outcome


def join_waitlist_service(
    course_name: str,
    class_number: int,
    issue_description: str,
    waitlist_confirmation: str,
    schedule_conflict,
):
    return {
        "status": "success",
        "params": {
            "course_name": course_name.value,
            "class_number": class_number.value,
            "issue_description": issue_description.value,
            "waitlist_confirmation": waitlist_confirmation.value,
        },
        "response": {
            "transaction_id": uuid4(),
        },
    }
