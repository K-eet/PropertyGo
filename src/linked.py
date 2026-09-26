"""Pre-linked Price Paid x EPC data (House Price per Square Metre, London Datastore).

Replaces our own address matching. Each row is one sale with EPC floor area.
Run: python -m src.linked
"""
import pandas as pd

import config
from src.boroughs import load_boundaries
from src.prices import add_borough_code, filter_london_houses, load_ppd


def load_hpm_london() -> pd.DataFrame:
    """Read the 33 London borough files (all years)."""
    codes = set(load_boundaries().GSS_CODE)
    parts = []
    for f in sorted(config.HPM_DIR.glob("*.csv")):
        if pd.read_csv(f, usecols=["lad23cd"], nrows=1)["lad23cd"].iloc[0] in codes:
            parts.append(pd.read_csv(f, low_memory=False))
    return pd.concat(parts, ignore_index=True)


def link_to_ppd(hpm: pd.DataFrame, ppd: pd.DataFrame) -> pd.DataFrame:
    """Keep linked sales that are in our filtered Price Paid set (houses, category A)."""
    keep = hpm[["transactionid", "tfarea", "numberrooms", "classt", "CONSTRUCTION_AGE_BAND"]]
    return ppd.merge(keep, left_on="transaction_id", right_on="transactionid", how="inner")


def clean_floor_area(df: pd.DataFrame) -> pd.DataFrame:
    """Drop floor areas outside the sanity limits in config."""
    ok = df["tfarea"].between(config.FLOOR_AREA_MIN_M2, config.FLOOR_AREA_MAX_M2)
    return df[ok].copy()


def main():
    hpm = load_hpm_london()
    hpm = hpm[hpm["year"] == config.YEAR]
    ppd = add_borough_code(filter_london_houses(load_ppd()))
    linked = link_to_ppd(hpm, ppd)
    clean = clean_floor_area(linked)

    match_rate = len(linked) / len(ppd)
    print(f"London houses, category A, {config.YEAR}: {len(ppd):,}")
    print(f"Linked to an EPC: {len(linked):,} ({match_rate:.1%})")
    print(f"After floor area limits: {len(clean):,} ({len(clean) / len(ppd):.1%})")
    print(clean.groupby("property_type").size().to_string())

    out = config.PROCESSED / f"linked_london_houses_{config.YEAR}.parquet"
    clean.to_parquet(out, index=False)
    print(f"-> {out.name}")


if __name__ == "__main__":
    main()
