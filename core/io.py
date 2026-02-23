"""Input/Output utilities for DR Margin Tool."""

from __future__ import annotations

import math
import re
from typing import Any

import pandas as pd


REQUIRED_COLUMNS = [
    "categoria cliente",
    "MARCA / ARTICOLO",
    "quantità",
    "ultimo prezzo acquisto",
    "prezzo vendita",
]

HEADER_ALIASES = {
    "categoria cliente": "categoria cliente",
    "cat cliente": "categoria cliente",
    "categoria": "categoria cliente",
    "ct": "categoria cliente",
    "marca / articolo": "MARCA / ARTICOLO",
    "marca/articolo": "MARCA / ARTICOLO",
    "articolo": "MARCA / ARTICOLO",
    "quantità": "quantità",
    "q.ta'": "quantità",
    "q.ta": "quantità",
    "qta": "quantità",
    "ultimo prezzo acquisto": "ultimo prezzo acquisto",
    "u.p.a.": "ultimo prezzo acquisto",
    "prz. ult.acq.": "ultimo prezzo acquisto",
    "prezzo vendita": "prezzo vendita",
    "p.v.": "prezzo vendita",
    "prezzo sc.": "prezzo vendita",
    "%ric.": "ricarico",
    "cfr": "codice cliente",
    "cs": "sottocategoria cliente",
}

HEADER_ALIASES_CF = {k.casefold(): v for k, v in HEADER_ALIASES.items()}


class MissingColumnsError(ValueError):
    """Raised when required columns are missing from input data."""


def to_float_it(x: Any) -> float:
    """Convert Italian-formatted numeric values to float.

    Handles values like:
    - "6,17000" -> 6.17
    - "1,000" -> 1.0
    - "+102,59" or "+102,59%" -> 102.59
    """
    if x is None:
        return math.nan

    if isinstance(x, float) and math.isnan(x):
        return math.nan

    if pd.isna(x):
        return math.nan

    if isinstance(x, (int, float)):
        return float(x)

    s = str(x).strip()
    if s == "":
        return math.nan

    # Remove optional plus sign and percent marker.
    s = s.replace("+", "").replace("%", "").strip()
    if s == "":
        return math.nan

    # Normalize spaces and common thousand separators.
    s = re.sub(r"\s+", "", s)

    # Italian format: comma as decimal separator.
    if "," in s and "." in s:
        # If both exist, assume dots are thousand separators in Italian input.
        s = s.replace(".", "")

    s = s.replace(",", ".")

    try:
        return float(s)
    except ValueError:
        return math.nan


def _normalize_column_name(name: Any) -> str:
    name_str = str(name).strip()
    return re.sub(r"\s{2,}", " ", name_str)


def _normalize_for_match(value: Any) -> str:
    text = _normalize_column_name(value).replace("’", "'")
    return text.casefold()


def _detect_header_row(raw_df: pd.DataFrame, scan_limit: int = 10) -> int:
    max_rows = min(scan_limit, len(raw_df.index))
    for idx in range(max_rows):
        row_values = {
            _normalize_for_match(value)
            for value in raw_df.iloc[idx].tolist()
            if not pd.isna(value) and str(value).strip()
        }

        has_customer = any(
            key in row_values
            for key in ("categoria cliente", "cat cliente", "categoria", "ct")
        )
        has_brand_item = any(
            key in row_values for key in ("marca / articolo", "marca/articolo", "articolo")
        )
        has_qty = any(key in row_values for key in {"q.ta'", "q.ta", "qta", "quantità"})

        if has_customer and has_brand_item and has_qty:
            return idx

    return 0


def load_sales_excel(file: Any) -> pd.DataFrame:
    """Load and clean sales Excel data uploaded from Streamlit."""
    file_name = getattr(file, "name", str(file))
    if not str(file_name).lower().endswith(".xlsx"):
        raise ValueError(
            "Formato file non supportato: esporta il file vendite come .xlsx e riprova."
        )

    if hasattr(file, "seek"):
        file.seek(0)

    preview = pd.read_excel(file, header=None, nrows=30)
    header_row = _detect_header_row(preview, scan_limit=30)

    if hasattr(file, "seek"):
        file.seek(0)

    df = pd.read_excel(file, header=header_row)

    df.columns = [_normalize_column_name(col) for col in df.columns]
    df = df.rename(
        columns=lambda col: HEADER_ALIASES_CF.get(col.casefold(), col)
    )

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise MissingColumnsError(
            "Colonne mancanti nel file Excel: " + ", ".join(missing)
        )

    numeric_columns = ["quantità", "ultimo prezzo acquisto", "prezzo vendita"]
    for col in numeric_columns:
        df[col] = df[col].map(to_float_it)

    split_cols = df["MARCA / ARTICOLO"].astype(str).str.split("/", n=1, expand=True)
    df["marca"] = split_cols[0].str.strip()
    if split_cols.shape[1] > 1:
        df["articolo"] = split_cols[1].str.strip()
    else:
        df["articolo"] = ""

    return df
