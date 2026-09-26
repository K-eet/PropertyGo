"""All project assumptions. Do not put these numbers directly in analysis code.

Every value here must have a source recorded in ASSUMPTIONS.md.
"""
from pathlib import Path

# --- Scope -----------------------------------------------------------------
# Most recent full year in the pre-linked Price Paid x EPC dataset (it ends 31 Oct 2024).
YEAR = 2023

# Sanity limits on EPC floor area (m²) for a house. Records outside are dropped.
FLOOR_AREA_MIN_M2 = 30
FLOOR_AREA_MAX_M2 = 1000

# Boroughs with fewer sales than this are shown as 'too few sales' (e.g. City of London).
MIN_SALES_PER_BOROUGH = 30

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

# --- New-build appraisal (not used for resales: a homeowner seller makes no developer profit) ---
# Developer profit as a share of sale price. PPG Viability para 018: 15-20% of gross
# development value is a suitable return for plan-making. We use the midpoint.
DEVELOPER_PROFIT_SHARE_OF_PRICE = 0.175
# PROVISIONAL: professional fees, finance, sales and marketing, as a share of build cost.
OTHER_DEV_COSTS_SHARE_OF_BUILD = 0.15

# Calculation modes.
MODES = {"resale": "Resale (existing house)", "new_build": "New build (developer appraisal)"}

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
# House price per m² (Price Paid x EPC, pre-linked), one CSV per local authority.
HPM_DIR = RAW / "hpm" / "hpm_la_2024" / "hpm_la_2024"
