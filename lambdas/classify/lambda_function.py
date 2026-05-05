"""
L2 — classify
Adds `severity` (urgent | normal | low) by combining the numeric
priority_score with keyword signals found in the description.

Score thresholds (base level before keyword adjustment):
  >= 70  → urgent
  40–69  → normal
  < 40   → low

Each urgent keyword found raises severity by one level (capped at urgent).
Each low keyword found lowers severity by one level (floor at low).
"""

URGENT_KEYWORDS = [
    "urgent", "down", "not working", "unresponsive", "crash", "outage",
    "critical", "broken", "emergency", "asap", "immediately", "failure",
    "cannot access", "data loss", "offline",
]

LOW_KEYWORDS = [
    "question", "how to", "feature request", "suggestion", "feedback",
    "curious", "wondering", "nice to have", "when will",
]

_LEVELS = ["low", "normal", "urgent"]


def _count(text, keywords):
    t = text.lower()
    return sum(1 for kw in keywords if kw in t)


def lambda_handler(event, context):
    score = event["priority_score"]
    desc  = event["description"]

    # Base level from numeric score
    if score >= 70:
        idx = 2  # urgent
    elif score >= 40:
        idx = 1  # normal
    else:
        idx = 0  # low

    urgent_hits = _count(desc, URGENT_KEYWORDS)
    low_hits    = _count(desc, LOW_KEYWORDS)

    idx = min(2, idx + urgent_hits)
    idx = max(0, idx - low_hits)

    return {
        **event,
        "severity": _LEVELS[idx],
        "classification_metadata": {
            "urgent_keywords_found": urgent_hits,
            "low_keywords_found":    low_hits,
            "classified_by":         "classify-lambda",
        },
    }
