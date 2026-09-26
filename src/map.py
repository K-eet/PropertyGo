"""Borough maps of median land share, one per calculation mode.

Run: python -m src.map
"""
import matplotlib.pyplot as plt
import pandas as pd

import config
from src.boroughs import load_boundaries

# Same colour scale on both maps so they can be compared side by side. Green = low, red = high.
VMIN, VMAX = 0.2, 0.9

TITLES = {
    "resale": "Resale: price minus the cost to rebuild the house",
    "new_build": "New build: price minus build cost, other development costs and developer profit",
}
NOTES = {
    "resale": "Land share = (price − build cost) ÷ price. A homeowner seller makes no developer "
              "profit, so the rest is land and location.",
    "new_build": f"Land share = (price − build cost − professional fees "
                 f"({config.PROFESSIONAL_FEES_SHARE_OF_BUILD:.0%} of build cost) − marketing and legal "
                 f"({config.MARKETING_AND_LEGAL_SHARE_OF_PRICE:.2%} of price) − developer profit "
                 f"({config.DEVELOPER_PROFIT_SHARE_OF_PRICE:.1%} of price)) ÷ price. Finance not included. "
                 "Applied to all sales at local prices.",
}


def load_map_data(mode: str):
    summary = pd.read_csv(config.OUTPUTS / f"borough_summary_{config.YEAR}.csv")
    gdf = load_boundaries().merge(summary, left_on="GSS_CODE", right_on="borough_code", how="left")
    gdf["value"] = gdf[f"median_land_share_{mode}"].where(gdf["enough_sales"] == True)
    return gdf


def plot_land_share(gdf, mode: str, path):
    fig, ax = plt.subplots(figsize=(10, 8))
    gdf.plot(
        column="value", ax=ax, cmap="RdYlGn_r", vmin=VMIN, vmax=VMAX, edgecolor="white",
        linewidth=0.6, legend=True, missing_kwds={"color": "lightgrey"},
        legend_kwds={"label": "Median land share of sale price", "shrink": 0.6,
                     "format": lambda x, _: f"{x:.0%}"},
    )
    for _, row in gdf.iterrows():
        if pd.notna(row["value"]):
            p = row.geometry.representative_point()
            ax.annotate(f"{row['value']:.0%}", (p.x, p.y), ha="center", va="center", fontsize=7)
    ax.set_title(
        f"How much of a London house price is land?\n{TITLES[mode]}, house sales {config.YEAR}",
        fontsize=12, loc="left",
    )
    ax.text(
        0, -0.04,
        f"{NOTES[mode]} Build cost £{config.BUILD_COST_PER_M2:,}/m² of EPC floor area (BCIS estate "
        "housing, outer London, via Harrow and Croydon Local Plan Viability Assessments 2024). "
        "Grey: City of London (too few house sales).\n"
        "Sources: HM Land Registry Price Paid Data; EPC floor area via House Price per Square Metre "
        "(London Datastore); GLA borough boundaries; PPG Viability. Full list: ASSUMPTIONS.md.",
        transform=ax.transAxes, fontsize=7, va="top", color="#555", wrap=True,
    )
    ax.set_axis_off()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"-> {path.name}")


def main():
    for mode in config.MODES:
        plot_land_share(load_map_data(mode), mode,
                        config.OUTPUTS / f"map_land_share_{mode}_{config.YEAR}.png")


if __name__ == "__main__":
    main()
