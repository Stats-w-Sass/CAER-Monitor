import hashlib
import html
import re
from typing import Any, Dict, Iterable, List


def normalize_message_text(value: str) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<.*?>", " ", text)
    text = text.replace("&nbsp;", " ")
    text = text.replace("&", " and ")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def content_hash(message_text: str) -> str:
    normalized = normalize_message_text(message_text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def stable_message_id(facility: str, posted_datetime: str, message_text: str) -> str:
    canonical = "|".join([
        (facility or "").strip(),
        (posted_datetime or "").strip(),
        normalize_message_text(message_text),
    ])
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_message_record(
    facility: str,
    posted_datetime: str,
    message_text: str,
    source_url: str,
    retrieved_datetime: str,
    category: Iterable[str],
    status: str,
    previously_seen: bool,
    first_seen: str | None = None,
    last_seen: str | None = None,
    message_id: str | None = None,
) -> Dict[str, Any]:
    normalized = normalize_message_text(message_text)
    message_id = message_id or stable_message_id(facility, posted_datetime, message_text)
    category_list = list(category or [])
    record = {
        "message_id": message_id,
        "facility": (facility or "").strip(),
        "posted_datetime": posted_datetime,
        "retrieved_datetime": retrieved_datetime,
        "message_text": (message_text or "").strip(),
        "normalized_message_text": normalized,
        "content_hash": content_hash(normalized),
        "category": category_list,
        "status": status,
        "previously_seen": previously_seen,
        "first_seen": first_seen or retrieved_datetime,
        "last_seen": last_seen or retrieved_datetime,
        "source_url": source_url,
        "versions": [{
            "retrieved_datetime": retrieved_datetime,
            "status": status,
            "content_hash": content_hash(normalized),
            "message_text": (message_text or "").strip(),
            "category": category_list,
        }],
    }
    return record


def compare_message_status(existing_record: Dict[str, Any] | None, current_record: Dict[str, Any]) -> str:
    if existing_record is None:
        return "new"
    if existing_record.get("content_hash") == current_record.get("content_hash"):
        return "previous message still posted"
    return "updated"


def merge_message_state(
    existing_records: List[Dict[str, Any]],
    current_records: List[Dict[str, Any]],
    retrieved_datetime: str,
    source_url: str,
) -> List[Dict[str, Any]]:
    existing_by_id = {record["message_id"]: record for record in existing_records}
    current_by_id = {record["message_id"]: record for record in current_records}
    merged = []
    seen_ids = set()

    for message_id, current in current_by_id.items():
        previous = existing_by_id.get(message_id)
        status = compare_message_status(previous, current)
        current_copy = dict(current)
        current_copy["status"] = status
        current_copy["previously_seen"] = previous is not None
        current_copy["first_seen"] = previous.get("first_seen") if previous else current_copy.get("first_seen")
        current_copy["last_seen"] = retrieved_datetime
        current_copy.setdefault("versions", [])
        current_copy["versions"].append(
            {
                "retrieved_datetime": retrieved_datetime,
                "status": status,
                "content_hash": current_copy.get("content_hash"),
                "message_text": current_copy.get("message_text"),
                "category": current_copy.get("category", []),
            }
        )
        merged.append(current_copy)
        seen_ids.add(message_id)

    for previous in existing_records:
        if previous["message_id"] not in current_by_id:
            cleared = dict(previous)
            cleared["status"] = "cleared"
            cleared["previously_seen"] = True
            cleared["last_seen"] = previous.get("last_seen") or previous.get("retrieved_datetime")
            cleared.setdefault("versions", []).append(
                {
                    "retrieved_datetime": retrieved_datetime,
                    "status": "cleared",
                    "content_hash": previous.get("content_hash"),
                    "message_text": previous.get("message_text"),
                    "category": previous.get("category", []),
                }
            )
            merged.append(cleared)

    for current in current_records:
        if current["message_id"] not in seen_ids:
            merged.append(dict(current))

    return merged
