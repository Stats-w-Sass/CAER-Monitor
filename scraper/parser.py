import html as html_lib
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from bs4 import BeautifulSoup

DATE_FORMATS = [
    "%m/%d/%Y %I:%M:%S %p",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %I:%M %p",
    "%Y-%m-%d %H:%M:%S",
]


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape((value or "")).replace("\xa0", " ")).strip()


def parse_datetime(value: str | None) -> str | None:
    if not value:
        return None
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(value.strip(), fmt)
            return dt.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue
    return None


def split_facility_and_posted(heading_text: str) -> Tuple[str, str | None]:
    text = clean_text(heading_text)
    if "Posted On - " in text:
        facility_part, posted_part = text.split("Posted On - ", 1)
        facility = facility_part.strip(" ,")
        posted_text = posted_part.split(" - ", 1)[0].strip()
        return facility, posted_text
    return text, None


def html_to_text_fragment(fragment: str) -> str:
    soup = BeautifulSoup(fragment, "html.parser")
    return clean_text(soup.get_text(" ", strip=False))


def parse_entries(block_html: str, facility_name: str) -> List[Dict[str, Any]]:
    text = html_to_text_fragment(block_html)
    entries: List[Dict[str, Any]] = []
    for part in re.split(r"(?=Posted On - )", text):
        part = part.strip()
        if not part or not part.startswith("Posted On - "):
            continue
        match = re.match(r"Posted On - (?P<posted>.+?) - (?P<label>.+?)\s+(?P<message>.+)", part, flags=re.DOTALL)
        if not match:
            continue
        posted = parse_datetime(match.group("posted"))
        message = clean_text(match.group("message"))
        message = re.sub(r"^[0-9]+\s+", "", message)
        message = re.sub(r"^report\s*", "", message, flags=re.IGNORECASE)
        message = re.sub(r"^update\s*", "", message, flags=re.IGNORECASE)
        message = re.sub(r"^initial\s*", "", message, flags=re.IGNORECASE)
        message = re.sub(r"^initial\s+report\s*", "", message, flags=re.IGNORECASE)
        message = message.strip()
        if not message:
            continue
        entries.append({
            "facility": facility_name,
            "posted_datetime": posted or match.group("posted"),
            "message_text": message,
        })
    return entries


def parse_feed(html_text: str, source_url: str = "") -> Dict[str, Any]:
    soup = BeautifulSoup(html_text, "html.parser")
    messages: List[Dict[str, Any]] = []
    errors: List[str] = []
    body = soup.body or soup
    heading_matches = list(body.find_all("h5"))
    if not heading_matches:
        return {"messages": [], "errors": ["No facility headings were found in the page."]}

    for idx, heading in enumerate(heading_matches):
        facility, posted = split_facility_and_posted(heading.get_text(" ", strip=True))
        if not facility:
            continue
        next_heading = heading_matches[idx + 1] if idx + 1 < len(heading_matches) else None
        block_nodes = []
        current = heading.next_sibling
        while current is not None and current is not next_heading:
            block_nodes.append(current)
            current = current.next_sibling
        block_html = "".join(str(node) for node in block_nodes if str(node).strip())
        try:
            parsed_entries = parse_entries(block_html, facility)
        except Exception as exc:  # pragma: no cover - defensive guard
            errors.append(f"Failed to parse facility block '{facility}': {exc}")
            continue
        for item in parsed_entries:
            if posted and not item["posted_datetime"]:
                item["posted_datetime"] = parse_datetime(posted)
            messages.append({
                **item,
                "source_url": source_url,
            })

    return {"messages": messages, "errors": errors}
