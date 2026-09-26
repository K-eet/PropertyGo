# Assumptions, sources and limits

All values live in `config.py`. Each assumption below gives its value, its source (see the numbered source list at the end) and its status.

- **Sourced**: taken directly from a published source.
- **Derived**: calculated by us from a published source; the method is given.
- **Team choice**: a judgement call, stated openly.

## 1. Scope

| # | Assumption | Value | Source / reason | Status |
|---|---|---|---|---|
| 1.1 | Year of sales (`YEAR`) | 2023 | Latest full year in the pre-linked Price Paid × EPC dataset [S2], which ends 31 Oct 2024 | Team choice |
| 1.2 | London only | County = `GREATER LONDON` | Price Paid county field [S1] | Sourced |
| 1.3 | Houses only (`HOUSE_TYPES`) | D, S, T | Flats share land, so the land share of a flat is not clear | Team choice |
| 1.4 | Standard sales only (`PPD_CATEGORIES`) | Category A | Category B includes repossessions, buy-to-let and company sales, which are not full market value [S1] | Sourced |
| 1.5 | Freehold and leasehold houses both kept | — | Leasehold houses are a small share in London | Team choice |
| 1.6 | Borough assignment | Price Paid `district` → GSS code | Only `CITY OF WESTMINSTER` → Westminster needed a fix [S1, S3] | Sourced |
| 1.7 | Floor area | EPC total floor area (`tfarea`) | Pre-linked by the dataset authors [S2] | Sourced |
| 1.8 | Floor area limits | 30 to 1,000 m² | Removes 16 implausible records | Team choice |
| 1.9 | Minimum sales per borough on the map | 30 | Only City of London falls below (1 house sale) | Team choice |

## 2. Build cost

| # | Assumption | Value | Source / reason | Status |
|---|---|---|---|---|
| 2.1 | Build cost (`BUILD_COST_PER_M2`) | **£1,900 per m²** | BCIS 810.1 "Estate housing generally", rebased to outer London, plus 10% external works. Harrow: £1,711 + 10% = £1,882 [S5, Table 4.13.1]. Croydon (outside the town centre): £1,754 + 10% = £1,929 [S6, paras 4.12–4.13]. Rounded to £1,900 | Sourced |
| 2.2 | Sensitivity range (`BUILD_COST_RANGE_PER_M2`) | £1,520 to £2,500 | Low = −20%. High = £2,500, above central Croydon (£2,001 + 10% = £2,201 [S6]) to allow for inner London and net-zero costs (+4.2% to 5.2% for houses [S6, para 4.14]) | Team choice |
| 2.3 | Labour share of build cost (`LABOUR_SHARE`) | **38% (estimate)**, range 22% to 52% | Derived from ONS Input-Output Analytical Tables 2023 [S7], UK construction (CPA F41–43), output £399bn. Employee pay = 15.3% of output; operating surplus and mixed income = 21.1%; construction bought from other construction firms (subcontracting) = 30.8%. Treating subcontracted work as having the same cost structure: employees only = 15.3 ÷ (1 − 0.308) = 22%; employees plus all self-employed income and surplus = (15.3 + 21.1) ÷ (1 − 0.308) = 52%. We use 38%, about the middle | Derived |

## 3. Resale method

Price = build cost (labour + materials) + land and location.

| # | Assumption | Value | Source / reason | Status |
|---|---|---|---|---|
| 3.1 | Developer profit on a resale | 0 | The seller of an existing house is a homeowner, not a developer. 99.6% of 2023 London house sales were resales (32,345 of 32,486) [S1] | Sourced |
| 3.2 | Land and location | Price − build cost | What is left after the cost to rebuild the house | Method |

## 4. New-build method (developer appraisal)

Price = build cost + professional fees + marketing and legal + developer profit + land. This is the residual method used in Local Plan viability studies [S5, S6] and in national guidance [S8].

| # | Assumption | Value | Source / reason | Status |
|---|---|---|---|---|
| 4.1 | Developer profit (`DEVELOPER_PROFIT_SHARE_OF_PRICE`) | **17.5% of sale price** | PPG Viability para 018: 15–20% of gross development value [S8]. Harrow [S5, para 4.33] and Croydon [S6, para 4.29] use 17.5% | Sourced |
| 4.2 | Professional fees (`PROFESSIONAL_FEES_SHARE_OF_BUILD`) | **10% of build cost** | Harrow [S5, para 4.22], Croydon [S6, para 4.18]. Croydon gives a range of 6% to 12% | Sourced |
| 4.3 | Marketing and legal (`MARKETING_AND_LEGAL_SHARE_OF_PRICE`) | **2.75% of sale price** | Marketing and agents 2.5% plus sales legal fees 0.25% [S5, para 4.24; S6, para 4.20] | Sourced |
| 4.4 | Finance | **Not included** | The studies give an interest rate (Croydon 6.5%, Harrow 7%) [S5, S6], not a share. A share needs a build period assumption. So new-build land is slightly overstated | Team choice |
| 4.5 | New-build method on the borough map | Applied to all sales at local prices | Only 141 actual new-build house sales in 2023; no borough has 30. Read as "if this house were sold new" | Team choice |

