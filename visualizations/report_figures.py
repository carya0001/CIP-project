"""Static figures for the project report (docs/figures/report_fig*.png).

Same data and colours as the affordability dashboard, drawn with matplotlib so they can
be placed in the Word/PDF report.

Run from the repository root:
    python visualizations/report_figures.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "docs" / "figures"

# Dashboard palette (light mode)
PREMIUM, INCOME, AQUA, YELLOW = "#eb6834", "#2a78d6", "#1baf7a", "#eda100"
TEXT, MUTED, GRID, CONTEXT = "#0b0b0b", "#52514e", "#e1e0d9", "#c9c8c1"
MODELS = {"standard": ("Standard", PREMIUM), "family_doctor": ("Family doctor", INCOME),
          "hmo": ("HMO", AQUA), "other": ("Other (telemedicine)", YELLOW)}

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 9, "axes.edgecolor": CONTEXT, "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 10, "axes.titleweight": "bold",
    "axes.titlecolor": TEXT, "axes.titlelocation": "left", "legend.frameon": False, "savefig.dpi": 200,
})


def load_panel():
    income = pd.read_csv(PROCESSED / "income_canton_year.csv")
    premium = pd.read_csv(PROCESSED / "priminfo_premiums_per_canton.csv")
    df = income.merge(premium, left_on=["year", "canton_abbr"], right_on=["year", "canton"], validate="one_to_one")
    df["burden"] = df["premium_year"] / df["median_steink"] * 100
    return df


def fig_scissors(df):
    """Figure 1: premium vs income index, median canton with P10-P90 band."""
    fig, ax = plt.subplots(figsize=(6.3, 2.7))
    for col, colour, label in [("premium_year", PREMIUM, "Premium"), ("median_steink", INCOME, "Median taxable income")]:
        wide = df.pivot(index="year", columns="canton_abbr", values=col)
        idx = wide / wide.iloc[0] * 100
        ax.fill_between(idx.index, idx.quantile(0.1, axis=1), idx.quantile(0.9, axis=1), color=colour, alpha=0.15, lw=0)
        mid = idx.median(axis=1)
        ax.plot(mid.index, mid, color=colour, lw=2, marker="o", ms=3.5, label=label)
        ax.annotate(f"{mid.iloc[-1] - 100:+.1f}%", (mid.index[-1], mid.iloc[-1]), xytext=(6, 0),
                    textcoords="offset points", va="center", color=TEXT, fontweight="bold")
    ax.axhline(100, color=CONTEXT, lw=0.8)
    ax.set_xticks(range(2012, 2023))
    ax.set_xlim(2011.7, 2023.1)
    ax.set_ylabel("Index (2012 = 100)")
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT / "report_fig1_scissors.png")


def fig_burden(df):
    """Figure 2: burden 2012 vs 2022 per canton (dot plot)."""
    wide = df.pivot(index="canton_abbr", columns="year", values="burden").sort_values(2022)
    fig, ax = plt.subplots(figsize=(6.3, 3.0))
    x = range(len(wide))
    ax.vlines(x, wide[2012], wide[2022], color=CONTEXT, lw=2)
    ax.scatter(x, wide[2012], color=MUTED, s=18, zorder=3, label="2012")
    ax.scatter(x, wide[2022], color=PREMIUM, s=22, zorder=3, label="2022")
    ax.set_xticks(list(x), wide.index, fontsize=8)
    ax.set_ylabel("Premium as % of median\ntaxable income")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left", ncols=2)
    fig.tight_layout()
    fig.savefig(OUT / "report_fig2_burden_by_canton.png")


LABELLED = {"GE", "BS", "NE", "JU", "TI", "VD", "BE", "ZH", "ZG", "AI", "VS", "BL", "SZ", "NW", "GR", "AG"}


def fig_scatter(df):
    """Figure 3: income vs premium per canton 2022 with lines of equal burden."""
    g = df[df["year"] == 2022]
    fig, ax = plt.subplots(figsize=(6.3, 3.0))
    xs = pd.Series([38000, 68000])
    for b in (8, 10, 12, 14, 16, 18):
        ax.plot(xs, xs * b / 100, color=CONTEXT, lw=0.8, ls="--", zorder=1)
        y_end = min(68000 * b / 100, 8300)
        ax.text(y_end / (b / 100), y_end, f" {b}%", color=MUTED, fontsize=7, va="bottom" if y_end == 8300 else "center")
    ax.scatter(g["median_steink"], g["premium_year"], s=g["stpf"] / 2500, color=INCOME, alpha=0.8,
               edgecolor="white", lw=1, zorder=3)
    # label only the cantons discussed in the text; the crowded middle stays readable
    for _, r in g[g["canton_abbr"].isin(LABELLED)].iterrows():
        ax.annotate(r["canton_abbr"], (r["median_steink"], r["premium_year"]), xytext=(0, 6), textcoords="offset points",
                    ha="center", fontsize=7, color=MUTED)
    ax.set_xlim(38000, 68000)
    ax.set_ylim(4200, 8300)
    ax.set_xlabel("Median taxable income per tax unit (CHF)")
    ax.set_ylabel("Annual premium (CHF)")
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:,.0f}".replace(",", "'"))
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}".replace(",", "'"))
    fig.tight_layout()
    fig.savefig(OUT / "report_fig3_income_vs_premium.png")


def fig_choices(df):
    """Figure 4: (a) premium by model and deductible, (b) burden standard vs cheapest choice, 2022."""
    opt = pd.read_csv(PROCESSED / "premiums_by_model_deductible.csv")
    opt = opt[(opt["accident"] == "mit_unfall") & (opt["year"] == 2022)]
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.3, 2.8), gridspec_kw={"width_ratios": [1, 1.5]})

    typical = opt.groupby(["model", "deductible"])["premium_year"].median().unstack(0)
    for key, (label, colour) in MODELS.items():
        a.plot(range(len(typical)), typical[key], color=colour, lw=1.8, marker="o", ms=3, label=label)
    a.set_xticks(range(len(typical)), [f"{d:,}".replace(",", "'") for d in typical.index], fontsize=7)
    a.set_xlabel("Deductible (CHF)")
    a.set_ylabel("Annual premium (CHF)")
    a.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}".replace(",", "'"))
    a.set_title("(a) Typical canton", fontsize=9)
    a.legend(fontsize=7, loc="lower left")

    income = df[df["year"] == 2022].set_index("canton_abbr")["median_steink"]
    ref = opt[(opt["model"] == "standard") & (opt["deductible"] == 300)].set_index("canton")["premium_year"]
    cheapest = opt[opt["deductible"] == 2500].groupby("canton")["premium_year"].min()
    burden = pd.DataFrame({"ref": ref / income * 100, "best": cheapest / income * 100}).sort_values("ref")
    x = range(len(burden))
    b.vlines(x, burden["best"], burden["ref"], color=CONTEXT, lw=2)
    b.scatter(x, burden["best"], color=MUTED, s=14, zorder=3, label="Cheapest model, CHF 2'500")
    b.scatter(x, burden["ref"], color=PREMIUM, s=16, zorder=3, label="Standard, CHF 300")
    b.axhline(burden["ref"].min(), color=PREMIUM, lw=0.8, ls=":", label=f"Lowest standard burden (ZG, {burden['ref'].min():.1f}%)")
    b.set_xticks(list(x), burden.index, fontsize=6, rotation=90)
    b.set_ylim(0, None)
    b.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    b.set_ylabel("Premium as % of income")
    b.grid(axis="x", visible=False)
    b.set_title("(b) Burden per canton", fontsize=9)
    b.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT / "report_fig4_insurance_choices.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_panel()
    fig_scissors(df)
    fig_burden(df)
    fig_scatter(df)
    fig_choices(df)
    print(f"[done] wrote 4 figures to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
