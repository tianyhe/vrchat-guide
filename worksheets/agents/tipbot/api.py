from uuid import uuid4


def send_tip(params):
    """Send a tip to the tipbot."""
    return {
        "type": "send_tip",
        "params": params,
        "id": str(uuid4()),
    }
