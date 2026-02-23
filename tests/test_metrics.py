import pandas as pd
import pytest

from core.metrics import (
    add_margin_columns,
    add_opportunity,
    clienti_brand_opportunities,
    flotte_brand_opportunities,
    low_margin_articles,
    non_flotte_brand_opportunities,
    segment_article_drilldown,
    segment_kpis,
)


def test_brand_opportunity_functions_are_importable_from_core_metrics():
    from core.metrics import clienti_brand_opportunities as clienti_imported
    from core.metrics import flotte_brand_opportunities as flotte_imported

    assert flotte_imported is flotte_brand_opportunities
    assert clienti_imported is clienti_brand_opportunities


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


def test_add_opportunity_computes_migliorabile_euro():
    df_brand = pd.DataFrame(
        {
            "marca": ["A", "B"],
            "fatturato": [100.0, 200.0],
            "margine_euro": [30.0, 120.0],
            "margine_pct": [0.30, 0.60],
        }
    )

    result = add_opportunity(df_brand, target_pct=0.50)

    assert result.loc[0, "target_pct"] == pytest.approx(0.50)
    assert result.loc[1, "target_pct"] == pytest.approx(0.50)
    assert result.loc[0, "migliorabile_euro"] == pytest.approx(20.0)
    assert result.loc[1, "migliorabile_euro"] == pytest.approx(0.0)


def test_brand_opportunities_filter_segments_correctly():
    df = pd.DataFrame(
        {
            "categoria cliente": [46, 46, 10, 10],
            "marca": ["Fleet", "Fleet2", "Client", "Client2"],
            "fatturato_riga": [100.0, 150.0, 200.0, 50.0],
            "margine_euro": [20.0, 60.0, 40.0, 10.0],
        }
    )

    flotte_result = flotte_brand_opportunities(df, target_pct=0.50)
    clienti_result = clienti_brand_opportunities(df, target_pct=0.45)

    assert set(flotte_result["marca"]) == {"Fleet", "Fleet2"}
    assert set(clienti_result["marca"]) == {"Client", "Client2"}
    assert "Client" not in set(flotte_result["marca"])
    assert "Fleet" not in set(clienti_result["marca"])


def test_clienti_brand_opportunities_is_wrapper_for_non_flotte():
    df = pd.DataFrame(
        {
            "categoria cliente": [46, 10],
            "marca": ["Fleet", "Client"],
            "fatturato_riga": [100.0, 200.0],
            "margine_euro": [20.0, 40.0],
        }
    )

    wrapper_result = clienti_brand_opportunities(df, target_pct=0.45)
    canonical_result = non_flotte_brand_opportunities(df, target_pct=0.45)

    pd.testing.assert_frame_equal(wrapper_result, canonical_result)


def test_low_margin_articles_returns_only_rows_below_threshold():
    df = pd.DataFrame(
        {
            "categoria cliente": [46, 46, 10],
            "marca": ["A", "A", "B"],
            "articolo": ["x", "y", "z"],
            "quantità": [10.0, 5.0, 10.0],
            "fatturato_riga": [100.0, 100.0, 100.0],
            "margine_euro": [5.0, 20.0, 8.0],
            "costo_riga": [95.0, 80.0, 92.0],
        }
    )

    result = low_margin_articles(df, segment="tutti", threshold_pct=0.10)

    assert set(result["articolo"]) == {"x", "z"}
    assert (result["margine_pct"] < 0.10).all()


def test_segment_article_drilldown_filters_selected_brand_and_sorts_by_margin_pct():
    df = pd.DataFrame(
        {
            "categoria cliente": [46, 46, 46, 10],
            "marca": ["A", "A", "A", "B"],
            "articolo": ["high", "low", "mid", "other"],
            "quantità": [10.0, 10.0, 10.0, 10.0],
            "fatturato_riga": [100.0, 100.0, 100.0, 100.0],
            "margine_euro": [30.0, 5.0, 20.0, 1.0],
            "costo_riga": [70.0, 95.0, 80.0, 99.0],
        }
    )

    result = segment_article_drilldown(
        df,
        segment="flotte",
        selected_brand="A",
        target_pct=0.25,
    )

    assert set(result["marca"]) == {"A"}
    assert list(result["articolo"]) == ["low", "mid", "high"]
    assert result["margine_pct"].is_monotonic_increasing
