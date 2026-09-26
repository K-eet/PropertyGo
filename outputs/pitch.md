# Pitch: Land, not bricks

House London #2, 26 September 2026. Figures are 2023 house sales (detached, semi-detached, terraced; standard sales only), resale method, build cost £1,900 per m² (BCIS via Harrow and Croydon viability studies), unless stated.

## One sentence

In Kensington and Chelsea, about 90p of every pound paid for a house is not the cost of building it: it is the land and its location.

## The story (3 minutes)

1. **The problem.** London's housing debate is often about build costs. The data says otherwise. Across London the median house sale is 70% land and location. In Barking and Dagenham it is 62%; in Kensington and Chelsea it is 90% (Borough map page, `outputs/borough_summary_2023.csv`).
2. **Zoom in.** In Kensington and Chelsea, 349 houses sold for about £1.73 billion in 2023. Building them again would cost about £140 million. The median house sold for £3.4 million; its build cost was about £342,000. 96% of sales have a land share above 80%. Even if a developer had built them new, with profit and fees taken out, land would still be 69% of the price.
3. **Who owns it.** The street map adds every property title in the borough held by a company registered outside the UK (HM Land Registry OCOD). Figures to quote after running `python -m src.ocod`: number of overseas-company titles in the borough: ____; top places of incorporation: ____.
4. **The tool.** Open the Streamlit app, street map page. A councillor, activist or journalist can walk a street, hover over a house and see what it sold for against what it cost to build, with overseas-company ownership in red on the same map.
5. **The ask.** Treat land value and ownership transparency as the policy lever. Building cheaper does not fix a price that is 90% land.

## Who it is for

- Councillors and MPs walking their ward or constituency.
- Housing activists and tenants' groups preparing evidence.
- Journalists looking for a street-level example.

## Demo script

1. `.venv\Scripts\streamlit run app.py` (macOS/Linux: `.venv/bin/streamlit run app.py`), open http://localhost:8501.
2. Borough map page: Kensington and Chelsea is the reddest borough.
3. Street map page: zoom into Chelsea or Notting Hill; hover over a blue dot; point out the land value in pounds.
4. "Look at one sale": pick 13 Dawson Place (£44.75 million, 98% land share).
5. Move the build cost slider from £1,900 to £2,500 per m²: the median land share only falls from 90% to 87%. The result does not depend on the exact build cost.
6. Switch the sidebar to "New build": land is still about 69% after developer profit and fees.
7. Look up a house page: enter any London postcode to show the same split elsewhere.

## Caveats slide (say these out loud)

- Build cost is one figure per m² for all of London, from outer London viability studies. Inner London costs more; £1,520 to £2,500 moves Kensington and Chelsea between 92% and 87%, and no borough changes rank.
- Resale "land and location" is what is left after the cost to rebuild the house; new-build profit, fees and marketing are standard appraisal assumptions, not data for each sale.
- OCOD lists overseas **companies** only. Individuals, UK companies and trusts are missing, so the red layer undercounts offshore ownership.
- OCOD shows who owns a title today, not who bought in 2023.
- Map points are postcode centres, not front doors.
- Houses only for the land share; flats appear only on the ownership layer.

Full list: `ASSUMPTIONS.md`.
