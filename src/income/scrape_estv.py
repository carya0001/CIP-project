"""Scrape the ESTV 'Statistische Kennzahlen' files (taxable income per canton).

The ESTV overview page links one XLSX per tax year. The download URLs contain a
random hash, so they are collected from the page with BeautifulSoup instead of
being hard-coded. We use the series "natürliche Personen mit und ohne Belastung"
(file names 'kennzahlen-ohne-<year>'), which covers all taxpayers.

Run from the repository root:  python src/income/scrape_estv.py
"""

import csv
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.estv.admin.ch"
OVERVIEW_URL = f"{BASE_URL}/de/statistiken-zur-direkten-bundessteuer"
USER_AGENT = "CIP-HS26-Group105 student project (HSLU)"

YEARS = range(2012, 2023)  # tax years 2012-2022
FILE_PATTERN = re.compile(r"statistik-dbst-np-kennzahlen-ohne-(\d{4})(?:-de)?\.xlsx$")
DELAY_SECONDS = 1.5

RAW_DIR = Path("data/raw/estv")
MANIFEST = RAW_DIR / "manifest.csv"


def check_robots(session: requests.Session, url: str) -> None:
    """Stop if robots.txt disallows the URL for our user agent.

    robots.txt is fetched with our own session: the server resets connections
    from urllib's default user agent, so RobotFileParser.read() would fail.
    """
    response = session.get(urljoin(BASE_URL, "/robots.txt"), timeout=30)
    response.raise_for_status()
    robots = RobotFileParser()
    robots.parse(response.text.splitlines())
    if not robots.can_fetch(USER_AGENT, url):
        raise PermissionError(f"robots.txt disallows {url}")


def find_file_links(session: requests.Session) -> dict[int, str]:
    """Return {year: download URL} for the Kennzahlen files of the wanted years."""
    response = session.get(OVERVIEW_URL, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    links = {}
    for a in soup.find_all("a", href=True):
        match = FILE_PATTERN.search(a["href"])
        if match and int(match.group(1)) in YEARS:
            links[int(match.group(1))] = urljoin(BASE_URL, a["href"])
    return dict(sorted(links.items()))


def download(session: requests.Session, url: str, target: Path) -> int:
    response = session.get(url, timeout=60)
    response.raise_for_status()
    target.write_bytes(response.content)
    return len(response.content)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    check_robots(session, OVERVIEW_URL)

    links = find_file_links(session)
    missing = sorted(set(YEARS) - set(links))
    print(f"Found {len(links)} files on the overview page.")
    if missing:
        print(f"WARNING: no file found for years {missing}")

    # Keep the retrieval dates of earlier runs for files we don't download again.
    manifest = {}
    if MANIFEST.exists():
        with MANIFEST.open(newline="") as f:
            manifest = {int(row["year"]): row for row in csv.DictReader(f)}

    for year, url in links.items():
        target = RAW_DIR / f"kennzahlen_ohne_{year}.xlsx"
        if target.exists() and year in manifest:
            print(f"{year}: already downloaded, skipping")
            continue
        size = download(session, url, target)
        manifest[year] = {
            "year": year,
            "url": url,
            "file": target.name,
            "bytes": size,
            "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        print(f"{year}: saved {target} ({size / 1024:.0f} kB)")
        time.sleep(DELAY_SECONDS)

    with MANIFEST.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["year", "url", "file", "bytes", "retrieved_at"])
        writer.writeheader()
        writer.writerows(manifest[y] for y in sorted(manifest))
    print(f"Manifest written to {MANIFEST}")


if __name__ == "__main__":
    main()
