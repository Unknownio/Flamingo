# Flamingo Exposure Scanner

A lightweight Python OSINT utility that scans major people-search/data-broker websites and checks public email breach exposure to produce a consolidated personal exposure report.

## Overview

Flamingo helps you quickly assess how visible a person’s information is across:

- Public people-search and data-broker domains (30 sources)
- Public breach records via Have I Been Pwned (HIBP)

It generates a JSON report with discovered listings, breach summary, and a computed exposure score (0–100).

## Key Features

- Scans 30 common broker/directories in controlled batches
- Retries on temporary search rate limits
- Applies pacing between scan batches to reduce throttling
- Checks email breach status from HIBP endpoint
- Calculates a simple weighted exposure score and threat label
- Exports full results to `exposure_report.json`

## Tech Stack

- Python 3.9+
- [`ddgs`](https://pypi.org/project/ddgs/) for search queries
- [`requests`](https://pypi.org/project/requests/) for HTTP calls

## Installation

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install ddgs requests
```

## Usage

Run the scanner:

```bash
python /home/runner/work/Flamingo/Flamingo/exposure_scanner.py
```

You will be prompted for:

- Full name
- City/state or country (optional)
- Primary email

## Output

After execution, the script prints a terminal summary and writes:

- `exposure_report.json` — full structured report including:
  - Target details
  - Exposure score and status
  - Broker findings and listing URLs
  - Breach lookup summary

## Scoring Model (Current)

- Broker findings: `5 points` per hit (capped at `70`)
- Breaches: `8 points` per breach (capped at `30`)
- Location boost: `+10%` when location is provided and broker hits exist

Status labels:

- `0`: **RAW**
- `1–29`: **RARE**
- `30–59`: **MEDIUM WELL**
- `60+`: **FULLY COOKED**

## Notes & Limitations

- Search and third-party source availability may vary over time.
- HIBP v3 typically requires an API key for full breach details; unauthenticated requests may return limited data.
- This tool is informational and should not be treated as legal/compliance advice.

## Responsible Use

Use this project ethically and only for authorized personal security/privacy assessment purposes.

## License

No license file is currently included. Add a `LICENSE` file if you want to define usage rights.
