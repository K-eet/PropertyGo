# Pitch: Land, not bricks

House London #2, 26 September 2026. Figures are 2023 house sales (detached, semi-detached, terraced; standard sales only) at a build cost of £2,500 per m² unless stated.

## One sentence

In Kensington and Chelsea, about 87p of every pound paid for a house is not the cost of building it: it is land, profit and other costs.

## The story (3 minutes)

1. **The problem.** London's housing debate is often about build costs. The data says otherwise. Across London the median house sale is 61% land, profit and other costs. In Barking and Dagenham it is 49%; in Kensington and Chelsea it is 87% (`outputs/map_land_share_2023.png`, `outputs/borough_summary_2023.csv`).
2. **Zoom in.** In Kensington and Chelsea, 349 houses sold for about £1.73 billion in 2023. Building them again would cost about £184 million. The median house sold for £3.4 million; its build cost was about £450,000. 88% of sales have a land share above 80%.
3. **Who owns it.** The street map adds every property title in the borough held by a company registered outside the UK (HM Land Registry OCOD). Figures to quote after running `python -m src.ocod`: number of overseas-company titles in the borough: ____; top places of incorporation: ____.
4. **The tool.** Open the Streamlit app, first tab. A councillor, activist or journalist can walk a street, hover over a house and see what it sold for against what it cost to build, with overseas-company ownership in red on the same map.
5. **The ask.** Treat land value and ownership transparency as the policy lever. Building cheaper does not fix a price that is almost 90% land.

## Who it is for

- Councillors and MPs walking their ward or constituency.
- Housing activists and tenants' groups preparing evidence.
- Journalists looking for a street-level example.

## Demo script

1. `.venv\Scripts\streamlit run app.py` (macOS/Linux: `.venv/bin/streamlit run app.py`), open http://localhost:8501.
2. First tab: zoom into Chelsea or Notting Hill; hover over a blue dot; point out the gap in pounds.
3. "Look at one sale": pick 13 Dawson Place (£44.75 million, 97% land share).
4. Move the build cost slider from £2,500 to £3,500 per m²: the median land share only falls from 87% to 82%. The result does not depend on the exact build cost.
5. Second tab: enter any London postcode to show the same split elsewhere.

## Caveats slide (say these out loud)

- Build cost is one London figure per m² and is still **provisional**; the team must cite a source (Turner & Townsend, Arcadis or Gleeds). ±20% moves Kensington and Chelsea between 85% and 90%.
- The "land share" includes developer profit and other costs, not only land.
- OCOD lists overseas **companies** only. Individuals, UK companies and trusts are missing, so the red layer undercounts offshore ownership.
- OCOD shows who owns a title today, not who bought in 2023.
- Map points are postcode centres, not front doors.
- Houses only for the land share; flats appear only on the ownership layer.

Full list: `ASSUMPTIONS.md`.
