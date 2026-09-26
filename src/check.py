"""Print a fingerprint of this machine's setup, so two team members can compare.

Run: python -m src.check   (then compare the output line by line)
Git only syncs code. data/raw/ and data/processed/ are not in git, so they can differ.
"""
import hashlib
import importlib.metadata as md
import subprocess

import pandas as pd

import config

APP_FILES = {
    "sales (all pages)": config.PROCESSED / f"land_share_london_houses_{config.YEAR}.parquet",
    "locations (detailed map)": config.PROCESSED / f"sale_locations_{config.YEAR}.parquet",
    "K&C sales (street map)": config.PROCESSED / f"kc_sales_{config.YEAR}.parquet",
    "K&C OCOD (street map)": config.PROCESSED / "kc_ocod.parquet",
}


def git(*args) -> str:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True, cwd=config.ROOT).stdout.strip()
    except OSError:
        return "git not found"


def short_hash(path) -> str:
    """Hash of the table's contents, not the file bytes, so the same data gives the same hash."""
    df = pd.read_parquet(path)
    return hashlib.md5(pd.util.hash_pandas_object(df, index=False).values.tobytes()).hexdigest()[:10]


def main():
    print(f"git commit          {git('rev-parse', '--short', 'HEAD')}")
    dirty = git("status", "--porcelain", "--untracked-files=no")
    print(f"uncommitted changes {'YES: ' + ' '.join(dirty.split()) if dirty else 'none'}")
    print(f"config              YEAR={config.YEAR} BUILD_COST_PER_M2={config.BUILD_COST_PER_M2} "
          f"LABOUR_SHARE={config.LABOUR_SHARE} PROFIT={config.DEVELOPER_PROFIT_SHARE_OF_PRICE}")
    print(f"packages            " + " ".join(f"{p}={md.version(p)}" for p in
                                             ("streamlit", "plotly", "pandas", "geopandas")))
    ocod_raw = sorted(config.OCOD_DIR.glob(config.OCOD_GLOB)) if config.OCOD_DIR.exists() else []
    print(f"raw OCOD file       {ocod_raw[-1].name if ocod_raw else 'MISSING'}")
    for name, path in APP_FILES.items():
        if not path.exists():
            print(f"{name:<26} MISSING ({path.name})")
            continue
        n = len(pd.read_parquet(path, columns=None))
        print(f"{name:<26} rows={n:<7} hash={short_hash(path)}")

    sales = pd.read_parquet(APP_FILES["sales (all pages)"])
    from src.costs import split_price
    share = split_price(sales["price"], sales["tfarea"], config.BUILD_COST_PER_M2)["land_share"]
    print(f"headline            London median land share {share.median():.1%} "
          f"({len(sales):,} sales)")


if __name__ == "__main__":
    main()
