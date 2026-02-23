"""Streamlit app entrypoint for DR Margin Tool."""

import streamlit as st

from core.io import MissingColumnsError, load_sales_excel
from core.metrics import (
    add_margin_columns,
    clienti_brand_opportunities,
    flotte_brand_opportunities,
    segment_kpis,
)


st.set_page_config(page_title="DR Margin Tool", layout="wide")
st.title("DR Margin Tool")

target_flotte_pct = st.sidebar.number_input(
    "Target margine % Flotte",
    min_value=0.0,
    max_value=100.0,
    value=50.0,
    step=1.0,
) / 100

target_clienti_pct = st.sidebar.number_input(
    "Target margine % Clienti",
    min_value=0.0,
    max_value=100.0,
    value=45.0,
    step=1.0,
) / 100

uploaded_file = st.file_uploader(
    "Carica file Excel vendite (.xlsx)",
    type=["xlsx"],
    help="L'app supporta solo esportazioni in formato .xlsx.",
)

if uploaded_file is not None:
    try:
        data = load_sales_excel(uploaded_file)
        data = add_margin_columns(data)
        kpi_df = segment_kpis(data)

        st.subheader("KPI per segmento")
        flotte_col, non_flotte_col, totale_col = st.columns(3)

        segment_layout = [
            ("flotte", "Flotte", flotte_col),
            ("non_flotte", "Non Flotte", non_flotte_col),
            ("totale", "Totale", totale_col),
        ]

        for segment_key, segment_label, segment_col in segment_layout:
            values = kpi_df.loc[segment_key]
            with segment_col:
                st.markdown(f"**{segment_label}**")
                st.metric("Fatturato", f"€ {values['fatturato_totale']:,.2f}")
                st.metric("Margine €", f"€ {values['margine_totale']:,.2f}")
                margin_pct = values["margine_medio_pct"]
                margin_pct_text = "n/d" if margin_pct != margin_pct else f"{margin_pct:.2%}"
                st.metric("Margine %", margin_pct_text)

        st.subheader("Margine migliorabile € per marca")
        flotte_tab, clienti_tab = st.tabs(["Flotte", "Clienti"])

        with flotte_tab:
            flotte_brand_df = flotte_brand_opportunities(data, target_flotte_pct)
            st.dataframe(
                flotte_brand_df.style.format(
                    {
                        "fatturato": "€ {:,.2f}",
                        "margine_euro": "€ {:,.2f}",
                        "margine_pct": "{:.2%}",
                        "target_pct": "{:.2%}",
                        "migliorabile_euro": "€ {:,.2f}",
                    }
                ),
                use_container_width=True,
            )

        with clienti_tab:
            clienti_brand_df = clienti_brand_opportunities(data, target_clienti_pct)
            st.dataframe(
                clienti_brand_df.style.format(
                    {
                        "fatturato": "€ {:,.2f}",
                        "margine_euro": "€ {:,.2f}",
                        "margine_pct": "{:.2%}",
                        "target_pct": "{:.2%}",
                        "migliorabile_euro": "€ {:,.2f}",
                    }
                ),
                use_container_width=True,
            )

        st.subheader("Anteprima dati (prime 20 righe)")
        preview_columns = [
            "categoria cliente",
            "MARCA / ARTICOLO",
            "quantità",
            "ultimo prezzo acquisto",
            "prezzo vendita",
            "fatturato_riga",
            "margine_euro",
            "margine_pct",
        ]
        available_columns = [col for col in preview_columns if col in data.columns]
        st.dataframe(data[available_columns].head(20), use_container_width=True)
    except MissingColumnsError as exc:
        st.error(f"Il file caricato non contiene le colonne richieste. Dettaglio: {exc}")
    except ValueError as exc:
        st.error(str(exc))
    except Exception:
        st.error(
            "Si è verificato un errore durante la lettura del file. "
            "Verifica che sia un file .xlsx valido e riprova."
        )