## Results (London, 2023, build cost £1,900/m²)

| | Sales | Median price | Median land share | At £1,520/m² | At £2,500/m² |
|---|---|---|---|---|---|
| All sales, resale method | 32,486 | £625,000 | **70%** | | |
| All sales, new-build method | 32,486 | £625,000 | **47%** | | |
| Actual resales, resale method | 32,345 | £625,000 | 70% | | |
| Actual new builds, new-build method | 141 | £690,000 | 46% | | |
| Kensington and Chelsea (highest), resale | 349 | £3,400,000 | 90% | 92% | 87% |
| Barking and Dagenham (lowest), resale | 805 | £400,000 | 62% | 69% | 49% |
| Kensington and Chelsea, new build | | | 69% | 71% | 66% |
| Barking and Dagenham, new build | | | 37% | 46% | 24% |

No borough changes rank anywhere in the £1,520 to £2,500 range. Full table: `outputs/borough_summary_2023.csv`.

## Match rate

- London houses (D/S/T), category A, 2023 in Price Paid [S1]: **33,919**
- Linked to an EPC floor area [S2]: **32,502 (95.8%)**
- After floor area limits: **32,486 (95.8%)**

Matching was done by the authors of [S2]; we join to Price Paid on transaction ID.

## Validation

- Borough rank of our median resale land share against MHCLG residential land value (£/ha, 2023) [S4]: Spearman ρ = **0.63** (low density), **0.70** (medium density), 32 boroughs. MHCLG values a hypothetical new-build scheme, so we compare rankings only, not amounts.

## Known limits (for the presentation)

- Build cost is one figure per m² for all of London, from outer London boroughs. Inner London costs more; the £2,500 upper figure covers this. The ranking of boroughs does not depend on it.
- The labour and materials split is a national estimate for all construction, not data for each house.
- Resale: the part left after build cost is land and location. It includes no developer profit. The cost to build a new house is more than an old house is worth, so the resale land share is, if anything, too low.
- New build: profit, fees and marketing are standard appraisal assumptions, not data for each sale. Finance is left out.
- 4.2% of house sales could not be linked to an EPC, which can make the sample less representative.
- EPC floor area can be old or incorrect.

## Sources

| ID | Source | Used for |
|---|---|---|
| S1 | HM Land Registry, Price Paid Data, 2023 and 2025 files. https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads | Sale prices, property type, category, new-build flag |
| S2 | House Price per Square Metre in England and Wales (Price Paid × EPC, pre-linked), London Datastore, file dated 26 Dec 2024. https://data.london.gov.uk/dataset/house-price-per-square-metre-in-england-and-wales | EPC floor area per sale |
| S3 | GLA Statistical GIS Boundary Files for London, London Datastore | Borough boundaries and GSS codes |
| S4 | MHCLG, Land Value Estimates for Policy Appraisal 2023 (published March 2026). https://www.gov.uk/government/publications/land-value-estimates-for-policy-appraisal-2023 | Validation of borough ranking |
| S5 | BNP Paribas Real Estate for London Borough of Harrow, Local Plan Viability Assessment, October 2024. https://www.harrow.gov.uk/downloads/file/32803/EBLE02_Plan_level_Viability_Assessment__October_2024_.pdf | Build cost (BCIS), fees, marketing, profit |
| S6 | BNP Paribas Real Estate for London Borough of Croydon, Local Plan Viability Assessment, 2024. https://www.croydon.gov.uk/sites/default/files/2024-03/new-lb-croydon-local-plan-viability-assessment-final-2024_0.pdf | Build cost (BCIS), fees, marketing, net-zero uplift |
| S7 | ONS, UK Input-Output Analytical Tables, detailed, 2023 (product by product). https://www.ons.gov.uk/economy/nationalaccounts/supplyandusetables/datasets/ukinputoutputanalyticaltablesdetailed. Local copy: `data/raw/iot2023product.xlsx` | Labour share of construction |
| S8 | MHCLG, Planning Practice Guidance: Viability, para 018. https://www.gov.uk/guidance/viability | Developer profit 15–20% of GDV |
