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

# Street-level demo: one borough (Kensington and Chelsea).
TARGET_BOROUGH_CODE = "E09000020"
TARGET_BOROUGH_NAME = "Kensington and Chelsea"
# Price Paid / OCOD district strings that mean this borough (upper case).
TARGET_DISTRICT_NAMES = ("KENSINGTON AND CHELSEA", "KENSINGTON & CHELSEA")

# --- Build cost ------------------------------------------------------------
# GBP per m² of floor area, houses, including 10% external works. BCIS 810.1 "Estate housing
# generally" rebased to outer London: Harrow LPVA Oct 2024 Table 4.13.1 (£1,711 + 10% = £1,882);
# Croydon LPVA 2024 para 4.12 (£1,754 + 10% = £1,929). Both by BNP Paribas Real Estate.
BUILD_COST_PER_M2 = 1900

# Sensitivity range (low, high) in GBP per m². Low = -20%. High = £2,500, a cautious figure
# above central Croydon (£2,201) to allow for inner London and net-zero costs.
BUILD_COST_RANGE_PER_M2 = (1520, 2500)

# ESTIMATE: labour share of build cost, derived from ONS Input-Output Analytical Tables 2023
# (UK construction, all types). Employee pay only gives 22%; adding all self-employed income
# and surplus gives 52%. We use 38%, about the middle. Label as an estimate in outputs.
LABOUR_SHARE = 0.38
LABOUR_SHARE_RANGE = (0.22, 0.52)

# --- New-build appraisal (not used for resales: a homeowner seller makes no developer profit) ---
# Developer profit as a share of sale price. PPG Viability para 018: 15-20% of gross
# development value is a suitable return. Harrow and Croydon LPVAs 2024 use 17.5%.
DEVELOPER_PROFIT_SHARE_OF_PRICE = 0.175
# Professional fees as a share of build cost. Harrow LPVA para 4.22, Croydon para 4.18: 10%.
PROFESSIONAL_FEES_SHARE_OF_BUILD = 0.10
# Marketing and agents 2.5% plus sales legal fees 0.25% of sale price. Harrow para 4.24,
# Croydon para 4.20.
MARKETING_AND_LEGAL_SHARE_OF_PRICE = 0.0275
# Finance is not included: the studies give an interest rate (6.5-7%), not a share, and a
# share needs a build period assumption. So new-build land is slightly overstated.

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
MSOA_SHP = (
    RAW / "london_boundaries" / "statistical-gis-boundaries-london" / "ESRI"
    / "MSOA_2011_London_gen_MHW.shp"
)
# Neighbourhoods (MSOAs) with fewer house sales than this are shown grey on the detailed map.
MIN_SALES_PER_MSOA = 10
LAND_VALUES_FILE = RAW / "land_value_estimates_2023.xlsx"
# House price per m² (Price Paid x EPC, pre-linked), one CSV per local authority.
HPM_DIR = RAW / "hpm" / "hpm_la_2024" / "hpm_la_2024"
# Overseas companies that own property (Land Registry OCOD). Unzip the full file here;
# the newest OCOD_FULL_*.csv is used. example.csv (public sample) is only used for column checks.
OCOD_DIR = RAW / "ocod"
OCOD_GLOB = "OCOD_FULL_*.csv"

# postcodes.io bulk lookup allows at most this many postcodes per request.
POSTCODES_BULK_LIMIT = 100
