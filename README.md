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

## Google Sheets reporting via Apps Script

This project keeps GitHub as the authoritative source of truth. The Python scraper writes the canonical archive to `data/caer_messages.json` and related files. Google Sheets is a reporting layer only.

The spreadsheet that receives the output is:

`1l9dbT-NsvKrPSby63Kko6GmO3fgPfKXQGTl4PR1qfNo`

The Google Sheet is populated by a Google Apps Script bound to the spreadsheet itself. The script reads the processed CAER JSON from GitHub's raw URL, rebuilds the reporting sheets, and updates them without any Google Cloud service account or billing setup.

### What the Apps Script does

- Reads the current processed CAER dataset from the GitHub raw file
- Uses the already-classified Python data; no second classification system is created in Apps Script
- Updates these sheets:
  - `Current Messages`
  - `New Messages`
  - `Still Posted`
  - `Cleared Messages`
  - `App vs Website`
  - `Data Dictionary`
- Writes the actual message content and a dedicated filterable `Tags` column
- Leaves existing spreadsheet data intact if the GitHub source cannot be reached
- Is idempotent: refreshing with the same dataset does not create duplicate rows

### Apps Script setup

1. Open the target Google Sheet:
   `https://docs.google.com/spreadsheets/d/1l9dbT-NsvKrPSby63Kko6GmO3fgPfKXQGTl4PR1qfNo/edit`
2. In the sheet, open Extensions → Apps Script.
3. Replace the default script with the contents of `google-apps-script/Code.gs`.
4. Save the project.
5. In the Apps Script editor, click Run → `refreshData` once to test it.
6. If prompted, allow the script to access the sheet.
7. From the Apps Script editor, open Triggers → Add Trigger.
8. Configure:
   - Function to run: `refreshData`
   - Event source: `Time-driven`
   - Type: `Every 18 hours`
9. Optionally, add a custom menu in the sheet by leaving `onOpen()` enabled; a CAER menu will appear with a `Refresh Data` action.

The Apps Script is intentionally only a reporting layer. GitHub Actions remains responsible for collection, normalization, deduplication, classification, and historical archiving.

### Raw GitHub source URL

The script reads the canonical processed JSON from:

`https://raw.githubusercontent.com/Stats-w-Sass/CAER-Monitor/main/data/caer_messages.json`

This is the stable source that should be used for the Google Sheet refresh.

### Sheet layout

The primary `Current Messages` tab contains the rows users actually monitor. Required columns are:

- Status
- Facility
- Posted Date
- Posted Time
- Tags
- Message
- First Seen
- Last Seen
- Source
- Previously Seen
- Message ID

The `Tags` column is a dedicated, directly filterable column. Values are taken from the Python classifier's controlled vocabulary and are written as consistent semicolon-delimited text, for example:

`Flaring; Smoke; Noise`

Other tabs include the same message dataset in filtered views:

- `New Messages`
- `Still Posted`
- `Cleared Messages`
- `App vs Website`
- `Data Dictionary`

### Important constraints

- No Google Cloud service account is required.
- No Google Cloud billing setup is required.
- No Google credentials are stored in GitHub.
- No personal Google credentials are required in GitHub Actions.
- If the GitHub dataset is unavailable, Apps Script leaves the sheet content as-is and reports the failure.
- Re-running `refreshData` with the same GitHub dataset does not create duplicates.

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
