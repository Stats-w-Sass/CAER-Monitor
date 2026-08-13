from pathlib import Path

from scraper.parser import parse_feed

FIXTURE = Path(__file__).parent / "fixtures" / "live_feed_sample.html"


def test_parse_feed_extracts_messages():
    html = FIXTURE.read_text(encoding="utf-8")
    result = parse_feed(html, source_url="https://example.com/live")
    assert result["errors"] == []
    assert len(result["messages"]) >= 2
    first = result["messages"][0]
    assert "PEMEX Deer Park" in first["facility"]
    assert first["posted_datetime"]
    assert "flaring" in first["message_text"].lower()


def test_parse_feed_handles_empty_feed():
    result = parse_feed("<html><body></body></html>", source_url="https://example.com/empty")
    assert result["messages"] == []
