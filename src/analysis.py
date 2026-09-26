"""Build cost, land share (resale and new-build methods) and borough summary.

Run: python -m src.analysis
"""
import pandas as pd

import config
from src.boroughs import load_boundaries
from src.costs import split_price


def add_splits(df: pd.DataFrame) -> pd.DataFrame:
    """Add the price split for both modes, plus the ±build cost sensitivity."""
    low, high = config.BUILD_COST_SENSITIVITY
    df["price_per_m2"] = df["price"] / df["tfarea"]
    for mode in config.MODES:
        parts = split_price(df["price"], df["tfarea"], mode=mode)
        df["build_cost"] = parts["build_cost"]
        df["labour_cost_est"] = parts["labour_est"]
        df[f"land_{mode}"] = parts["land"]
        df[f"land_share_{mode}"] = parts["land_share"]
        for tag, k in (("cost_minus_20pct", low), ("cost_plus_20pct", high)):
            df[f"land_share_{mode}_{tag}"] = split_price(
                df["price"], df["tfarea"], config.BUILD_COST_PER_M2 * k, mode)["land_share"]
    return df


def borough_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Medians per borough. Both methods are applied to every sale at local prices."""
    aggs = dict(
        sales=("price", "size"),
        new_build_sales=("old_new", lambda s: (s == "Y").sum()),
        median_price=("price", "median"),
        median_floor_area_m2=("tfarea", "median"),
        median_price_per_m2=("price_per_m2", "median"),
        median_build_cost=("build_cost", "median"),
    )
    for mode in config.MODES:
        aggs[f"median_land_share_{mode}"] = (f"land_share_{mode}", "median")
        aggs[f"land_share_{mode}_if_cost_minus_20pct"] = (f"land_share_{mode}_cost_minus_20pct", "median")
        aggs[f"land_share_{mode}_if_cost_plus_20pct"] = (f"land_share_{mode}_cost_plus_20pct", "median")
    summary = df.groupby("borough_code").agg(**aggs)
    names = load_boundaries().set_index("GSS_CODE")["NAME"]
    summary.insert(0, "borough", names.reindex(summary.index))
    summary["enough_sales"] = summary["sales"] >= config.MIN_SALES_PER_BOROUGH
    return summary.sort_values("median_land_share_resale", ascending=False)


def new_vs_resale(df: pd.DataFrame) -> pd.DataFrame:
    """London-wide: actual new-build sales (new-build method) vs actual resales (resale method)."""
    rows = []
    for flag, mode in (("N", "resale"), ("Y", "new_build")):
        d = df[df["old_new"] == flag]
        rows.append({
            "sales_type": config.MODES[mode], "sales": len(d),
            "median_price": d["price"].median(), "median_floor_area_m2": d["tfarea"].median(),
            "median_price_per_m2": d["price_per_m2"].median(),
            "median_build_cost": d["build_cost"].median(),
            "median_land": d[f"land_{mode}"].median(),
            "median_land_share": d[f"land_share_{mode}"].median(),
        })
    return pd.DataFrame(rows)


def main():
    df = pd.read_parquet(config.PROCESSED / f"linked_london_houses_{config.YEAR}.parquet")
    df = add_splits(df)
    df.to_parquet(config.PROCESSED / f"land_share_london_houses_{config.YEAR}.parquet", index=False)

    summary = borough_summary(df)
    summary.to_csv(config.OUTPUTS / f"borough_summary_{config.YEAR}.csv")
    nvr = new_vs_resale(df)
    nvr.to_csv(config.OUTPUTS / f"new_vs_resale_{config.YEAR}.csv", index=False)

    print(f"{len(df):,} sales, build cost £{config.BUILD_COST_PER_M2:,}/m²")
    for mode, label in config.MODES.items():
        print(f"London median land share, {label}: {df[f'land_share_{mode}'].median():.1%}")
    print("\nActual sales by type:\n" + nvr.round(2).to_string(index=False))
    cols = ["borough", "sales", "new_build_sales", "median_price",
            "median_land_share_resale", "median_land_share_new_build"]
    print("\n" + summary[cols].to_string(formatters={
        "median_price": "£{:,.0f}".format,
        "median_land_share_resale": "{:.0%}".format,
        "median_land_share_new_build": "{:.0%}".format}))


if __name__ == "__main__":
    main()
