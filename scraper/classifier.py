import re
from typing import List

CATEGORY_RULES = [
    (
        "Emergency Response",
        [
            r"\bemergency\b",
            r"\bevacuat(e|ion)\b",
            r"\bresponse\b",
            r"\bshelter\b",
            r"\bincident response\b",
        ],
    ),
    (
        "Facilities",
        [
            r"\bfacility\b",
            r"\bplant\b",
            r"\bsite\b",
            r"\bunit\b",
            r"\bprocessing\b",
            r"\brefinery\b",
        ],
    ),
    (
        "Flaring",
        [
            r"\bflare(?:s|d|\s+stack)?\b",
            r"\bflaring\b",
        ],
    ),
    (
        "Incidents",
        [
            r"\bincident\b",
            r"\baccident\b",
            r"\brelease\b",
            r"\bfire\b",
            r"\bmedical\b",
            r"\balert\b",
        ],
    ),
    (
        "Noise",
        [
            r"\bnoise\b",
            r"\bnoisy\b",
            r"\bsound\b",
            r"\baudible\b",
        ],
    ),
    (
        "Odors",
        [
            r"\bodor\b",
            r"\bodour\b",
            r"\bsmell\b",
        ],
    ),
    (
        "Pipelines",
        [
            r"\bpipeline\b",
            r"\bline\b",
            r"\btransmission line\b",
        ],
    ),
    (
        "Rail Cars",
        [
            r"\brailcar\b",
            r"\brail car\b",
            r"\btrain\b",
            r"\brailroad\b",
        ],
    ),
    (
        "Smoke",
        [
            r"\bsmoke\b",
            r"\bsmoky\b",
        ],
    ),
    (
        "Tanker Trucks",
        [
            r"\btanker\b",
            r"\btanker truck\b",
            r"\btruck\b",
        ],
    ),
    (
        "Training/Drills",
        [
            r"\btraining\b",
            r"\bdrill\b",
            r"\bexercise\b",
            r"\bemergency exercise\b",
        ],
    ),
]


def classify_message(message_text: str) -> List[str]:
    """Return a list of matching categories, in a controlled order."""
    text = (message_text or "").lower()
    matched: List[str] = []
    for category, patterns in CATEGORY_RULES:
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                matched.append(category)
                break
    return matched
