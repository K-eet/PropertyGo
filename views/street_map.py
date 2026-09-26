"""Page 3: street map of one borough. House sales (price vs build cost) and overseas-company titles."""
import pandas as pd
import streamlit as st

import config
from src.costs import split_price
from src.streetmap import aggregate_ocod, sale_address, street_map
from src.ui import LAND_LABEL, gbp, method_caption

SALES_FILE = config.PROCESSED / f"kc_sales_{config.YEAR}.parquet"
OCOD_FILE = config.PROCESSED / "kc_ocod.parquet"


def file_version(path):
    """Modification time, so cached data reloads after `python -m src.ocod` is rerun."""
    return path.stat().st_mtime if path.exists() else None


@st.cache_data
def load_target_sales(version) -> pd.DataFrame:
    return pd.read_parquet(SALES_FILE)


@st.cache_data
def load_target_ocod(version):
    return pd.read_parquet(OCOD_FILE) if version is not None else None


@st.cache_data
def ocod_per_postcode(ocod: pd.DataFrame) -> pd.DataFrame:
    return aggregate_ocod(ocod)


mode = st.session_state["mode"]
cost_per_m2 = st.session_state["cost_per_m2"]
name = config.TARGET_BOROUGH_NAME
label = LAND_LABEL[mode]

st.title(f"Walk {name}: land, not bricks")
if file_version(SALES_FILE) is None:
    st.error("Street map data not built yet. Run `python -m src.ocod`.")
    st.stop()

kc = load_target_sales(file_version(SALES_FILE))
ocod = load_target_ocod(file_version(OCOD_FILE))
parts = split_price(kc["price"], kc["tfarea"], cost_per_m2, mode)

st.write(
    f"Every blue dot is a house sold in {name} in {config.YEAR}. Hover to see the sale price against "
    f"what it would cost to build that house (about **{gbp(cost_per_m2)} per m²**). "
    f"Showing: **{config.MODES[mode].lower()}** (change it in the sidebar). "
    "Red circles are property titles currently held by companies registered **outside the UK**."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric(f"House sales, {config.YEAR}", f"{len(kc):,}")
c2.metric("Median sale price", gbp(kc["price"].median()))
c3.metric(f"Median {label.lower()} share", f"{parts['land_share'].median():.0%}")
if ocod is not None:
    c4.metric("Overseas-company titles", f"{len(ocod):,}", help="HM Land Registry OCOD, current snapshot")
else:
    c4.metric(f"Median {label.lower()} per house", gbp(parts["land"].median()))
    st.info(
        "Overseas ownership layer not loaded yet. Download the OCOD full file from "
        "[Use land and property data](https://use-land-property-data.service.gov.uk/datasets/ocod), "
        "unzip it into `data/raw/ocod/`, then run `python -m src.ocod`."
    )

st.plotly_chart(
    street_map(kc, ocod_per_postcode(ocod) if ocod is not None else None, cost_per_m2, mode),
    width="stretch", config={"scrollZoom": True, "displaylogo": False},
)

left, right = st.columns([3, 2])
with left:
    kc = kc.assign(label=kc.apply(sale_address, axis=1) + ", " + kc["postcode"] + " — " + kc["price"].map(gbp))
    pick = st.selectbox("Look at one sale", kc.sort_values("price", ascending=False)["label"].tolist())
    row = kc[kc["label"] == pick].iloc[0]
    p = split_price(row["price"], row["tfarea"], cost_per_m2, mode)
    st.subheader(f"{sale_address(row.to_dict())}: sold {row['date']:%B %Y}, {row['tfarea']:.0f} m²")
    m1, m2, m3 = st.columns(3)
    m1.metric("Sale price", gbp(p["price"]))
    m2.metric("Estimated build cost", gbp(p["build_cost"]))
    m3.metric(f"{label} share", f"{p['land_share']:.0%}", gbp(p["land"]), delta_color="off")
    if row["offshore_company_title"]:
        st.error(f"This title is now held by {str(row['proprietor']).title()}, "
                 f"incorporated in {str(row['country_incorporated']).title()}.")
with right:
    if ocod is not None:
        st.subheader("Where the owning companies are registered")
        countries = (ocod["country_incorporated"].fillna("Unknown").str.title()
                     .value_counts().head(10).rename_axis("Country").reset_index(name="Titles"))
        st.dataframe(countries, hide_index=True, width="stretch")
        st.caption(f"{int(kc['offshore_company_title'].sum())} of {len(kc)} house sales in {config.YEAR} "
                   "match a title now held by an overseas company (same postcode and house number or name).")

st.caption(
    "**Street map.** Houses only for the land share; the red layer includes flats. OCOD lists overseas "
    "companies only, not individuals or UK companies, and shows who owns a title today, not who bought "
    f"in {config.YEAR}. Points are postcode centres, spread slightly when they share a postcode. "
    "Sources: HM Land Registry OCOD; postcodes.io."
)
st.divider()
method_caption()
