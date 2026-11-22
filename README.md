# Crash Flight Pro

Windows desktop application with an embedded browser and a historical Crash-round analyzer.

## Features
- Embedded browser for navigating to a game website manually (website compatibility is not guaranteed)
- CSV import of historical multipliers
- Median and frequency statistics, including the last 30 rounds
- No betting automation and no claim to predict the next round

## Installation (Windows)
1. Install Python 3.11+.
2. Open PowerShell in this repository.
3. Run `py -m venv .venv` and `.venv\Scripts\Activate.ps1`.
4. Run `pip install -r requirements.txt`.
5. Run `python main.py`.

## CSV format
```csv
multiplier
1.24
2.50
1.01
```

**Security:** Never put your 1xBet credentials, authentication codes, or API tokens into the repository. The application does not extract hidden game outcomes. Historical rounds cannot reliably reveal future outcomes of an independent random game.
