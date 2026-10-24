"""Build the premiums-vs-income dashboard (visualizations/affordability_dashboard.html).

Merges the ESTV income table with the priminfo premium tables (with and without
accident cover) per canton and year, computes the premium burden and inserts the
data as JSON into affordability_template.html.

Burden = annual premium (adult, standard model, CHF 300 deductible) / median taxable income.

Run from the repository root:
    python visualizations/build_affordability_dashboard.py
"""
import json
from pathlib import Path

import pandas as pd

from build_income_dashboard import ROOT, TILE_GRID, records

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "affordability_template.html"
OUTPUT = HERE / "affordability_dashboard.html"

PROCESSED = ROOT / "data" / "processed"
INCOME_FILE = PROCESSED / "income_canton_year.csv"
PREMIUM_NAMES = {
    "with": "priminfo_premiums_per_canton.csv",
    "without": "priminfo_premiums_per_canton_ohne_unfall.csv",
}


def find_premium_file(name):
    path = PROCESSED / name
    if not path.exists():
        raise SystemExit(f"Premium file {name} not found in {PROCESSED}")
    return path


def main():
    income = pd.read_csv(INCOME_FILE)
    panel = income[["year", "canton_abbr", "canton_name", "grossregion", "stpf", "median_steink"]].rename(
        columns={"canton_abbr": "canton"})

    for variant, name in PREMIUM_NAMES.items():
        path = find_premium_file(name)
        premium = pd.read_csv(path)
        premium["year"] = premium["year"].astype(int)
        premium = premium[["year", "canton", "premium_month", "premium_year"]].rename(columns={
            "premium_month": f"prem_m_{variant}", "premium_year": f"prem_y_{variant}"})
        before = len(panel)
        panel = panel.merge(premium, on=["year", "canton"], how="inner", validate="one_to_one")
        if len(panel) != before:
            raise SystemExit(f"{name}: only {len(panel)} of {before} canton-years matched the income data")
        print(f"[data] premiums {variant} accident cover: {path.relative_to(ROOT)}")

    if panel.isna().any().any():
        raise SystemExit("Missing values after the merge:\n" + str(panel[panel.isna().any(axis=1)]))

    for variant in PREMIUM_NAMES:
        panel[f"burden_{variant}"] = panel[f"prem_y_{variant}"] / panel["median_steink"] * 100

    data = {
        "panel": records(panel, {
            "year": "year", "canton": "c", "canton_name": "name", "grossregion": "region", "stpf": "stpf",
            "median_steink": "income", "prem_m_with": "pm_with", "prem_y_with": "py_with",
            "prem_m_without": "pm_without", "prem_y_without": "py_without",
            "burden_with": "b_with", "burden_without": "b_without",
        }),
        "tiles": {c: list(pos) for c, pos in TILE_GRID.items()},
    }

    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html = TEMPLATE.read_text(encoding="utf-8").replace("__DASHBOARD_DATA__", payload)
    OUTPUT.write_text(html, encoding="utf-8")

    typical = panel.groupby("year")["burden_with"].median()
    print(f"[data] merged canton-years: {len(panel)} ({panel['canton'].nunique()} cantons, "
          f"{panel['year'].min()}-{panel['year'].max()})")
    print(f"[data] typical burden with accident cover: {typical.iloc[0]:.1f}% ({typical.index[0]}) -> "
          f"{typical.iloc[-1]:.1f}% ({typical.index[-1]})")
    print(f"[done] wrote {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
