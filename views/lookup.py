"""Page 1: look up a postcode or house and split its price."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
from src.costs import split_price
from src.lookup import (
    format_address, normalise_postcode, postcode_info, postcode_sector,
    sales_at_postcode, sales_in_sector,
)
from src.ui import LAND_LABEL, gbp, load_sales, method_caption

COLOURS = {"labour": "#4C78A8", "materials": "#9ECAE9", "other": "#EECA3B",
           "profit": "#B279A2", "land": "#E45756"}


@st.cache_data(show_spinner=False)
def cached_postcode_info(postcode):
    return postcode_info(postcode)


def split_chart(parts: dict, mode: str) -> go.Figure:
    """One horizontal stacked bar whose parts add up to the sale price."""
    bars = [
        ("Labour (estimate)", parts["labour_est"], COLOURS["labour"]),
        ("Materials and other build costs", parts["materials_est"], COLOURS["materials"]),
    ]
    if mode == "new_build":
        bars += [
            ("Fees, marketing and legal", parts["other_dev_costs"], COLOURS["other"]),
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


mode = st.session_state["mode"]
cost_per_m2 = st.session_state["cost_per_m2"]
sales = load_sales()

st.title("What are you really paying for?")
st.write(
    f"Enter a London postcode. We compare the sale price of houses there with what it would "
    f"cost to build them today (about **{gbp(cost_per_m2)} per m²**). "
    f"The rest is mostly the value of the land. Showing: **{config.MODES[mode].lower()}** "
    f"(change it in the sidebar)."
)

with st.form("lookup"):
    c1, c2 = st.columns([2, 1])
    # Default to the last search, so it is still there after a visit to the map page.
    postcode_text = c1.text_input("Postcode", placeholder="e.g. E7 8HP", key="postcode_text",
                                  value=st.session_state.get("saved_postcode", ""))
    house = c2.text_input("House number or name (optional)", placeholder="e.g. 14", key="house_text",
                          value=st.session_state.get("saved_house", ""))
    submitted = st.form_submit_button("Look up", type="primary")
if submitted:
    st.session_state["saved_postcode"], st.session_state["saved_house"] = postcode_text, house

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

# Remembered so the borough map can mark this postcode.
st.session_state["last_lookup"] = info
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
                   f"Switch the type of sale in the sidebar to see its actual split.")
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
        st.info(f"No house sales near {postcode} in {config.YEAR}. See the borough map instead.")

st.page_link("views/borough_map.py", label=f"See {info['borough']} on the borough map", icon="🗺️")

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

st.divider()
method_caption()
