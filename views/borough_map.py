"""Page 2: interactive London map at three levels of detail. Green = low land share, red = high."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
from src.analysis import area_shares, borough_shares, sale_shares
from src.ui import (
    LAND_LABEL, gbp, load_borough_geojson, load_located_sales, load_msoa_geojson, load_sales,
    method_caption,
)

# Green (low) to red (high).
COLOURSCALE = "RdYlGn_r"
DETAIL = {"borough": "Borough", "msoa": "Neighbourhood (MSOA)", "sales": "Individual sales"}
LONDON = dict(lat=51.49, lon=-0.11)


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



def lookup_marker(marker):
    """Star for the last looked-up postcode, on a tile map."""
    return go.Scattermap(
        lat=[marker["lat"]], lon=[marker["lon"]], mode="markers+text", text=[marker["postcode"]],
        textposition="top center", marker=dict(size=16, color="#1F1F1F"), hoverinfo="text",
        hovertext=f"{marker['postcode']} ({marker['borough']})", name="Your postcode",
    )


def tile_layout(fig, zoom, center=LONDON):
    fig.update_layout(
        map=dict(style="carto-positron", center=center, zoom=zoom),
        height=680, margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
    )
    return fig


def msoa_map(stats, geojson, borough_geojson, label, stretch, marker) -> go.Figure:
    ok = stats[stats["enough_sales"]]
    few = stats[~stats["enough_sales"]]
    lo, hi = (ok["median_share"].quantile(0.02), ok["median_share"].quantile(0.98)) if stretch else (0.0, 1.0)
    fig = go.Figure()
    fig.add_trace(go.Choroplethmap(
        geojson=geojson, featureidkey="properties.msoa_code", locations=ok["msoa_code"],
        z=ok["median_share"], zmin=lo, zmax=hi, colorscale=COLOURSCALE, marker_opacity=0.8,
        marker_line_width=0.3, marker_line_color="white",
        customdata=ok[["msoa_name", "sales", "median_price", "median_build_cost"]],
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>" + label + " share: %{z:.0%}<br>"
            "Median price: £%{customdata[2]:,.0f}<br>Median build cost: £%{customdata[3]:,.0f}<br>"
            "%{customdata[1]:,} house sales<extra></extra>"
        ),
        colorbar=dict(title=dict(text=f"{label}<br>share of price"), tickformat=".0%", len=0.8),
    ))
    if len(few):
        fig.add_trace(go.Choroplethmap(
            geojson=geojson, featureidkey="properties.msoa_code", locations=few["msoa_code"],
            z=[0] * len(few), colorscale=[[0, "#D9D9D9"], [1, "#D9D9D9"]], showscale=False,
            marker_opacity=0.6, marker_line_width=0.3, customdata=few[["msoa_name", "sales"]],
            hovertemplate="<b>%{customdata[0]}</b><br>Too few house sales (%{customdata[1]})<extra></extra>",
        ))
    # Borough outlines on top, for orientation.
    codes = [f["properties"]["GSS_CODE"] for f in borough_geojson["features"]]
    fig.add_trace(go.Choroplethmap(
        geojson=borough_geojson, featureidkey="properties.GSS_CODE", locations=codes,
        z=[0] * len(codes), colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], showscale=False,
        marker_line_width=1.5, marker_line_color="#444", hoverinfo="skip",
    ))
    if marker:
        fig.add_trace(lookup_marker(marker))
    return tile_layout(fig, zoom=9.1)


def sales_map(sales, shares, label, stretch, marker, cost_per_m2) -> go.Figure:
    lo, hi = (shares.quantile(0.05), shares.quantile(0.95)) if stretch else (0.0, 1.0)
    hover = (
        "<b>" + sales["address"] + "</b><br>Sold for " + sales["price"].map(gbp)
        + ", " + sales["tfarea"].round().astype(int).astype(str) + " m²"
        + "<br>Build cost (estimate): " + (sales["tfarea"] * cost_per_m2).map(gbp)
        + f"<br>{label} share: <b>" + (shares * 100).round().astype(int).astype(str) + "%</b>"
    )
    fig = go.Figure(go.Scattermap(
        lat=sales["lat_plot"], lon=sales["lon_plot"], mode="markers",
        marker=dict(size=5, color=shares, colorscale=COLOURSCALE, cmin=lo, cmax=hi, opacity=0.85,
                    colorbar=dict(title=dict(text=f"{label}<br>share of price"), tickformat=".0%", len=0.8)),
        text=hover, hoverinfo="text",
    ))
    if marker:
        fig.add_trace(lookup_marker(marker))
        return tile_layout(fig, zoom=14, center=dict(lat=marker["lat"], lon=marker["lon"]))
    return tile_layout(fig, zoom=9.1)


def top_bottom_metrics(ok, name_col, noun):
    c1, c2, c3 = st.columns(3)
    top, bottom = ok.loc[ok["median_share"].idxmax()], ok.loc[ok["median_share"].idxmin()]
    c1.metric("Highest", f"{top['median_share']:.0%}", top[name_col], delta_color="off")
    c2.metric("Lowest", f"{bottom['median_share']:.0%}", bottom[name_col], delta_color="off")
    c3.metric(f"Middle {noun}", f"{ok['median_share'].median():.0%}",
              ok.sort_values("median_share").iloc[len(ok) // 2][name_col], delta_color="off")


def area_table(ok, name_col, name_label, label):
    st.dataframe(
        ok.sort_values("median_share", ascending=False)[
            [name_col, "sales", "median_price", "median_build_cost", "median_share"]],
        hide_index=True, width="stretch",
        column_config={
            name_col: name_label, "sales": "House sales",
            "median_price": st.column_config.NumberColumn("Median price", format="£%d"),
            "median_build_cost": st.column_config.NumberColumn("Median build cost", format="£%d"),
            "median_share": st.column_config.ProgressColumn(
                f"{label} share", min_value=0, max_value=1, format="percent"),
        },
    )


mode = st.session_state["mode"]
cost_per_m2 = st.session_state["cost_per_m2"]
marker = st.session_state.get("last_lookup")

st.title("How much of a London house price is land?")

located = load_located_sales()
options = list(DETAIL) if located is not None else ["borough"]
detail = st.segmented_control(
    "Detail", options=options, format_func=DETAIL.get, default="borough", key="detail",
    help="Borough: 33 areas. Neighbourhood: 983 MSOAs (about 8,000 residents each). "
         "Individual sales: every house sale at its postcode centre.",
) or "borough"
if located is None:
    st.caption("Neighbourhood and individual-sale views need `python -m src.locate` to be run once.")

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
    help="Off (default): green = lowest, red = highest on this map. "
         "On: green = 0%, red = 100%, so every map uses the same colours.",
)
stretch = not full_scale
label = share_label(mode, include_profit)
unit = {"borough": "median per borough", "msoa": "median per neighbourhood (MSOA)",
        "sales": "each dot is one house sale"}[detail]
grey = {"borough": f"Grey: fewer than {config.MIN_SALES_PER_BOROUGH} house sales. ",
        "msoa": f"Grey: fewer than {config.MIN_SALES_PER_MSOA} house sales. ", "sales": ""}[detail]
st.write(
    f"**{label} as a share of the sale price**, {unit}, house sales {config.YEAR}. "
    f"{config.MODES[mode]}, build cost {gbp(cost_per_m2)}/m². "
    + ("**Red = highest, green = lowest on this map.** " if stretch else "**Red = 100%, green = 0%.** ")
    + grey
)
chart_config = {"displayModeBar": False, "scrollZoom": detail != "borough"}

if detail == "borough":
    geojson = load_borough_geojson()
    props = pd.DataFrame([f["properties"] for f in geojson["features"]])
    stats = borough_shares(load_sales(), cost_per_m2, mode, include_profit).merge(
        props[["GSS_CODE", "NAME", "label_lon", "label_lat"]].rename(
            columns={"GSS_CODE": "borough_code", "NAME": "borough"}),
        on="borough_code",
    )
    ok = stats[stats["enough_sales"]]
    top_bottom_metrics(ok, "borough", "borough")
    st.plotly_chart(borough_map(stats, geojson, label, stretch, marker), width="stretch", config=chart_config)
    with st.expander("Table of all boroughs"):
        area_table(ok, "borough", "Borough", label)

elif detail == "msoa":
    names = located.groupby("msoa_code")["msoa_name"].first()
    stats = area_shares(located, "msoa_code", cost_per_m2, mode, include_profit,
                        min_sales=config.MIN_SALES_PER_MSOA)
    stats["msoa_name"] = stats["msoa_code"].map(names)
    ok = stats[stats["enough_sales"]]
    top_bottom_metrics(ok, "msoa_name", "neighbourhood")
    st.plotly_chart(msoa_map(stats, load_msoa_geojson(), load_borough_geojson(), label, stretch, marker),
                    width="stretch", config=chart_config)
    st.caption(f"{len(ok)} of 983 neighbourhoods have at least {config.MIN_SALES_PER_MSOA} house sales. "
               "Scroll to zoom. MSOA 2011 boundaries.")
    with st.expander("Table of all neighbourhoods"):
        area_table(ok, "msoa_name", "Neighbourhood (MSOA)", label)

else:
    shares = sale_shares(located, cost_per_m2, mode, include_profit)
    c1, c2, c3 = st.columns(3)
    c1.metric("House sales", f"{len(located):,}")
    c2.metric(f"Median {label.lower()} share", f"{shares.median():.0%}")
    c3.metric("Sales above 80%", f"{(shares > 0.8).mean():.0%}")
    st.plotly_chart(sales_map(located, shares, label, stretch, marker, cost_per_m2),
                    width="stretch", config=chart_config)
    st.caption("Scroll to zoom. Dots are postcode centres, spread slightly when several sales share one. "
               + ("Zoomed to your last looked-up postcode. " if marker else "")
               + ("Colours stretched between the 5th and 95th percentile of sales." if stretch else ""))

st.divider()
method_caption()
