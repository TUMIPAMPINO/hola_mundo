import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Test Google Sheets", page_icon="📊")
st.title("📊 Prueba de conexión a Google Sheets")

# Conexión (lee la URL desde los Secrets)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)

    # Prueba 1: leer sin worksheet (primera pestaña)
    st.subheader("1️⃣ Lectura sin especificar pestaña")
    try:
        df_test = conn.read(ttl=0)
        st.success(f"✅ Funciona. Filas: {len(df_test)}, Columnas: {list(df_test.columns)}")
        st.dataframe(df_test.head())
    except Exception as e:
        st.error(f"❌ Falló sin worksheet: {type(e).__name__}: {e}")

    # Prueba 2: leer pestaña "datos"
    st.subheader("2️⃣ Lectura de la pestaña 'datos'")
    try:
        df_datos = conn.read(worksheet="datos", ttl=0)
        st.success(f"✅ Funciona. Filas: {len(df_datos)}, Columnas: {list(df_datos.columns)}")
        st.dataframe(df_datos.head())

        # Histograma simple de intencion_voto si existe
        if "intencion_voto" in df_datos.columns:
            st.subheader("3️⃣ Histograma de intencion_voto")
            df_datos["intencion_voto"] = pd.to_numeric(
                df_datos["intencion_voto"], errors="coerce"
            )
            fig = px.histogram(
                df_datos, x="intencion_voto", nbins=20,
                title="Distribución de intención de voto"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("La columna 'intencion_voto' no existe en la pestaña 'datos'.")
    except Exception as e:
        st.error(f"❌ Falló con worksheet='datos': {type(e).__name__}: {e}")

except Exception as e:
    st.error(f"❌ Error creando la conexión: {type(e).__name__}: {e}")
    st.info(
        "Revisa que en **Secrets** tengas:\n"
        "```toml\n"
        "[connections.gsheets]\n"
        'spreadsheet = "https://docs.google.com/spreadsheets/d/1MfxIbBTKLN1xyNIc_WKnHM0755uX5N9zCd_mUKyy63E/edit"\n'
        "```"
    )
