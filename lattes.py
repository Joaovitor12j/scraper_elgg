import argparse
import json
import os
import re
import sys
import time

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

RATE_LIMIT_S = int(os.environ.get("SCRAPING_RATE_LIMIT_MS", 1000)) / 1000
YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")

# Lattes section headings that contain article publications
ARTICLE_SECTIONS = re.compile(r"artigo|publicac", re.IGNORECASE)


def build_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def parse_publication(element, fallback_url: str) -> dict:
    title_tag = element.find("b") or element.find("strong")
    title = title_tag.get_text(strip=True) if title_tag else ""
    body = element.get_text(separator=" ", strip=True)
    year_match = YEAR_PATTERN.search(body)
    return {
        "title": title,
        "body": body,
        "published_at": year_match.group() if year_match else "",
        "source_url": fallback_url,
    }


def scrape_lattes(url: str) -> list:
    driver = build_driver()
    try:
        driver.get(url)
        # Wait for the CV identity section to confirm the CV loaded (not a CAPTCHA page)
        WebDriverWait(driver, 40).until(
            EC.presence_of_element_located((By.ID, "identificacao"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")
    finally:
        driver.quit()

    items = []

    # Primary: sections annotated with data-cv-group (Vue-rendered Lattes pages)
    for section in soup.select("div[data-cv-group]"):
        if not ARTICLE_SECTIONS.search(section.get("data-cv-group", "")):
            continue
        for pub in section.select("div.cita-artigo, div.artigo-completo, li"):
            items.append(parse_publication(pub, url))

    # Fallback: common static Lattes page selectors
    if not items:
        for pub in soup.select("div.artigo, div.producao-bibliografica li, div.list-article"):
            items.append(parse_publication(pub, url))

    return items


def main():
    parser = argparse.ArgumentParser(description="Lattes CV scraper (Selenium + BeautifulSoup)")
    parser.add_argument("--user-guid", required=True, help="User identifier passed through to output")
    parser.add_argument("--url", required=True, help="Full Lattes CV URL (lattes.cnpq.br/...)")
    args = parser.parse_args()

    time.sleep(RATE_LIMIT_S)
    try:
        items = scrape_lattes(args.url)
    except Exception as e:
        print(f"ERRO: {e}", file=sys.stderr)
        items = []

    result = {
        "user_guid": args.user_guid,
        "source": "lattes",
        "items": items,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
