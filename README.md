# Flamingo Exposure Scanner

Flamingo is a Python-based OSINT utility that helps assess publicly visible personal exposure by scanning common data broker sites and checking email breach history.

## Features

- Scans **30 major people-search and broker domains** in managed batches.
- Uses retry logic and pacing delays to reduce search-rate issues.
- Checks email breach exposure via the **XposedOrNot** public API.
- Calculates a combined exposure score (`0-100`) with a human-readable risk label.
- Exports full scan results to `exposure_report.json`.

## Requirements

- Python 3.8+
- Internet access
- Python packages:
  - `requests`
  - `ddgs`

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install requests ddgs
```

## Usage

Run the scanner:

```bash
python exposure_scanner.py
```

You will be prompted for:

1. Full name
2. Location (optional)
3. Primary email

## Output

After execution, the script:

- Prints a summary report to the terminal
- Saves detailed structured output to:

```text
exposure_report.json
```

The JSON report includes:

- Target inputs
- Exposure score and status
- Matching broker listings
- Breach count and breach source details

## Notes & Disclaimer

- This tool depends on third-party search and breach APIs, which may change behavior or limit requests.
- Results are best-effort and not guaranteed to be complete.
- Use responsibly and only for lawful, authorized personal security assessment.
