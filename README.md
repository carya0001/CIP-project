# CIP HS26 – Group 105: Premiums vs. Paychecks

Health insurance affordability across Swiss cantons, 2012–2022.
Team: Alisa Bitschnau, Chaitanya Arya, Jobin Joseph. See `docs/` for the feasibility study.

## Setup

```bash
pip install -r requirements.txt
```

All scripts are run from the repository root.

## Income data (Chaitanya Arya)

Code in `src/income/`. Run in this order:

| Step | Script | Method | Output |
|---|---|---|---|
| 1 | `scrape_estv.py` | Static scraping (requests + BeautifulSoup): collects the ESTV "Statistische Kennzahlen" XLSX links from the overview page and downloads tax years 2012–2022 | `data/raw/estv/*.xlsx`, `manifest.csv` (URL and retrieval date) |
| 2 | `fetch_bfs_wages.py` | BFS PxWeb API (JSON POST), table `px-x-0304010000_201` (LSE): median, P25, P75 and median by sex | `data/raw/bfs/*.json`, `data/processed/wages_grossregion_year.csv` |
| 3 | `clean_income.py` | Harmonises the yearly files, runs the cleaning checks and adds enrichment columns | `data/processed/income_canton_year.csv`, `income_canton_year_household.csv` |

`notebooks/income_checks.ipynb` contains visual sanity checks.

**Main table for merging:** `data/processed/income_canton_year.csv`, one row per canton × year (286 rows).
Merge key: `canton_abbr` + `year`. Main income measure: `median_steink`, the median taxable income
in CHF of all taxpayers (with and without federal tax liability).

**Cleaning:**
- Column names, canton names, sheet names and household categories differ between years. Everything is mapped to one schema, keyed by the BFS canton number.
- Gaps: all 286 canton-years are present, with no missing values.
- Data types are cast explicitly.
- Range checks: positive values, Gini between 0 and 1, P25 ≤ median ≤ P75 ≤ mean.
- Outliers: year-on-year jumps are flagged with a 3·IQR rule (`yoy_outlier`) and kept, not dropped.
  The only flag is VS 2020 (+6.6%), when the number of taxpayers fell while incomes rose. This is most likely a change in the source data, not real growth.

**Enrichment:**
- `canton_abbr` and `grossregion`
- `median_steink_index_2012` and `median_steink_yoy_pct`
- `annual_gross_wage_region`: BFS median × 12. Odd years are linearly interpolated and flagged with `wage_interpolated`.
- `taxable_income_to_wage_ratio`

**Limitations:**
- Taxable income is income after deductions, counted per tax unit; a married couple is one unit.
- The household categories change in 2020 (unmarried → single parents + others), so only `total` and `married` are comparable over the whole period.
- BFS wages exist only for 7 large regions and only for even years.

## Premium data

*(to be added)*
