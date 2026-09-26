# Pitch: Land, not bricks

House London #2, 26 September 2026. All figures: London house sales in 2023 (detached, semi-detached, terraced; standard sales only), resale method, build cost £1,900 per m² (BCIS via the Harrow and Croydon viability studies), unless stated. Sources and method: `ASSUMPTIONS.md`.

## One sentence

A typical London house sold for £625,000 in 2023; rebuilding it would cost about £188,000. The other 70% is the land it stands on.

## Slides

### 1. The question and the answer

**What part of a London house price is build cost, and what part is land?**

- Typical (median) London house: **£625,000**.
- Cost to rebuild it: **£188,000 (30%)**. Of that, labour is about **£71,000, only 11% of the price** (38% of build cost; ONS input-output estimate).
- The rest, **70%**, is land and location.

Say: "London does not have a build-cost problem. It has a land problem."

### 2. The map

Image: `outputs/map_land_share_resale_2023.png`

- Every borough is at least **62%** land (Barking and Dagenham). The centre reaches **90%** (Kensington and Chelsea).
- The further in, the less of the price is the house.

### 3. Why you can trust it

- **Build cost:** anywhere from £1,520 to £2,500 per m², no borough changes rank. Kensington and Chelsea stays between 87% and 92%.
- **Developer view:** even if every house were sold new, after the developer's profit (17.5%), fees and marketing, land is still **37% to 69%** of the price (`outputs/map_land_share_new_build_2023.png`).
- **Government check:** our borough ranking agrees with MHCLG's own residential land values for 2023 (Spearman rank correlation **0.70**, medium density; 0.63 low density; 32 boroughs). We built ours from sale prices and floor areas; they built theirs from valuations. Same answer.

### 4. Zoom in: Kensington and Chelsea

- 349 houses sold for **£1.73 billion** in 2023. Rebuilding all of them would cost about **£140 million**.
- The median house sold for £3.4 million; its build cost was about £342,000.
- 96% of sales were more than 80% land. 13 Dawson Place sold for £44.75 million: **98% land**.

### 5. Who holds that land value

Image: `outputs/map_kc_street_ocod_2023.png`

- HM Land Registry lists **4,950** property titles in Kensington and Chelsea held by companies registered outside the UK (September 2026). Only Westminster has more (9,649).
- **37%** are British Virgin Islands companies; **76%** are in six offshore jurisdictions (British Virgin Islands, Jersey, Guernsey, Isle of Man, Panama, Cayman Islands).
- **46%** of the borough's 2023 house sales were in a postcode with at least one of these titles. Across London the figure is **3.9%**. Kensington and Chelsea is the highest of all 33 boroughs.
- Across boroughs, the higher the land share, the more overseas-company ownership nearby (Spearman **0.82**, 32 boroughs).

Say: "This is a pattern, not proof of cause. But the places where the price is almost all land are the places where that land is most often held offshore."

### 6. The tool and the ask

- **Tool:** a street map for councillors, housing activists and journalists. Hover over any house sold in 2023 to see its price against its build cost; overseas-company titles appear in red on the same map. Any London postcode can be looked up.
- **Ask:** treat land value and ownership transparency as the policy lever. Cheaper building cannot fix a price that is 70% land in a typical borough and 90% in the most expensive.

### Backup: caveats (have ready for questions)

- Build cost is one figure per m² for all of London, from outer London viability studies. Inner London costs more; the £2,500 upper figure covers this and the ranking does not change.
- Resale "land and location" is what is left after the cost to rebuild the house. New-build profit, fees and marketing are standard appraisal assumptions, not data for each sale. Finance is left out.
- The labour split is a national estimate for all construction (range 22% to 52% of build cost), not data for each house.
- Houses only. Flats share land, so their land share is not clear. Flats do appear on the ownership layer.
- OCOD lists overseas **companies** only. Individuals, UK companies and trusts are missing, so it undercounts offshore ownership.
- OCOD shows who owns a title today, not who bought in 2023. Only 1 of 349 Kensington and Chelsea house sales matches a specific overseas-company title, so we never claim a given sale was offshore.
- Map points are postcode centres, not front doors.
- 4.2% of house sales could not be linked to an EPC floor area.

## Demo script (2 minutes)

1. `.venv\Scripts\streamlit run app.py` (macOS/Linux: `.venv/bin/streamlit run app.py`), open http://localhost:8501.
2. **Borough map:** Kensington and Chelsea is the reddest borough.
3. **Street map:** red is 4,950 overseas-company titles. Zoom into Chelsea or South Kensington; hover over a red circle (countries, companies), then a blue dot (land value in pounds).
4. **Look at one sale:** 13 Dawson Place, £44.75 million, 98% land.
5. **Build cost slider:** £1,900 to £2,500 per m². The median only falls from 90% to 87%.
6. **Look up a house:** enter a judge's own postcode.
