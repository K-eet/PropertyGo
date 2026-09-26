"""Load and filter HM Land Registry Price Paid Data for London houses.

Run: python -m src.prices
"""
import pandas as pd

import config
from src.boroughs import ppd_district_to_code

# Official column order. The CSV has no header row. Source:
# https://www.gov.uk/guidance/about-the-price-paid-data#explanations-of-column-headers-in-the-ppd
PPD_COLUMNS = [
    "transaction_id", "price", "date", "postcode", "property_type", "old_new",
    "duration", "paon", "saon", "street", "locality", "town", "district",
    "county", "ppd_category", "record_status",
]


def load_ppd(path=config.PPD_FILE, nrows=None) -> pd.DataFrame:
    """Read the raw Price Paid CSV with named columns."""
    df = pd.read_csv(path, header=None, names=PPD_COLUMNS, dtype=str, nrows=nrows)
    df["price"] = df["price"].astype(int)
    df["date"] = pd.to_datetime(df["date"])
    return df


def filter_london_houses(df: pd.DataFrame) -> pd.DataFrame:
    """Keep London, houses only, standard (category A) sales."""
    keep = (
        (df["county"] == "GREATER LONDON")
        & df["property_type"].isin(config.HOUSE_TYPES)
        & df["ppd_category"].isin(config.PPD_CATEGORIES)
    )
    return df[keep].copy()


def add_borough_code(df: pd.DataFrame) -> pd.DataFrame:
    """Add the GSS borough code from the district name."""
    df["borough_code"] = ppd_district_to_code(df["district"])
    missing = df["borough_code"].isna().sum()
    if missing:
        raise ValueError(f"{missing} rows have no borough code")
    return df


def main():
    raw = load_ppd()
    london = raw[raw["county"] == "GREATER LONDON"]
    houses = add_borough_code(filter_london_houses(raw))
    out = config.PROCESSED / f"ppd_london_houses_{config.YEAR}.parquet"
    houses.to_parquet(out, index=False)
    print(f"All sales {config.YEAR}: {len(raw):,}")
    print(f"London sales: {len(london):,}")
    print(f"London houses, category A: {len(houses):,} -> {out.name}")
    print(houses["property_type"].value_counts().to_string())


if __name__ == "__main__":
    main()
