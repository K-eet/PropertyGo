"""Page 2: interactive borough map. Green = low land share, red = high."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
from src.analysis import borough_shares
from src.ui import LAND_LABEL, gbp, load_borough_geojson, load_sales, method_caption

# Green (low) to red (high).
COLOURSCALE = "RdYlGn_r"


def share_label(mode: str, include_profit: bool) -> str:
    if mode == "new_build" and include_profit:
        return "Land and developer profit"
    return LAND_LABEL[mode]


def borough_map(stats: pd.DataFrame, geojson: dict, label: str, stretch: bool, marker) -> go.Figure:
    ok = stats[stats["enough_sales"]]
    few = stats[~stats["enough_sales"]]
    lo, hi = (ok["median_share"].min(), ok["median_share"].max()) if stretch else (0.0, 1.0)

    fig = go.Figure()
    fig.add_trace(go.Choropleth(
        geojson=geojson, featureidkey="properties.GSS_CODE", locations=ok["borough_code"],
        z=ok["median_share"], zmin=lo, zmax=hi, colorscale=COLOURSCALE,
        marker_line_color="white", marker_line_width=1,
        customdata=ok[["borough", "sales", "median_price", "median_build_cost"]],
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>" + label + " share: %{z:.0%}<br>"
            "Median price: £%{customdata[2]:,.0f}<br>Median build cost: £%{customdata[3]:,.0f}<br>"
            "%{customdata[1]:,} house sales<extra></extra>"
        ),
        colorbar=dict(title=dict(text=f"{label}<br>share of price"), tickformat=".0%", len=0.8),
    ))
    if len(few):
        fig.add_trace(go.Choropleth(
            geojson=geojson, featureidkey="properties.GSS_CODE", locations=few["borough_code"],
            z=[0] * len(few), colorscale=[[0, "#D9D9D9"], [1, "#D9D9D9"]], showscale=False,
            marker_line_color="white", customdata=few[["borough", "sales"]],
            hovertemplate="<b>%{customdata[0]}</b><br>Too few house sales (%{customdata[1]})<extra></extra>",
        ))
    fig.add_trace(go.Scattergeo(
        lon=ok["label_lon"], lat=ok["label_lat"], mode="text",
        text=[f"{v:.0%}" for v in ok["median_share"]], textfont=dict(size=11, color="black"),
        hoverinfo="skip",
    ))
    if marker:
        fig.add_trace(go.Scattergeo(
            lon=[marker["lon"]], lat=[marker["lat"]], mode="markers+text",
            marker=dict(size=12, color="#1F1F1F", symbol="star", line=dict(color="white", width=1)),
            text=[marker["postcode"]], textposition="top center",
            textfont=dict(size=12, color="#1F1F1F"), hoverinfo="text",
            hovertext=f"{marker['postcode']} ({marker['borough']})",
        ))
    fig.update_geos(fitbounds="locations", visible=False, projection_type="mercator")
    fig.update_layout(height=640, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
    return fig


mode = st.session_state["mode"]
cost_per_m2 = st.session_state["cost_per_m2"]

st.title("How much of a London house price is land?")

c1, c2 = st.columns([2, 1])
include_profit = False
if mode == "new_build":
    include_profit = c1.radio(
        "Colour by", options=[False, True], horizontal=True, key="include_profit",
        format_func=lambda x: "Land and developer profit" if x else "Land only",
        help="New build only. Developer profit is "
             f"{config.DEVELOPER_PROFIT_SHARE_OF_PRICE:.1%} of price (planning guidance: 15–20%).",
    )
full_scale = c2.toggle(
    "Full 0–100% colour scale", value=False, key="full_scale",
    help="Off (default): green = lowest borough, red = highest borough. "
         "On: green = 0%, red = 100%, so every map uses the same colours.",
)
stretch = not full_scale
label = share_label(mode, include_profit)

geojson = load_borough_geojson()
props = pd.DataFrame([f["properties"] for f in geojson["features"]])
stats = borough_shares(load_sales(), cost_per_m2, mode, include_profit).merge(
    props[["GSS_CODE", "NAME", "label_lon", "label_lat"]].rename(
        columns={"GSS_CODE": "borough_code", "NAME": "borough"}),
    on="borough_code",
)
ok = stats[stats["enough_sales"]]

st.write(
    f"**{label} as a share of the sale price**, median per borough, house sales {config.YEAR}. "
    f"{config.MODES[mode]}, build cost {gbp(cost_per_m2)}/m². "
    + ("**Red = highest borough, green = lowest.** " if stretch else "**Red = 100%, green = 0%.** ")
    + "Grey: too few house sales."
)
c1, c2, c3 = st.columns(3)
top, bottom = ok.loc[ok["median_share"].idxmax()], ok.loc[ok["median_share"].idxmin()]
c1.metric("Highest", f"{top['median_share']:.0%}", top["borough"], delta_color="off")
c2.metric("Lowest", f"{bottom['median_share']:.0%}", bottom["borough"], delta_color="off")
c3.metric("Middle borough", f"{ok['median_share'].median():.0%}",
          ok.sort_values("median_share").iloc[len(ok) // 2]["borough"], delta_color="off")

st.plotly_chart(
    borough_map(stats, geojson, label, stretch, st.session_state.get("last_lookup")),
    width="stretch", config={"displayModeBar": False, "scrollZoom": False},
)

with st.expander("Table of all boroughs", expanded=False):
    st.dataframe(
        ok.sort_values("median_share", ascending=False)[
            ["borough", "sales", "median_price", "median_build_cost", "median_share"]],
        hide_index=True, width="stretch",
        column_config={
            "borough": "Borough", "sales": "House sales",
            "median_price": st.column_config.NumberColumn("Median price", format="£%d"),
            "median_build_cost": st.column_config.NumberColumn("Median build cost", format="£%d"),
            "median_share": st.column_config.ProgressColumn(
                f"{label} share", min_value=0, max_value=1, format="percent"),
        },
    )

st.divider()
method_caption()
