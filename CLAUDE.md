# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (copy and fill in)
cp .env.exemple .env
# Edit .env: set SCRAPING_API_KEY and optionally SCRAPING_RATE_LIMIT_MS
```

## Running scripts

All scripts write JSON to stdout. Redirect to a file if persistence is needed.

```bash
# LinkedIn publications scraper
python scrapingdog-linkedIn.py --user-guid <guid> --profile-url <linkedin_url>

# Google Scholar scraper
python scrapingdog-academico.py --user-guid <guid> --author "Nome Completo"

# Lattes CV scraper
python lattes.py --user-guid <guid> --url "https://lattes.cnpq.br/..."
```

No test suite or linter is configured.

## Architecture

Three production scripts, each producing the same JSON contract:

```json
{
  "user_guid": "<passed-in arg>",
  "source": "linkedin | google_scholar | lattes",
  "items": [
    { "title": "", "body": "", "published_at": "", "source_url": "" }
  ]
}
```

- `scrapingdog-linkedIn.py`: calls `api.scrapingdog.com/profile` with `premium: true`, filters publications matching `(?i)artigo|article`.
- `scrapingdog-academico.py`: calls `api.scrapingdog.com/google_scholar` with `author:"name"` syntax.
- `lattes.py`: uses Selenium (headless Chrome) + BeautifulSoup to scrape Lattes (lattes.cnpq.br); waits on `#identificacao` to confirm the CV page loaded before parsing.

## Key conventions

- Rate limiting is controlled by `SCRAPING_RATE_LIMIT_MS` env var (default 1000 ms). No hardcoded sleeps.
- `SCRAPING_API_KEY` is required for the two ScrapingDog scripts; loaded from `.env` via `python-dotenv`.
- Errors are printed to stderr; the script still outputs a valid JSON result with an empty `items` array on failure.
- ScrapingDog LinkedIn calls use `premium: true` to bypass LinkedIn's bot detection.
