"""Clean and combine the ESTV income files and the BFS wages into tidy tables.

Inputs  (from scrape_estv.py and fetch_bfs_wages.py):
  data/raw/estv/kennzahlen_ohne_<year>.xlsx
  data/processed/wages_grossregion_year.csv
Outputs:
  data/processed/income_canton_year_household.csv  all household types, long format
  data/processed/income_canton_year.csv            one row per canton and year (total)

Run from the repository root:  python src/income/clean_income.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).parent))
from cantons import CANTON_TO_GROSSREGION, CANTONS, GROSSREGIONS  # noqa: E402

RAW_DIR = Path("data/raw/estv")
WAGES_FILE = Path("data/processed/wages_grossregion_year.csv")
OUT_HOUSEHOLD = Path("data/processed/income_canton_year_household.csv")
OUT_TOTAL = Path("data/processed/income_canton_year.csv")

YEARS = range(2012, 2023)

# Column names differ between years (e.g. 'ktnr' vs 'Kantonsnummer\nCode canton')
COLUMN_ALIASES = {"Kantonsnummer": "ktnr", "Kanton": "ktname"}

# Household categories: up to 2019 the ESTV splits taxpayers into married and
# unmarried; from 2020 on into married, single parents and other taxpayers.
HOUSEHOLDS = {
    "Verheiratet": "married",
    "Verheiratete oder eingetragene Partnerschaften": "married",
    "Unverheiratet": "unmarried",
    "Einelternfamilien": "single_parent",
    "Übrige Steuerpflichtige": "other",
    "Total": "total",
}

# stpf = number of taxpayers, steink = taxable income, reink = net income (CHF)
VALUE_COLUMNS = [
    "stpf", "mean_steink", "median_steink", "gini_steink",
    "mean_reink", "median_reink", "p25", "p75",
]


# ---------------------------------------------------------------- loading

def read_year(year: int) -> pd.DataFrame:
    """Read the canton sheet of one ESTV file and bring it into a common shape."""
    path = RAW_DIR / f"kennzahlen_ohne_{year}.xlsx"
    excel = pd.ExcelFile(path)
    sheet = next(s for s in excel.sheet_names if s.startswith("Kanton"))  # name varies
    df = pd.read_excel(excel, sheet_name=sheet)

    # Headers in newer files are bilingual: 'Kanton\nCanton' -> 'Kanton'
    df.columns = [str(c).split("\n")[0].strip() for c in df.columns]
    df = df.rename(columns=COLUMN_ALIASES)

    # Drop footer/note rows, which have no canton number
    df = df[pd.to_numeric(df["ktnr"], errors="coerce").notna()]

    unknown = set(df["Einheit"]) - set(HOUSEHOLDS)
    if unknown:
        raise ValueError(f"{year}: unknown household categories {unknown}")

    out = pd.DataFrame({
        "year": year,
        "canton_nr": df["ktnr"].astype(int),
        "household": df["Einheit"].map(HOUSEHOLDS),
    })
    for col in VALUE_COLUMNS:
        out[col] = pd.to_numeric(df[col], errors="coerce")
    return out


def load_all() -> pd.DataFrame:
    frames = [read_year(y) for y in YEARS]
    df = pd.concat(frames, ignore_index=True)
    df["stpf"] = df["stpf"].astype("Int64")
    df["household"] = df["household"].astype("category")
    return df


# ---------------------------------------------------------------- checks

def check_gaps(df: pd.DataFrame) -> None:
    print("\n[1] Gaps / missing data")
    expected = pd.MultiIndex.from_product([YEARS, CANTONS], names=["year", "canton_nr"])
    present = df.loc[df["household"] == "total"].set_index(["year", "canton_nr"]).index
    missing = expected.difference(present)
    print(f"  canton-year combinations (total): {len(present)} of {len(expected)} expected")
    if len(missing):
        print(f"  MISSING: {list(missing)}")
    na = df[VALUE_COLUMNS].isna().sum()
    print(f"  missing values per column: {na[na > 0].to_dict() or 'none'}")


def check_dtypes(df: pd.DataFrame) -> None:
    print("\n[2] Data types")
    for col, dtype in df.dtypes.items():
        print(f"  {col:15} {dtype}")


def check_ranges(df: pd.DataFrame) -> None:
    print("\n[3] Value ranges")
    rules = {
        "taxpayers > 0": df["stpf"] > 0,
        "incomes > 0": (df[["mean_steink", "median_steink", "mean_reink", "median_reink"]] > 0).all(axis=1),
        "gini between 0 and 1": df["gini_steink"].between(0, 1),
        "p25 <= median <= p75": (df["p25"] <= df["median_steink"]) & (df["median_steink"] <= df["p75"]),
        "median <= mean (right-skewed)": df["median_steink"] <= df["mean_steink"],
        "taxable <= net income": df["median_steink"] <= df["median_reink"],
    }
    for name, ok in rules.items():
        bad = df.loc[~ok.fillna(False)]
        print(f"  {name:32} {'OK' if bad.empty else f'{len(bad)} rows violate'}")
        if not bad.empty:
            print(bad[["year", "canton_nr", "household"]].head().to_string(index=False))


def flag_outliers(total: pd.DataFrame) -> pd.DataFrame:
    """Flag unusual year-on-year jumps in the median taxable income.

    Uses the 3*IQR rule on all canton-year changes. Flagged rows are kept and
    printed for inspection; levels themselves (e.g. ZG) are not outliers.
    """
    print("\n[4] Outliers (year-on-year change of median taxable income, 3*IQR rule)")
    yoy = total["median_steink_yoy_pct"]
    q1, q3 = yoy.quantile([0.25, 0.75])
    low, high = q1 - 3 * (q3 - q1), q3 + 3 * (q3 - q1)
    total["yoy_outlier"] = ~yoy.between(low, high) & yoy.notna()
    print(f"  accepted range: {low:.1f}% to {high:.1f}%")
    flagged = total.loc[total["yoy_outlier"], ["year", "canton_abbr", "median_steink", "median_steink_yoy_pct"]]
    print(flagged.to_string(index=False) if not flagged.empty else "  none")
    return total


# ---------------------------------------------------------------- enrichment

def add_canton_info(df: pd.DataFrame) -> pd.DataFrame:
    df.insert(2, "canton_abbr", df["canton_nr"].map(lambda n: CANTONS[n][0]))
    df.insert(3, "canton_name", df["canton_nr"].map(lambda n: CANTONS[n][1]))
    df.insert(4, "grossregion_code", df["canton_abbr"].map(CANTON_TO_GROSSREGION))
    df.insert(5, "grossregion", df["grossregion_code"].map(GROSSREGIONS))
    return df


def add_growth(total: pd.DataFrame) -> pd.DataFrame:
    total = total.sort_values(["canton_nr", "year"])
    by_canton = total.groupby("canton_nr")["median_steink"]
    total["median_steink_index_2012"] = 100 * total["median_steink"] / by_canton.transform("first")
    total["median_steink_yoy_pct"] = 100 * by_canton.pct_change()
    return total


def add_regional_wage(total: pd.DataFrame) -> pd.DataFrame:
    """Attach the BFS regional median wage (annualised, x12).

    The LSE exists only for even years; odd years are linearly interpolated
    between the neighbouring surveys and flagged.
    """
    wages = pd.read_csv(WAGES_FILE)
    wages = wages.query("sex == 'total' and stat == 'median' and grossregion_code > 0")
    wide = wages.pivot(index="year", columns="grossregion_code", values="monthly_gross_wage_chf")
    wide = wide.reindex(YEARS)
    interpolated = wide.isna()
    wide = wide.interpolate(method="index", limit_area="inside")

    long = (12 * wide).stack().rename("annual_gross_wage_region").reset_index()
    flags = interpolated.stack().rename("wage_interpolated").reset_index()
    long = long.merge(flags, on=["year", "grossregion_code"])
    return total.merge(long, on=["year", "grossregion_code"], how="left")


# ---------------------------------------------------------------- main

def main() -> None:
    df = add_canton_info(load_all())
    df = df.sort_values(["year", "canton_nr", "household"]).reset_index(drop=True)

    check_gaps(df)
    check_dtypes(df)
    check_ranges(df)

    total = df.loc[df["household"] == "total"].drop(columns="household")
    total = add_growth(total)
    total = flag_outliers(total)
    total = add_regional_wage(total)
    total["taxable_income_to_wage_ratio"] = total["median_steink"] / total["annual_gross_wage_region"]
    total = total.sort_values(["year", "canton_nr"]).round(4)

    OUT_HOUSEHOLD.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_HOUSEHOLD, index=False)
    total.to_csv(OUT_TOTAL, index=False)
    print(f"\nSaved {len(df)} rows to {OUT_HOUSEHOLD}")
    print(f"Saved {len(total)} rows to {OUT_TOTAL}")


if __name__ == "__main__":
    main()
