import math

import pytest

from core.io import to_float_it


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
