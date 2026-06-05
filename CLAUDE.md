# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API key (copy and fill in)
cp .env.exemple .env
# Edit .env and set SCRAPING_API_KEY="your_key_here"
```

## Running scripts

```bash
# LinkedIn profile scraper (edit the `perfis` list in the script first)
python scrapingdog-linkedIn.py

# Google Scholar scraper (edit `termos_de_pesquisa` list first)
python scrapingdog-academico.py

# Prototype/test scripts
python teste-prodotipos-scraping/main.py        # DuckDuckGo search (site-specific)
python teste-prodotipos-scraping/sem_site_especifico.py  # DuckDuckGo (open search)
python teste-prodotipos-scraping/scholar.py     # scholarly library direct access
python teste-prodotipos-scraping/web-scraping.py  # Selenium scraper for Lattes
python teste-prodotipos-scraping/filtroJson.py  # Post-process existing LinkedIn JSON results
```

No test suite or linter is configured.

## Architecture

The project has two layers:

**Production scripts (root)** — use the [ScrapingDog](https://www.scrapingdog.com/) paid API (`SCRAPING_API_KEY`) to collect structured data:
- `scrapingdog-linkedIn.py`: fetches a LinkedIn profile via `api.scrapingdog.com/profile`, then filters the `publications` array for entries matching the regex `artigo|article`, and writes two JSON outputs per profile — full data to `resultados_linkedin/` and filtered data to `resultados_linkedin_filtrados/`.
- `scrapingdog-academico.py`: queries `api.scrapingdog.com/google_scholar` with `author:"name"` syntax and writes results to `resultados_academico/`.

Both root scripts iterate over a hardcoded list (`perfis` / `termos_de_pesquisa`) and include `time.sleep()` rate limiting between requests.

**Prototype scripts (`teste-prodotipos-scraping/`)** — exploratory approaches without a paid API:
- `main.py` / `sem_site_especifico.py`: use the `ddgs` library to run DuckDuckGo searches, optionally restricted to specific sites (e.g., `scholar.google.com`).
- `scholar.py`: uses the `scholarly` library to query Google Scholar directly.
- `web-scraping.py`: uses Selenium + ChromeDriver + BeautifulSoup to scrape Lattes (Brazilian academic CV platform at lattes.cnpq.br), which requires JavaScript rendering and handles CAPTCHA waits manually.
- `filtroJson.py`: standalone post-processor that reads from `resultados_linkedin/` and re-applies the article filter — useful for reprocessing previously saved raw data without re-hitting the API.
- `TesteZenRows.py`: prototype for ZenRows API with JS rendering and CAPTCHA solving enabled.

## Key conventions

- Output directories (`resultados_linkedin/`, `resultados_linkedin_filtrados/`, `resultados_academico/`) are created at runtime if missing; they are gitignored.
- The article filter regex `(?i)artigo|article` is defined at module level for efficiency and reused across multiple scripts.
- The `perfis` list in `scrapingdog-linkedIn.py` uses the format `['display_name', 'linkedin_profile_url']`; the display name becomes the output filename.
- ScrapingDog LinkedIn calls use `premium: true` to bypass LinkedIn's bot detection.
