"""Overseas company ownership (Land Registry OCOD) for the target borough, joined to house sales.

Run: python -m src.ocod
Writes data/processed/kc_sales_<YEAR>.parquet and data/processed/kc_ocod.parquet.
"""
import re

import pandas as pd

import config
from src.lookup import geocode_postcodes, normalise_address_part, normalise_postcode

# Columns checked against the public example.csv (same layout as the full file).
OCOD_COLUMNS = {
    "Title Number": "title_number",
    "Tenure": "tenure",
    "Property Address": "property_address",
    "District": "district",
    "Region": "region",
    "Postcode": "postcode",
    "Multiple Address Indicator": "multiple_address",
    "Price Paid": "ocod_price_paid",
    "Proprietor Name (1)": "proprietor",
    "Proprietorship Category (1)": "proprietor_category",
    "Country Incorporated (1)": "country_incorporated",
    "Date Proprietor Added": "date_proprietor_added",
}

# First address part that starts with one of these is a flat or unit, not a whole house.
FLAT_WORDS = ("FLAT", "APARTMENT", "MAISONETTE", "UNIT", "STUDIO", "PENTHOUSE", "ROOM", "BASEMENT")
LEADING_NUMBER = re.compile(r"^(\d+[A-Z]?)\b")
TRAILING_POSTCODE = re.compile(r"\s*\([^)]*\)\s*$")


def find_ocod_file():
    """Newest OCOD full CSV in OCOD_DIR, or None if it has not been downloaded."""
    files = sorted(config.OCOD_DIR.glob(config.OCOD_GLOB))
    return files[-1] if files else None


def read_filtered(path, districts, nrows, encoding) -> pd.DataFrame:
    parts = []
    for chunk in pd.read_csv(path, usecols=list(OCOD_COLUMNS), dtype=str, nrows=nrows,
                             chunksize=100_000, encoding=encoding):
        if districts:
            chunk = chunk[chunk["District"].str.upper().isin(districts)]
        parts.append(chunk)
    return pd.concat(parts, ignore_index=True)


def load_ocod(path, districts=config.TARGET_DISTRICT_NAMES, nrows=None) -> pd.DataFrame:
    """Read OCOD and keep only titles in the target borough (filtered chunk by chunk)."""
    try:
        df = read_filtered(path, districts, nrows, "utf-8")
    except UnicodeDecodeError:
        df = read_filtered(path, districts, nrows, "cp1252")
    df = df.rename(columns=OCOD_COLUMNS)
    df["postcode"] = df["postcode"].fillna("").map(normalise_postcode)
    df["ocod_price_paid"] = pd.to_numeric(df["ocod_price_paid"], errors="coerce")
    df["date_proprietor_added"] = pd.to_datetime(
        df["date_proprietor_added"], format="mixed", dayfirst=True, errors="coerce")
    df["multiple_address"] = df["multiple_address"].eq("Y")
    return df


def address_parts(address) -> list:
    """'FLAT 1, 12 ONSLOW SQUARE, LONDON (SW7 3NP)' -> ['FLAT 1', '12 ONSLOW SQUARE', 'LONDON']."""
    text = "" if pd.isna(address) else TRAILING_POSTCODE.sub("", str(address))
    return [p for p in (normalise_address_part(x) for x in text.split(",")) if p]


def is_flat_address(address) -> bool:
    parts = address_parts(address)
    return bool(parts) and parts[0].startswith(FLAT_WORDS)


def house_tokens(address) -> set:
    """House numbers and names that could equal a Price Paid PAON.

    '12 ONSLOW SQUARE' -> {'12'}; 'ROSE COTTAGE, 5 X ROAD' -> {'ROSE COTTAGE', '5'}.
    Stops at the first part with a number, so the street and town are not tokens.
    """
    tokens = set()
    for part in address_parts(address)[:2]:
        m = LEADING_NUMBER.match(part)
        if m:
            tokens.add(m.group(1))
            break
        tokens.add(part)
    return tokens


def paon_token(paon) -> str:
    """Price Paid PAON as a match token: '12A' -> '12A', '12-14' -> '12', 'ROSE COTTAGE' as is."""
    p = normalise_address_part(paon)
    m = LEADING_NUMBER.match(p)
    return m.group(1) if m else p


