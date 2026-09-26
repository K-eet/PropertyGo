"""Build cost, land share and borough summary.

Run: python -m src.analysis
"""
import pandas as pd

import config
from src.boroughs import load_boundaries


def add_build_cost(df: pd.DataFrame, cost_per_m2=config.BUILD_COST_PER_M2) -> pd.DataFrame:
    """Estimated build cost = floor area x cost per m²."""
    df["build_cost"] = df["tfarea"] * cost_per_m2
    df["labour_cost_est"] = df["build_cost"] * config.LABOUR_SHARE
    return df


def add_land_share(df: pd.DataFrame) -> pd.DataFrame:
    """Land share = (sale price - build cost) / sale price. Includes profit and other costs."""
    df["land_share"] = (df["price"] - df["build_cost"]) / df["price"]
    df["price_per_m2"] = df["price"] / df["tfarea"]
    return df


def borough_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Medians per borough, with sensitivity range on build cost."""
    low, high = config.BUILD_COST_SENSITIVITY
    df = df.assign(
        land_share_high_cost=1 - df["tfarea"] * config.BUILD_COST_PER_M2 * high / df["price"],
        land_share_low_cost=1 - df["tfarea"] * config.BUILD_COST_PER_M2 * low / df["price"],
    )
    summary = df.groupby("borough_code").agg(
        sales=("price", "size"),
        median_price=("price", "median"),
        median_floor_area_m2=("tfarea", "median"),
        median_price_per_m2=("price_per_m2", "median"),
        median_build_cost=("build_cost", "median"),
        median_land_share=("land_share", "median"),
        land_share_if_cost_plus_20pct=("land_share_high_cost", "median"),
        land_share_if_cost_minus_20pct=("land_share_low_cost", "median"),
    )
    names = load_boundaries().set_index("GSS_CODE")["NAME"]
    summary.insert(0, "borough", names.reindex(summary.index))
    summary["enough_sales"] = summary["sales"] >= config.MIN_SALES_PER_BOROUGH
    return summary.sort_values("median_land_share", ascending=False)


def main():
    df = pd.read_parquet(config.PROCESSED / f"linked_london_houses_{config.YEAR}.parquet")
    df = add_land_share(add_build_cost(df))
    df.to_parquet(config.PROCESSED / f"land_share_london_houses_{config.YEAR}.parquet", index=False)

    summary = borough_summary(df)
    summary.to_csv(config.OUTPUTS / f"borough_summary_{config.YEAR}.csv")
    print(f"London median land share: {df['land_share'].median():.1%} "
          f"(build cost £{config.BUILD_COST_PER_M2:,}/m², {len(df):,} sales)")
    print(f"Share of sales where build cost > price: {(df['land_share'] < 0).mean():.1%}")
    cols = ["borough", "sales", "median_price", "median_build_cost", "median_land_share"]
    print(summary[cols].to_string(formatters={
        "median_price": "£{:,.0f}".format, "median_build_cost": "£{:,.0f}".format,
        "median_land_share": "{:.0%}".format}))


if __name__ == "__main__":
    main()
