from scraper.storage import flatten_versions, write_csv_archive, write_json_archive, write_text_archive


def test_storage_writes_outputs(tmp_path):
    records = [{
        "message_id": "abc123",
        "facility": "PEMEX Deer Park",
        "posted_datetime": "2026-08-13T11:21:00+00:00",
        "retrieved_datetime": "2026-08-13T12:00:00+00:00",
        "message_text": "Smoke and flaring may occur.",
        "normalized_message_text": "smoke and flaring may occur.",
        "content_hash": "hash1",
        "category": ["Flaring", "Smoke"],
        "status": "previous message still posted",
        "previously_seen": True,
        "first_seen": "2026-08-13T10:00:00+00:00",
        "last_seen": "2026-08-13T12:00:00+00:00",
        "source_url": "https://example.com/live",
        "versions": [{
            "retrieved_datetime": "2026-08-13T12:00:00+00:00",
            "status": "previous message still posted",
            "content_hash": "hash1",
            "message_text": "Smoke and flaring may occur.",
            "category": ["Flaring", "Smoke"],
        }],
    }]

    json_path = tmp_path / "caer_messages.json"
    txt_path = tmp_path / "caer_messages.txt"
    csv_path = tmp_path / "metadata.csv"

    write_json_archive(records, json_path)
    write_text_archive(records, txt_path)
    write_csv_archive(records, csv_path)

    assert json_path.exists()
    assert txt_path.exists()
    assert csv_path.exists()
    assert len(flatten_versions(records)) == 1
