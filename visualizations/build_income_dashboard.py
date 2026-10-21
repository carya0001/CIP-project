"""Build the interactive income dashboard (visualizations/income_dashboard.html).

Reads the three processed income tables, packs them into JSON and inserts that
JSON into dashboard_template.html. The result is a single HTML file that opens
in any browser without a server (Plotly.js is loaded from a CDN).

Run from the repository root:
    python visualizations/build_income_dashboard.py
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "dashboard_template.html"
OUTPUT = HERE / "income_dashboard.html"

# Position of each canton on a simplified tile map of Switzerland: (column, row).
# Roughly follows the real geography: Basel top left, Geneva bottom left, Ticino bottom.
TILE_GRID = {
    "BS": (2, 0), "SH": (4, 0),
    "JU": (1, 1), "BL": (2, 1), "AG": (3, 1), "ZH": (4, 1), "TG": (5, 1),
    "NE": (1, 2), "SO": (2, 2), "LU": (3, 2), "ZG": (4, 2), "SG": (5, 2), "AR": (6, 2),
    "FR": (1, 3), "BE": (2, 3), "OW": (3, 3), "SZ": (4, 3), "GL": (5, 3), "AI": (6, 3),
    "VD": (1, 4), "VS": (2, 4), "NW": (3, 4), "UR": (4, 4), "GR": (5, 4),
    "GE": (0, 5), "TI": (4, 5),
}


def none_if_nan(value):
    """JSON has no NaN, so missing values become null."""
    return None if pd.isna(value) else value


def records(df, columns):
    """Turn selected columns into a list of short dicts (renamed keys keep the HTML small)."""
    out = []
    for row in df[list(columns)].itertuples(index=False):
        out.append({new: none_if_nan(v) for new, v in zip(columns.values(), row)})
    return out


def main():
    income = pd.read_csv(PROCESSED / "income_canton_year.csv")
    household = pd.read_csv(PROCESSED / "income_canton_year_household.csv")
    wages = pd.read_csv(PROCESSED / "wages_grossregion_year.csv")

    missing = set(income["canton_abbr"]) ^ set(TILE_GRID)
    if missing:
        raise SystemExit(f"Tile grid and income data disagree on cantons: {missing}")

    data = {
        "income": records(income, {
            "year": "year", "canton_abbr": "c", "canton_name": "name",
            "grossregion_code": "rc", "grossregion": "region", "stpf": "stpf",
            "median_steink": "median", "mean_steink": "mean", "gini_steink": "gini",
            "p25": "p25", "p75": "p75", "median_reink": "median_net",
            "median_steink_index_2012": "idx", "median_steink_yoy_pct": "yoy",
            "yoy_outlier": "outlier", "annual_gross_wage_region": "wage",
            "wage_interpolated": "wage_interp", "taxable_income_to_wage_ratio": "ratio",
        }),
        "household": records(household, {
            "year": "year", "canton_abbr": "c", "household": "hh",
            "stpf": "stpf", "median_steink": "median", "mean_steink": "mean",
        }),
        "wages": records(wages, {
            "year": "year", "grossregion_code": "rc", "grossregion": "region",
            "sex": "sex", "stat": "stat", "monthly_gross_wage_chf": "chf",
        }),
        "tiles": {c: list(pos) for c, pos in TILE_GRID.items()},
    }

    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html = TEMPLATE.read_text(encoding="utf-8").replace("__DASHBOARD_DATA__", payload)
    OUTPUT.write_text(html, encoding="utf-8")

    print(f"[data] income rows: {len(income)}  "
          f"({income['canton_abbr'].nunique()} cantons, {income['year'].min()}-{income['year'].max()})")
    print(f"[data] household rows: {len(household)}  wage rows: {len(wages)}")
    print(f"[done] wrote {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
