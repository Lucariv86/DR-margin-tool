"""Metrics utilities for margin calculations and KPI segmentation."""

from __future__ import annotations

import numpy as np
import pandas as pd


__all__ = [
    "REQUIRED_METRIC_COLUMNS",
    "add_margin_columns",
    "segment_kpis",
    "brand_summary",
    "add_opportunity",
    "flotte_brand_opportunities",
    "non_flotte_brand_opportunities",
    "clienti_brand_opportunities",
]


REQUIRED_METRIC_COLUMNS = [
    "prezzo vendita",
    "ultimo prezzo acquisto",
    "quantità",
    "categoria cliente",
]


def add_margin_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of *df* with revenue and margin columns.

    Added columns:
    - fatturato_riga = prezzo vendita * quantità
    - margine_euro = (prezzo vendita - ultimo prezzo acquisto) * quantità
    - margine_pct = (prezzo vendita - ultimo prezzo acquisto) / prezzo vendita
      (NaN when prezzo vendita is 0 or NaN)
    """
    result = df.copy()

    sale_price = pd.to_numeric(result["prezzo vendita"], errors="coerce")
    purchase_price = pd.to_numeric(result["ultimo prezzo acquisto"], errors="coerce")
    quantity = pd.to_numeric(result["quantità"], errors="coerce")

    result["fatturato_riga"] = sale_price * quantity
    result["margine_euro"] = (sale_price - purchase_price) * quantity

    denominator = sale_price.where((sale_price != 0) & sale_price.notna())
    result["margine_pct"] = (sale_price - purchase_price) / denominator

    return result


def segment_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Compute KPI aggregates for flotte, non_flotte, and totale segments."""
    categoria = pd.to_numeric(df["categoria cliente"], errors="coerce")

    segment_masks = {
        "flotte": categoria == 46,
        "non_flotte": categoria != 46,
        "totale": pd.Series(True, index=df.index),
    }

    rows = {}
    for segment_name, mask in segment_masks.items():
        segment_df = df.loc[mask]
        fatturato_totale = segment_df["fatturato_riga"].sum()
        margine_totale = segment_df["margine_euro"].sum()
        margine_medio_pct = (
            np.nan if fatturato_totale == 0 else margine_totale / fatturato_totale
        )

        rows[segment_name] = {
            "fatturato_totale": fatturato_totale,
            "margine_totale": margine_totale,
            "margine_medio_pct": margine_medio_pct,
        }

    return pd.DataFrame.from_dict(rows, orient="index")


def brand_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate revenue and margin metrics by brand."""
    grouped = (
        df.groupby("marca", dropna=False, as_index=False)
        .agg(
            fatturato=("fatturato_riga", "sum"),
            margine_euro=("margine_euro", "sum"),
        )
    )

    grouped["margine_pct"] = np.where(
        grouped["fatturato"] == 0,
        np.nan,
        grouped["margine_euro"] / grouped["fatturato"],
    )
    return grouped


def add_opportunity(df_brand: pd.DataFrame, target_pct: float) -> pd.DataFrame:
    """Add target and improvable euro margin based on target margin percent."""
    result = df_brand.copy()
    result["target_pct"] = target_pct

    opportunity = (target_pct - result["margine_pct"]) * result["fatturato"]
    result["migliorabile_euro"] = opportunity.clip(lower=0)
    return result


def flotte_brand_opportunities(df: pd.DataFrame, target_pct: float) -> pd.DataFrame:
    """Compute brand opportunities for fleet clients (categoria cliente == 46)."""
    categoria = pd.to_numeric(df["categoria cliente"], errors="coerce")
    flotte_df = df.loc[categoria == 46]

    summary = brand_summary(flotte_df)
    with_opportunity = add_opportunity(summary, target_pct)
    return with_opportunity.sort_values("migliorabile_euro", ascending=False)


def non_flotte_brand_opportunities(df: pd.DataFrame, target_pct: float) -> pd.DataFrame:
    """Compute brand opportunities for non-fleet clients (categoria cliente != 46)."""
    categoria = pd.to_numeric(df["categoria cliente"], errors="coerce")
    clienti_df = df.loc[categoria != 46]

    summary = brand_summary(clienti_df)
    with_opportunity = add_opportunity(summary, target_pct)
    return with_opportunity.sort_values("migliorabile_euro", ascending=False)


def clienti_brand_opportunities(df: pd.DataFrame, target_pct: float) -> pd.DataFrame:
    """Backward-compatible name used by app.py for non-fleet opportunities."""
    return non_flotte_brand_opportunities(df, target_pct)
