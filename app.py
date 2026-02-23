"""Streamlit app entrypoint for DR Margin Tool."""

import streamlit as st

from core.io import MissingColumnsError, load_sales_excel
from core.metrics import add_margin_columns, segment_kpis


st.set_page_config(page_title="DR Margin Tool", layout="wide")
st.title("DR Margin Tool")

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
