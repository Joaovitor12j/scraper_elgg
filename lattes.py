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
ARTICLE_SECTIONS = re.compile(r"artigo|publica[cç]", re.IGNORECASE)


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
        for pub in section.select(
            "li.artigo-completo, li.artigo-aceito, "
            "div.cita-artigo, div.artigo-completo"
        ):
            items.append(parse_publication(pub, url))

    # Fallback: static Lattes page selectors (older layout)
    if not items:
        for pub in soup.select(
            "li.artigo-completo, li.artigo-aceito, "
            "div.artigo, div.producao-bibliografica li, div.list-article"
        ):
            items.append(parse_publication(pub, url))

    # Last-resort: any list item inside a section whose heading mentions artigo/publicação
    if not items:
        for heading in soup.find_all(re.compile(r"^h\d$"), string=ARTICLE_SECTIONS):
            container = heading.find_parent("div")
            if container:
                for pub in container.select("li"):
                    if pub.find("b") or pub.find("strong"):
                        items.append(parse_publication(pub, url))

    return items


def main():
    parser = argparse.ArgumentParser(description="Lattes CV scraper (Selenium + BeautifulSoup)")
    parser.add_argument("--user-guid", required=True, help="User identifier passed through to output")
    parser.add_argument("--url", required=True, help="Full Lattes CV URL (lattes.cnpq.br/...)")
    args = parser.parse_args()

    if os.environ.get("MOCK_MODE") == "1":
        mock_items = [{"title": "Artigo Mock Lattes", "body": "Resumo do artigo mock do Lattes", "published_at": "2022", "source_url": "https://lattes.cnpq.br/mock"}]
        print(json.dumps({"user_guid": args.user_guid, "source": "lattes", "items": mock_items}, ensure_ascii=False))
        sys.exit(0)

    try:
        items = scrape_lattes(args.url)
    except Exception as e:
        print(f"ERRO: {e}", file=sys.stderr)
        items = []
    time.sleep(RATE_LIMIT_S)

    result = {
        "user_guid": args.user_guid,
        "source": "lattes",
        "items": items,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
