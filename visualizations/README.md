# Visualizations

Two interactive dashboards. Open them in a browser (they need internet once, to load Plotly.js from cdnjs).

| Page | Question |
|---|---|
| `affordability_dashboard.html` | **Premiums vs. paychecks**: how heavy is the health premium compared with income, per canton and year? |
| `income_dashboard.html` | How much do the cantons earn, and how unequal is it? |

# Affordability dashboard (premiums vs. income)

Rebuild from the repository root:

```bash
python visualizations/build_affordability_dashboard.py
```

The script merges `data/processed/income_canton_year.csv` with the two premium tables
(`priminfo_premiums_per_canton.csv` and `..._ohne_unfall.csv`, read from `data_premium/processed/`, or from
`data/processed/` if they are moved there) on year + canton. It stops if a canton-year is missing.
**Burden = annual premium ÷ median taxable income × 100.** Layout and charts live in `affordability_template.html`.

Global controls: year slider with play button, accident cover with / without, canton picker. Clicking a canton
in any chart selects it everywhere.

| Chart | Shows |
|---|---|
| Key figures | Typical burden and change since 2012, premium vs. income growth, highest and lowest burden |
| The scissors | Premium index vs. income index (2012 = 100) for the typical canton, with the P10–P90 band of cantons |
| Tile map | Burden, premium or income per canton |
| Income vs. premium | Bubble chart with lines of equal burden, animated by year |
| Burden 2012 → year | Dumbbell per canton, sorted by the increase |
| Growth 2012 → year | Premium growth vs. income growth per canton |
| Burden heatmap | Canton × year |
| With vs. without accident cover | Premium difference and rank correlation of the burden |

A method note on the page explains the limits: one adult's premium against one tax unit's taxable income, before subsidies.

# Income dashboard

## Rebuild

Run from the repository root after the income pipeline (`src/income/`) has produced new CSVs:

```bash
python visualizations/build_income_dashboard.py
```

The script reads the three processed tables, embeds them as JSON into `dashboard_template.html` and writes
`income_dashboard.html`. Change the layout or charts in the template, never in the generated file.

| File | Role |
|---|---|
| `build_income_dashboard.py` | Loads the CSVs, adds the tile-map position of each canton, writes the HTML |
| `dashboard_template.html` | Page layout, styles and chart code (Plotly.js); `__DASHBOARD_DATA__` is replaced by the data |
| `income_dashboard.html` | Generated output, self-contained |

## What is in the dashboard

Global controls: year slider with play button (2012–2022), measure switch (median, mean, growth index, Gini,
income ÷ regional wage), and a canton picker. Clicking a canton in any chart selects it everywhere.

| Chart | Data | Shows |
|---|---|---|
| Key figures | `income_canton_year.csv` | Typical canton, highest and lowest canton, taxpayers (or the selected canton's rank) |
| Tile map | `income_canton_year.csv` | The chosen measure per canton, on a simplified map of Switzerland |
| Spread inside each canton | `income_canton_year.csv` | P25–P75 range, median and mean per canton, sorted |
| Who grew since 2012? | `median_steink_index_2012` | Index lines for all cantons; Geneva below 100, Valais 2020 outlier marked |
| Rank by median income | `median_steink` | Bump chart of the ranking 2012–2022 |
| Income vs. inequality | `median_steink`, `gini_steink`, `stpf` | Bubble chart, animated by year |
| Married vs. single taxpayers | `income_canton_year_household.csv` | Median per household type (categories change in 2020) |
| Gross wages by large region | `wages_grossregion_year.csv` | BFS median with P25–P75 band, men vs. women, Switzerland for comparison |

A sortable data table for the selected year sits at the bottom of the page.
