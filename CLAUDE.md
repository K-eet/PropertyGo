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
5. Calculate land share in two modes (`src/costs.py`, `split_price`, shared by analysis, maps and demo):
   - **Resale:** land and location = price − build cost. A homeowner seller makes no developer profit. 99.6% of 2023 house sales are resales.
   - **New build (developer appraisal):** land = price − build cost − professional fees − marketing and legal − developer profit. Finance is left out.
6. Aggregate by borough with medians, not means. Both modes are applied to every sale at local prices; the London-wide table also compares actual new builds with actual resales.
7. Show the build cost range (`BUILD_COST_RANGE_PER_M2`) next to every headline figure.

## Data sources

### Core (required)

- **House Price per Square Metre (Price Paid x EPC, pre-linked):** https://data.london.gov.uk/dataset/house-price-per-square-metre-in-england-and-wales. One CSV per local authority with `transactionid`, `price`, `tfarea` (EPC floor area), `lad23cd`, `classt` (11 = one EPC, 12 = several). Field list in `data/raw/hpm/Readme.pdf`. Latest file ends 31 Oct 2024, so **2023 is the latest full year**. Downloaded: `data/raw/hpm/`. Loader: `src/linked.py`.
- **Price Paid Data:** HM Land Registry, CSV download. The CSV has no header row. Column order is in `src/prices.py` (from the official guidance). Keep county `GREATER LONDON`, property type D/S/T, PPD category A only. Needed to filter category A and to measure the match rate. Downloaded: `data/raw/pp-2023.csv`, `data/raw/pp-2025.csv`. The `prod.publicdata...` host may not resolve; use `http://prod2.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-<YEAR>.csv`.
- **EPC register:** https://get-energy-performance-data.communities.gov.uk/. Only needed if we extend to 2025 sales with our own address matching. Not needed for the main result.
- **Borough boundaries:** London Datastore, statistical GIS boundary files. Downloaded: `data/raw/london_boundaries/`. Use `London_Borough_Excluding_MHW.shp`. Join on `GSS_CODE`, not the name.

### For assumptions in `config.py` (full citations with paragraph numbers in `ASSUMPTIONS.md`)

- **Build cost, fees, marketing, profit:** BCIS figures are paywalled, but London boroughs publish them in their Local Plan Viability Assessments. We use Harrow (BNP Paribas, Oct 2024) and Croydon (BNP Paribas, 2024): BCIS 810.1 "Estate housing generally" rebased to outer London, £1,711–£1,754 + 10% external works ≈ **£1,900/m²**; professional fees 10% of build cost; marketing 2.5% + legal 0.25% of price; profit 17.5% of price.
- **Developer profit range:** Planning Practice Guidance: Viability, para 018 (15–20% of GDV).
- **Labour share:** derived from ONS Input-Output Analytical Tables 2023 (`data/raw/iot2023product.xlsx`), UK construction. Range 22% (employees only) to 52% (plus self-employed income and surplus); we use 38%. Method in `ASSUMPTIONS.md` 2.3.
- Not good enough to cite: blog "cost per m²" calculators, and Turner & Townsend / Arcadis London averages (they cover all building types, not houses).

### Validation and context

- **MHCLG Land Value Estimates for Policy Appraisal 2023:** residential land £/ha per borough. Downloaded: `data/raw/land_value_estimates_2023.xlsx`. Use to check the borough ranking only.
- **Forest MCP:** open UK data (login can expire: run `/mcp` to sign in again). No construction cost or appraisal data, one value per parliamentary constituency (PCON24), not per borough or per sale. It cannot replace Price Paid + EPC. Useful for context: `average_house_price_gbp` (ONS UK HPI, to cross-check our medians), `parliament_house_price_to_earnings_ratio`, `homes_completed_annual`, `dwelling_flat_pct`, `bedrooms_*_pct` (fallback proxy for floor area if matching fails).
- **HM Land Registry OCOD (overseas companies that own property):** https://use-land-property-data.service.gov.uk/datasets/ocod. Free account needed, so download by hand. Unzip the full file into `data/raw/ocod/` (`OCOD_FULL_*.csv`), then run `python -m src.ocod`. Overseas companies only (no individuals, UK companies or trusts); today's owners, not 2023 buyers.
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

