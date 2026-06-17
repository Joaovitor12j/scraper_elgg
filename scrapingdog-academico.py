import argparse
import json
import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

RATE_LIMIT_S = int(os.environ.get("SCRAPING_RATE_LIMIT_MS", 1000)) / 1000


def fetch_author_id(author: str) -> str | None:
    api_key = os.environ.get("SCRAPING_API_KEY")
    if not api_key:
        print("ERRO: SCRAPING_API_KEY não configurada.", file=sys.stderr)
        return None
    try:
        response = requests.get(
            "https://api.scrapingdog.com/google_scholar/profiles",
            params={
                "api_key": api_key,
                "mauthors": author,
            },
            timeout=45,
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return None
    profiles = data.get("profiles") if isinstance(data, dict) else None
    if not profiles:
        return None
    return profiles[0].get("author_id")


def fetch_author_articles(author_id: str) -> dict | None:
    api_key = os.environ.get("SCRAPING_API_KEY")
    if not api_key:
        print("ERRO: SCRAPING_API_KEY não configurada.", file=sys.stderr)
        return None
    try:
        response = requests.get(
            "https://api.scrapingdog.com/google_scholar/author",
            params={
                "api_key": api_key,
                "author_id": author_id,
            },
            timeout=45,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return None


def map_to_items(raw: dict) -> list:
    if not isinstance(raw, dict):
        return []
    articles = sorted(
        raw.get("articles", []),
        key=lambda a: a.get("year") or "",
        reverse=True,
    )[:5]
    items = []
    for article in articles:
        items.append({
            "title": article.get("title", ""),
            "body": article.get("publication", ""),
            "published_at": str(article.get("year") or ""),
            "source_url": article.get("link", ""),
        })
    return items


def main():
    parser = argparse.ArgumentParser(description="Google Scholar scraper via ScrapingDog")
    parser.add_argument("--user-guid", required=True, help="User identifier passed through to output")
    parser.add_argument("--author", required=True, help="Author name to search (e.g. 'Fulano de Tal')")
    args = parser.parse_args()

    if os.environ.get("MOCK_MODE") == "1":
        mock_items = [{"title": "Artigo Mock Scholar", "body": "Abstract mock do artigo acadêmico", "published_at": "2023", "source_url": "https://scholar.google.com/mock"}]
        print(json.dumps({"user_guid": args.user_guid, "source": "google_scholar", "items": mock_items}, ensure_ascii=False))
        sys.exit(0)

    author_id = fetch_author_id(args.author)
    time.sleep(RATE_LIMIT_S)

    raw = fetch_author_articles(author_id) if author_id else None
    time.sleep(RATE_LIMIT_S)

    result = {
        "user_guid": args.user_guid,
        "source": "google_scholar",
        "items": map_to_items(raw) if raw else [],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
