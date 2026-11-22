# Crash Flight Pro

Windows desktop historical-round analyzer with an embedded browser. **This is not a future-round predictor.** Independent random outcomes cannot be known from past results.

## Current features
- Embedded web view for manually opening an HTTPS website; some sites may refuse embedded browsers
- CSV import and export of completed multipliers
- Manual entry of completed rounds
- Local JSON persistence under the Windows application data directory
- Historical median, last-30 median, frequency below/above 2x
- Walk-forward error evaluation of a rolling median against a constant historical baseline
- Confirmation before clearing local history
- No browser scraping, betting automation, or credential storage

## Run on Windows
Install Python 3.11 or newer, then in PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

## Test

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Import file
```csv
multiplier
1.24
2.50
1.01
```

CSV imports append rows. Identical multipliers are retained because repeated numerical results may represent different rounds. Do not import the same CSV twice unless you want duplicates. There is no automatic connection to 1xBet game data yet.

**Security:** Never publish credentials, recovery codes, browser cookies, or GitHub tokens. Browser website compatibility and Windows packaging have not been verified on a Windows machine.

## Offline message structure inspection (experimental)

Use only messages you are authorized to export. Remove session identifiers, cookies, tokens, account details and other private fields **before** creating or sharing the file. The tool does not connect to 1xBet or capture traffic.

Example `messages.jsonl`:

```jsonl
{"timestamp":"2026-11-22T12:00:00.000Z","direction":"received","payload":{"event":"round_start","round_id":"example"}}
{"timestamp":"2026-11-22T12:00:07.000Z","direction":"received","payload":{"event":"round_end","multiplier":2.4}}
```

These are illustrative message names, **not confirmed 1xBet protocol fields**. Run:

```powershell
py message_inspector.py messages.jsonl --output message_report.json
```

The report summarizes payload shapes and timestamps; it does not infer future crash outcomes. Do not publish raw network captures, even if the report itself masks sensitive-looking field names.
