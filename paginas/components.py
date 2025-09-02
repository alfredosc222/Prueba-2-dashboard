# components.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from theme import theme 
import numpy as np
from statsmodels.tsa.stattools import acf
from scipy.stats import norm
from streamlit_option_menu import option_menu
from plotly.subplots import make_subplots

# --- COMPONENTE 1: TARJETA DE KPIs ---
def display_kpi_card(title, kpis):

    with st.container(border=True):
        theme.render_subheader(title)
        cols = st.columns(len(kpis))

        for i, (label, value) in enumerate(kpis.items()):
            with cols[i]:
                theme.render_metric(label, value)


# --- COMPONENTE 2: GRÁFICA DE PROYECCIÓN ---
def display_projection_chart(title, x_axis_label, y_axis_label, historico_data, proy_base, proy_positivo, proy_negativo):

    with st.container(border=True):
        theme.render_subheader(title)

        # Unir datos para una línea continua
        base_para_graficar = pd.concat([historico_data.iloc[-1:], proy_base])
        positivo_para_graficar = pd.concat([historico_data.iloc[-1:], proy_positivo])
        negativo_para_graficar = pd.concat([historico_data.iloc[-1:], proy_negativo])

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=historico_data.index, y=historico_data, mode='lines', name='Histórico', line=dict(color=theme.get_color("historico"))))
        fig.add_trace(go.Scatter(x=base_para_graficar.index, y=base_para_graficar, mode='lines', name='Escenario Base', line=dict(color=theme.get_color("primario"))))
        fig.add_trace(go.Scatter(x=positivo_para_graficar.index, y=positivo_para_graficar, mode='lines', name='Escenario Positivo', line=dict(color=theme.get_color("exito"), dash='dash')))
        fig.add_trace(go.Scatter(x=negativo_para_graficar.index, y=negativo_para_graficar, mode='lines', name='Escenario Negativo', line=dict(color=theme.get_color("peligro"), dash='dash')))
        
        fig.update_layout(template="plotly_white", xaxis_title=x_axis_label, yaxis_title=y_axis_label, height=500, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)


# --- COMPONENTE 3: TARJETA CON TABLA DE DATOS ---
def display_summary_table(title, dataframe, format_str="{:.2f}%"):

    with st.container(border=True):
        theme.render_subheader(title)
        col_margen1, col_contenido, col_margen2 = st.columns([1, 4, 1])
        with col_contenido:
            st.dataframe(dataframe.style.format(format_str), use_container_width=True)




# --- COMPONENTE 4: TARJETA DE DIAGNÓSTICOS DEL MODELO ---
def display_model_diagnostics_card(resultados):
    """
    Crea una "tarjeta" que muestra los resultados de las pruebas de
    selección del modelo econométrico (VAR/VECM).
    """
    with st.container(border=True):
        theme.render_subheader("Pruebas de Selección de Modelo")
        
        st.info(f"El modelo seleccionado automáticamente fue un **{resultados['modelo_usado']}**.")
        
        col1, col2 = st.columns(2, gap="large")

        with col1:
            theme.render_label("Prueba de Estacionariedad (ADF)")
            
            nombres_mapa = {'inflacion': 'inflación', 'tasa_interes': 'tasa de interés', 'tipo_cambio': 'tipo de cambio', 'pol_monetaria': 'politica monetaria', 'term_spread': 'diferencial de rendimiento', 'bonos_20': 'bonos del tesoro a 20 años'}
            variables_no_est = resultados['series_no_estacionarias']
            lista_series = ", ".join([nombres_mapa.get(var, var) for var in variables_no_est]) if variables_no_est else "Ninguna"
            
            theme.render_justified_text(f"Se concluyó que las siguientes variables no son estacionarias en niveles: <b>{lista_series}</b>.")

        with col2:
            theme.render_label("Prueba de Cointegración (Johansen)")
            
            num_rel = resultados['relaciones_coint']
            theme.render_justified_text(f"Se encontraron <b>{num_rel}</b> relaciones de cointegración entre las variables no estacionarias.")
            
            if num_rel > 0:
                theme.render_caption("Esto justifica el uso de un modelo VECM.")
            else:
                theme.render_caption("Al no encontrar cointegración, se utiliza un modelo VAR aplicando diferencias.")


