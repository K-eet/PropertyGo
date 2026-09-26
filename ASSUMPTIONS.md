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

## Validation data

- **MHCLG Land Value Estimates for Policy Appraisal 2023** (published March 2026, valuation date 1 Oct 2023). Residential land value in £/ha per local authority. We use the low-density median as the comparison for houses. It is used to check the borough ranking, not in the main calculation.

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
- The land share includes developer profit and other costs, not only land.
- Unmatched addresses can make the sample less representative.
- EPC floor area can be old or incorrect.
- One London-wide build cost ignores differences between boroughs. This moves absolute land shares, but the ranking between boroughs is more robust.
