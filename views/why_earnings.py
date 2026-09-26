"""Page: Why does it matter? The land alone, in years of local earnings."""
import plotly.graph_objects as go
import streamlit as st

import config
from src.ui import LAND_LABEL, gbp, load_sales, method_caption
from src.why import load_earnings, years_of_earnings


@st.cache_data
def earnings():
    return load_earnings()


mode = st.session_state["mode"]
cost_per_m2 = st.session_state["cost_per_m2"]
label = LAND_LABEL[mode]

st.title("Why it matters: years of pay for the land alone")
st.write(
    f"How many years of the **median full-time salary of people living in each borough** would it take "
    f"to pay for the median house? And how much of that is just the {label.lower()}? "
    "Before tax, spending nothing else."
)

b = years_of_earnings(load_sales(), earnings(), cost_per_m2, mode)
top, bottom = b.iloc[0], b.iloc[-1]
marker = st.session_state.get("last_lookup")
you = b[b["borough_code"] == marker["borough_code"]] if marker else b.iloc[0:0]

c1, c2, c3 = st.columns(3)
c1.metric(f"{label}: most years", f"{top['land_years']:.0f} years", top["borough"], delta_color="off")
c2.metric(f"{label}: fewest years", f"{bottom['land_years']:.0f} years", bottom["borough"], delta_color="off")
if len(you):
    y = you.iloc[0]
    c3.metric(f"{y['borough']} (your postcode)", f"{y['land_years']:.0f} years",
              f"of {y['price_years']:.0f} years for the whole house", delta_color="off")
else:
    c3.metric("Middle borough", f"{b['land_years'].median():.0f} years",
              b.sort_values("land_years").iloc[len(b) // 2]["borough"], delta_color="off")

s = b.sort_values("land_years")
highlight = marker["borough_code"] if marker else None
fig = go.Figure()
fig.add_bar(
    y=s["borough"], x=s["land_years"], orientation="h", name=label,
    marker_color=["#B22222" if c == highlight else "#E45756" for c in s["borough_code"]],
    customdata=s[["median_price", "median_land", "median_earnings"]],
    hovertemplate=("<b>%{y}</b><br>" + label + ": %{x:.1f} years<br>Median house £%{customdata[0]:,.0f}, "
                   "of which " + label.lower() + " £%{customdata[1]:,.0f}<br>"
                   "Median local full-time pay £%{customdata[2]:,.0f}<extra></extra>"),
)
fig.add_bar(
    y=s["borough"], x=s["rest_years"], orientation="h", name="Rest of the price",
    marker_color=["#2F5C8A" if c == highlight else "#4C78A8" for c in s["borough_code"]],
    text=[f"{l:.0f} of {p:.0f} years" for l, p in zip(s["land_years"], s["price_years"])],
    textposition="outside", hovertemplate="Rest of the price: %{x:.1f} years<extra></extra>",
)
fig.update_layout(
    barmode="stack", height=820, margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", y=1.03),
    xaxis=dict(title="Years of median local full-time earnings (before tax)",
               range=[0, s["price_years"].max() * 1.15]),
)
st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

st.caption(
    f"Median house price and median {label.lower()} per sale, 2023 house sales, "
    f"{config.MODES[mode].lower()}, build cost {gbp(cost_per_m2)}/m². "
    f"Earnings: ONS, house price to residence-based earnings ratio, Table 5b, median gross annual pay of "
    f"full-time employees living in the borough, {config.YEAR}. City of London not shown (earnings suppressed, "
    "one house sale). Houses only, so these are higher than the ONS all-homes ratios."
)
with st.expander("Table"):
    st.dataframe(
        b[["borough", "median_price", "median_land", "median_earnings", "price_years", "land_years"]],
        hide_index=True, width="stretch",
        column_config={
            "borough": "Borough",
            "median_price": st.column_config.NumberColumn("Median house price", format="£%d"),
            "median_land": st.column_config.NumberColumn(f"Median {label.lower()}", format="£%d"),
            "median_earnings": st.column_config.NumberColumn("Median local pay", format="£%d"),
            "price_years": st.column_config.NumberColumn("Whole house (years)", format="%.1f"),
            "land_years": st.column_config.NumberColumn(f"{label} (years)", format="%.1f"),
        },
    )

st.divider()
method_caption()