# --- COMPONENTE 5:
def display_residuals_analysis(resultados):
    """
    Crea una "tarjeta" que muestra las gráficas de análisis de residuos (ACF e Histograma).
    """
    with st.container(border=True):
        theme.render_subheader("Análisis de Residuos")
        
        col1, col2 = st.columns(2, gap="large")

        with col1:
            theme.render_label("Autocorrelación (ACF)")
            
            # Gráfica ACF
            residuos = resultados['residuos']
            acf_values, confint = acf(residuos, nlags=24, alpha=0.05)
            x_axis = np.arange(1, 25)
            
            fig_acf = go.Figure()
            # Banda de confianza
            conf_upper = confint[1:, 1] - acf_values[1:]
            conf_lower = confint[1:, 0] - acf_values[1:]
            fig_acf.add_trace(go.Scatter(x=np.concatenate([x_axis, x_axis[::-1]]), y=np.concatenate([conf_upper, conf_lower[::-1]]), fill='toself', fillcolor='rgba(173, 216, 230, 0.5)', line=dict(color='rgba(255,255,255,0)'), showlegend=False))
            # Barras finas
            fig_acf.add_trace(go.Bar(x=x_axis, y=acf_values[1:], name='ACF', width=0.2))
            fig_acf.update_layout(template="plotly_white", height=400)
            st.plotly_chart(fig_acf, use_container_width=True)

        with col2:
            theme.render_label("Histograma de Residuos")
            
            mu, std = norm.fit(residuos)



            # Gráfica Histograma
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(x=residuos, nbinsx=25, histnorm='probability density', name='Frecuencia de Residuos', marker=dict(color='#6699CC', line=dict(color='#003366', width=1))))
            x_curve = np.linspace(residuos.min(), residuos.max(), 100)
            y_curve = norm.pdf(x_curve, mu, std)
            fig_hist.add_trace(go.Scatter(x=x_curve, y=y_curve, mode='lines', name='Distribución Normal Teórica',line=dict(color=theme.get_color("peligro"), width=2)))
            fig_hist.update_layout(template="plotly_white", height=400, bargap=0.05, yaxis_title="Densidad",legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_hist, use_container_width=True)
            
        # Interpretación
        theme.render_caption("<b>Interpretación:<b> Para que el resultado sea valido, la mayoria de las barras mostradas del ACF deben estar dentro del área sombreada; mientras que en el histograma la distribución debe parecer una distribucion normal.")

# Subpestañas
def render_tabs_menu(options, icons):
    """
    Crea un menú de pestañas horizontales con un estilo estandarizado.
    """
    # Usamos st.columns para forzar la alineación a la izquierda
    col_menu, col_espacio = st.columns([len(options), len(options) ])
    
    with col_menu:
        selected_tab = option_menu(
            menu_title=None,
            options=options,
            icons=icons,
            orientation="horizontal",
            styles=theme.estilo_subpestanas # Asumimos que los estilos están en theme.py
        )
    return selected_tab

