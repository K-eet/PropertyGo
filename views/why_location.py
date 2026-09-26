"""Page: Why? Location. The same house costs the same to build everywhere, but not to buy."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
from src.ui import LAND_LABEL, LOCATIONS_FILE, SALES_FILE, file_version, gbp, load_located_sales, method_caption
from src.why import add_distance_km, msoa_by_distance, rank_correlation, same_house_by_distance

HOUSE_TYPES = {"T": "Terraced", "S": "Semi-detached", "D": "Detached"}


@st.cache_data
def located_with_distance(sales_version, locations_version):
    return add_distance_km(load_located_sales())


mode = st.session_state["mode"]
cost_per_m2 = st.session_state["cost_per_m2"]
label = LAND_LABEL[mode]

st.title("Why? Location.")
located = load_located_sales()
if located is None:
    st.error("Run `python -m src.locate` once to give every sale a location.")
    st.stop()
d = located_with_distance(file_version(SALES_FILE), file_version(LOCATIONS_FILE))

st.write(
    "Pick one kind of house. It costs about the same to build anywhere in London. "
    "Then see what the **same house** sells for at different distances from the centre. "
    "The difference is not the bricks. It is the land, and what the land gives access to: "
    "jobs, transport and the city."
)

c1, c2 = st.columns(2)
types = c1.multiselect("House type", options=list(HOUSE_TYPES), default=["T"], format_func=HOUSE_TYPES.get,
                       key="why_types") or ["T"]
area = c2.slider("Floor area (m²)", min_value=40, max_value=300, value=(90, 110), step=5, key="why_area")

t = same_house_by_distance(d, types, area, cost_per_m2, mode)
kind = " and ".join(HOUSE_TYPES[x].lower() for x in types)
if len(t) < 2 or t["sales"].min() < 10:
    st.warning("Few sales in some distance bands for this choice. Widen the floor area range.")

near, far = t.iloc[0], t.iloc[-1]
m1, m2, m3 = st.columns(3)
m1.metric(f"Build cost, {near['band']}", gbp(near["median_build"]))
m2.metric(f"Build cost, {far['band']}", gbp(far["median_build"]))
m3.metric("Price difference", gbp(near["median_price"] - far["median_price"]),
          f"{near['median_price'] / far['median_price']:.1f}× the price for the same house", delta_color="off")

fig = go.Figure()
fig.add_bar(x=t["band"].astype(str), y=t["median_build"], name="Build cost", marker_color="#4C78A8",
            hovertemplate="Build cost: £%{y:,.0f}<extra></extra>")
if mode == "new_build":
    fig.add_bar(x=t["band"].astype(str), y=t["median_other"], name="Fees, marketing, legal and developer profit",
                marker_color="#B279A2", hovertemplate="Fees and profit: £%{y:,.0f}<extra></extra>")
fig.add_bar(x=t["band"].astype(str), y=t["bar_land"], name=label, marker_color="#E45756",
            customdata=t[["median_price", "median_share", "sales"]],
            text=[f"{gbp(p)}<br>{s:.0%} {label.lower()}" for p, s in zip(t["median_price"], t["median_share"])],
            textposition="outside",
            hovertemplate=(label + ": £%{y:,.0f}<br>Median price: £%{customdata[0]:,.0f}<br>"
                           "%{customdata[2]:,} sales<extra></extra>"))
fig.update_layout(
    barmode="stack", height=460, margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", y=1.08),
    yaxis=dict(tickprefix="£", tickformat=",.0f", range=[0, t["median_price"].max() * 1.2]),
    xaxis_title="Distance from Charing Cross",
)
st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
st.caption(f"Median of {int(t['sales'].sum()):,} {kind} house sales of {area[0]}–{area[1]} m² in "
           f"{config.YEAR}, {config.MODES[mode].lower()}, build cost {gbp(cost_per_m2)}/m². "
           "Each bar is the median price; the red part is the median price minus the median build cost.")

st.subheader("Every neighbourhood tells the same story")
m = msoa_by_distance(d, cost_per_m2, mode)
rho = rank_correlation(m["share"], m["km"])
sc = go.Figure(go.Scatter(
    x=m["km"], y=m["share"], mode="markers",
    marker=dict(size=7, color=m["share"], colorscale="RdYlGn_r", opacity=0.75, line=dict(width=0)),
    customdata=m[["msoa_name", "sales", "median_price"]],
    hovertemplate=("<b>%{customdata[0]}</b><br>%{x:.1f} km from Charing Cross<br>" + label +
                   " share: %{y:.0%}<br>Median price £%{customdata[2]:,.0f}, %{customdata[1]} sales<extra></extra>"),
))
marker = st.session_state.get("last_lookup")
if marker:
    you = add_distance_km(pd.DataFrame([marker]))["km"].iloc[0]
    sc.add_vline(x=you, line_dash="dot", line_color="#1F1F1F",
                 annotation_text=f"{marker['postcode']}: {you:.1f} km", annotation_position="top right")
sc.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0), xaxis_title="Distance from Charing Cross (km)",
                 yaxis=dict(title=f"{label} share (median)", tickformat=".0%"))
st.plotly_chart(sc, width="stretch", config={"displayModeBar": False})
st.caption(f"{len(m)} neighbourhoods (MSOAs) with at least {config.MIN_SALES_PER_MSOA} house sales. "
           f"Rank correlation between distance and {label.lower()} share: **{rho:.2f}** "
           "(−1 would mean a perfect fall with distance). Distance is a stand-in for access to jobs and "
           "transport; it is not the only reason, but it is the biggest single pattern.")

st.divider()
method_caption()
