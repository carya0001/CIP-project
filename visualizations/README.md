# Visualizations: income dashboard

`income_dashboard.html` is an interactive dashboard of the income data in `data/processed/`.
Open it in a browser (it needs internet once, to load Plotly.js from cdnjs).

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
