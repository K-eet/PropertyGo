"""Demo: how much of a London house price is build cost, and who owns the land?

Run: .venv/bin/streamlit run app.py   (Windows: .venv\\Scripts\\streamlit run app.py)
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
from src.lookup import (
    format_address, normalise_postcode, postcode_info, postcode_sector,
    sales_at_postcode, sales_in_sector, split_price,
)
from src.streetmap import aggregate_ocod, sale_address, street_map

st.set_page_config(page_title="London house prices: land vs build cost", page_icon="🏠", layout="wide")

COLOURS = {"labour": "#4C78A8", "materials": "#9ECAE9", "land": "#E45756"}


@st.cache_data
def load_sales() -> pd.DataFrame:
    return pd.read_parquet(config.PROCESSED / f"land_share_london_houses_{config.YEAR}.parquet")


@st.cache_data
def load_summary() -> pd.DataFrame:
    return pd.read_csv(config.OUTPUTS / f"borough_summary_{config.YEAR}.csv")


TARGET_SALES_FILE = config.PROCESSED / f"kc_sales_{config.YEAR}.parquet"
TARGET_OCOD_FILE = config.PROCESSED / "kc_ocod.parquet"


def file_version(path):
    """Modification time, so cached data reloads after `python -m src.ocod` is rerun."""
    return path.stat().st_mtime if path.exists() else None


@st.cache_data
def load_target_sales(version) -> pd.DataFrame:
    return pd.read_parquet(TARGET_SALES_FILE)


@st.cache_data
def load_target_ocod(version):
    return pd.read_parquet(TARGET_OCOD_FILE) if version is not None else None


@st.cache_data
def ocod_per_postcode(ocod: pd.DataFrame) -> pd.DataFrame:
    return aggregate_ocod(ocod)


@st.cache_data(show_spinner=False)
def cached_postcode_info(postcode):
    return postcode_info(postcode)


def gbp(x) -> str:
    return f"£{x:,.0f}"


def split_chart(parts: dict) -> go.Figure:
    """One horizontal stacked bar: labour + materials + land and profit = price."""
    bars = [
        ("Labour (estimate)", parts["labour_est"], COLOURS["labour"]),
        ("Materials and other build costs", parts["materials_est"], COLOURS["materials"]),
        ("Land, profit and other costs", parts["land_and_profit"], COLOURS["land"]),
    ]
    fig = go.Figure()
    for name, value, colour in bars:
        share = value / parts["price"]
        fig.add_bar(
            y=["Sale price"], x=[value], name=name, orientation="h", marker_color=colour,
            text=f"{gbp(value)}<br>{share:.0%}" if share > 0.08 else "",
            textposition="inside", insidetextanchor="middle",
            hovertemplate=f"{name}: {gbp(value)} ({share:.0%})<extra></extra>",
        )
    fig.update_layout(
        barmode="stack", height=180, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=-0.35), xaxis=dict(tickprefix="£", tickformat=",.0f"),
        yaxis=dict(showticklabels=False),
    )
    return fig


def borough_chart(summary: pd.DataFrame, highlight_code: str) -> go.Figure:
    s = summary[summary["enough_sales"]].sort_values("median_land_share")
    colours = [COLOURS["land"] if c == highlight_code else "#CCCCCC" for c in s["borough_code"]]
    fig = go.Figure(go.Bar(
        x=s["median_land_share"], y=s["borough"], orientation="h", marker_color=colours,
        hovertemplate="%{y}: %{x:.0%}<extra></extra>",
    ))
    fig.update_layout(
        height=650, margin=dict(l=0, r=0, t=10, b=0), xaxis=dict(tickformat=".0%", range=[0, 1]),
    )
    return fig


def show_split(price, floor_area, cost_per_m2, heading):
    parts = split_price(price, floor_area, cost_per_m2)
    st.subheader(heading)
    c1, c2, c3 = st.columns(3)
    c1.metric("Sale price", gbp(parts["price"]))
    c2.metric("Estimated build cost", gbp(parts["build_cost"]))
    c3.metric("Land, profit and other", f"{parts['land_share']:.0%}")
    st.plotly_chart(split_chart(parts), width="stretch", config={"displayModeBar": False})
    if parts["land_share"] < 0:
        st.warning("The estimated build cost is higher than the price. The floor area or price may be wrong.")


# --- Street map tab ----------------------------------------------------------
def render_street_map(cost_per_m2):
    name = config.TARGET_BOROUGH_NAME
    kc = load_target_sales(file_version(TARGET_SALES_FILE))
    ocod = load_target_ocod(file_version(TARGET_OCOD_FILE))

    st.header(f"Walk {name}: land, not bricks")
    st.write(
        f"Every blue dot is a house sold in {name} in {config.YEAR}. Hover to see the sale price against "
        f"what it would cost to build that house (about **{gbp(cost_per_m2)} per m²**). "
        "The gap is the land, the developer's profit and other costs. "
        "Red circles are property titles currently held by companies registered **outside the UK**."
    )

    share = 1 - kc["tfarea"] * cost_per_m2 / kc["price"]
    gap = kc["price"] - kc["tfarea"] * cost_per_m2
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"House sales, {config.YEAR}", f"{len(kc):,}")
    c2.metric("Median sale price", gbp(kc["price"].median()))
    c3.metric("Median land share", f"{share.median():.0%}", help="(Sale price − build cost) ÷ sale price")
    if ocod is not None:
        c4.metric("Overseas-company titles", f"{len(ocod):,}", help="HM Land Registry OCOD, current snapshot")
    else:
        c4.metric("Median gap per house", gbp(gap.median()))

    if ocod is None:
        st.info(
            "Overseas ownership layer not loaded yet. Download the OCOD full file from "
            "[Use land and property data](https://use-land-property-data.service.gov.uk/datasets/ocod), "
            f"unzip it into `data/raw/ocod/`, then run `python -m src.ocod`."
        )
    st.plotly_chart(
        street_map(kc, ocod_per_postcode(ocod) if ocod is not None else None, cost_per_m2),
        width="stretch", config={"scrollZoom": True, "displaylogo": False},
    )

    left, right = st.columns([3, 2])
    with left:
        kc = kc.assign(label=kc.apply(sale_address, axis=1) + ", " + kc["postcode"]
                       + " — " + kc["price"].map(gbp))
        options = kc.sort_values("price", ascending=False)["label"].tolist()
        pick = st.selectbox("Look at one sale", options, index=0)
        row = kc[kc["label"] == pick].iloc[0]
        show_split(row["price"], row["tfarea"], cost_per_m2,
                   f"{sale_address(row.to_dict())}: sold {row['date']:%B %Y}, {row['tfarea']:.0f} m²")
        if row["offshore_company_title"]:
            st.error(f"This title is now held by {str(row['proprietor']).title()}, "
                     f"incorporated in {str(row['country_incorporated']).title()}.")
    with right:
        if ocod is not None:
            st.subheader("Where the owning companies are registered")
            countries = (ocod["country_incorporated"].fillna("Unknown").str.title()
                         .value_counts().head(10).rename_axis("Country").reset_index(name="Titles"))
            st.dataframe(countries, hide_index=True, width="stretch")
            matched = int(kc["offshore_company_title"].sum())
            st.caption(f"{matched} of {len(kc)} house sales in {config.YEAR} match a title now held by an "
                       "overseas company (same postcode and house number or name).")

    st.caption(
        f"**How to read this.** Build cost = EPC floor area × {gbp(cost_per_m2)}/m² (one London figure, "
        "provisional). The gap includes land, developer profit and other costs, not only land. Houses only "
        "for the land share; the red layer includes flats. OCOD lists overseas companies only, not "
        "individuals or UK companies, and shows who owns a title today, not who bought in "
        f"{config.YEAR}. Points are postcode centres, spread slightly when they share a postcode."
    )


# --- London lookup tab -------------------------------------------------------
def render_lookup(cost_per_m2):
    sales = load_sales()
    summary = load_summary()

    st.header("What are you really paying for?")
    st.write(
        f"Enter a London postcode. We compare the sale price of houses there with what it would "
        f"cost to build them today (about **{gbp(cost_per_m2)} per m²**). "
        f"The rest is mostly the value of the land."
    )

    with st.form("lookup"):
        c1, c2 = st.columns([2, 1])
        postcode_text = c1.text_input("Postcode", placeholder="e.g. E7 8HP")
        house = c2.text_input("House number or name (optional)", placeholder="e.g. 14")
        submitted = st.form_submit_button("Look up", type="primary")

    postcode = normalise_postcode(postcode_text)
    if submitted and not postcode:
        st.error("That does not look like a postcode.")
        return
    if not postcode:
        st.info("Try E7 8HP, W14 8JS or RM3 9RS.")
        return

    info = cached_postcode_info(postcode)
    if info is None:
        st.error(f"We could not find {postcode}. Check the postcode and try again.")
        return
    if not info["in_london"]:
        st.error(f"{postcode} is in {info['borough']}, not London. This demo covers London only.")
        return

    st.caption(f"{postcode} · {info['borough']}")

    # 1. This house, if it sold in the year.
    exact = sales_at_postcode(sales, postcode, house) if house else pd.DataFrame()
    if len(exact):
        row = exact.iloc[0]
        show_split(
            row["price"], row["tfarea"], cost_per_m2,
            f"{format_address(row.to_dict())} sold for {gbp(row['price'])} "
            f"({row['date']:%B %Y}), {row['tfarea']:.0f} m²",
        )
    else:
        if house:
            st.info(f"No house sale at {house}, {postcode} in {config.YEAR}. Showing nearby sales instead.")
        here = sales_at_postcode(sales, postcode)
        area = here if len(here) >= 3 else sales_in_sector(sales, postcode)
        label = postcode if len(here) >= 3 else f"postcode sector {postcode_sector(postcode)}"
        if len(area):
            show_split(
                area["price"].median(), area["tfarea"].median(), cost_per_m2,
                f"Typical house in {label}: {gbp(area['price'].median())}, "
                f"{area['tfarea'].median():.0f} m² ({len(area)} sale{'s' if len(area) != 1 else ''} in {config.YEAR})",
            )
        else:
            st.info(f"No house sales near {postcode} in {config.YEAR}. See the borough figures below.")

    # 2. Your own numbers.
    with st.expander("Try your own numbers"):
        c1, c2 = st.columns(2)
        my_price = c1.number_input("Sale price (£)", min_value=10_000, value=600_000, step=10_000)
        my_area = c2.number_input("Floor area (m²)", min_value=20, value=100, step=5)
        show_split(my_price, my_area, cost_per_m2, "Your house")

    # 3. Nearby sales table.
    nearby = sales_in_sector(sales, postcode)
    if len(nearby):
        with st.expander(f"House sales in {postcode_sector(postcode)} in {config.YEAR} ({len(nearby)})"):
            t = nearby.assign(
                address=nearby.apply(lambda r: format_address(r.to_dict()), axis=1),
                build_cost=nearby["tfarea"] * cost_per_m2,
            )
            t["land_share"] = 1 - t["build_cost"] / t["price"]
            st.dataframe(
                t[["address", "postcode", "date", "price", "tfarea", "build_cost", "land_share"]]
                .sort_values("date", ascending=False),
                hide_index=True, width="stretch",
                column_config={
                    "address": "Address", "postcode": "Postcode",
                    "date": st.column_config.DateColumn("Sold", format="D MMM YYYY"),
                    "price": st.column_config.NumberColumn("Price", format="£%d"),
                    "tfarea": st.column_config.NumberColumn("Floor area (m²)", format="%d"),
                    "build_cost": st.column_config.NumberColumn("Build cost", format="£%d"),
                    "land_share": st.column_config.ProgressColumn(
                        "Land share", min_value=0, max_value=1, format="percent"),
                },
            )
    st.map(pd.DataFrame({"lat": [info["lat"]], "lon": [info["lon"]]}), zoom=13, size=60)

    # 4. Borough context (at the default build cost).
    b = summary[summary["borough_code"] == info["borough_code"]]
    if len(b) and b["enough_sales"].iloc[0]:
        b = b.iloc[0]
        st.subheader(f"{b['borough']} compared with other boroughs")
        st.write(
            f"Median house price **{gbp(b['median_price'])}**, median land share "
            f"**{b['median_land_share']:.0%}** ({int(b['sales']):,} sales, "
            f"build cost {gbp(config.BUILD_COST_PER_M2)}/m²)."
        )
        st.plotly_chart(borough_chart(summary, info["borough_code"]), width="stretch",
                        config={"displayModeBar": False})


# --- Page --------------------------------------------------------------------
cost_per_m2 = st.sidebar.slider(
    "Build cost per m² (£)", min_value=1500, max_value=4500, step=100,
    value=config.BUILD_COST_PER_M2,
    help="Change this to see how the result depends on the build cost assumption.",
)
st.sidebar.caption(
    f"Default {gbp(config.BUILD_COST_PER_M2)}/m² is provisional. "
    f"Labour share of build cost: {config.LABOUR_SHARE:.0%} (national estimate)."
)

map_tab, lookup_tab = st.tabs([f"{config.TARGET_BOROUGH_NAME} street map", "London postcode lookup"])
with map_tab:
    render_street_map(cost_per_m2)
with lookup_tab:
    render_lookup(cost_per_m2)

st.divider()
st.caption(
    f"**Method.** Build cost = EPC floor area × build cost per m². Land share = (price − build cost) ÷ price. "
    f"It includes land, developer profit and other costs, not only land. The labour and materials split "
    f"is a national estimate ({config.LABOUR_SHARE:.0%} labour), not data for each house. Houses only, "
    f"standard sales, {config.YEAR}. EPC floor area can be old or incorrect.  \n"
    "**Sources.** HM Land Registry Price Paid Data; HM Land Registry Overseas companies that own property "
    "in England and Wales (OCOD); House Price per Square Metre (Price Paid × EPC, London Datastore); "
    "postcodes.io; GLA borough boundaries. Contains HM Land Registry data © Crown copyright and database "
    "right. Full list in ASSUMPTIONS.md."
)