# Grafica 1+3
def display_scenario_bar_chart(title, x_axis_label, y_axis_label, historico, base, positivo, negativo, y_axis_range=None, color_threshold=0, 
                               nombre_escenarios = ("Rendimiento Histórico", "Escenario Positivo", "Escenario Base", "Escenario Negativo") ):
    """
    Crea una "tarjeta" con una gráfica de barras 1+3 para visualizar escenarios.
    """
    with st.container(border=True):
        theme.render_subheader(title)

        # Paleta de colores
        color_pos_bar = theme.get_color('exito')
        color_neg_bar = theme.get_color('peligro')

        # Crear listas de colores para cada serie
        colores_hist = [color_pos_bar if v >= color_threshold else color_neg_bar for v in historico]
        colores_base = [color_pos_bar if v >= color_threshold else color_neg_bar for v in base]
        colores_pos = [color_pos_bar if v >= color_threshold else color_neg_bar for v in positivo]
        colores_neg = [color_pos_bar if v >= color_threshold else color_neg_bar for v in negativo]

        # Crear figura con layout 1 arriba y 3 abajo
        fig = make_subplots(
            rows=2, cols=3,
            specs=[[{"colspan": 3}, None, None], [{}, {}, {}]],
            subplot_titles=nombre_escenarios,
            vertical_spacing=0.30
        )

        # Añadir las 4 gráficas de barras
        fig.add_trace(go.Bar(x=historico.index, y=historico, marker_color=colores_hist), row=1, col=1)
        fig.add_trace(go.Bar(x=positivo.index, y=positivo, marker_color=colores_pos, opacity=0.7), row=2, col=1)
        fig.add_trace(go.Bar(x=base.index, y=base, marker_color=colores_base, opacity=0.8), row=2, col=2)
        fig.add_trace(go.Bar(x=negativo.index, y=negativo, marker_color=colores_neg, opacity=0.7), row=2, col=3)

        # Actualizar diseño
        fig.update_layout(showlegend=False, height=800, template="plotly_white")
        fig.update_xaxes(title_text=x_axis_label)
        fig.update_yaxes(title_text=y_axis_label,range=y_axis_range,row=1, col=1)
        fig.update_yaxes(title_text=y_axis_label,range=y_axis_range,row=2)
        
        st.plotly_chart(fig, use_container_width=True)


# Histograma SP500

def display_diagnostic_histograms(anos_proyeccion, data_distribucion_final, titulo_distribucion_final, eje_x_distribucion_final, caption_distribucion_final, data_rendimientos_historicos, titulo_rendimientos_historicos, eje_x_rendimientos_historicos, caption_rendimientos_historicos):
    """
    Crea una tarjeta genérica con dos histogramas para análisis de distribución y diagnóstico.
    """
    with st.container(border=True):
        theme.render_subheader("Análisis de distribución y diagnósticos")
        
        col1, col2 = st.columns(2, gap="large")

        with col1:
            # Histograma de Distribución de Valores Finales (Genérico)
            fig_dist = go.Figure()
            fig_dist.add_trace(go.Histogram(
                x=data_distribucion_final, 
                nbinsx=100, 
                marker=dict(color='#6699CC', line=dict(color='#003366', width=1))
            ))
            fig_dist.update_layout(
                template="plotly_white", height=400,
                title_text=theme.render_label(f"{titulo_distribucion_final} a {anos_proyeccion} años"),
                xaxis_title=eje_x_distribucion_final,
                yaxis_title="Nº de simulaciones [1]",
                bargap=0.05
            )
            st.plotly_chart(fig_dist, use_container_width=True)
            theme.render_caption(caption_distribucion_final)

        with col2:
            # Histograma de Rendimientos Diarios (Genérico)
            fig_hist_log = go.Figure()
            fig_hist_log.add_trace(go.Histogram(
                x=data_rendimientos_historicos, 
                nbinsx=100, 
                marker=dict(color='#6699CC', line=dict(color='#003366', width=1))
            ))
            fig_hist_log.update_layout(
                template="plotly_white", height=400,
                title_text=theme.render_label(titulo_rendimientos_historicos),
                xaxis_title=eje_x_rendimientos_historicos,
                yaxis_title="Frecuencia [Días]",
                bargap=0.05
            )
            st.plotly_chart(fig_hist_log, use_container_width=True)
            theme.render_caption(caption_rendimientos_historicos)



# KPI en la seccion de resumen
def display_kpi_resumen(title, kpis):

    with st.container(border=True):
        theme.render_subheader(title, align="center")

        for label, value in kpis.items():
            theme.render_metric(label, value)


def display_percentiles_table(title, description, percentiles_data, column_name):

    with st.container(border=True):
        theme.render_subheader(title)
        st.write(description)

        col_margen1, col_contenido, col_margen2 = st.columns([1, 1.5, 1])
        
        with col_contenido:
            df = pd.DataFrame(percentiles_data)
            df.columns = [column_name]    
            df.index = [f"Percentil {int(p*100)}%" for p in df.index]
            styled_df = df.style.format("{:,.2f}")
            st.dataframe(styled_df, use_container_width=True)



