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
