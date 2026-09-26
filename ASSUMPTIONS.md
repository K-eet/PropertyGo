# Assumptions and limits

Each assumption lists its value, its source, and its status. Values live in `config.py`.

## Assumptions

| # | Assumption | Value | Source | Status |
|---|---|---|---|---|
| 1 | Year of sales (`YEAR`) | 2023 | Latest full year in the pre-linked Price Paid x EPC dataset (it ends 31 Oct 2024). Price Paid has 2025, but using it would need our own address matching | Confirmed |
| 2 | London sales only | County = `GREATER LONDON` | Price Paid Data county field | Confirmed |
| 3 | Houses only (`HOUSE_TYPES`) | D, S, T | Flats share land, so the land share of a flat is not clear | Confirmed |
| 4 | Standard sales only (`PPD_CATEGORIES`) | A | Category B includes repossessions, buy-to-let and company sales, which are not full market value | Confirmed |
| 5 | Build cost (`BUILD_COST_PER_M2`) | £2,500 per m² | **No source yet** | **PROVISIONAL: team must set and cite** |
| 6 | Build cost sensitivity range | ×0.8 to ×1.2 | Team choice to show how results move | Confirmed |
| 7 | Labour share of build cost (`LABOUR_SHARE`) | 45% | **No source yet.** Candidate: ONS Input-Output Analytical Tables, construction compensation of employees | **PROVISIONAL ESTIMATE** |
| 8 | Borough assignment | Price Paid `district` field mapped to GSS code | Only one name differs: `CITY OF WESTMINSTER` → Westminster | Confirmed |
| 9 | Freehold and leasehold houses both kept | — | Leasehold houses are a small share in London | Confirmed |
| 10 | Floor area source | EPC total floor area (`tfarea`) | House Price per Square Metre dataset, London Datastore (Price Paid x EPC, pre-linked by the dataset authors) | Confirmed |
| 11 | Floor area sanity limits | 30 to 1,000 m² | Team choice; removes 16 records | Confirmed |
| 12 | Minimum sales per borough on the map | 30 | Team choice. Only City of London falls below (1 house sale) | Confirmed |
| 13 | Resale: no developer profit | 0 | The seller of an existing house is a homeowner. 99.6% of 2023 London house sales were resales (32,345 of 32,486) | Confirmed |
| 14 | New build: developer profit (`DEVELOPER_PROFIT_SHARE_OF_PRICE`) | 17.5% of sale price | Planning Practice Guidance, Viability, para 018: 15–20% of gross development value. Midpoint used | Confirmed (source: PPG) |
| 15 | New build: fees, finance, sales and marketing (`OTHER_DEV_COSTS_SHARE_OF_BUILD`) | 15% of build cost | **No source yet** | **PROVISIONAL** |
| 16 | New-build method on the borough map | Applied to all sales at local prices | Only 141 actual new-build house sales in 2023; no borough has 30. Read as "if this house were sold new" | Confirmed |

## Validation data

- **MHCLG Land Value Estimates for Policy Appraisal 2023** (published March 2026, valuation date 1 Oct 2023). Residential land value in £/ha per local authority. We use the low-density median as the comparison for houses. It is used to check the borough ranking, not in the main calculation.

## Results by type of sale (London, 2023)

| | Sales | Median price | Median land share |
|---|---|---|---|
| Resales, resale method | 32,345 | £625,000 | 61% |
| Actual new builds, new-build method | 141 | £690,000 | 36% |
| All sales, new-build method | 32,486 | | 38% |

## Match rate

- London houses (D/S/T), category A, 2023 in Price Paid: **33,919**
- Linked to an EPC floor area: **32,502 (95.8%)**
- After floor area limits: **32,486 (95.8%)**

Matching done by the House Price per Square Metre dataset authors; we join to Price Paid on transaction ID.

## Validation

- Borough rank of our median land share against MHCLG residential land value (£/ha, 2023): Spearman ρ = **0.63** (low density), **0.70** (medium density), 32 boroughs.
- Build cost ±20%: the lowest borough (Barking and Dagenham) moves from 49% to a range of 39% to 59%; the highest (Kensington and Chelsea) from 87% to 85% to 90%. The ranking does not change.

## Known limits (for the presentation)

- Build cost is an estimate from one cost per square metre, not the real cost of each home.
- The labour and materials split is a national estimate, not data for each home.
- Resale: the part left after build cost is land and location. It includes no developer profit, but it does include any error in the build cost. The build cost of a new house is more than an old house is worth, so the resale land share is, if anything, too low.
- New build: developer profit and other development costs are standard appraisal assumptions, not data for each sale.
- Unmatched addresses can make the sample less representative.
- EPC floor area can be old or incorrect.
- One London-wide build cost ignores differences between boroughs. This moves absolute land shares, but the ranking between boroughs is more robust.