def display_download_button(df_descarga, nombre_archivo, titulo="Descargar Datos"):
    with st.container(border=True):
        # Usamos la función del tema con el parámetro de alineación
        theme.render_subheader(titulo, align="center")
        
        # Preparamos los datos para la descarga
        df_formateado = df_descarga.round(2)
        csv_data = df_formateado.to_csv(index=True).encode('utf-8')
        
        # Usamos columnas para centrar el botón
        col1, col2, col3 = st.columns([1, 10, 1]) # Ligeramente más espacio a los lados
        with col2:
            st.download_button(
                label="Descargar Proyección (CSV)",
                data=csv_data,
                file_name=nombre_archivo,
                mime='text/csv',
                use_container_width=True
            )

# Revisar colores
def display_distribution_histogram(title, data, anos_proyeccion, x_axis_title, y_axis_title, caption):
    """
    Crea una "tarjeta" que muestra un histograma de distribución de resultados finales.
    """
    with st.container(border=True):
        theme.render_subheader(title)
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=data, 
            nbinsx=100, 
            marker=dict(color='#6699CC', line=dict(color='#003366', width=1))
        ))
        
        fig.update_layout(
            template="plotly_white", 
            height=400,
            title_text=f"Distribución a {anos_proyeccion} Años",
            xaxis_title=x_axis_title,
            yaxis_title=y_axis_title,
            bargap=0.05
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.caption(caption)


def display_deviation_chart(title, y_axis_label, base_scenario, positive_scenario, negative_scenario):

    with st.container(border=True):
        theme.render_subheader(title)

        desviacion_positiva = positive_scenario - base_scenario
        desviacion_negativa = negative_scenario - base_scenario

        # --- 2. Creación de la Gráfica ---
        fig = go.Figure()

        # Línea Cero (representa el escenario base)
        fig.add_hline(y=0, line_dash="dash", line_color="black")

        # Rellenar el área entre las desviaciones
        fig.add_trace(go.Scatter(
            x=desviacion_positiva.index.tolist() + desviacion_negativa.index.tolist()[::-1],
            y=desviacion_positiva.tolist() + desviacion_negativa.tolist()[::-1],
            fill='toself',
            fillcolor='rgba(160, 180, 200, 0.4)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Rango de Desviación'
        ))
        
        # Líneas de desviación
        fig.add_trace(go.Scatter(
            x=desviacion_positiva.index, y=desviacion_positiva,
            mode='lines+markers', name='Desviación Positiva',
            line=dict(color=theme.get_color("exito"))
        ))
        fig.add_trace(go.Scatter(
            x=desviacion_negativa.index, y=desviacion_negativa,
            mode='lines+markers', name='Desviación Negativa',
            line=dict(color=theme.get_color("peligro"))
        ))

        # --- 3. Estética Final ---
        fig.update_layout(
            template="plotly_white",
            yaxis_title=y_axis_label,
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)


def display_rating_chart(title, dataframe_con_calificacion):
    """
    Crea una "tarjeta" con una gráfica escalonada que muestra la evolución
    de la calificación crediticia a lo largo del tiempo.
    """
    with st.container(border=True):
        theme.render_subheader(title)
        
        # --- 1. Preparación de Datos ---
        # Plotly necesita categorías numéricas para el eje Y, las convertimos aquí
        rating_map = {
            "AAA": 7, "AA": 6, "A": 5, "BBB": 4, 
            "BB": 3, "B": 2, "CCC o Menor": 1, "N/A": 0
        }
        df_grafica = dataframe_con_calificacion.copy()
        df_grafica['Rating_Num'] = df_grafica['Calificacion_Implícita'].map(rating_map)
        
        # --- 2. Creación de la Gráfica Escalonada ---
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_grafica.index, 
            y=df_grafica['Rating_Num'],
            mode='lines',
            line_shape='hv', # 'hv' crea el efecto de escalón horizontal-vertical
            line=dict(color=theme.get_color("primario"), width=3)
        ))

        # --- 3. Estética y Ejes Personalizados ---
        fig.update_layout(
            template="plotly_white",
            height=400,
            xaxis_title="Año de la Proyección",
            yaxis_title="Calificación Crediticia"
        )
        
        # Reemplazamos las etiquetas numéricas del eje Y con los nombres de las calificaciones
        fig.update_yaxes(
            tickvals=list(rating_map.values()),
            ticktext=list(rating_map.keys())
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # --- 4. Descripción de la Calificación Final ---
        calificacion_final = df_grafica['Calificacion_Implícita'].iloc[-1]
        st.markdown(f"**Calificación al final del periodo:**")
        theme.render_text(f"La proyección converge a una calificación implícita de **{calificacion_final}**.")



def display_session_status(analisis_a_revisar, expander_title):
        """
        Crea un expander en la barra lateral que muestra el estado de carga
        de los diferentes análisis guardados en la sesión.
        """
        with st.sidebar.expander(expander_title, expanded=False):
            # Iterar sobre el diccionario para generar el estado de cada análisis
            for nombre, clave in analisis_a_revisar.items():
                
                if st.session_state.get(clave):
                    # Si los resultados existen, mostrar un indicador de éxito
                    status_html = f"""
                    <div style="text-align: left; margin-bottom: 5px;">
                        <span style="color: {theme.get_color('texto_principal')};">{nombre}:</span>
                        <span style="color: {theme.get_color('exito')}; font-weight: bold;">✔️ Cargado</span>
                    </div>
                    """
                else:
                    # Si no existen, mostrar un indicador pendiente
                    status_html = f"""
                    <div style="text-align: left; margin-bottom: 5px;">
                        <span style="color: {theme.get_color('texto_principal')};">{nombre}:</span>
                        <span style="color: {theme.get_color('texto_secundario')};">⭕ Pendiente</span>
                    </div>
                    """
                st.markdown(status_html, unsafe_allow_html=True)


def display_session_status1(analisis_a_revisar, expander_title):
    """
    Crea un expander que muestra el estado de carga de los análisis
    en una tabla de dos columnas perfectamente alineada.
    """
    with st.sidebar.expander(expander_title, expanded=False):
        
        # Iterar sobre el diccionario para generar el estado de cada análisis
        for nombre, clave in analisis_a_revisar.items():
            
            # --- LA CORRECCIÓN CLAVE ESTÁ AQUÍ ---
            # Creamos un nuevo juego de columnas PARA CADA fila del bucle
            col_nombre, col_status = st.columns([2, 1])

            # Escribimos el nombre en la primera columna
            with col_nombre:
                # Usamos st.markdown para un control más fino del estilo si es necesario
                st.markdown(f"<span style='color: {theme.get_color('texto_principal')};'>{nombre}</span>", unsafe_allow_html=True)
            
            # Escribimos el estado en la segunda columna
            with col_status:
                if st.session_state.get(clave):
                    st.markdown(f"<span style='color: {theme.get_color('exito')}; font-weight: bold;'>✔️ Proyectado</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color: {theme.get_color('texto_secundario')};'>⭕ Pendiente</span>", unsafe_allow_html=True)


# Mostrar datos utilizados con un componente desplegable
def display_data_table(expander_title, dataframe, column_rename_map, format_str="{:.2f}"):
    
    with st.expander(expander_title):
        # Hacemos una copia para no modificar el DataFrame original
        df_display = dataframe.copy()
        
        # Renombramos las columnas usando el diccionario
        df_display.rename(columns=column_rename_map, inplace=True)
        
        # Aplicamos el estilo y mostramos
        st.dataframe(df_display.style.format(format_str), use_container_width=True)




def render_analysis_page(page_title, tabs_config):
    """
    Renderiza una página de análisis completa con una estructura de pestañas.

    Args:
        page_title (str): El título principal de la página.
        page_icon (str): El emoji para el título.
        tabs_config (dict): Un diccionario que define las pestañas.
                           Ej: {"Nombre de Pestaña": funcion_a_renderizar, ...}
    """
    theme.render_title(page_title)

    # Extraer opciones e íconos de la configuración
    options = list(tabs_config.keys())
    icons = [config["icon"] for config in tabs_config.values()]
    
    # Llamar al componente de menú de pestañas
    selected_tab = render_tabs_menu(options, icons)

    # Ejecutar la función de renderizado de la pestaña seleccionada
    if selected_tab:
        render_function = tabs_config[selected_tab]["render_func"]
        render_function()

