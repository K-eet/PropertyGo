"""Give every London house sale a location (postcode centre) and a neighbourhood (MSOA 2011).

Run: python -m src.locate   (first run geocodes ~24,500 postcodes via postcodes.io; cached after)
"""
import geopandas as gpd
import pandas as pd

import config
from src.lookup import geocode_postcodes

OUT = config.PROCESSED / f"sale_locations_{config.YEAR}.parquet"


def load_msoas() -> gpd.GeoDataFrame:
    """983 London MSOAs (2011). The file has no CRS recorded; it is British National Grid."""
    g = gpd.read_file(config.MSOA_SHP)
    if g.crs is None:
        g = g.set_crs(27700)
    return g[["MSOA11CD", "MSOA11NM", "LAD11CD", "geometry"]].rename(
        columns={"MSOA11CD": "msoa_code", "MSOA11NM": "msoa_name", "LAD11CD": "msoa_borough_code"})


def assign_msoa(points: pd.DataFrame, msoas: gpd.GeoDataFrame) -> pd.DataFrame:
    """Spatial join of lat/lon points to MSOA polygons."""
    g = gpd.GeoDataFrame(points, geometry=gpd.points_from_xy(points["lon"], points["lat"]), crs=4326)
    j = gpd.sjoin(g.to_crs(msoas.crs), msoas, how="left", predicate="within")
    return pd.DataFrame(j.drop(columns=["geometry", "index_right"]))


def main():
    sales = pd.read_parquet(config.PROCESSED / f"land_share_london_houses_{config.YEAR}.parquet",
                            columns=["transaction_id", "postcode", "borough_code"])
    cents = geocode_postcodes(sales["postcode"])
    located = sales.merge(cents, on="postcode", how="left")
    have = located["lat"].notna()
    out = assign_msoa(located[have], load_msoas())
    out = pd.concat([out, located[~have]], ignore_index=True)

    print(f"Sales: {len(sales):,}. With a location: {have.sum():,} ({have.mean():.1%})")
    print(f"In an MSOA: {out['msoa_code'].notna().sum():,}")
    agree = (out["msoa_borough_code"] == out["borough_code"]).mean()
    print(f"MSOA borough agrees with Price Paid borough: {agree:.1%}")
    per = out.groupby("msoa_code").size()
    print(f"MSOAs with sales: {len(per)} of 983; median sales per MSOA {per.median():.0f}; "
          f"with at least {config.MIN_SALES_PER_MSOA}: {(per >= config.MIN_SALES_PER_MSOA).sum()}")
    out.to_parquet(OUT, index=False)
    print(f"-> {OUT.name}")


if __name__ == "__main__":
    main()
