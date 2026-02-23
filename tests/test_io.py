import math

import pandas as pd
import pytest

from core.io import _detect_header_row, load_sales_excel, to_float_it


@pytest.mark.parametrize(
    "value, expected",
    [
        ("6,17000", 6.17),
        ("1,000", 1.0),
        ("+102,59", 102.59),
        ("+102,59%", 102.59),
        ("", math.nan),
        (None, math.nan),
    ],
)
def test_to_float_it(value, expected):
    result = to_float_it(value)
    if math.isnan(expected):
        assert math.isnan(result)
    else:
        assert result == pytest.approx(expected)


@pytest.mark.parametrize("qty_header", ["Q.TA", "Q.TA’"])
def test_detect_header_row_accepts_qty_variants(qty_header):
    raw_df = pd.DataFrame(
        [
            ["report vendite", None, None],
            ["Categoria Cliente", "Marca / Articolo", qty_header],
            ["Farmacia", "Brand / Item", 10],
        ]
    )

    assert _detect_header_row(raw_df) == 1


class NamedBytesIO(__import__("io").BytesIO):
    def __init__(self, *args, name: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name


def test_load_sales_excel_accepts_abbreviated_headers():
    source_df = pd.DataFrame(
        {
            "CT": ["Farmacia"],
            "MARCA / ARTICOLO": ["Brand / Item"],
            "Q.TA'": ["10,00"],
            "PRZ. ULT.ACQ.": ["2,00"],
            "PREZZO SC.": ["3,50"],
        }
    )

    excel_file = NamedBytesIO(name="vendite.xlsx")
    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        source_df.to_excel(writer, index=False)

    loaded = load_sales_excel(excel_file)

    assert "categoria cliente" in loaded.columns
    assert "quantità" in loaded.columns
    assert "ultimo prezzo acquisto" in loaded.columns
    assert "prezzo vendita" in loaded.columns
