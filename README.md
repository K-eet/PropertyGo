# PropertyGo

What part of a London home's sale price is build cost, and what part is land value and profit?

Built at House London #2, Newspeak House, 26 September 2026. See `CLAUDE.md` for the method, `ASSUMPTIONS.md` for assumptions and sources, and `outputs/pitch.md` for the pitch.

Raw data is not in git. See the data sources in `CLAUDE.md` to download it into `data/raw/`.

## Run

```
python -m src.linked      # London house sales linked to EPC floor area
python -m src.analysis    # land share and borough summary
python -m src.map         # borough map
python -m src.ocod        # Kensington and Chelsea sales + overseas-company titles (needs OCOD in data/raw/ocod/)
streamlit run app.py      # demo: street map and postcode lookup
```
