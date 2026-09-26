# CLAUDE.md: PropertyGo (London Land Value Project)

## Context

This repo is for a one-day data sprint: House London #2, Newspeak House, 26 September 2026.
Time is very limited. Speed and a clear story are more important than complete code.
Use British English in all text, charts, and comments.

## Research question

What part of a London home's sale price is build cost, and what part is land value and profit?

The expected story: in London, land cost is a larger problem than build cost.

## Deliverables (in priority order)

1. A map of London that shows the land share of sale price, per borough.
2. A short summary table per borough: median sale price, median estimated build cost, median land share.
3. A small demo: the user enters an address or postcode and sees build cost against sale price.
4. A list of assumptions and limits in `ASSUMPTIONS.md`.

Do not start item 3 until items 1 and 2 are complete.

## Method

1. Get sale prices from HM Land Registry Price Paid Data.
2. Get floor area from the EPC register (Energy Performance Certificates).
3. Match the two datasets. **Done for us:** use the pre-linked House Price per Square Metre dataset (see below), joined to Price Paid on transaction ID. Our own address matching is now only a fallback.
4. Calculate estimated build cost: floor area multiplied by `BUILD_COST_PER_M2`.
5. Calculate land share: (sale price minus build cost) divided by sale price.
6. Aggregate by borough with medians, not means.

## Data sources

### Core (required)

- **House Price per Square Metre (Price Paid x EPC, pre-linked):** https://data.london.gov.uk/dataset/house-price-per-square-metre-in-england-and-wales. One CSV per local authority with `transactionid`, `price`, `tfarea` (EPC floor area), `lad23cd`, `classt` (11 = one EPC, 12 = several). Field list in `data/raw/hpm/Readme.pdf`. Latest file ends 31 Oct 2024, so **2023 is the latest full year**. Downloaded: `data/raw/hpm/`. Loader: `src/linked.py`.
- **Price Paid Data:** HM Land Registry, CSV download. The CSV has no header row. Column order is in `src/prices.py` (from the official guidance). Keep county `GREATER LONDON`, property type D/S/T, PPD category A only. Needed to filter category A and to measure the match rate. Downloaded: `data/raw/pp-2023.csv`, `data/raw/pp-2025.csv`. The `prod.publicdata...` host may not resolve; use `http://prod2.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-<YEAR>.csv`.
- **EPC register:** https://get-energy-performance-data.communities.gov.uk/. Only needed if we extend to 2025 sales with our own address matching. Not needed for the main result.
- **Borough boundaries:** London Datastore, statistical GIS boundary files. Downloaded: `data/raw/london_boundaries/`. Use `London_Borough_Excluding_MHW.shp`. Join on `GSS_CODE`, not the name.

### For assumptions in `config.py`

- **Build cost per m²:** BCIS (paywalled), or the free summary figures in Turner & Townsend, Arcadis or Gleeds international cost reports. Use a London figure, not a UK average. Record the price year.
- **Labour share:** ONS Input-Output Analytical Tables (construction compensation of employees).

### Validation and context

- **MHCLG Land Value Estimates for Policy Appraisal 2023:** residential land £/ha per borough. Downloaded: `data/raw/land_value_estimates_2023.xlsx`. Use to check the borough ranking only.
- **Forest MCP:** open UK data, one value per parliamentary constituency (PCON24), not per borough or per sale. It cannot replace Price Paid + EPC. Useful for context: `average_house_price_gbp` (ONS UK HPI, to cross-check our medians), `parliament_house_price_to_earnings_ratio`, `homes_completed_annual`, `dwelling_flat_pct`, `bedrooms_*_pct` (fallback proxy for floor area if matching fails).
- **Postcode lookup (demo only):** postcodes.io API, or ONS Postcode Directory if offline.

### Team list: other datasets (not used in the main result; use for extra slides only if time permits)

- **Demand and need:** WhereToBuild (wheretobuild.warwick.ac.uk), ONS Census 2021 (Nomis), English Indices of Deprivation 2025, GLA Housing in London report.
- **Supply:** Planning London Datahub starts/completions dashboards, London Development Database export, Affordable Housing Open Data, GLA Affordable Housing Programme outturn, EPCs for new dwellings, MHCLG indicators of new supply, Housing Delivery Test.
- **Planning process:** planning.data.gov.uk API, Digital Planning Register, UK PlanIt API, London Plan Opportunity Areas, planning application live tables, Digital Planning Data Schemas.
- **Land, price, ownership:** UK House Price Index, vacant dwellings (Live Table 615), OCOD/CCOD company ownership, brownfield land registers (planning.data.gov.uk).
- **Glue:** ONS geography lookups (LSOA/MSOA/ward/borough), Local Planning Authority boundaries, OS Open Data.

Best candidates for a second slide: Housing Delivery Test or LDD completions per borough (supply) against our land share (price), and brownfield land per borough.

Before you write code for a dataset, load a sample and print the columns and data types.
Do not guess field names.

## Scope limits

- Use London sales only.
- Use one recent full year of sales.
- Use houses only (detached, semi-detached, terraced) for the main result. Flats share land, so the land share of a flat is not clear.
- Use the most recent EPC for each address.

## Configuration

Keep all assumptions in `config.py`:

- `BUILD_COST_PER_M2`: the team must set this value and record the source in `ASSUMPTIONS.md`.
- `LABOUR_SHARE`: one national estimate for the labour part of build cost. Label it as an estimate in all outputs.
- `YEAR`: the year of sales.

Do not put numbers for these assumptions directly in analysis code.

## Address matching (fallback only)

The pre-linked dataset removes this task for 2023. Use the steps below only for years it does not cover.

This is the highest risk task. Limit it to two hours.

1. Normalise both address sets: upper case, remove punctuation, remove extra spaces.
2. Match on postcode plus house number or house name.
3. For flats, also match on flat number (SAON in Price Paid).
4. Report the match rate as a percentage.
5. If the match rate is low after two hours, stop and continue with the matched records.

Do not use fuzzy matching libraries unless the simple method fails.

## Repo layout

```
data/raw/        original downloads, never edit
data/processed/  cleaned and matched files
notebooks/       exploration only
src/             reusable functions
outputs/         charts and tables for the presentation
.venv/           Python environment (pip install -r requirements.txt)
config.py
ASSUMPTIONS.md
```

## Stack

- Python, pandas
- geopandas and plotly (or matplotlib) for the map
- Streamlit for the demo: `.venv/bin/streamlit run app.py` (http://localhost:8501). Lookup logic in `src/lookup.py`, postcodes via postcodes.io

Do not add other frameworks.

## Working rules

- Write small functions. Test each function on a sample of 1,000 rows first.
- Commit to git after each working step.
- Save intermediate results to `data/processed/` so the team does not run slow steps again.
- Record each assumption in `ASSUMPTIONS.md` when you make it.
- If a task takes more than 30 minutes with no result, stop and tell the team.

## Known limits (put these in the presentation)

- Build cost is an estimate from one cost per square metre, not the real cost of each home.
- The labour and materials split is a national estimate, not data for each home.
- The land share includes developer profit and other costs, not only land.
- Unmatched addresses can make the sample less representative.
- EPC floor area can be old or incorrect.

## Definition of done

- The borough map and summary table are in `outputs/`.
- `ASSUMPTIONS.md` lists all assumptions with sources.
- The match rate is recorded.
- The team can explain the main result in one sentence.