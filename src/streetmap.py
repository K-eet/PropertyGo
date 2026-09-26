"""Street-level map for one borough: house sales (cost vs price) and overseas-company titles."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

import config

# Points that share a postcode centroid are spread on a small circle so each can be hovered.
SPREAD_RADIUS_DEG = 0.00009  # about 10 m north-south
OCOD_RED = "#D62728"
SALES_SCALE = "Blues"


def gbp(x) -> str:
    return f"£{x:,.0f}" if pd.notna(x) else "n/a"


def spread_points(df: pd.DataFrame) -> pd.DataFrame:
    """Offset rows that share a lat/lon so they sit on a small circle round the centroid."""
    df = df.copy()
    grp = df.groupby(["lat", "lon"])
    n = grp["lat"].transform("size")
    i = grp.cumcount()
    angle = 2 * np.pi * i / n
    r = np.where(n > 1, SPREAD_RADIUS_DEG, 0.0)
    df["lat_plot"] = df["lat"] + r * np.sin(angle)
    df["lon_plot"] = df["lon"] + r * np.cos(angle) / np.cos(np.radians(df["lat"]))
    return df


def sale_address(row) -> str:
    """'FLAT 1', '5', 'CADOGAN STREET' -> 'Flat 1, 5 Cadogan Street'."""
    def clean(x):
        return str(x).title().strip() if pd.notna(x) and str(x).strip() else ""
    house = " ".join(p for p in (clean(row.get("paon")), clean(row.get("street"))) if p)
    return ", ".join(p for p in (clean(row.get("saon")), house) if p)


def sales_hover(df: pd.DataFrame, cost_per_m2: float) -> pd.Series:
    build = df["tfarea"] * cost_per_m2
    gap = df["price"] - build
    share = gap / df["price"]
    lines = (
        "<b>" + df.apply(sale_address, axis=1) + "</b>, " + df["postcode"]
        + "<br>Sold " + df["date"].dt.strftime("%b %Y") + " for <b>" + df["price"].map(gbp) + "</b>"
        + "<br>Floor area " + df["tfarea"].round().astype(int).astype(str) + " m²"
        + "<br>Build cost (estimate): " + build.map(gbp)
        + "<br>Gap (land, profit, other): <b>" + gap.map(gbp) + "</b>"
        + "<br>Land share: <b>" + (share * 100).round().astype(int).astype(str) + "%</b>"
    )
    offshore = np.where(
        df["offshore_company_title"],
        "<br><span style='color:" + OCOD_RED + "'>Title held by overseas company: "
        + df["proprietor"].fillna("").str.title() + " (" + df["country_incorporated"].fillna("").str.title() + ")</span>",
        "",
    )
    return lines + offshore


def aggregate_ocod(ocod: pd.DataFrame, examples: int = 3) -> pd.DataFrame:
    """One row per postcode: number of overseas-company titles, main countries, example titles."""
    ocod = ocod.dropna(subset=["lat", "lon"])

    def summarise(g):
        countries = g["country_incorporated"].fillna("Unknown").str.title().value_counts()
        top = ", ".join(f"{c} ({n})" for c, n in countries.head(3).items())
        ex = "<br>".join(
            "· " + g["property_address"].str.title().str.slice(0, 60).head(examples)
            + " — " + g["proprietor"].fillna("").str.title().str.slice(0, 40).head(examples)
        )
        more = f"<br>· and {len(g) - examples} more" if len(g) > examples else ""
        return pd.Series({
            "lat": g["lat"].iloc[0], "lon": g["lon"].iloc[0], "titles": len(g),
            "flats": int(g["is_flat"].sum()),
            "hover": (f"<b>{g.name}: {len(g)} overseas-company title{'s' if len(g) != 1 else ''}</b>"
                      f" ({int(g['is_flat'].sum())} flats)<br>Incorporated in: {top}<br>{ex}{more}"),
        })

    return ocod.groupby("postcode").apply(summarise, include_groups=False).reset_index()


def street_map(sales: pd.DataFrame, ocod_by_postcode, cost_per_m2: float) -> go.Figure:
    """Blue points: house sales coloured by land share. Red: overseas-company titles per postcode."""
    s = spread_points(sales.dropna(subset=["lat", "lon"]))
    share = 1 - s["tfarea"] * cost_per_m2 / s["price"]
    fig = go.Figure()

    if ocod_by_postcode is not None and len(ocod_by_postcode):
        o = ocod_by_postcode
        fig.add_trace(go.Scattermap(
            lat=o["lat"], lon=o["lon"], mode="markers", name="Overseas-company titles (per postcode)",
            marker=dict(size=np.clip(6 + 3 * np.sqrt(o["titles"]), 7, 40), color=OCOD_RED, opacity=0.55),
            text=o["hover"], hovertemplate="%{text}<extra></extra>",
        ))

    fig.add_trace(go.Scattermap(
        lat=s["lat_plot"], lon=s["lon_plot"], mode="markers", name=f"House sales {config.YEAR}",
        marker=dict(size=11, color=share, colorscale=SALES_SCALE, cmin=0.5, cmax=1.0,
                    colorbar=dict(title="Land share", tickformat=".0%", x=1.0, len=0.6)),
        text=sales_hover(s, cost_per_m2), hovertemplate="%{text}<extra></extra>",
    ))

    matched = s[s["offshore_company_title"]]
    if len(matched):
        fig.add_trace(go.Scattermap(
            lat=matched["lat_plot"], lon=matched["lon_plot"], mode="markers",
            name="House sale, title now held by overseas company",
            marker=dict(size=17, color=OCOD_RED), text=sales_hover(matched, cost_per_m2),
            hovertemplate="%{text}<extra></extra>",
        ))

    fig.update_layout(
        map=dict(style="open-street-map", center=dict(lat=s["lat"].mean(), lon=s["lon"].mean()), zoom=13),
        height=620, margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation="h", y=-0.02, yanchor="top", x=0),
        hoverlabel=dict(align="left"),
    )
    return fig
