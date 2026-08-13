from scraper.deduplicator import content_hash, normalize_message_text, stable_message_id


def test_normalization_stabilizes_text():
    left = "  Smoke & Flaring   occurs!  "
    right = "smoke and flaring occurs!"
    assert normalize_message_text(left) == normalize_message_text(right)


def test_message_id_is_stable_for_repeated_messages():
    first = stable_message_id("PEMEX Deer Park", "8/13/2026 7:21:00 AM", "Smoke and flaring may occur.")
    second = stable_message_id("PEMEX Deer Park", "8/13/2026 7:21:00 AM", "smoke and flaring may occur.")
    assert first == second
    assert content_hash("Smoke and flaring may occur.") == content_hash("smoke and flaring may occur.")
