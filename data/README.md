# Data catalog

Every dataset of the project, where it comes from and who collected it.
`raw/` holds the files as downloaded or scraped; `processed/` holds the cleaned tables used for the analysis.
Merge key across all tables: canton abbreviation (`canton_abbr` / `canton`) + `year`.

```
data/
├── raw/
│   ├── estv/              income: ESTV tax statistics (XLSX)          – Chaitanya
│   ├── bfs/               income: BFS wage statistics (JSON)          – Chaitanya
│   ├── priminfo_pdfs/     premiums 2012–2022: priminfo PDFs           – Alisa
│   ├── priminfo_archiv.html, download_log.csv                         – Alisa
│   └── priminfo_2026/     premiums 2026: Selenium scrape (CSV)        – Jobin
└── processed/             cleaned tables, one row per canton × year
```

## Overview

| Topic | Years | Source | Method | Collected by | Raw | Processed |
|---|---|---|---|---|---|---|
| Taxable income per canton | 2012–2022 | ESTV, *Statistische Kennzahlen direkte Bundessteuer* | Static scraping (requests + BeautifulSoup), XLSX download | Chaitanya Arya | `raw/estv/` | `processed/income_canton_year.csv`, `processed/income_canton_year_household.csv` |
| Gross wages per large region | 2012–2022 (even years) | BFS, LSE table `px-x-0304010000_201` | PxWeb API (JSON POST) | Chaitanya Arya | `raw/bfs/` | `processed/wages_grossregion_year.csv` |
| Health insurance premiums | 2012–2022 | BAG priminfo archive (premium PDFs) | Static scraping of the archive page + PDF parsing with pdfplumber | Alisa Bitschnau | `raw/priminfo_pdfs/`, `raw/priminfo_archiv.html`, `raw/download_log.csv` | `processed/priminfo_premiums_per_canton.csv`, `processed/priminfo_premiums_per_canton_ohne_unfall.csv` |
| Health insurance premiums | 2026 | priminfo.admin.ch premium calculator | Dynamic scraping with Selenium | Jobin Joseph | `raw/priminfo_2026/priminfo_premiums_raw.csv` | – (used as scraped) |

## Raw files

### `raw/estv/` – ESTV tax statistics (income)
| File | Content |
|---|---|
| `kennzahlen_ohne_2012.xlsx` … `kennzahlen_ohne_2022.xlsx` | Key figures per canton, taxpayers with and without federal tax liability, by household type. Input of `src/income/clean_income.py`. |
| `manifest.csv` | Year, download URL, file name, size and retrieval time of each XLSX |
| `statistik-dbst-np-kanton-2022-nk-ohne-belastung-normalfall.xlsx` | ESTV 2022, taxpayers **without** federal tax liability per canton (added by Jobin, reference only) |
| `*.numbers` | Apple Numbers copies of the 2022 ESTV tables (added by Jobin, reference only) |

### `raw/bfs/` – BFS wage statistics (income cross-check)
| File | Content |
|---|---|
| `lse_px-x-0304010000_201_total.json` | Monthly gross wage, median / P25 / P75, per large region, even years |
| `lse_px-x-0304010000_201_by_sex.json` | Median monthly gross wage by sex |

### Premiums 2012–2022
| File | Content |
|---|---|
| `priminfo_pdfs/praemien_<year>.pdf` | Official premium tables of all insurers, cantons, regions, age groups, deductibles and models (11 files, up to 22 MB each) |
| `priminfo_archiv.html` | Saved copy of the priminfo archive page the PDF links were taken from |
| `download_log.csv` | Timestamp, URL and HTTP status of every download |

Code: `notebooks/priminfo_pdf_scraping.ipynb`.

### `raw/priminfo_2026/` – Premiums 2026
`priminfo_premiums_raw.csv`, 628 rows: one row per insurer offer in each canton's main town, scraped from the priminfo premium calculator.

| Column | Meaning |
|---|---|
| `postal_code`, `canton` | One postal code per canton (the capital, e.g. 8001 Zürich, 1201 Genève) |
| `birth_year`, `franchise`, `accident`, `model_category`, `insurance_model` | Profile used for every query: born 1988 (adult), CHF 300 deductible, with accident cover, standard model, basic insurance |
| `insurer` | Insurance company (21–28 per canton) |
| `monthly_premium`, `monthly_reimbursement`, `monthly_total` | CHF per month; reimbursement = environmental levy refund, total = premium − reimbursement |
| `yearly_premium`, `yearly_reimbursement`, `yearly_total` | CHF per year (`yearly_premium` and `yearly_total` use `'` as thousands separator, e.g. `7'596.00`) |

The profile matches the 2012–2022 reference case (adult, CHF 300, with accident cover, standard model), but covers only the
premium region of the capital, not an average over all premium regions of the canton. Median monthly premium per canton:
CHF 444 (ZG) to CHF 771 (GE); chart in `docs/figures/premium_2026_median_by_canton.png`.

## Processed tables

| File | Rows | Grain | Key columns |
|---|---|---|---|
| `income_canton_year.csv` | 286 | canton × year, 2012–2022 | `median_steink` (median taxable income, CHF), `mean_steink`, `gini_steink`, `p25`, `p75`, `stpf` (taxpayers), `median_steink_index_2012`, `yoy_outlier`, `annual_gross_wage_region` |
| `income_canton_year_household.csv` | 936 | canton × year × household type | `household`, `stpf`, `median_steink`, `mean_steink` |
| `wages_grossregion_year.csv` | 280 | large region × year × sex × statistic | `monthly_gross_wage_chf` |
| `priminfo_premiums_per_canton.csv` | 286 | canton × year, 2012–2022 | `premium_month`, `premium_year` (CHF), `n_regions` – adult, standard model, CHF 300 deductible, **with** accident cover; mean over insurers, then over premium regions |
| `priminfo_premiums_per_canton_ohne_unfall.csv` | 286 | canton × year, 2012–2022 | same, **without** accident cover |

All 286 canton-years of income and premiums match one to one; `visualizations/build_affordability_dashboard.py` stops if they do not.
