"""Postcode and address lookup for the demo."""
import re

import pandas as pd
import requests

import config

POSTCODES_API = "https://api.postcodes.io/postcodes/"
# Outward code (e.g. SW11, E7, EC2Y) then inward code (e.g. 6AB), no space.
UK_POSTCODE = re.compile(r"^[A-Z]{1,2}[0-9][A-Z0-9]?[0-9][A-Z]{2}$")


def normalise_postcode(text: str) -> str:
    """'sw11 6ab' -> 'SW11 6AB'. Returns '' if it does not look like a postcode."""
    s = re.sub(r"[^A-Z0-9]", "", (text or "").upper())
    if not UK_POSTCODE.match(s):
        return ""
    return f"{s[:-3]} {s[-3:]}"


def postcode_sector(postcode: str) -> str:
    """'SW11 6AB' -> 'SW11 6'."""
    return postcode[:-2]


def normalise_address_part(text) -> str:
    """Upper case, no punctuation, single spaces."""
    if pd.isna(text):
        return ""
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", str(text).upper())).strip()


def postcode_info(postcode: str):
    """Borough code, name and location from postcodes.io. None if not found."""
    try:
        r = requests.get(POSTCODES_API + postcode.replace(" ", ""), timeout=5)
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None
    res = r.json()["result"]
    return {
        "postcode": res["postcode"],
        "in_london": res.get("region") == "London",
        "borough_code": res["codes"]["admin_district"],
        "borough": res["admin_district"],
        "lat": res["latitude"],
        "lon": res["longitude"],
    }


def geocode_postcodes(postcodes, cache_path=config.PROCESSED / "postcode_centroids.parquet") -> pd.DataFrame:
    """Postcode centroids (postcode, lat, lon) from postcodes.io bulk, cached on disk.

    Postcodes that postcodes.io does not know (e.g. terminated) come back with no lat/lon.
    """
    wanted = sorted({p for p in postcodes if p})
    cache = pd.read_parquet(cache_path) if cache_path.exists() else pd.DataFrame(columns=["postcode", "lat", "lon"])
    todo = [p for p in wanted if p not in set(cache["postcode"])]
    rows = []
    for i in range(0, len(todo), config.POSTCODES_BULK_LIMIT):
        batch = todo[i:i + config.POSTCODES_BULK_LIMIT]
        r = requests.post(POSTCODES_API.rstrip("/"), json={"postcodes": batch}, timeout=30)
        r.raise_for_status()
        for item in r.json()["result"]:
            res = item["result"] or {}
            rows.append({"postcode": item["query"], "lat": res.get("latitude"), "lon": res.get("longitude")})
    if rows:
        cache = pd.concat([cache, pd.DataFrame(rows)], ignore_index=True)
        cache.to_parquet(cache_path, index=False)
    return cache[cache["postcode"].isin(wanted)].reset_index(drop=True)


def sales_at_postcode(df: pd.DataFrame, postcode: str, house: str = "") -> pd.DataFrame:
    """Sales at a postcode. If house is given, match it to PAON or SAON."""
    hits = df[df["postcode"] == postcode]
    house = normalise_address_part(house)
    if house:
        paon = hits["paon"].map(normalise_address_part)
        saon = hits["saon"].map(normalise_address_part)
        hits = hits[(paon == house) | (saon == house)]
    return hits.sort_values("date", ascending=False)


def sales_in_sector(df: pd.DataFrame, postcode: str) -> pd.DataFrame:
    """Sales in the same postcode sector (e.g. SW11 6)."""
    return df[df["postcode"].str.startswith(postcode_sector(postcode))]


def split_price(price: float, floor_area: float, cost_per_m2: float) -> dict:
    """Split a sale price into build cost (labour, materials) and land plus profit."""
    build = floor_area * cost_per_m2
    labour = build * config.LABOUR_SHARE
    return {
        "price": price,
        "build_cost": build,
        "labour_est": labour,
        "materials_est": build - labour,
        "land_and_profit": price - build,
        "land_share": (price - build) / price if price else float("nan"),
    }


def format_address(row) -> str:
    parts = [row.get("saon"), row.get("paon"), row.get("street")]
    return ", ".join(str(p).title() for p in parts if pd.notna(p) and str(p).strip())
