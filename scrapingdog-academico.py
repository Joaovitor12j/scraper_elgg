import argparse
import json
import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

RATE_LIMIT_S = int(os.environ.get("SCRAPING_RATE_LIMIT_MS", 1000)) / 1000


def fetch_scholar(author: str) -> dict | None:
    api_key = os.environ.get("SCRAPING_API_KEY")
    if not api_key:
        print("ERRO: SCRAPING_API_KEY não configurada.", file=sys.stderr)
        return None
    try:
        response = requests.get(
            "https://api.scrapingdog.com/google_scholar",
            params={
                "api_key": api_key,
                "query": f'author:"{author}"',
                "language": "PT-BR",
                "page": 0,
                "results": 30,
            },
            timeout=45,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return None


def map_to_items(raw: dict) -> list:
    items = []
    for result in raw.get("search_results", []):
        items.append({
            "title": result.get("title", ""),
            "body": result.get("snippet", ""),
            "published_at": str(result.get("year", "")),
            "source_url": result.get("link", ""),
        })
    return items


def main():
    parser = argparse.ArgumentParser(description="Google Scholar scraper via ScrapingDog")
    parser.add_argument("--user-guid", required=True, help="User identifier passed through to output")
    parser.add_argument("--author", required=True, help="Author name to search (e.g. 'Fulano de Tal')")
    args = parser.parse_args()

    raw = fetch_scholar(args.author)
    time.sleep(RATE_LIMIT_S)

    result = {
        "user_guid": args.user_guid,
        "source": "google_scholar",
        "items": map_to_items(raw) if raw else [],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
