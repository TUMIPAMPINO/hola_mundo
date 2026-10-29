import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import base64
import io

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Donut Interactivo",
                   layout="wide", page_icon="🍩")

# 2. CARGA DE DATOS


@st.cache_data
def cargar_datos():
    nombre_archivo = "mio.xlsx"
    try:
        df_votos = pd.read_excel(nombre_archivo, sheet_name="datos")
        df_logos = pd.read_excel(nombre_archivo, sheet_name="logos")
        if "partido_politico" in df_votos.columns and "partido_politico" in df_logos.columns:
            df_final = pd.merge(df_votos, df_logos[[
                                "partido_politico", "logo_url"]], on="partido_politico", how="left")
        else:
            df_final = df_votos
            df_final["logo_url"] = None
        df_final['intencion_voto'] = pd.to_numeric(
            df_final['intencion_voto'], errors='coerce')
        df_final['intencion_voto'] = df_final['intencion_voto'].fillna(0.0)
        df_final.loc[df_final['intencion_voto'] <= 1.0,
                     'intencion_voto'] = df_final['intencion_voto'] * 100
        df_final = df_final[df_final['candidato'].notna() & (
            df_final['candidato'] != 'mm')]
        return df_final.sort_values(by="intencion_voto", ascending=False).reset_index(drop=True)
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()


df = cargar_datos()

if not df.empty:
    # FILTROS
    ambito = st.sidebar.selectbox("Ámbito:", df.iloc[:, 0].unique())
    df_f1 = df[df.iloc[:, 0] == ambito]
    localidad = st.sidebar.selectbox(
        "Localidad/Distrito:", df_f1.iloc[:, 1].unique())
    df_filtrado = df_f1[df_f1.iloc[:, 1] == localidad].sort_values(
        by="intencion_voto", ascending=False).reset_index(drop=True)

