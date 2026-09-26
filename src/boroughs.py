"""London borough boundaries and name-to-code lookup."""
import geopandas as gpd

import config

# Price Paid district names that differ from the boundary file names.
PPD_NAME_FIXES = {"CITY OF WESTMINSTER": "WESTMINSTER"}


def load_boundaries() -> gpd.GeoDataFrame:
    """Load the 33 London boroughs (British National Grid)."""
    gdf = gpd.read_file(config.BOROUGH_SHP)
    return gdf[["NAME", "GSS_CODE", "HECTARES", "ONS_INNER", "geometry"]]


def name_to_code() -> dict:
    """Map upper-case borough name to GSS code."""
    b = load_boundaries()
    return dict(zip(b.NAME.str.upper(), b.GSS_CODE))


def ppd_district_to_code(districts):
    """Convert a Series of Price Paid district names to GSS codes."""
    lookup = name_to_code()
    return districts.replace(PPD_NAME_FIXES).map(lookup)
