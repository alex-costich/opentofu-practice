"""
L1 — validate
Receives the raw ticket event, validates required fields, and returns the
enriched event. Raises ValueError for any invalid field — Step Functions
will catch it and route to the Fail state.
"""


def lambda_handler(event, context):
    ticket_id = event.get("ticket_id", "unknown")
    customer  = event.get("customer", "")
    score     = event.get("priority_score")
    desc      = event.get("description", "")

    # priority_score must be a number between 0 and 100
    if score is None:
        raise ValueError(f"[{ticket_id}] Missing priority_score")
    if not isinstance(score, (int, float)):
        raise ValueError(f"[{ticket_id}] priority_score must be numeric, got {type(score).__name__}")
    if not (0 <= score <= 100):
        raise ValueError(f"[{ticket_id}] priority_score out of range: {score}")

    # description must be non-empty
    if not str(desc).strip():
        raise ValueError(f"[{ticket_id}] description must not be empty")

    # customer must be present
    if not str(customer).strip():
        raise ValueError(f"[{ticket_id}] customer must not be empty")

    return {
        **event,
        "validation_passed": True,
        "validated_by": "validate-lambda",
    }
