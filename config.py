"""All project assumptions. Do not put these numbers directly in analysis code.

Every value here must have a source recorded in ASSUMPTIONS.md.
"""
from pathlib import Path

# --- Scope -----------------------------------------------------------------
YEAR = 2025  # most recent full calendar year in Price Paid Data

# Price Paid property types kept for the main result (houses only).
# D = detached, S = semi-detached, T = terraced. F (flat) and O (other) are excluded.
HOUSE_TYPES = ["D", "S", "T"]

# PPD category A = standard price paid (full market value).
# Category B (repossessions, buy-to-let, company sales) is excluded.
PPD_CATEGORIES = ["A"]

# --- Build cost ------------------------------------------------------------
# PROVISIONAL: the team must confirm this value and its source in ASSUMPTIONS.md.
BUILD_COST_PER_M2 = 2500  # GBP per m² of floor area, London, houses

# Multipliers for the sensitivity check (low, high) on BUILD_COST_PER_M2.
BUILD_COST_SENSITIVITY = (0.8, 1.2)

# PROVISIONAL ESTIMATE: national labour share of build cost. Label as an estimate in outputs.
LABOUR_SHARE = 0.45

# --- Paths -----------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"

PPD_FILE = RAW / f"pp-{YEAR}.csv"
BOROUGH_SHP = (
    RAW / "london_boundaries" / "statistical-gis-boundaries-london" / "ESRI"
    / "London_Borough_Excluding_MHW.shp"
)
LAND_VALUES_FILE = RAW / "land_value_estimates_2023.xlsx"
