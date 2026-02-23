import pytest
import pandas as pd

from core.metrics import add_margin_columns, segment_kpis


def test_add_margin_columns_computes_margine_pct_known_case():
    df = pd.DataFrame(
        {
            "prezzo vendita": [10.0],
            "ultimo prezzo acquisto": [6.0],
            "quantità": [2.0],
            "categoria cliente": [46],
        }
    )

    result = add_margin_columns(df)

    assert result.loc[0, "fatturato_riga"] == pytest.approx(20.0)
    assert result.loc[0, "margine_euro"] == pytest.approx(8.0)
    assert result.loc[0, "margine_pct"] == pytest.approx(0.4)


def test_segment_kpis_handles_flotte_non_flotte_and_totale():
    df = pd.DataFrame(
        {
            "categoria cliente": [46, 12],
            "fatturato_riga": [100.0, 80.0],
            "margine_euro": [20.0, 10.0],
        }
    )

    result = segment_kpis(df)

    assert list(result.index) == ["flotte", "non_flotte", "totale"]
    assert result.loc["flotte", "fatturato_totale"] == pytest.approx(100.0)
    assert result.loc["flotte", "margine_totale"] == pytest.approx(20.0)
    assert result.loc["flotte", "margine_medio_pct"] == pytest.approx(0.2)

    assert result.loc["non_flotte", "fatturato_totale"] == pytest.approx(80.0)
    assert result.loc["non_flotte", "margine_totale"] == pytest.approx(10.0)
    assert result.loc["non_flotte", "margine_medio_pct"] == pytest.approx(0.125)

    assert result.loc["totale", "fatturato_totale"] == pytest.approx(180.0)
    assert result.loc["totale", "margine_totale"] == pytest.approx(30.0)
    assert result.loc["totale", "margine_medio_pct"] == pytest.approx(30.0 / 180.0)
