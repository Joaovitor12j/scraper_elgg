import argparse
import json
import os
import re
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

ARTICLE_PATTERN = re.compile(r"(?i)artigo|article")
RATE_LIMIT_S = int(os.environ.get("SCRAPING_RATE_LIMIT_MS", 1000)) / 1000

def fetch_profile(profile_url: str) -> list | None:
    api_key = os.environ.get("SCRAPING_API_KEY")
    if not api_key:
        print("ERRO: SCRAPING_API_KEY não configurada.", file=sys.stderr)
        return None
    try:
        response = requests.get(
            "https://api.scrapingdog.com/profile",
            params={"api_key": api_key, "type": "profile", "id": profile_url, "premium": "true"},
            timeout=45,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return None

def map_to_items(raw: list) -> list:
    if not raw or not isinstance(raw, list) or "publications" not in raw[0]:
        return []

    items = []
    for pub in raw[0]["publications"]:
        if not any(isinstance(v, str) and ARTICLE_PATTERN.search(v) for v in pub.values()):
            continue
        items.append({
            "title": pub.get("title", ""),
            "body": pub.get("description", ""),
            "published_at": pub.get("date", ""),
            "source_url": pub.get("url", ""),
        })
    return items

def main():
    parser = argparse.ArgumentParser(description="LinkedIn publications scraper via ScrapingDog")
    parser.add_argument("--user-guid", required=True, help="User identifier passed through to output")
    parser.add_argument("--profile-url", required=True, help="LinkedIn profile URL")
    args = parser.parse_args()

    if os.environ.get("MOCK_MODE") == "1":
        mock_items = [{"title": "Artigo Mock LinkedIn", "body": "Resumo mock de publicação", "published_at": "2024", "source_url": "https://linkedin.com/mock"}]
        print(json.dumps({"user_guid": args.user_guid, "source": "linkedin", "items": mock_items}, ensure_ascii=False))
        sys.exit(0)

    raw = fetch_profile(args.profile_url)
    time.sleep(RATE_LIMIT_S)

    result = {
        "user_guid": args.user_guid,
        "source": "linkedin",
        "items": map_to_items(raw) if raw else [],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
