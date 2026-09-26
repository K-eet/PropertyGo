"""Demo: how much of a London house price is build cost?

Run: .venv/bin/streamlit run app.py
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
from src.lookup import (
    format_address, normalise_postcode, postcode_info, postcode_sector,
    sales_at_postcode, sales_in_sector, split_price,
)

st.set_page_config(page_title="London house prices: land vs build cost", page_icon="🏠", layout="centered")

COLOURS = {"labour": "#4C78A8", "materials": "#9ECAE9", "land": "#E45756"}


@st.cache_data
def load_sales() -> pd.DataFrame:
    return pd.read_parquet(config.PROCESSED / f"land_share_london_houses_{config.YEAR}.parquet")


@st.cache_data
def load_summary() -> pd.DataFrame:
    return pd.read_csv(config.OUTPUTS / f"borough_summary_{config.YEAR}.csv")


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


# --- Page ------------------------------------------------------------------
st.title("What are you really paying for?")
st.write(
    f"Enter a London postcode. We compare the sale price of houses there with what it would "
    f"cost to build them today (about **{gbp(config.BUILD_COST_PER_M2)} per m²**). "
    f"The rest is mostly the value of the land."
)

sales = load_sales()
summary = load_summary()

with st.form("lookup"):
    c1, c2 = st.columns([2, 1])
    postcode_text = c1.text_input("Postcode", placeholder="e.g. E7 8HP")
    house = c2.text_input("House number or name (optional)", placeholder="e.g. 14")
    submitted = st.form_submit_button("Look up", type="primary")

cost_per_m2 = st.sidebar.slider(
    "Build cost per m² (£)", min_value=1500, max_value=4500, step=100,
    value=config.BUILD_COST_PER_M2,
    help="Change this to see how the result depends on the build cost assumption.",
)
st.sidebar.caption(
    f"Default {gbp(config.BUILD_COST_PER_M2)}/m² is provisional. "
    f"Labour share of build cost: {config.LABOUR_SHARE:.0%} (national estimate)."
)

postcode = normalise_postcode(postcode_text)
if submitted and not postcode:
    st.error("That does not look like a postcode.")
    st.stop()
if not postcode:
    st.info("Try E7 8HP, W14 8JS or RM3 9RS.")
    st.stop()

info = cached_postcode_info(postcode)
if info is None:
    st.error(f"We could not find {postcode}. Check the postcode and try again.")
    st.stop()
if not info["in_london"]:
    st.error(f"{postcode} is in {info['borough']}, not London. This demo covers London only.")
    st.stop()

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

st.divider()
st.caption(
    f"**Method.** Build cost = EPC floor area × build cost per m². Land share = (price − build cost) ÷ price. "
    f"It includes land, developer profit and other costs, not only land. The labour and materials split "
    f"is a national estimate ({config.LABOUR_SHARE:.0%} labour), not data for each house. Houses only, "
    f"standard sales, {config.YEAR}. EPC floor area can be old or incorrect.  \n"
    "**Sources.** HM Land Registry Price Paid Data; House Price per Square Metre (Price Paid × EPC, "
    "London Datastore); postcodes.io; GLA borough boundaries. Contains HM Land Registry data © Crown "
    "copyright and database right. Full list in ASSUMPTIONS.md."
)
