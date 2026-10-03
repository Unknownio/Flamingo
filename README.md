# Flamingo Exposure Scanner

Flamingo is a Python OSINT utility that helps assess publicly visible personal exposure across data brokers, Gravatar, and email breach sources.

## Project status

This project is currently closed due to limited support for cities outside the USA. It is best suited for people in the USA, and development will continue when I have more time to find a workaround.

## Features

- Scans **30 people-search and broker domains** in rate-limited batches.
- Retries data broker lookups when search requests are limited.
- Checks for public **Gravatar** profile/avatar exposure from an email hash.
- Checks known email breach exposure through the **XposedOrNot** API.
- Calculates an exposure score (`0-100`) and risk status.
- Exports full structured results to `exposure_report.json`.

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

### CLI scanner

```bash
python exposure_scanner.py
```

### GUI app

```bash
python app.py
```

Prompts:

1. Full name
2. Location (optional)
3. Primary email

At least one of **full name** or **email** is required.

## What the scan checks

- **Data broker exposure:** Finds public listing matches and includes opt-out links.
- **Gravatar footprint:** Detects public profile/avatar presence tied to the email hash.
- **Email breach exposure:** Reports known breach source names from XposedOrNot.

## Output

After execution, Flamingo:

- Prints a terminal summary (score, threat level, findings count)
- Saves detailed results to:

```text
exposure_report.json
```

The JSON report includes:

- Target inputs (`name`, `location`, `email`)
- `exposure_score` and status
- Data broker findings and per-result opt-out URLs
- Gravatar footprint details
- Breach count and breach identifiers

## Notes & disclaimer

- Results are best-effort and rely on third-party services that may throttle, fail, or change behavior.
- No API keys are required for current integrations, but remote service policies can change.
- Use only for lawful and authorized personal security assessment.
