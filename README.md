# CAER Monitor

The CAER Monitor is a low-impact Python application that polls the public CAER live message feed, classifies messages into a controlled vocabulary, detects new, unchanged, updated, and cleared states, and preserves a historical archive.

## Purpose

This project monitors the public CAER feed at https://www.incident-reporter.net/e-notifycaerfeed/caermessagelive.html and the archived/recently-cleared feed when available. It captures facility, posted timestamp, full message text, categories, and message status while avoiding browser automation or anti-bot evasion.

## Architecture

- `scraper/parser.py`: HTML parsing and feed extraction
- `scraper/classifier.py`: rule-based category classification
- `scraper/deduplicator.py`: stable identifiers, hashing, and duplicate detection
- `scraper/storage.py`: archive persistence to JSON, TXT, and CSV
- `scraper/scraper.py`: fetching, state transitions, and command-line execution
- `tests/`: automated regression tests with fixture HTML

## Installation

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Local execution

```bash
python -m scraper.scraper
```

Set a custom User-Agent if needed:

```bash
export CAER_USER_AGENT='CAER-Monitor/1.0 (+https://github.com/<repository>)'
python -m scraper.scraper
```

## Testing

```bash
pytest -q
```

## GitHub Actions

The workflow in `.github/workflows/caer-monitor.yml` checks out the repository, installs dependencies, runs the scraper, runs tests, checks whether data files changed, and commits back any updates.

The workflow schedule uses a best-effort cron expression because GitHub Actions is not a real-time scheduler. It is configured to run at minutes 0 and 29 of each hour (cron: "0,29 * * * *"). This is a best-effort schedule — actual execution times may vary due to runner availability, queueing, or other GitHub Actions scheduling constraints. The scraper itself is scheduler-agnostic so it can be moved to a more precise timer later if needed.

## Polling limitations

GitHub Actions cron jobs are best-effort and subject to runner availability, queue delay, and repository restrictions. The project is designed so the scraper itself is scheduler-agnostic, meaning the polling mechanism can later move to another scheduler without rewriting the parser or state logic.

## Data schema

The canonical archive is stored in `data/caer_messages.json` as a list of message records with fields including:

- `message_id`
- `facility`
- `posted_datetime`
- `retrieved_datetime`
- `message_text`
- `normalized_message_text`
- `content_hash`
- `category`
- `status`
- `previously_seen`
- `first_seen`
- `last_seen`
- `source_url`
- `versions`

The `versions` list preserves audit history for each message.

## Duplicate detection

Messages are identified deterministically from the tuple of facility, posted timestamp, and normalized message text. A SHA-256 message identifier is generated from that canonical representation. The `message_id` indicates the underlying message; the `content_hash` indicates the exact message text at a particular retrieval.

Possible states include:

- `new`: never seen before
- `previous message still posted`: same message remains active with unchanged content
- `updated`: message was observed before but changed
- `cleared`: message previously active is no longer present on the live feed after a successful retrieval and parse

## Category definitions

The controlled vocabulary is intentionally explicit and easy to extend. Categories include:

- Emergency Response
- Facilities
- Flaring
- Incidents
- Noise
- Odors
- Pipelines
- Rail Cars
- Smoke
- Tanker Trucks
- Training/Drills

Rules live in `scraper/classifier.py` and can be modified without changing the parsing logic.

## Responsible scraping behavior

This project uses a single normal HTTP GET call per source per polling cycle with timeouts, retry with backoff, and a descriptive User-Agent. It does not use browser automation, proxies, anti-bot evasion, CAPTCHA bypass, or fingerprint spoofing. The code will log and back off when a site appears to be rate-limiting or denying automated access.

## Troubleshooting

- Verify network access to the public CAER feed
- Confirm that the `CAER_USER_AGENT` is set appropriately
- Ensure `requests` and `beautifulsoup4` are installed
- Inspect logs emitted by the scraper for HTTP status or parse failures
- Re-run tests with `pytest -q` if parsing or classification changes

## Changing the polling mechanism later

The scraper is implemented as a modular library; the scheduling layer is intentionally separate from the retrieval/parsing logic. A future scheduler could run the same scraper through GitHub Actions, cron, a VM, or a platform task runner without changing the CAER parsing code.