def match_titles_to_sales(sales: pd.DataFrame, ocod: pd.DataFrame) -> pd.DataFrame:
    """Flag house sales whose postcode, house number/name and street match a single-address OCOD title.

    Flat titles and multiple-address titles are not matched to house sales. The street check stops
    '19 Francis House, Coleridge Gardens' matching '19 Burnaby Street' in the same postcode.
    """
    single = ocod[~ocod["multiple_address"] & ~ocod["is_flat"]]
    keys = single.assign(token=single["property_address"].map(house_tokens)).explode("token")
    keys = keys.dropna(subset=["token"])[
        ["postcode", "token", "property_address", "title_number", "proprietor", "country_incorporated"]
    ]

    s = sales.assign(token=sales["paon"].map(paon_token))
    cand = s[["transaction_id", "postcode", "token", "street"]].merge(keys, on=["postcode", "token"])
    ocod_addr = cand["property_address"].map(normalise_address_part)
    street = cand["street"].map(normalise_address_part)
    same_street = [st != "" and st in a for st, a in zip(street, ocod_addr)]
    cand = cand[same_street].drop_duplicates("transaction_id")[
        ["transaction_id", "title_number", "proprietor", "country_incorporated"]]

    out = s.drop(columns="token").merge(cand, on="transaction_id", how="left")
    out["offshore_company_title"] = out["title_number"].notna()

    per_postcode = ocod.groupby("postcode").size().rename("ocod_titles_in_postcode")
    out = out.merge(per_postcode, left_on="postcode", right_index=True, how="left")
    out["ocod_titles_in_postcode"] = out["ocod_titles_in_postcode"].fillna(0).astype(int)
    return out


def load_target_sales() -> pd.DataFrame:
    """House sales in the target borough, with build cost and land share (from src.analysis)."""
    df = pd.read_parquet(config.PROCESSED / f"land_share_london_houses_{config.YEAR}.parquet")
    return df[df["borough_code"] == config.TARGET_BOROUGH_CODE].reset_index(drop=True)


def add_location(df: pd.DataFrame) -> pd.DataFrame:
    centroids = geocode_postcodes(df["postcode"])
    return df.merge(centroids, on="postcode", how="left")


def main():
    sales = load_target_sales()
    print(f"{config.TARGET_BOROUGH_NAME} house sales, {config.YEAR}: {len(sales):,}")

    path = find_ocod_file()
    if path is None:
        print(f"No {config.OCOD_GLOB} in {config.OCOD_DIR}. Writing sales without the OCOD layer.")
        sales = sales.assign(offshore_company_title=False, ocod_titles_in_postcode=0,
                             title_number=None, proprietor=None, country_incorporated=None)
    else:
        ocod = load_ocod(path)
        ocod["is_flat"] = ocod["property_address"].map(is_flat_address)
        print(f"OCOD file: {path.name}")
        print(f"Overseas-company titles in {config.TARGET_BOROUGH_NAME}: {len(ocod):,} "
              f"({ocod['is_flat'].sum():,} flats, {ocod['multiple_address'].sum():,} multiple-address)")
        print("Top countries of incorporation:")
        print(ocod["country_incorporated"].value_counts().head(8).to_string())

        sales = match_titles_to_sales(sales, ocod)
        n = sales["offshore_company_title"].sum()
        print(f"House sales matched to an OCOD title (postcode + house number/name + street): "
              f"{n:,} of {len(sales):,} ({n / len(sales):.1%})")
        in_pc = (sales["ocod_titles_in_postcode"] > 0).mean()
        print(f"House sales in a postcode with at least one OCOD title: {in_pc:.1%}")

        ocod = add_location(ocod)
        print(f"OCOD titles with a location: {ocod['lat'].notna().mean():.1%}")
        ocod.to_parquet(config.PROCESSED / "kc_ocod.parquet", index=False)

    sales = add_location(sales)
    print(f"House sales with a location: {sales['lat'].notna().mean():.1%}")
    out = config.PROCESSED / f"kc_sales_{config.YEAR}.parquet"
    sales.to_parquet(out, index=False)
    print(f"-> {out.name}")


if __name__ == "__main__":
    main()
