import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from scraper.classifier import classify_message
from scraper.deduplicator import build_message_record, merge_message_state
from scraper.parser import parse_feed
from scraper.storage import load_archive, write_outputs

DEFAULT_URLS = [
    "https://www.incident-reporter.net/e-notifycaerfeed/caermessagelive.html",
    "https://www.incident-reporter.net/e-NotifyCaerFeed/CaerMessageArchived.html",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1,
        status_forcelist=(403, 429, 500, 502, 503, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_feed(url: str, user_agent: str) -> Dict[str, Any]:
    session = build_session()
    headers = {"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml"}
    try:
        response = session.get(url, headers=headers, timeout=(10, 20))
        if response.status_code == 403:
            return {"success": False, "status": 403, "error": "Access denied by server."}
        if response.status_code == 429:
            return {"success": False, "status": 429, "error": "Rate limited by server."}
        if response.status_code >= 400:
            return {"success": False, "status": response.status_code, "error": response.text[:200]}
        response.raise_for_status()
        return {"success": True, "status": response.status_code, "text": response.text}
    except requests.Timeout:
        return {"success": False, "status": "timeout", "error": "Request timed out."}
    except requests.RequestException as exc:
        return {"success": False, "status": "request_error", "error": str(exc)}


def normalize_feed_records(records: List[Dict[str, Any]], source_url: str, retrieved_datetime: str) -> List[Dict[str, Any]]:
    normalized = []
    for record in records:
        message_text = record.get("message_text", "")
        categories = classify_message(message_text)
        normalized.append(
            build_message_record(
                facility=record.get("facility", ""),
                posted_datetime=record.get("posted_datetime", ""),
                message_text=message_text,
                source_url=source_url,
                retrieved_datetime=retrieved_datetime,
                category=categories,
                status="new",
                previously_seen=False,
            )
        )
    return normalized


def process_sources(existing_records: List[Dict[str, Any]], user_agent: str) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    summary: Dict[str, int] = {
        "new": 0,
        "unchanged": 0,
        "updated": 0,
        "cleared": 0,
        "network_errors": 0,
        "parsing_errors": 0,
    }
    archive = existing_records

    live_url = DEFAULT_URLS[0]
    live_result = fetch_feed(live_url, user_agent)
    if live_result.get("success"):
        parse_result = parse_feed(live_result["text"], source_url=live_url)
        if parse_result.get("errors"):
            summary["parsing_errors"] += len(parse_result["errors"])
        live_records = normalize_feed_records(parse_result.get("messages", []), live_url, utc_now_iso())
        archive = merge_message_state(archive, live_records, utc_now_iso(), live_url)
        for record in archive:
            if record.get("source_url") == live_url and record.get("status") == "new" and record["message_id"] in {item["message_id"] for item in live_records}:
                summary["new"] += 1
            elif record.get("source_url") == live_url and record.get("status") == "previous message still posted":
                summary["unchanged"] += 1
            elif record.get("source_url") == live_url and record.get("status") == "updated":
                summary["updated"] += 1
            elif record.get("status") == "cleared":
                summary["cleared"] += 1
    else:
        summary["network_errors"] += 1

    archived_url = DEFAULT_URLS[1]
    archived_result = fetch_feed(archived_url, user_agent)
    if archived_result.get("success"):
        parse_result = parse_feed(archived_result["text"], source_url=archived_url)
        if parse_result.get("errors"):
            summary["parsing_errors"] += len(parse_result["errors"])
        archived_records = normalize_feed_records(parse_result.get("messages", []), archived_url, utc_now_iso())
        existing_by_id = {record["message_id"]: record for record in archive}
        for record in archived_records:
            if record["message_id"] not in existing_by_id:
                archive.append(record)

    return archive, summary


def main() -> int:
    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    archive_path = data_dir / "caer_messages.json"
    user_agent = os.environ.get("CAER_USER_AGENT", "CAER-Monitor/1.0 (+https://github.com/<repository>)")
    existing_records = load_archive(archive_path)
    archive, summary = process_sources(existing_records, user_agent)
    write_outputs(archive, data_dir)
    print(json.dumps({"summary": summary, "archive_size": len(archive)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
