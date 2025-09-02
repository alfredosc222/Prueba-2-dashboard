import streamlit as st
import pandas as pd
from modulos.modelos_econometricos import generar_proyeccion_econometrica
from theme import theme
from paginas import components

def render_tab_metodologia():
    theme.render_header("Metodología del Análisis")
    col1, col2 = st.columns(2, gap="large")

    with col1:
        with st.container(border=True):
            theme.render_subheader("Modelo Econométrico", align="center")
            st.markdown("""
            El núcleo del análisis es un modelo econométrico que captura la interdependencia entre las variables clave de la política monetaria.

            - **Selección Automática:** El script elige entre un modelo **VAR** (Vector Autorregresivo) o **VECM** (Vector de Corrección de Errores) basándose en pruebas estadísticas formales:
                1.  **Prueba de Estacionariedad (ADF):** Para identificar si las series tienen una tendencia persistente.
                2.  **Prueba de Cointegración (Johansen):** Para determinar si las series no estacionarias mantienen una relación de equilibrio a largo plazo.
            """)

        with st.container(border=True):
            theme.render_subheader("Lógica de Escenarios", align="center")
            st.markdown("""
            Las proyecciones a 30 años se construyen en dos etapas para asegurar su realismo:

            1.  **Pronóstico del Modelo (Primeros 5 Años):** Se utiliza el pronóstico directo del modelo VAR/VECM, incluyendo sus intervalos de confianza para definir los escenarios optimista y pesimista.
            2.  **Convergencia Suave a la Meta:** Después de los primeros 5 años, los escenarios son guiados gradualmente hacia una meta de largo plazo (ej. 3% para Banxico), reflejando la expectativa de que la política monetaria eventualmente anclará la inflación.
            """)

    with col2:
        with st.container(border=True):
            theme.render_subheader("Variables Utilizadas:", align="center")
            st. markdown("""
            * **Inflación (Variable a Proyectar):** Se usa la variación anual del Índice de Precios al Consumidor para todos los Consumidores Urbanos (CPI-U). Es la medida de inflación más utilizada en el país.
                * *ID de Serie (FRED):* `CPIAUCSL` (se usa el índice para luego calcular la variación anual).

            * **Tasa de Interés:** Se utiliza la Tasa de Fondos Federales Efectiva (Effective Federal Funds Rate). Es la tasa de interés principal que la Reserva Federal (Fed) utiliza para dirigir su política monetaria.
                * *ID de Serie (FRED):* `EFFR`

            * **Tipo de Cambio:** Se emplea el Índice Ponderado del Dólar contra una canasta de monedas de economías extranjeras avanzadas. Mide la fortaleza del dólar a nivel internacional. Se utiliza su logaritmo para estabilizar la varianza.
                * *ID de Serie (FRED):* `DTWEXAFEGS`

            **Para hacer uso del modelo es necesario que el usuario cuente con una clave de API. Si el usuario aún no cuenta con una, puede obtenerla en la siguiente dirección: https://fred.stlouisfed.org/docs/api/api_key.html**
            """)


