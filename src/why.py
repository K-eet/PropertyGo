"""The two "Why?" sections: location (same house, different place) and years of earnings.

Run: python -m src.why   (writes tables and slide charts to outputs/)
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config
from src.boroughs import load_boundaries
from src.costs import split_price

BAND_LABELS = [f"{a}–{b} km" for a, b in zip(config.DISTANCE_BANDS_KM[:-1], config.DISTANCE_BANDS_KM[1:])]
BAND_LABELS[-1] = f"{config.DISTANCE_BANDS_KM[-2]}+ km"


# --- Location ------------------------------------------------------------------

def add_distance_km(df: pd.DataFrame) -> pd.DataFrame:
    """Straight-line distance from the centre of London (Charing Cross), in km."""
    lat0, lon0 = config.CENTRE_LAT_LON
    dlat = np.radians(df["lat"] - lat0)
    dlon = np.radians(df["lon"] - lon0) * np.cos(np.radians(lat0))
    df = df.copy()
    df["km"] = 6371 * np.sqrt(dlat ** 2 + dlon ** 2)
    df["band"] = pd.cut(df["km"], config.DISTANCE_BANDS_KM, labels=BAND_LABELS, include_lowest=True)
    return df


def same_house_by_distance(df, types, area_range, cost_per_m2, mode) -> pd.DataFrame:
    """Median price, build cost and land for one house type and size, by distance band."""
    lo, hi = area_range
    d = df[df["property_type"].isin(types) & df["tfarea"].between(lo, hi)]
    parts = split_price(d["price"], d["tfarea"], cost_per_m2, mode)
    d = d.assign(build=parts["build_cost"], land=parts["land"], share=parts["land_share"],
                 other=parts["other_dev_costs"] + parts["developer_profit"])
    return d.groupby("band", observed=True).agg(
        sales=("price", "size"), median_price=("price", "median"), median_floor_area=("tfarea", "median"),
        median_build=("build", "median"), median_other=("other", "median"),
        median_land=("land", "median"), median_share=("share", "median"),
    ).reset_index().assign(
        # Drawn so each bar is exactly the median price: medians of parts do not add up.
        bar_land=lambda t: t["median_price"] - t["median_build"] - t["median_other"])


def msoa_by_distance(df, cost_per_m2, mode, min_sales=config.MIN_SALES_PER_MSOA) -> pd.DataFrame:
    """One row per neighbourhood: median distance and median land share."""
    d = df.assign(share=split_price(df["price"], df["tfarea"], cost_per_m2, mode)["land_share"])
    m = d.groupby(["msoa_code", "msoa_name"]).agg(
        sales=("price", "size"), km=("km", "median"), share=("share", "median"),
        median_price=("price", "median")).reset_index()
    return m[m["sales"] >= min_sales]


def rank_correlation(a: pd.Series, b: pd.Series) -> float:
    return a.rank().corr(b.rank())


# --- Years of earnings ------------------------------------------------------------

def load_earnings(year=config.YEAR) -> pd.DataFrame:
    """Median gross annual residence-based earnings (full-time) per London borough, ONS Table 5b."""
    raw = pd.read_excel(config.EARNINGS_FILE, sheet_name=config.EARNINGS_SHEET, header=None)
    header = raw.index[raw.iloc[:, 0].astype(str).str.contains("Country/Region code")][0]
    t = pd.read_excel(config.EARNINGS_FILE, sheet_name=config.EARNINGS_SHEET, header=header)
    t.columns = [str(c).strip() for c in t.columns]
    t = t[t["Country/Region name"] == "London"]
    return pd.DataFrame({
        "borough_code": t["Local authority code"],
        "median_earnings": pd.to_numeric(t[str(year)], errors="coerce"),  # '[x]' = suppressed
    }).dropna().reset_index(drop=True)


def years_of_earnings(df, earnings, cost_per_m2, mode) -> pd.DataFrame:
    """Per borough: the median house price and its land part, in years of median local earnings."""
    parts = split_price(df["price"], df["tfarea"], cost_per_m2, mode)
    d = df.assign(land=parts["land"])
    b = d.groupby("borough_code").agg(
        sales=("price", "size"), median_price=("price", "median"), median_land=("land", "median"),
    ).reset_index().merge(earnings, on="borough_code")
    b = b[b["sales"] >= config.MIN_SALES_PER_BOROUGH]
    b["price_years"] = b["median_price"] / b["median_earnings"]
    b["land_years"] = b["median_land"] / b["median_earnings"]
    b["rest_years"] = b["price_years"] - b["land_years"]
    names = load_boundaries().set_index("GSS_CODE")["NAME"]
    b.insert(0, "borough", b["borough_code"].map(names))
    return b.sort_values("land_years", ascending=False).reset_index(drop=True)


# --- Slide charts ------------------------------------------------------------------

def plot_same_house(t, path, title_note):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    x = np.arange(len(t))
    ax.bar(x, t["median_build"], color="#4C78A8", label="Build cost")
    ax.bar(x, t["bar_land"], bottom=t["median_build"], color="#E45756", label="Land and location")
    for i, r in t.iterrows():
        ax.text(i, r["median_price"] + 15_000, f"£{r['median_price'] / 1000:,.0f}k\n"
                f"{r['median_share']:.0%} land", ha="center", fontsize=9)
    ax.set_xticks(x, t["band"].astype(str))
    ax.set_xlabel("Distance from Charing Cross")
    ax.yaxis.set_major_formatter(lambda v, _: f"£{v / 1000:,.0f}k")
    ax.set_ylim(0, t["median_price"].max() * 1.2)
    ax.set_title("Same bricks, different price\n" + title_note, loc="left", fontsize=12)
    ax.legend(frameon=False, loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, -0.02, "Sources: HM Land Registry Price Paid; EPC floor area (London Datastore); postcodes.io. "
             f"Build cost £{config.BUILD_COST_PER_M2:,}/m² (BCIS via Harrow and Croydon viability studies).",
             fontsize=7, color="#555")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"-> {path.name}")


def plot_years(b, path):
    b = b.sort_values("land_years")
    fig, ax = plt.subplots(figsize=(10, 9))
    y = np.arange(len(b))
    ax.barh(y, b["land_years"], color="#E45756", label="Land and location")
    ax.barh(y, b["rest_years"], left=b["land_years"], color="#4C78A8", label="Rest of the price (build cost)")
    for i, (_, r) in enumerate(b.iterrows()):
        ax.text(r["price_years"] + 0.3, i, f"{r['land_years']:.0f} of {r['price_years']:.0f} years",
                va="center", fontsize=7.5)
    ax.set_yticks(y, b["borough"], fontsize=8)
    ax.set_xlabel("Years of median local full-time earnings (before tax)")
    ax.set_title(f"How many years of local pay does the land cost?\nMedian house sold in {config.YEAR}, "
                 "resale", loc="left", fontsize=12)
    ax.legend(frameon=False, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, -0.01, "Sources: HM Land Registry Price Paid; EPC floor area; ONS house price to "
             f"residence-based earnings, Table 5b ({config.YEAR}). Build cost £{config.BUILD_COST_PER_M2:,}/m².",
             fontsize=7, color="#555")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"-> {path.name}")


def main():
    sales = pd.read_parquet(config.PROCESSED / f"land_share_london_houses_{config.YEAR}.parquet")
    loc = pd.read_parquet(config.PROCESSED / f"sale_locations_{config.YEAR}.parquet",
                          columns=["transaction_id", "lat", "lon", "msoa_code", "msoa_name"])
    located = add_distance_km(sales.merge(loc, on="transaction_id"))

    t = same_house_by_distance(located, ["T"], (90, 110), config.BUILD_COST_PER_M2, "resale")
    t.to_csv(config.OUTPUTS / f"why_location_{config.YEAR}.csv", index=False)
    print("Same house (terraced, 90–110 m²), resale:\n" + t.round(2).to_string(index=False))
    m = msoa_by_distance(located, config.BUILD_COST_PER_M2, "resale")
    print(f"Rank correlation, neighbourhood land share vs distance: {rank_correlation(m['share'], m['km']):.2f} "
          f"({len(m)} neighbourhoods)")
    plot_same_house(t, config.OUTPUTS / f"why_location_{config.YEAR}.png",
                    f"Terraced houses of 90–110 m² sold in {config.YEAR}: the build cost is the same, the price is not")

    b = years_of_earnings(sales, load_earnings(), config.BUILD_COST_PER_M2, "resale")
    b.to_csv(config.OUTPUTS / f"why_years_of_earnings_{config.YEAR}.csv", index=False)
    print("\nYears of median local earnings (resale):")
    print(b[["borough", "median_earnings", "price_years", "land_years"]].round(1).to_string(index=False))
    plot_years(b, config.OUTPUTS / f"why_years_of_earnings_{config.YEAR}.png")


if __name__ == "__main__":
    main()
