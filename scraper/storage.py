import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def load_archive(path: str | Path) -> List[Dict[str, Any]]:
    archive_path = Path(path)
    if not archive_path.exists():
        return []
    try:
        data = json.loads(archive_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def ensure_data_dir(path: str | Path) -> Path:
    data_dir = Path(path)
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def write_json_archive(records: List[dict], path: str | Path) -> None:
    archive_path = Path(path)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")


def write_text_archive(records: List[dict], path: str | Path) -> None:
    archive_path = Path(path)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for record in records:
        lines.append("=" * 60)
        lines.append("CAER MESSAGE")
        lines.append("=" * 60)
        lines.append(f"Message ID: {record.get('message_id', '')}")
        lines.append(f"Facility: {record.get('facility', '')}")
        lines.append(f"Posted: {record.get('posted_datetime', '')}")
        lines.append(f"Retrieved: {record.get('retrieved_datetime', '')}")
        lines.append(f"Status: {record.get('status', '')}")
        lines.append(f"Previously Seen: {record.get('previously_seen', '')}")
        lines.append(f"Category: {', '.join(record.get('category', []))}")
        lines.append(f"First Seen: {record.get('first_seen', '')}")
        lines.append(f"Last Seen: {record.get('last_seen', '')}")
        lines.append(f"Source: {record.get('source_url', '')}")
        lines.append("-" * 60)
        lines.append("Message:")
        lines.append(record.get("message_text", ""))
        lines.append("=" * 60)
    archive_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def flatten_versions(records: Iterable[dict]) -> List[dict]:
    rows = []
    for record in records:
        versions = record.get("versions", []) or [{}]
        for version in versions:
            rows.append({
                "message_id": record.get("message_id", ""),
                "facility": record.get("facility", ""),
                "posted_datetime": record.get("posted_datetime", ""),
                "retrieved_datetime": version.get("retrieved_datetime", record.get("retrieved_datetime", "")),
                "message_text": version.get("message_text", record.get("message_text", "")),
                "content_hash": version.get("content_hash", record.get("content_hash", "")),
                "category": ", ".join(record.get("category", []) or []),
                "status": version.get("status", record.get("status", "")),
                "previously_seen": record.get("previously_seen", False),
                "first_seen": record.get("first_seen", ""),
                "last_seen": record.get("last_seen", ""),
                "source_url": record.get("source_url", ""),
            })
    return rows


def write_csv_archive(records: List[dict], path: str | Path) -> None:
    archive_path = Path(path)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    rows = flatten_versions(records)
    fieldnames = [
        "message_id",
        "facility",
        "posted_datetime",
        "retrieved_datetime",
        "message_text",
        "content_hash",
        "category",
        "status",
        "previously_seen",
        "first_seen",
        "last_seen",
        "source_url",
    ]
    with archive_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_outputs(records: List[dict], data_dir: str | Path) -> None:
    data_dir = ensure_data_dir(data_dir)
    write_json_archive(records, data_dir / "caer_messages.json")
    write_text_archive(records, data_dir / "caer_messages.txt")
    write_csv_archive(records, data_dir / "metadata.csv")
