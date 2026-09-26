"""MHCLG Land Value Estimates for Policy Appraisal 2023 (validation only).

Run: python -m src.land_values
"""
import pandas as pd

import config

# Column positions in the 'Residential' sheet. Header rows are 3-4; data starts at row 5.
COLS = {
    1: "region", 2: "borough_code", 3: "la_name",
    4: "density_low_dph", 5: "density_medium_dph", 6: "density_high_dph",
    9: "land_gbp_per_ha_low_density_median",
    14: "land_gbp_per_ha_medium_density_median",
    19: "land_gbp_per_ha_high_density_median",
}


def load_residential_land_values(path=config.LAND_VALUES_FILE) -> pd.DataFrame:
    """Residential land value (£/ha, October 2023) for London boroughs."""
    df = pd.read_excel(path, sheet_name="Residential", header=None, skiprows=5)
    df = df[list(COLS)].rename(columns=COLS)
    return df[df["region"] == "London"].reset_index(drop=True)


def main():
    df = load_residential_land_values()
    out = config.PROCESSED / "land_values_london_2023.csv"
    df.to_csv(out, index=False)
    print(f"{len(df)} boroughs -> {out.name}")
    print(df.sort_values("land_gbp_per_ha_low_density_median", ascending=False)
          [["la_name", "land_gbp_per_ha_low_density_median"]].to_string(index=False))


if __name__ == "__main__":
    main()
