"""Fetch median gross monthly wages by large region from the BFS PxWeb API.

Source: Swiss Earnings Structure Survey (LSE), table px-x-0304010000_201.
The LSE is run every two years and published only for the 7 BFS large regions
(Grossregionen), not for single cantons.

Two queries are made:
  1. median, P25 and P75 for all employees (total over sectors, positions, sexes)
  2. median split by sex

Run from the repository root:  python src/income/fetch_bfs_wages.py
"""

import json
from pathlib import Path

import pandas as pd
import requests

TABLE = "px-x-0304010000_201"
URL = f"https://www.pxweb.bfs.admin.ch/api/v1/de/{TABLE}/{TABLE}.px"

RAW_DIR = Path("data/raw/bfs")
OUT_FILE = Path("data/processed/wages_grossregion_year.csv")

TOTAL = "-1"  # PxWeb code for "... - Total"
STAT_CODES = {"1": "median", "3": "p25", "4": "p75"}
SEX_CODES = {"-1": "total", "1": "female", "2": "male"}


def item(code: str, values: list[str]) -> dict:
    return {"code": code, "selection": {"filter": "item", "values": values}}


def run_query(filters: list[dict]) -> dict:
    response = requests.post(URL, json={"query": filters, "response": {"format": "json"}}, timeout=60)
    response.raise_for_status()
    return response.json()


def to_frame(result: dict, meta: dict) -> pd.DataFrame:
    """Flatten a PxWeb JSON answer into one row per data point."""
    codes = [c["code"] for c in result["columns"] if c["type"] != "c"]
    rows = [dict(zip(codes, d["key"])) | {"value": d["values"][0]} for d in result["data"]]
    df = pd.DataFrame(rows)

    region_names = dict(zip(meta["Grossregion"]["values"], meta["Grossregion"]["valueTexts"]))
    return pd.DataFrame({
        "year": df["Jahr"].astype(int),
        "grossregion_code": df["Grossregion"].astype(int),
        "grossregion": df["Grossregion"].map(region_names),
        "sex": df["Geschlecht"].map(SEX_CODES),
        "stat": df["Zentralwert und andere Perzentile"].map(STAT_CODES),
        # Suppressed cells are returned as '...' or similar -> NaN
        "monthly_gross_wage_chf": pd.to_numeric(df["value"], errors="coerce"),
    })


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    meta = {v["code"]: v for v in requests.get(URL, timeout=60).json()["variables"]}

    queries = {
        "total": [
            item("Wirtschaftsabteilung", [TOTAL]),
            item("Berufliche Stellung", [TOTAL]),
            item("Geschlecht", [TOTAL]),
            item("Zentralwert und andere Perzentile", list(STAT_CODES)),
        ],
        "by_sex": [
            item("Wirtschaftsabteilung", [TOTAL]),
            item("Berufliche Stellung", [TOTAL]),
            item("Geschlecht", ["1", "2"]),
            item("Zentralwert und andere Perzentile", ["1"]),
        ],
    }

    frames = []
    for name, filters in queries.items():
        result = run_query(filters)
        (RAW_DIR / f"lse_{TABLE}_{name}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))
        frame = to_frame(result, meta)
        print(f"Query '{name}': {len(frame)} rows")
        frames.append(frame)

    wages = pd.concat(frames, ignore_index=True).sort_values(["year", "grossregion_code", "sex", "stat"])
    wages.to_csv(OUT_FILE, index=False)
    print(f"Saved {len(wages)} rows to {OUT_FILE}")


if __name__ == "__main__":
    main()
