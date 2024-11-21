from uuid import UUID, uuid4


def bank_fraud_report(full_name, fraud_report, **kwargs):
    return {
        "status": "success",
        "error": None,
        "report_id": str(uuid4()),
    }
