"""Borough map of median land share.

Run: python -m src.map
"""
import matplotlib.pyplot as plt
import pandas as pd

import config
from src.boroughs import load_boundaries


def load_map_data() -> "gpd.GeoDataFrame":
    summary = pd.read_csv(config.OUTPUTS / f"borough_summary_{config.YEAR}.csv")
    gdf = load_boundaries().merge(summary, left_on="GSS_CODE", right_on="borough_code", how="left")
    gdf.loc[gdf["enough_sales"] != True, "median_land_share"] = None
    return gdf


def plot_land_share(gdf, path):
    fig, ax = plt.subplots(figsize=(10, 8))
    gdf.plot(
        column="median_land_share", ax=ax, cmap="YlOrRd", edgecolor="white", linewidth=0.6,
        legend=True, missing_kwds={"color": "lightgrey", "label": f"Fewer than {config.MIN_SALES_PER_BOROUGH} sales"},
        legend_kwds={"label": "Median land share of sale price", "shrink": 0.6,
                     "format": lambda x, _: f"{x:.0%}"},
    )
    for _, row in gdf.iterrows():
        if pd.notna(row["median_land_share"]):
            p = row.geometry.representative_point()
            ax.annotate(f"{row['median_land_share']:.0%}", (p.x, p.y), ha="center",
                        va="center", fontsize=7)
    ax.set_title(
        f"How much of a London house price is not build cost?\n"
        f"Median land share per borough, house sales {config.YEAR}",
        fontsize=13, loc="left",
    )
    ax.text(
        0, -0.04,
        f"Land share = (sale price − floor area × £{config.BUILD_COST_PER_M2:,}/m²) ÷ sale price. "
        "Includes land, developer profit and other costs. Grey: City of London (too few house sales).\n"
        "Sources: HM Land Registry Price Paid Data; EPC floor area via House Price per Square Metre "
        "(London Datastore); GLA borough boundaries.",
        transform=ax.transAxes, fontsize=7, va="top", color="#555",
    )
    ax.set_axis_off()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    print(f"-> {path.name}")


def main():
    plot_land_share(load_map_data(), config.OUTPUTS / f"map_land_share_{config.YEAR}.png")


if __name__ == "__main__":
    main()
