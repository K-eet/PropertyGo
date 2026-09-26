# Assumptions and limits

Each assumption lists its value, its source, and its status. Values live in `config.py`.

## Assumptions

| # | Assumption | Value | Source | Status |
|---|---|---|---|---|
| 1 | Year of sales (`YEAR`) | 2025 | Most recent full calendar year in HM Land Registry Price Paid Data (file updated 28 Aug 2026) | Confirmed |
| 2 | London sales only | County = `GREATER LONDON` | Price Paid Data county field | Confirmed |
| 3 | Houses only (`HOUSE_TYPES`) | D, S, T | Flats share land, so the land share of a flat is not clear | Confirmed |
| 4 | Standard sales only (`PPD_CATEGORIES`) | A | Category B includes repossessions, buy-to-let and company sales, which are not full market value | Confirmed |
| 5 | Build cost (`BUILD_COST_PER_M2`) | £2,500 per m² | **No source yet** | **PROVISIONAL: team must set and cite** |
| 6 | Build cost sensitivity range | ×0.8 to ×1.2 | Team choice to show how results move | Confirmed |
| 7 | Labour share of build cost (`LABOUR_SHARE`) | 45% | **No source yet.** Candidate: ONS Input-Output Analytical Tables, construction compensation of employees | **PROVISIONAL ESTIMATE** |
| 8 | Borough assignment | Price Paid `district` field mapped to GSS code | Only one name differs: `CITY OF WESTMINSTER` → Westminster | Confirmed |
| 9 | Freehold and leasehold houses both kept | — | Leasehold houses are a small share in London | Confirmed |

## Validation data

- **MHCLG Land Value Estimates for Policy Appraisal 2023** (published March 2026, valuation date 1 Oct 2023). Residential land value in £/ha per local authority. We use the low-density median as the comparison for houses. It is used to check the borough ranking, not in the main calculation.

## Match rate

Not measured yet. Record here when the Price Paid to EPC address matching is complete.

## Known limits (for the presentation)

- Build cost is an estimate from one cost per square metre, not the real cost of each home.
- The labour and materials split is a national estimate, not data for each home.
- The land share includes developer profit and other costs, not only land.
- Unmatched addresses can make the sample less representative.
- EPC floor area can be old or incorrect.
- One London-wide build cost ignores differences between boroughs. This moves absolute land shares, but the ranking between boroughs is more robust.