if not df_filtrado.empty:

    st.sidebar.markdown("---")
    st.sidebar.header("🎨 Personalización del Donut")

    # ==================== 1. POSICIÓN DE LA LEYENDA ====================
    posicion_leyenda = st.sidebar.selectbox(
        "📍 Posición de la Leyenda:",
        ["Derecha", "Izquierda", "Abajo", "Arriba", "Ocultar"],
        index=0
    )

    mapa_leyenda = {
        "Derecha": {"x": 1.02, "y": 0.5, "xanchor": "left", "yanchor": "middle", "orientation": "v"},
        "Izquierda": {"x": -0.02, "y": 0.5, "xanchor": "right", "yanchor": "middle", "orientation": "v"},
        "Abajo": {"x": 0.5, "y": -0.1, "xanchor": "center", "yanchor": "top", "orientation": "h"},
        "Arriba": {"x": 0.5, "y": 1.02, "xanchor": "center", "yanchor": "bottom", "orientation": "h"},
        "Ocultar": {"x": 0, "y": 0, "xanchor": "center", "yanchor": "middle", "orientation": "v"}
    }

    leyenda_config = mapa_leyenda[posicion_leyenda]

    # ==================== 2. MOSTRAR NOMBRES CERCA DEL DONUT ====================
    mostrar_nombres = st.sidebar.checkbox(
        "📝 Mostrar nombres cerca del donut", value=False)

    # ==================== 2.5. MOSTRAR POSICIONES EN VEZ DE PORCENTAJES ====================
    mostrar_posiciones = st.sidebar.checkbox(
        "🏆 Mostrar posiciones (1°, 2°, 3°...) en lugar de porcentajes",
        value=False,
        help="Si está activado, muestra la posición según el orden de votación. Si está desactivado, muestra el porcentaje numérico."
    )

    # ==================== 3. PALETA BASE (se usará para el degradado) ====================
    paleta_base = st.sidebar.selectbox(
        "🎨 Paleta de Colores Base:",
        [
            "Verde",
            "Azul",
            "Rojo",
            "Naranja",
            "Morado",
            "Turquesa",
            "Rosa",
            "Amarillo"
        ],
        index=0
    )

    # ==================== 4. INTENSIDAD MÁXIMA ====================
    intensidad_max = st.sidebar.slider(
        "🎯 Intensidad Máxima (Líder):", 0.5, 1.0, 0.95, 0.05)
    intensidad_min = st.sidebar.slider(
        "🎯 Intensidad Mínima (Último):", 0.1, 0.5, 0.25, 0.05)

    # ==================== 5. TAMAÑO GENERAL DEL LOGO ====================
    tamanio_logo_general = st.sidebar.slider(
        "📐 Tamaño General del Logo:", 0.04, 0.20, 0.09, 0.01)

    # ==================== 6. TAMAÑO DEL TEXTO DE NOMBRES ====================
    tamanio_nombre = st.sidebar.slider("📝 Tamaño del Nombre:", 8, 20, 12, 1)

    # ==================== 7. TAMAÑO DEL PORCENTAJE ====================
    tamanio_porcentaje = st.sidebar.slider(
        "📊 Tamaño del Porcentaje:", 8, 20, 14, 1)

    # ==================== 8. MOSTRAR/OCULTAR LÍNEAS ====================
    mostrar_lineas = st.sidebar.checkbox(
        "🔗 Mostrar líneas conectoras", value=True)

    st.sidebar.markdown("---")
    st.sidebar.header("🎯 Controles Individuales")

    # ==================== 9. CONTROLES INDIVIDUALES ====================
    controles_logos = {}
    controles_nombres = {}
    tamanios_individuales = {}

    for idx, row in df_filtrado.iterrows():
        st.sidebar.markdown(f"**{row['candidato']}**")

        # Tamaño individual del logo
        tamanio_individual = st.slider(
            "📐 Tamaño Logo",
            min_value=0.02,
            max_value=0.25,
            value=tamanio_logo_general,
            step=0.01,
            key=f"tam_logo_{idx}"
        )
        tamanios_individuales[row['candidato']] = tamanio_individual

        # Controles para el LOGO (ajuste fino de ángulo)
        st.sidebar.markdown("🖼️ **Posición Logo**")
        col1, col2 = st.sidebar.columns(2)

        with col1:
            angulo_logo = st.slider(
                "Ángulo Logo",
                min_value=-15,
                max_value=15,
                value=0,
                step=1,
                key=f"ang_logo_{idx}"
            )

        with col2:
            # Radio fijo en el borde exterior de la dona
            st.sidebar.markdown("*(Borde exterior de la dona)*")
            radio_logo = 0.50

        controles_logos[row['candidato']] = (angulo_logo, radio_logo)

        # Controles para el NOMBRE
        st.sidebar.markdown("📝 **Posición Nombre**")
        col5, col6 = st.sidebar.columns(2)

        with col5:
            angulo_nombre = st.slider(
                "Ángulo Nombre",
                min_value=-60,
                max_value=60,
                value=0,
                step=1,
                key=f"ang_nom_{idx}"
            )

        with col6:
            radio_nombre = st.slider(
                "Radio Nombre",
                min_value=0.15,
                max_value=0.85,
                value=0.65,
                step=0.01,
                key=f"rad_nom_{idx}"
            )

        controles_nombres[row['candidato']] = (angulo_nombre, radio_nombre)

        st.sidebar.markdown("---")

    # ==================== GENERAR PALETA CON DEGRADADO INTENSIDAD ====================
    def generar_paleta_degradada(paleta_base, n_colores, intensidad_max, intensidad_min):
        """Genera colores donde el más votado es más intenso y el menos votado es más pálido"""

        # Colores base según paleta
        colores_base = {
            "Verde": {'r': 76, 'g': 175, 'b': 80},
            "Azul": {'r': 33, 'g': 150, 'b': 243},
            "Rojo": {'r': 244, 'g': 67, 'b': 54},
            "Naranja": {'r': 255, 'g': 152, 'b': 0},
            "Morado": {'r': 156, 'g': 39, 'b': 176},
            "Turquesa": {'r': 0, 'g': 188, 'b': 212},
            "Rosa": {'r': 233, 'g': 30, 'b': 99},
            "Amarillo": {'r': 255, 'g': 193, 'b': 7}
        }

        base = colores_base.get(paleta_base, colores_base["Azul"])

        # Generar colores con intensidad decreciente según la posición (ordenados por voto)
        colores = []
        for i in range(n_colores):
            # Progresión lineal desde intensidad_max (primeros) hasta intensidad_min (últimos)
            if n_colores > 1:
                t = i / (n_colores - 1)
            else:
                t = 0

            # Intensidad: más intenso para los primeros (t=0), más pálido para los últimos (t=1)
            intensidad = intensidad_max - (intensidad_max - intensidad_min) * t

            r = int(base['r'] * intensidad + 255 * (1 - intensidad))
            g = int(base['g'] * intensidad + 255 * (1 - intensidad))
            b = int(base['b'] * intensidad + 255 * (1 - intensidad))

            colores.append(f'#{r:02x}{g:02x}{b:02x}')

        return colores

    # Generar colores con degradado de intensidad (más votado = más sólido)
    colores_usar = generar_paleta_degradada(
        paleta_base,
        len(df_filtrado),
        intensidad_max,
        intensidad_min
    )

    # ==================== CREAR GRÁFICO DONUT ====================
    fig_dona = go.Figure()

    # Agregar donut (SIN texto de porcentaje ni nombres)
    # Crear el pie con grupos de leyenda individuales
    fig_dona.add_trace(go.Pie(
        labels=df_filtrado['candidato'].tolist(),
        values=df_filtrado['intencion_voto'].tolist(),
        hole=0.50,
        marker=dict(
            colors=colores_usar,
            line=dict(color='#FFFFFF', width=2.5)
        ),
        textinfo='none',
        direction="clockwise",
        sort=False,
        pull=[0.02] * len(df_filtrado),
        hovertemplate="<b>%{label}</b><br>Votos: %{value:.1f}%<br>Participación: %{percent}<extra></extra>",
        showlegend=True,
        # Los nombres de los candidatos se usarán como grupos de leyenda
        legendgroup=df_filtrado['candidato'].tolist(
        )[0] if len(df_filtrado) > 0 else None,
        # Esto hace que cada slice tenga su propia entrada en la leyenda
        name=df_filtrado['candidato'].tolist()[0] if len(
            df_filtrado) > 0 else None
    ))

    # Actualizar la leyenda para mostrar todos los nombres individualmente
    fig_dona.update_traces(
        legendgroup=None,  # Resetear el grupo para que cada slice sea individual
        showlegend=True
    )

    # Para asegurar que cada slice tenga su propia entrada en la leyenda
    for i in range(len(df_filtrado)):
        fig_dona.data[0].update(
            legendgroup=df_filtrado.iloc[i]['candidato'],
            name=df_filtrado.iloc[i]['candidato']
        )

    # ==================== INSERTAR LOGOS Y PORCENTAJES ====================
    total_votos = df_filtrado['intencion_voto'].sum()

    if total_votos > 0:
        angulo_inicio = 90

        for idx, row in df_filtrado.iterrows():
            votos = float(row['intencion_voto'])
            if votos <= 0:
                continue

            # Ángulo base del sector
            amplitud_angulo = (votos / total_votos) * 360
            # Ángulo medio del sector (centro exacto de la porción)
            angulo_medio = angulo_inicio - (amplitud_angulo / 2)

            # ---- LOGO (en el borde exterior de la dona: radio = 0.50) ----
            if row['candidato'] in controles_logos:
                angulo_extra_logo, radio_logo = controles_logos[row['candidato']]
            else:
                angulo_extra_logo, radio_logo = 0, 0.50

            angulo_rad_logo = np.radians(angulo_medio + angulo_extra_logo)

            pos_x_logo = 0.5 + radio_logo * np.cos(angulo_rad_logo)
            pos_y_logo = 0.5 + radio_logo * np.sin(angulo_rad_logo)

            # ---- PORCENTAJE (en la misma dirección radial, dentro de la dona) ----
            radio_porcentaje = 0.38
            pos_x_pct = 0.5 + radio_porcentaje * np.cos(angulo_rad_logo)
            pos_y_pct = 0.5 + radio_porcentaje * np.sin(angulo_rad_logo)

            # ---- NOMBRE ----
            if row['candidato'] in controles_nombres:
                angulo_extra_nom, radio_extra_nom = controles_nombres[row['candidato']]
            else:
                angulo_extra_nom, radio_extra_nom = 0, 0.65

            angulo_rad_nom = np.radians(angulo_medio + angulo_extra_nom)

            pos_x_nom = 0.5 + radio_extra_nom * np.cos(angulo_rad_nom)
            pos_y_nom = 0.5 + radio_extra_nom * np.sin(angulo_rad_nom)

            # ---- LÍNEA CONECTORA (del porcentaje al logo) ----
            if mostrar_lineas:
                fig_dona.add_shape(
                    type="line",
                    x0=pos_x_pct, y0=pos_y_pct,
                    x1=pos_x_logo, y1=pos_y_logo,
                    xref="paper", yref="paper",
                    line=dict(color='#118DFF', width=1.5, dash='solid'),
                    opacity=0.5
                )

                # Punto en el porcentaje
                fig_dona.add_shape(
                    type="circle",
                    xref="paper", yref="paper",
                    x0=pos_x_pct - 0.006, x1=pos_x_pct + 0.006,
                    y0=pos_y_pct - 0.006, y1=pos_y_pct + 0.006,
                    fillcolor='#118DFF',
                    line_color='#118DFF',
                    line_width=1,
                    opacity=0.8
                )

            # ---- INSERTAR LOGO ----
            tamanio_logo_usar = tamanios_individuales.get(
                row['candidato'], tamanio_logo_general)

            if pd.notna(row['logo_url']) and str(row['logo_url']).strip() != "":
                try:
                    fig_dona.add_layout_image(
                        dict(
                            source=row['logo_url'],
                            xref="paper", yref="paper",
                            x=pos_x_logo,
                            y=pos_y_logo,
                            sizex=tamanio_logo_usar,
                            sizey=tamanio_logo_usar,
                            xanchor="center",
                            yanchor="middle"
                        )
                    )
                except:
                    pass

            # ---- INSERTAR PORCENTAJE O POSICIÓN ----
            if mostrar_posiciones:
                # Mostrar posición (1°, 2°, 3°...) sin emojis
                texto_mostrar = f"{idx+1}°"
            else:
                # Mostrar porcentaje
                texto_mostrar = f"{votos:.1f}%"

            fig_dona.add_annotation(
                text=texto_mostrar,
                x=pos_x_pct,
                y=pos_y_pct,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(
                    size=tamanio_porcentaje,
                    color='#000000',
                    family='Segoe UI, sans-serif',
                    weight='bold'
                ),
                align='center'
            )

            # ---- INSERTAR NOMBRE (SOLO SI ESTÁ ACTIVADO) ----
            if mostrar_nombres:
                offset_x_nom = 0.04 if pos_x_nom < 0.5 else -0.04
                offset_y_nom = -0.045

                fig_dona.add_annotation(
                    text=f"<b>{row['candidato']}</b>",
                    x=pos_x_nom + offset_x_nom,
                    y=pos_y_nom + offset_y_nom,
                    xref="paper", yref="paper",
                    showarrow=False,
                    font=dict(size=tamanio_nombre, color='#252423',
                              family='Segoe UI, sans-serif'),
                    align='center'
                )

            angulo_inicio -= amplitud_angulo

    # ==================== TEXTO DEL DISTRITO EN EL CENTRO ====================
    fig_dona.add_annotation(
        text=f"<b>{localidad}</b><br><span style='font-size:12px;'>{ambito}</span>",
        x=0.5, y=0.5,
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=18, color='#252423', family='Segoe UI, sans-serif'),
        align='center'
    )

    # ==================== LAYOUT CON LEYENDA POSICIONABLE ====================
    if posicion_leyenda != "Ocultar":
        fig_dona.update_layout(
            title={
                'text': f"<b>🍩 Participación Electoral</b><br><span style='font-size:14px; color:#605E5C;'>{localidad} - {ambito}</span>",
                'y': 0.95,
                'x': 0.05,
                'xanchor': 'left',
                'yanchor': 'top',
                'font': dict(size=20, color="#252423", family="Segoe UI, sans-serif")
            },
            showlegend=True,
            legend=dict(
                orientation=leyenda_config["orientation"],
                yanchor=leyenda_config["yanchor"],
                xanchor=leyenda_config["xanchor"],
                x=leyenda_config["x"],
                y=leyenda_config["y"],
                font=dict(family="Segoe UI", size=12, color="#252423"),
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor='#EAEAEA',
                borderwidth=1
            ),
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=120, b=60, l=60, r=120),
            height=700,
            width=700
        )
    else:
        fig_dona.update_layout(
            title={
                'text': f"<b>🍩 Participación Electoral</b><br><span style='font-size:14px; color:#605E5C;'>{localidad} - {ambito}</span>",
                'y': 0.95,
                'x': 0.05,
                'xanchor': 'left',
                'yanchor': 'top',
                'font': dict(size=20, color="#252423", family="Segoe UI, sans-serif")
            },
            showlegend=False,
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=120, b=60, l=60, r=60),
            height=700,
            width=700
        )

    # ==================== MOSTRAR GRÁFICO ====================
    st.plotly_chart(fig_dona, use_container_width=True,
                    config={'displayModeBar': False})

    # ==================== BOTONES DE DESCARGA ====================
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        csv_descarga = df_filtrado[['candidato', 'partido_politico', 'intencion_voto']].to_csv(
            index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar CSV",
            data=csv_descarga,
            file_name=f"Donut_{localidad}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col2:
        try:
            import plotly.io as pio
            img_bytes = pio.to_image(
                fig_dona, format='png', width=1200, height=800)
            b64_img = base64.b64encode(img_bytes).decode()
            href_img = f'<a href="data:image/png;base64,{b64_img}" download="Donut_{localidad}.png" style="display: inline-block; padding: 10px 20px; background: #4CAF50; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; text-align: center; width: 100%;">🖼️ Descargar PNG</a>'
            st.markdown(href_img, unsafe_allow_html=True)
        except Exception as e:
            st.warning("⚠️ Para descargar PNG instala: pip install -U kaleido")
            st.info("O usa el botón de HTML para guardar como imagen")

    with col3:
        try:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Donut - {localidad}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; background: white; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .header h1 {{ color: #118DFF; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #999; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🍩 Participación Electoral</h1>
                    <h2>{localidad} - {ambito}</h2>
                </div>
                <div>
                    {fig_dona.to_html(full_html=False, include_plotlyjs='cdn')}
                </div>
                <div class="footer">
                    <p>Generado el {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </body>
            </html>
            """

            b64_html = base64.b64encode(html_content.encode()).decode()
            href_html = f'<a href="data:text/html;base64,{b64_html}" download="Donut_{localidad}.html" style="display: inline-block; padding: 10px 20px; background: #FF6B6B; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; text-align: center; width: 100%;">📄 Descargar HTML</a>'
            st.markdown(href_html, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error: {e}")

else:
    st.warning("⚠️ No hay datos disponibles.")
