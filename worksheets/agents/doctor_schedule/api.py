import random
from uuid import UUID, uuid4


def check_availability(
    patient_name,
    doctor_name,
    day_of_visit,
    start_time,
    symptoms_of_patient,
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


def book_visit(
    patient_name,
    doctor_name,
    day_of_visit,
    start_time,
    symptoms_of_patient
):
    return {
        "status": "success",
        "booking_id": str(uuid4()),
    }
