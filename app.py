"""Demo: how much of a London house price is build cost?

Run: .venv/bin/streamlit run app.py
This router runs on every page, so the sidebar controls keep their values between pages.
"""
import streamlit as st

import config
from src.ui import gbp

st.set_page_config(page_title="London house prices: land vs build cost", page_icon="🏠", layout="wide")

page = st.navigation([
    st.Page("views/lookup.py", title="Look up a house", icon="🔎", default=True),
    st.Page("views/borough_map.py", title="Borough map", icon="🗺️"),
    st.Page("views/why_location.py", title="Why? Location", icon="🧱"),
    st.Page("views/why_earnings.py", title="Why it matters: years of pay", icon="⏳"),
    st.Page("views/street_map.py", title=f"{config.TARGET_BOROUGH_NAME} street map", icon="📍"),
])

with st.sidebar:
    st.radio(
        "Type of sale", options=list(config.MODES), format_func=config.MODES.get, key="mode",
        help="Resale: a homeowner sells, so there is no developer profit. New build: a developer also "
             "pays fees, marketing and legal costs, and takes a profit, before what is left for the land.",
    )
    st.slider(
        "Build cost per m² (£)", min_value=1500, max_value=4500, step=100,
        value=config.BUILD_COST_PER_M2, key="cost_per_m2",
        help="Change this to see how the result depends on the build cost assumption.",
    )
    st.caption(
        f"Default {gbp(config.BUILD_COST_PER_M2)}/m²: BCIS estate housing, outer London "
        f"(Harrow and Croydon Local Plan Viability Assessments 2024). "
        f"Labour share of build cost: {config.LABOUR_SHARE:.0%}, an estimate from ONS input-output "
        f"tables 2023 (range {config.LABOUR_SHARE_RANGE[0]:.0%}–{config.LABOUR_SHARE_RANGE[1]:.0%})."
    )

page.run()
