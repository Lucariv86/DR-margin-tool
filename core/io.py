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


def load_sales_excel(file: Any) -> pd.DataFrame:
    """Load and clean sales Excel data uploaded from Streamlit."""
    df = pd.read_excel(file)

    df.columns = [_normalize_column_name(col) for col in df.columns]

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
