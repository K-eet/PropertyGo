"""Demo: how much of a London house price is build cost?

Run: .venv/bin/streamlit run app.py
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
from src.costs import split_price
from src.lookup import (
    format_address, normalise_postcode, postcode_info, postcode_sector,
    sales_at_postcode, sales_in_sector,
)

st.set_page_config(page_title="London house prices: land vs build cost", page_icon="🏠", layout="centered")

COLOURS = {"labour": "#4C78A8", "materials": "#9ECAE9", "other": "#EECA3B",
           "profit": "#B279A2", "land": "#E45756"}
LAND_LABEL = {"resale": "Land and location", "new_build": "Land"}


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


def split_chart(parts: dict, mode: str) -> go.Figure:
    """One horizontal stacked bar whose parts add up to the sale price."""
    bars = [
        ("Labour (estimate)", parts["labour_est"], COLOURS["labour"]),
        ("Materials and other build costs", parts["materials_est"], COLOURS["materials"]),
    ]
    if mode == "new_build":
        bars += [
            ("Fees, finance, sales", parts["other_dev_costs"], COLOURS["other"]),
            ("Developer profit", parts["developer_profit"], COLOURS["profit"]),
        ]
    bars.append((LAND_LABEL[mode], parts["land"], COLOURS["land"]))
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


def borough_chart(summary: pd.DataFrame, highlight_code: str, mode: str) -> go.Figure:
    col = f"median_land_share_{mode}"
    s = summary[summary["enough_sales"]].sort_values(col)
    colours = [COLOURS["land"] if c == highlight_code else "#CCCCCC" for c in s["borough_code"]]
    fig = go.Figure(go.Bar(
        x=s[col], y=s["borough"], orientation="h", marker_color=colours,
        hovertemplate="%{y}: %{x:.0%}<extra></extra>",
    ))
    fig.update_layout(
        height=650, margin=dict(l=0, r=0, t=10, b=0), xaxis=dict(tickformat=".0%", range=[0, 1]),
    )
    return fig


def show_split(price, floor_area, cost_per_m2, heading, mode):
    parts = split_price(price, floor_area, cost_per_m2, mode)
    st.subheader(heading)
    c1, c2, c3 = st.columns(3)
    c1.metric("Sale price", gbp(parts["price"]))
    c2.metric("Estimated build cost", gbp(parts["build_cost"]))
    c3.metric(f"{LAND_LABEL[mode]} share", f"{parts['land_share']:.0%}")
    st.plotly_chart(split_chart(parts, mode), width="stretch", config={"displayModeBar": False})
    if parts["land_share"] < 0:
        st.warning("The estimated costs are higher than the price. The floor area or price may be wrong.")


# --- Page ------------------------------------------------------------------
st.title("What are you really paying for?")
st.write(
    f"Enter a London postcode. We compare the sale price of houses there with what it would "
    f"cost to build them today (about **{gbp(config.BUILD_COST_PER_M2)} per m²**). "
    f"The rest is mostly the value of the land."
)
mode = st.radio(
    "Type of sale", options=list(config.MODES), format_func=config.MODES.get, horizontal=True,
    help="Resale: a homeowner sells, so there is no developer profit. New build: a developer also "
         "pays fees, finance and sales costs, and takes a profit, before what is left for the land.",
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
    sold_new = row["old_new"] == "Y"
    show_split(
        row["price"], row["tfarea"], cost_per_m2,
        f"{format_address(row.to_dict())} sold {'new ' if sold_new else ''}for {gbp(row['price'])} "
        f"({row['date']:%B %Y}), {row['tfarea']:.0f} m²", mode,
    )
    if sold_new != (mode == "new_build"):
        st.caption(f"This house was sold {'new' if sold_new else 'as a resale'}. "
                   f"Switch the type of sale above to see its actual split.")
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
            mode,
        )
    else:
        st.info(f"No house sales near {postcode} in {config.YEAR}. See the borough figures below.")

# 2. Your own numbers.
with st.expander("Try your own numbers"):
    c1, c2 = st.columns(2)
    my_price = c1.number_input("Sale price (£)", min_value=10_000, value=600_000, step=10_000)
    my_area = c2.number_input("Floor area (m²)", min_value=20, value=100, step=5)
    show_split(my_price, my_area, cost_per_m2, "Your house", mode)

# 3. Nearby sales table.
nearby = sales_in_sector(sales, postcode)
if len(nearby):
    with st.expander(f"House sales in {postcode_sector(postcode)} in {config.YEAR} ({len(nearby)})"):
        t = nearby.assign(
            address=nearby.apply(lambda r: format_address(r.to_dict()), axis=1),
            build_cost=nearby["tfarea"] * cost_per_m2,
            new_build=nearby["old_new"] == "Y",
            land_share=split_price(nearby["price"], nearby["tfarea"], cost_per_m2, mode)["land_share"],
        )
        st.dataframe(
            t[["address", "postcode", "date", "new_build", "price", "tfarea", "build_cost", "land_share"]]
            .sort_values("date", ascending=False),
            hide_index=True, width="stretch",
            column_config={
                "address": "Address", "postcode": "Postcode",
                "date": st.column_config.DateColumn("Sold", format="D MMM YYYY"),
                "new_build": st.column_config.CheckboxColumn("Sold new"),
                "price": st.column_config.NumberColumn("Price", format="£%d"),
                "tfarea": st.column_config.NumberColumn("Floor area (m²)", format="%d"),
                "build_cost": st.column_config.NumberColumn("Build cost", format="£%d"),
                "land_share": st.column_config.ProgressColumn(
                    f"{LAND_LABEL[mode]} share", min_value=0, max_value=1, format="percent"),
            },
        )
st.map(pd.DataFrame({"lat": [info["lat"]], "lon": [info["lon"]]}), zoom=13, size=60)

# 4. Borough context (at the default build cost).
b = summary[summary["borough_code"] == info["borough_code"]]
if len(b) and b["enough_sales"].iloc[0]:
    b = b.iloc[0]
    st.subheader(f"{b['borough']} compared with other boroughs")
    st.write(
        f"Median house price **{gbp(b['median_price'])}**, median {LAND_LABEL[mode].lower()} share "
        f"**{b[f'median_land_share_{mode}']:.0%}** ({config.MODES[mode].lower()}, "
        f"{int(b['sales']):,} sales, build cost {gbp(config.BUILD_COST_PER_M2)}/m²)."
    )
    st.plotly_chart(borough_chart(summary, info["borough_code"], mode), width="stretch",
                    config={"displayModeBar": False})

st.divider()
st.caption(
    f"**Method.** Build cost = EPC floor area × build cost per m². "
    f"Resale: land and location = price − build cost; a homeowner seller makes no developer profit. "
    f"New build: land = price − build cost − fees, finance and sales "
    f"({config.OTHER_DEV_COSTS_SHARE_OF_BUILD:.0%} of build cost, provisional) − developer profit "
    f"({config.DEVELOPER_PROFIT_SHARE_OF_PRICE:.1%} of price, planning guidance: 15–20%). "
    f"The labour and materials split "
    f"is a national estimate ({config.LABOUR_SHARE:.0%} labour), not data for each house. Houses only, "
    f"standard sales, {config.YEAR}. EPC floor area can be old or incorrect.  \n"
    "**Sources.** HM Land Registry Price Paid Data; House Price per Square Metre (Price Paid × EPC, "
    "London Datastore); postcodes.io; GLA borough boundaries. Contains HM Land Registry data © Crown "
    "copyright and database right. Full list in ASSUMPTIONS.md."
)