- `YEAR` = 2023: the latest full year in the pre-linked data.
- `BUILD_COST_PER_M2` = £1,900 (sourced, BCIS via Harrow and Croydon), with `BUILD_COST_RANGE_PER_M2` = (£1,520, £2,500).
- `LABOUR_SHARE` = 38%, with `LABOUR_SHARE_RANGE` = (22%, 52%): one national estimate (ONS-derived). Label it as an estimate in all outputs.
- New build only: `DEVELOPER_PROFIT_SHARE_OF_PRICE` = 17.5%, `PROFESSIONAL_FEES_SHARE_OF_BUILD` = 10%, `MARKETING_AND_LEGAL_SHARE_OF_PRICE` = 2.75%.
- Every value in `config.py` must have a source or a stated reason in `ASSUMPTIONS.md`, with a status: sourced, derived or team choice.

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
views/           Streamlit pages (app.py is the router)
outputs/         charts and tables for the presentation; pitch.md = pitch script and demo steps
.venv/           Python environment (pip install -r requirements.txt)
config.py
ASSUMPTIONS.md
```

## Stack

- Python, pandas
- geopandas and matplotlib for the static maps in `outputs/` (same green-to-red colours), Plotly for the interactive map
- Streamlit for the demo: `.venv/bin/streamlit run app.py` (http://localhost:8501). Two pages:
  - `views/lookup.py` "Look up a house": postcode or address, price split bar, nearby sales. Lookup logic in `src/lookup.py`, postcodes via postcodes.io.
  - `views/borough_map.py` "Borough map": interactive Plotly map, **green = lower share, red = higher**, at three levels of detail: **Borough** (33), **Neighbourhood** (983 MSOAs, grey below `MIN_SALES_PER_MSOA` = 10 sales) and **Individual sales** (every sale at its postcode centre; zooms to the last looked-up postcode). The two detailed levels need `python -m src.locate` once (`src/locate.py`: postcodes.io bulk geocoding, cached in `data/processed/postcode_centroids.parquet`, then spatial join to MSOA 2011). Colours stretched to this map's range by default; toggle for a fixed 0–100% scale. In new-build mode, colour by "land only" or "land and developer profit". Marks the last looked-up postcode.
  - `views/street_map.py` "Kensington and Chelsea street map": every 2023 house sale as a point (postcode centroid), **blue shades by land share** (red is kept for ownership), with overseas-company titles (OCOD) as red circles. Borough set by `TARGET_BOROUGH_CODE` in `config.py`. Build its data with `python -m src.ocod` (`src/ocod.py`, `src/streetmap.py`); without the OCOD file it builds the sales layer only.
  - `app.py` is the router. The sidebar controls (type of sale, build cost per m²) live there so they keep their values across pages. Shared helpers in `src/ui.py`.
  - Needs internet: postcodes.io and Plotly's map base file (CDN).
  - Plotly geo maps need clockwise polygon rings (`src/ui.py`, `clockwise`), or boroughs do not draw.

Do not add other frameworks.

## Working rules

- Write small functions. Test each function on a sample of 1,000 rows first.
- Commit to git after each working step.
- Save intermediate results to `data/processed/` so the team does not run slow steps again.
- Record each assumption in `ASSUMPTIONS.md` when you make it.
- If a task takes more than 30 minutes with no result, stop and tell the team.

## Known limits (put these in the presentation)

- Build cost is one cost per m² for all of London, from outer London boroughs, not the real cost of each home. Inner London costs more; the £2,500 upper figure covers this. The borough ranking does not change across the range.
- The labour and materials split is a national estimate for all construction, not data for each home.
- Resale land share is land and location (no developer profit in a resale). It is if anything too low, because an old house is worth less than the cost to build it new.
- New-build land share subtracts standard appraisal assumptions (profit 17.5%, fees 10%, marketing and legal 2.75%). Finance is left out, so it is slightly too high.
- 4.2% of house sales could not be linked to an EPC; unmatched sales can make the sample less representative.
- EPC floor area can be old or incorrect.

## Current results (2023, £1,900/m²)

- London median land share: **70% as a resale, 47% as a new build**.
- Resale by borough: 62% (Barking and Dagenham) to 90% (Kensington and Chelsea). At £2,500/m²: 49% to 87%.
- Match rate 95.8%. Rank agreement with MHCLG land values: ρ = 0.63–0.70.
- One sentence: "Even in London's cheapest borough, most of a house's price is land, not bricks: about 62% on a resale, and still 37% after a developer's costs and profit."

## Definition of done

- The borough map and summary table are in `outputs/`.
- `ASSUMPTIONS.md` lists all assumptions with sources.
- The match rate is recorded.
- The team can explain the main result in one sentence.