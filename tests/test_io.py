import math

import pandas as pd
import pytest

from core.io import _detect_header_row, to_float_it


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
