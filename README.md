# CIP HS26 – Group 105: Premiums vs. Paychecks

Health insurance affordability across Swiss cantons, 2012–2022, plus a 2026 premium snapshot.
Team: Alisa Bitschnau, Chaitanya Arya, Jobin Joseph. See `docs/` for the feasibility study.

## Repository structure

| Folder | Content |
|---|---|
| `data/` | All raw and processed data. **`data/README.md` is the data catalog**: every file, its source, method and who collected it |
| `src/income/` | Income pipeline (ESTV scraping, BFS API, cleaning) |
| `src/premium/` | Premiums by insurance model and deductible (research question 3) |
| `Code/` | Selenium scraper for the current premiums (Jobin Joseph) |
| `notebooks/` | `priminfo_pdf_scraping.ipynb` (premiums 2012–2022), `income_checks.ipynb` (income sanity checks) |
| `visualizations/` | Interactive dashboards: premiums vs. income (`affordability_dashboard.html`) and income (`income_dashboard.html`) |
| `docs/` | Project description, feasibility study, team agreement, `figures/` |

## Data at a glance

| Data | Years | Method | Collected by |
|---|---|---|---|
| Taxable income per canton (ESTV) + regional wages (BFS) | 2012–2022 | Static scraping + API | Chaitanya Arya |
| Health insurance premiums per canton (priminfo PDFs) | 2012–2022 | Static scraping + PDF parsing | Alisa Bitschnau |
| Health insurance premiums per insurer, capital of each canton (priminfo calculator) | 2026 | Dynamic scraping (Selenium) | Jobin Joseph |

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

**Open points for the group:**
- **Valais 2020 outlier:** median taxable income rose 6.6%, while the median canton grew only 0.6% that year. Over the same period the number of taxpayers fell by about 6,000. This is most likely a change in the source data, not real income growth. The value is kept and flagged (`yoy_outlier`); we still need to decide how to treat it in the analysis.
- **Geneva:** median taxable income was lower in 2022 than in 2012 (index 98.7), while most other cantons grew 5–20%. This will directly affect the affordability results for GE.
- **Choice of income measure:** ESTV taxable income and the BFS regional wage correlate only moderately (r = 0.46, survey years 2012–2022). BFS gives one wage per large region, not per canton, so the cantonal tax data stays the main measure and BFS is the cross-check.

## Repository naming

The course requires the repository to be named `CIP_HS26_105` (convention `CIP_[HS/FS][YEAR]_groupnumber`). It is currently called `CIP-project` and still needs to be renamed under GitHub → Settings → General → Repository name. After renaming, each team member should update their local remote with:

```bash
git remote set-url origin https://github.com/carya0001/CIP_HS26_105.git
```

## Premium data 2012–2022 (Alisa Bitschnau)

Code: `notebooks/priminfo_pdf_scraping.ipynb`.

1. Checks `robots.txt`, downloads the BAG priminfo archive page (`data/raw/priminfo_archiv.html`) and collects the links to the yearly premium PDFs with BeautifulSoup.
2. Downloads `praemien_2012.pdf` … `praemien_2022.pdf` to `data/raw/priminfo_pdfs/` with a pause between requests. Every request is logged in `data/raw/download_log.csv`.
3. Parses all PDFs with pdfplumber, line by line, keeping model, canton, age group and region from the page header. Lines that cannot be read are counted and listed, never dropped silently.
4. Reduces the result to one premium per canton and year for a **reference case**: standard model, adults, CHF 300 deductible, with accident cover. The mean is taken over insurers, then over premium regions.

**Output:** `data/processed/priminfo_premiums_per_canton.csv` (286 rows) and `..._ohne_unfall.csv` (same, without accident cover).

### Insurance models and deductibles (research question 3, script by Chaitanya Arya)

`src/premium/premium_options.py` reads the full table from Step 8 of the notebook
(`data/processed/priminfo_premiums_2012_2022.csv`, 2.9 million premium values). That table is about 330 MB, so it is
not in Git; run Steps 1–8 of the notebook to create it.

```bash
python src/premium/premium_options.py
```

**Steps:**
1. Keeps adults and the four models: standard, family doctor, HMO, and other (mostly telemedicine). The tariffs for workers posted abroad ("Entsandte") are left out.
2. Runs the cleaning checks:
   - gaps
   - data types
   - ranges: positive premiums, valid deductibles, premiums falling with a higher deductible, lower without accident cover
   - outliers (3·IQR, flagged and kept)
3. Averages the same way as the reference case.
4. Adds the difference to the reference case as enrichment.

**Output:** `data/processed/premiums_by_model_deductible.csv`, 13,650 rows: year × canton × model × accident cover × deductible.

**Findings from the checks:**
- The only tariff that rises with a higher deductible is Helsana group's **BeneFit** at CHF 1,500 (1,018 of 148,242 tariffs). It is printed like this in the official PDFs, so it is kept.
- HMO is missing in GL and VS in some years before 2016.

## Premium data 2026 (Jobin Joseph)

Code: `Code/scrape_health_insurance_premiums.py` (needs Google Chrome).

Dynamic scraping of the priminfo premium calculator with Selenium. The calculator is a JavaScript form, so the script fills it in like a user:
1. Types the postal code and picks it from the typeahead list.
2. Enters the birth year.
3. Picks the deductible from the dropdown.
4. Ticks accident cover.
5. Selects the insurance model.
6. Clicks "calculate" and reads the results table.

The same profile was queried for the capital's postal code in each of the 26 cantons: born 1988, CHF 300 deductible, with accident cover, standard model. The first part of the script documents the exploration of the BFS and ESTV sources and a first manual run for Bern.

**Output:** `data/raw/priminfo_2026/priminfo_premiums_raw.csv` (628 rows, one per insurer offer). Column descriptions are in `data/README.md`.

The profile matches the 2012–2022 reference case, but it covers only the capital's premium region, so it is a snapshot rather than a continuation of the time series.

**Open point – premium year:** the calculator shows next year's premiums as soon as they are published at the end of September. The CSV was scraped in October 2026, so it most likely holds the **2027** premiums, not 2026. The manual test run in the script also labels its result `premium_year = 2027`. This needs to be confirmed before the data is called "2026" in the report.

## Visualizations

See `visualizations/README.md`. Rebuild with:

```bash
python visualizations/build_affordability_dashboard.py
python visualizations/build_income_dashboard.py
```

The affordability dashboard merges income and premiums 2012–2022. Its burden measure is the annual premium divided by the median taxable income. A second section compares insurance models and deductibles (research question 3).
