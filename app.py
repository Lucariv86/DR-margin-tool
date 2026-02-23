"""Streamlit app entrypoint for DR Margin Tool."""

import streamlit as st

from core.io import MissingColumnsError, load_sales_excel


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
        st.subheader("Anteprima dati (prime 10 righe)")
        st.dataframe(data.head(10), use_container_width=True)
    except MissingColumnsError as exc:
        st.error(f"Il file caricato non contiene le colonne richieste. Dettaglio: {exc}")
    except ValueError as exc:
        st.error(str(exc))
    except Exception:
        st.error(
            "Si è verificato un errore durante la lettura del file. "
            "Verifica che sia un file .xlsx valido e riprova."
        )