def render_tab_proyeccion():
    theme.render_header("Generar Proyección")  
    # Dividimos la página en una columna principal y una lateral para el formulario
    col_espacio1, col_analisis, col_espacio2, col_formulario = st.columns([0.5, 5.0, 0.5, 1])

    with col_formulario:
        theme.render_header("Parámetros", align="center")
        with st.form(key="form_bonos"):
            fred_api_key = st.text_input("Token de FRED", type="password")
            start_date_bonos = st.date_input("Fecha de Inicio", pd.to_datetime("2006-01-01"), min_value=pd.to_datetime("2006-01-01"))
            anos_proyeccion_bonos = st.number_input("Años a Proyectar", 5, 50, 30)

            col_metas1, col_metas2 = st.columns(2)
            with col_metas1:
                meta_central = st.number_input("Meta Central (%)", value=4.0, step=0.1)
                meta_baja = st.number_input("Meta Baja (%)", value=2.5, step=0.1)
            with col_metas2:
                meta_alta = st.number_input("Meta Alta (%)", value=5.5, step=0.1)
            
            col_btn_izq, col_btn_centro, col_btn_der = st.columns([1, 3, 1])
            with col_btn_centro:   
                submit_button_bonos = st.form_submit_button(label="Generar Proyección", use_container_width=True)

    with col_analisis:
        if submit_button_bonos:
            fecha_descarga = start_date_bonos - pd.DateOffset(years=1)
            if not fred_api_key:
                st.warning("Por favor, ingresa un Token de FRED válido.")
            else:
                with st.spinner("Ejecutando modelo econométrico..."):
                    
                    config_procesamiento_bonos = {
                        "bonos_20": {"type": "level", "source_col": "bonos_20"},
                        "cpi_index": {"type": "yoy_pct_change_calculated", "source_col": "cpi_index"},
                        "pol_monetaria": {"type": "level", "source_col": "pol_monetaria"},
                        "term_spread": {"type": "spread", "source_cols": ["bonos_10", "bonos_3"]}
                    }

                    variables_modelo_bonos = ['bonos_20', 'cpi_index', 'pol_monetaria', 'term_spread']

                    variable_objetivo_bonos = 'bonos_20'

                    params_escenarios = {
                        'anos_modelo': 5, 'meta_central': meta_central, 'meta_baja': meta_baja, 'meta_alta': meta_alta,
                        'theta_central': 0.030, 'theta_baja': 0.050, 'theta_alta': 0.015
                    }
                    series_ids = {
                        "bonos_20": "GS20", 
                        "cpi_index": "CPIAUCSL", 
                        "pol_monetaria": "EFFR", 
                        "bonos_10": "GS10", 
                        "bonos_3": "DTB3"
                    }
                        
                    # Llamamos a la función del módulo
                    resultados_bonos = generar_proyeccion_econometrica(
                        api_key={"fred": fred_api_key},
                        series_ids=series_ids,
                        processing_config=config_procesamiento_bonos,
                        start_date=fecha_descarga.strftime("%Y-%m-%d"),
                        anos_proyeccion=anos_proyeccion_bonos,
                        variables_modelo=variables_modelo_bonos,
                        variable_objetivo=variable_objetivo_bonos,
                        params_escenarios=params_escenarios,
                    )

                    st.session_state['resultados_bonos'] = resultados_bonos
                    st.rerun()

        if 'resultados_bonos' in  st.session_state and  st.session_state['resultados_bonos'] is not None:
            resultados_bonos = st.session_state['resultados_bonos'] # Guarda los resultados obtenidos en la pestaña proyeccion para visualizar diagnostico
            
            st.success("Proyección generada exitosamente.")

            # Mostrar KPIs (1/3)

            kpis_bonos = {
                #"Valor histórico": f"{resultados_bonos['promedios']['Historico']:.2f}%",
                "Escenario base": f"{resultados_bonos['promedios']['Base']:.2f}%",
                "Escenario de tasas bajas": f"{resultados_bonos['promedios']['Positivo']:.2f}%",
                "Escenario de tasas altas": f"{resultados_bonos['promedios']['Negativo']:.2f}%"
                }
            
            # --- LLAMADA A LOS COMPONENTES REUTILIZABLES ---
            components.display_kpi_card("Promedios Proyectados", kpis_bonos)

            st.write("")

            # Crear y mostrar graficas (2/3)

            components.display_projection_chart(
                title=f"Proyección de los bonos del tesoro {resultados_bonos['anos_proyectados']} años",
                x_axis_label="Años [1]",
                y_axis_label="Bonos del tesoro a 20 años [%]",
                historico_data=resultados_bonos['df_historico']['bonos_20'],
                proy_base=resultados_bonos['escenario_base'],
                proy_positivo=resultados_bonos['escenario_positivo'],
                proy_negativo=resultados_bonos['escenario_negativo']
                )
            
            st.write("")

            # Tabla comparativa de escenarios (3/3)

            components.display_summary_table(
                title="Comparativa de Escenarios",
                dataframe=resultados_bonos['tabla_escenarios'],
                format_str="{:.2f}"
            )

            st.write("")

            # Crear y mostrar la tabla resumen (3/3)

            nombres_col = {
                'bonos_20': 'Bonos a 20 años [%]',
                'inflacion': 'Inflación anual [%]',
                'pol_monetaria': 'Politica monetaria [1]',
                'term_spread': ' Diferencial de rendimiento [%]'
            }

            components.display_data_table(expander_title="Datos históricos utilizados", dataframe=resultados_bonos['df_historico'], column_rename_map=nombres_col) 

        elif submit_button_bonos:
            st.error("Ocurrió un error al generar la proyección.")

        else:
            st.info("Ingresa los parámetros en el formulario y haz clic en 'Generar Proyección' para ver los resultados.")



def render_tab_diagnosticos():
    theme.render_header("Diagnósticos del Modelo")
    if 'resultados_bonos' in st.session_state and st.session_state['resultados_bonos'] is not None:
        resultados_bonos = st.session_state['resultados_bonos']

        # Pruebas hechas (1/3)

        components.display_model_diagnostics_card(resultados_bonos)

        st.write("")

        # Sección de Análisis de Residuos (2/3)
        
        components.display_residuals_analysis(resultados_bonos)
    
        st.write("")

        # Resumen estadístico (3/3)
        
        with st.expander("Ver Resumen Estadístico Completo"):
            st.text(resultados_bonos['resumen_texto'])

    else:
        st.warning("Debes generar una proyección en la pestaña 'Proyección' para ver los diagnósticos del modelo.")



def render():
    tabs_config = {
        "Metodología": {"icon": "bi-diagram-3", 
                        "render_func": render_tab_metodologia},

        "Proyección": {"icon": "bi-graph-up", 
                       "render_func": render_tab_proyeccion},

        "Diagnósticos": {"icon": "bi-clipboard-pulse", 
                         "render_func": render_tab_diagnosticos}
    }
    
    components.render_analysis_page(
        page_title="Proyección para el índice de bonos de mercados emergentes",
        tabs_config=tabs_config
    )