"""Shared helpers for the Streamlit pages."""
import pandas as pd
import streamlit as st
from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.polygon import orient

import config
from src.boroughs import load_boundaries

LAND_LABEL = {"resale": "Land and location", "new_build": "Land"}


def gbp(x) -> str:
    return f"£{x:,.0f}"


@st.cache_data
def load_sales() -> pd.DataFrame:
    return pd.read_parquet(config.PROCESSED / f"land_share_london_houses_{config.YEAR}.parquet")


def clockwise(geom):
    """Plotly's geo maps (d3) need clockwise outer rings, or a shape fills the whole globe."""
    if isinstance(geom, Polygon):
        return orient(geom, sign=-1.0)
    if isinstance(geom, MultiPolygon):
        return MultiPolygon([orient(g, sign=-1.0) for g in geom.geoms])
    return geom


@st.cache_data
def load_borough_geojson() -> dict:
    """Borough outlines in WGS84, simplified for a fast web map."""
    gdf = load_boundaries().to_crs(4326)
    gdf["geometry"] = gdf.geometry.simplify(0.0003).apply(clockwise)
    gdf["label_lon"] = gdf.geometry.representative_point().x
    gdf["label_lat"] = gdf.geometry.representative_point().y
    return gdf.__geo_interface__


def method_caption():
    st.caption(
        f"**Method.** Build cost = EPC floor area × build cost per m². "
        f"Resale: land and location = price − build cost; a homeowner seller makes no developer profit. "
        f"New build: land = price − build cost − professional fees "
        f"({config.PROFESSIONAL_FEES_SHARE_OF_BUILD:.0%} of build cost) − marketing and legal "
        f"({config.MARKETING_AND_LEGAL_SHARE_OF_PRICE:.2%} of price) − developer profit "
        f"({config.DEVELOPER_PROFIT_SHARE_OF_PRICE:.1%} of price; planning guidance 15–20%). "
        f"Finance is not included, so new-build land is slightly overstated. The labour and materials "
        f"split is a national estimate ({config.LABOUR_SHARE:.0%} labour, ONS input-output tables 2023), "
        f"not data for each house. Houses only, standard sales, {config.YEAR}. EPC floor area can be old "
        f"or incorrect.  \n"
        "**Sources.** HM Land Registry Price Paid Data; House Price per Square Metre (Price Paid × EPC, "
        "London Datastore); postcodes.io; GLA borough boundaries; build cost and appraisal assumptions "
        "from BCIS via Harrow (Oct 2024) and Croydon (2024) Local Plan Viability Assessments; Planning "
        "Practice Guidance: Viability. Contains HM Land Registry data © Crown copyright and database "
        "right. Full list in ASSUMPTIONS.md."
    )
