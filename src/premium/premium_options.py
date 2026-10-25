"""Premiums by insurance model and deductible per canton and year (research question 3).

Input (Step 8 of notebooks/priminfo_pdf_scraping.ipynb, not in Git because of its size):
  data/processed/priminfo_premiums_2012_2022.csv   one row per insurer, region, age group,
                                                   model, accident cover and deductible
Output:
  data/processed/premiums_by_model_deductible.csv  one row per year, canton, model,
                                                   deductible and accident cover (adults)

Same averaging as the reference case in the notebook (Step 9): mean over insurers within
each premium region, then mean over the regions of a canton.

Run from the repository root:  python src/premium/premium_options.py
"""

from pathlib import Path

import pandas as pd

IN_FILE = Path("data/processed/priminfo_premiums_2012_2022.csv")
OUT_FILE = Path("data/processed/premiums_by_model_deductible.csv")

YEARS = range(2012, 2023)
DEDUCTIBLES = [300, 500, 1000, 1500, 2000, 2500]   # adult deductibles in CHF
AGE_GROUP = "Erwachsene"                          # adults (26+)

# Model names in the PDFs -> short English names. Other titles (e.g. "Entsandte ... "
# for workers posted abroad) are special tariffs and are left out.
MODELS = {
    "Grundversicherung": "standard",
    "Hausarztmodell": "family_doctor",
    "HMO": "hmo",
    "Weitere Versicherungsmodelle": "other",       # mostly telemedicine models
}


# ---------------------------------------------------------------- loading

def load() -> pd.DataFrame:
    if not IN_FILE.exists():
        raise SystemExit(f"{IN_FILE} not found: run Step 8 of notebooks/priminfo_pdf_scraping.ipynb first")
    df = pd.read_csv(IN_FILE)
    print(f"[load] {len(df):,} premium values from {IN_FILE}")
    return df


# ---------------------------------------------------------------- checks

def check_gaps(df: pd.DataFrame) -> None:
    print("\n[1] Gaps / missing data")
    na = df.isna().sum()
    print(f"  missing values per column: {na[na > 0].to_dict() or 'none'}")
    combos = df.groupby(["year", "model"])["canton"].nunique().unstack()
    incomplete = combos[combos < 26].stack()
    print(f"  model-years with fewer than 26 cantons: {incomplete.to_dict() or 'none'}")


def check_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[2] Data types")
    df = df.astype({"year": int, "region": int, "deductible": int, "premium_month": float,
                    "model": "category", "accident": "category", "canton": "category"})
    for col, dtype in df.dtypes.items():
        print(f"  {col:15} {dtype}")
    return df


def check_ranges(df: pd.DataFrame) -> None:
    """Premiums must be positive, fall with a higher deductible and be lower without accident cover."""
    print("\n[3] Value ranges")
    print(f"  premiums <= 0: {(df['premium_month'] <= 0).sum()}")
    print(f"  deductibles outside {DEDUCTIBLES}: {(~df['deductible'].isin(DEDUCTIBLES)).sum()}")

    keys = ["year", "canton", "region", "model", "insurer", "accident"]
    # Some insurers list two tariffs under the same name in one region; skip those for this check.
    unique = df[~df.duplicated(keys + ["deductible"], keep=False)]
    tariffs = unique.pivot_table(index=keys, columns="deductible", values="premium_month", observed=True)
    rising = tariffs[(tariffs.diff(axis=1) > 0).any(axis=1)].reset_index()
    print(f"  tariffs where the premium rises with a higher deductible: {len(rising)} of {len(tariffs):,}")
    if not rising.empty:
        # All of them are the BeneFit product of the Helsana group at CHF 1500, printed like this in the PDF.
        print("  by product:", rising["insurer"].str.split(", ").str[-1].value_counts().to_dict())

    wide = df.pivot_table(index=keys[:-1] + ["deductible"], columns="accident",
                          values="premium_month", aggfunc="first", observed=True).dropna()
    print(f"  without accident cover more expensive than with: "
          f"{(wide['ohne_unfall'] > wide['mit_unfall']).sum()} of {len(wide):,} pairs")


def flag_outliers(df: pd.DataFrame) -> None:
    """3*IQR rule within each year and deductible; flagged values are printed and kept."""
    print("\n[4] Outliers (3*IQR within year and deductible)")
    group = df.groupby(["year", "deductible"])["premium_month"]
    q1, q3 = group.transform("quantile", 0.25), group.transform("quantile", 0.75)
    out = df[(df["premium_month"] < q1 - 3 * (q3 - q1)) | (df["premium_month"] > q3 + 3 * (q3 - q1))]
    print(f"  flagged: {len(out)} of {len(df):,} values (kept: real tariffs, not reading errors)")
    if not out.empty:
        print(out.groupby(["canton", "model"], observed=True).size().sort_values(ascending=False).head().to_string())


# ---------------------------------------------------------------- transform

def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """Mean over insurers per region, then over regions per canton."""
    keys = ["year", "canton", "model", "accident", "deductible"]
    per_region = (df.groupby(keys + ["region"], observed=True)
                    .agg(premium_month=("premium_month", "mean"), n_insurers=("insurer", "nunique"))
                    .reset_index())
    out = (per_region.groupby(keys, observed=True)
                     .agg(premium_month=("premium_month", "mean"),
                          n_insurers=("n_insurers", "max"), n_regions=("region", "nunique"))
                     .reset_index())
    out["premium_year"] = (out["premium_month"] * 12).round(2)
    out["premium_month"] = out["premium_month"].round(2)
    return out


def add_comparisons(out: pd.DataFrame) -> pd.DataFrame:
    """Enrichment: difference to the reference case (standard model, CHF 300) of the same canton-year."""
    keys = ["year", "canton", "accident"]
    ref = (out[(out["model"] == "standard") & (out["deductible"] == 300)]
           .set_index(keys)["premium_month"].rename("ref_month"))
    out = out.join(ref, on=keys)
    out["pct_vs_reference"] = ((out["premium_month"] / out["ref_month"] - 1) * 100).round(2)
    # Yearly premium saved compared with the reference, minus the extra deductible one may have to pay:
    # positive = cheaper even in a year with high health costs.
    out["saving_year"] = ((out["ref_month"] - out["premium_month"]) * 12).round(2)
    out["worst_case_saving"] = (out["saving_year"] - (out["deductible"] - 300)).round(2)
    return out.drop(columns="ref_month")


def main() -> None:
    df = load()
    df = df[(df["age_group"] == AGE_GROUP) & df["model"].isin(MODELS) & df["year"].isin(YEARS)].copy()
    df["model"] = df["model"].map(MODELS)
    print(f"[filter] adults, 4 models: {len(df):,} values")

    check_gaps(df)
    df = check_dtypes(df)
    check_ranges(df)
    flag_outliers(df)

    out = add_comparisons(aggregate(df))
    expected = len(YEARS) * 26 * len(MODELS) * 2 * len(DEDUCTIBLES)
    print(f"\n[5] Result: {len(out)} of {expected} year-canton-model-accident-deductible rows")
    models = out.groupby(["year", "canton"], observed=True)["model"].nunique()
    print(f"  canton-years without all 4 models: {models[models < len(MODELS)].index.tolist()}")

    out = out.sort_values(["year", "canton", "accident", "model", "deductible"])
    out.to_csv(OUT_FILE, index=False)
    print(f"\nSaved {len(out)} rows to {OUT_FILE}")


if __name__ == "__main__":
    main()
