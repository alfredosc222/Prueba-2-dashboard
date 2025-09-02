import streamlit as st
import pandas as pd
from modulos.modelos_econometricos import generar_proyeccion_econometrica
from theme import theme
from paginas import components

def render_tab_metodologia():
    theme.render_header("Metodología del Análisis")

    with st.container(border=True):
            theme.render_subheader("Definición del indicador", align="center")
            st.markdown("""
            La inflación mide el aumento general de los precios de los bienes y servicios de una economía a lo largo del tiempo. 
            Este índice es una de las variables macroeconómicas más importantes a la hora de medir el comportamiento de una economía ya que permite predecir la evolución económica de un país.
            En este análisis se utilizó la variación porcentual del Índice de Precios al Consumidor (IPC).
            """)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        with st.container(border=True):
            theme.render_subheader("Modelo de proyección", align="center")
            st.markdown("""
            El núcleo del análisis es un modelo econométrico que captura la interdependencia entre las variables clave de la política monetaria.

            - **Selección Automática:** El script elige entre un modelo **VAR** (Vector Autorregresivo) o **VECM** (Vector de Corrección de Errores) basándose en pruebas estadísticas formales:
                1.  **Prueba de Estacionariedad (ADF):** Para identificar si las series tienen una tendencia persistente.
                2.  **Prueba de Cointegración (Johansen):** Para determinar si las series no estacionarias mantienen una relación de equilibrio a largo plazo.
            """)

        with st.container(border=True):
            theme.render_subheader("Diseño de escenarios", align="center")
            st.markdown("""
            Las proyecciones a 30 años se construyen en dos etapas para asegurar su realismo:

            1.  **Pronóstico del Modelo (Primeros 5 Años):** Se utiliza el pronóstico directo del modelo VAR/VECM, incluyendo sus intervalos de confianza para definir los escenarios optimista y pesimista.
            2.  **Convergencia Suave a la Meta:** Después de los primeros 5 años, los escenarios son guiados gradualmente hacia una meta de largo plazo (ej. 3% para Banxico), reflejando la expectativa de que la política monetaria eventualmente anclará la inflación.
            """)

    with col2:
        with st.container(border=True):
            theme.render_subheader("Variables del modelo", align="center")
            st. markdown(""" 
            * **Inflación (Variable a Proyectar):** Se usa la variación anual del Índice Nacional de Precios al Consumidor (INPC). Es la medida oficial de la inflación en el país.
                - *ID de Serie (Banxico):* `SP30578`
                        
            * **Tasa de Interés:** Se utiliza la Tasa de Interés Interbancaria de Equilibrio (TIIE) a 28 días. Refleja la postura del Banco de México y el costo del crédito a corto plazo.
                - *ID de Serie (Banxico):* `SF43783`
                        
            * **Tipo de Cambio:** Se emplea el Tipo de Cambio FIX (USD/MXN). Es el principal canal de transmisión de shocks externos a la economía mexicana y afecta los precios de los bienes importados. Se utiliza su logaritmo para estabilizar la varianza.
                - *ID de Serie (Banxico):* `SF43718`
                        
            **Para hacer uso del modelo es necesario que el usuario cuente con un token de consulta. Si el usuario aún no cuenta con uno puede descargarlo en la siguiente dirección: https://www.banxico.org.mx/SieAPIRest/service/v1/token**""")
        
        with st.container(border=True):
            theme.render_subheader("Limitaciones del modelo", align="center")

def render_tab_proyeccion():
    theme.render_header("Generar Proyección")  

    col_espacio1, col_analisis, col_espacio2, col_formulario = st.columns([0.5, 5.0, 0.5, 1])

    with col_formulario:
        theme.render_header("Parámetros", align="center")
        with st.form(key="form_mex"):
            token_banxico = st.text_input("Token de Banxico", type="password")
            start_date_mex = st.date_input("Fecha de Inicio", pd.to_datetime("2002-01-01"), min_value=pd.to_datetime("1995-01-01"))
            anos_proyeccion_mex = st.number_input("Años a Proyectar", 5, 50, 30)

            col_metas1, col_metas2 = st.columns(2)
            with col_metas1:
                meta_central = st.number_input("Meta Central (%)", value=3.0, step=0.1)
                meta_baja = st.number_input("Meta Baja (%)", value=3.0, step=0.1)
            with col_metas2:
                meta_alta = st.number_input("Meta Alta (%)", value=5.5, step=0.1)
            
            col_btn_izq, col_btn_centro, col_btn_der = st.columns([1, 3, 1])
            with col_btn_centro:
                submit_button_mex = st.form_submit_button(label="Generar proyección", use_container_width=True)

    with col_analisis:
        if submit_button_mex:
            if not token_banxico:
                st.warning("Por favor, ingresa un Token de Banxico válido.")
            else:
                with st.spinner("Ejecutando modelo econométrico..."):

                    config_procesamiento_mex = {
                        "inflacion": {"type": "level", "source_col": "cpi_banxico"},
                        "tasa_interes": {"type": "level", "source_col": "tiie_28"},
                        "tipo_cambio": {"type": "log", "source_col": "usd_mxn_fix"}
                    }

                    variables_modelo_mex = ['tasa_interes', 'tipo_cambio']


                    variable_objetivo_mex = 'inflacion'

                    params_escenarios = {
                        'anos_modelo': 5, 'meta_central': meta_central, 'meta_baja': meta_baja, 'meta_alta': meta_alta,
                        'theta_central': 0.030, 'theta_baja': 0.015, 'theta_alta': 0.050
                    }
                    series_ids = {
                        "cpi_banxico": "SP30578", 
                        "tiie_28": "SF43783", 
                        "usd_mxn_fix": "SF43718"
                    }
                    
                    resultados_mex = generar_proyeccion_econometrica(
                        api_key={"banxico": token_banxico},
                        series_ids=series_ids,
                        processing_config=config_procesamiento_mex,
                        start_date=start_date_mex.strftime("%Y-%m-%d"),
                        anos_proyeccion=anos_proyeccion_mex,
                        variables_modelo=variables_modelo_mex,
                        variable_objetivo=variable_objetivo_mex,
                        params_escenarios=params_escenarios,
                    )

                    st.session_state['resultados_mex'] = resultados_mex
                    st.rerun()

        if 'resultados_mex' in st.session_state and st.session_state['resultados_mex'] is not None:
            resultados_mex = st.session_state['resultados_mex']
            
            st.success("Proyección generada exitosamente.")
            
            # Mostrar KPIs (1/3)

            kpis_inflacion = {

                "Escenario central": f"{resultados_mex['promedios']['Base']:.2f}%",
                "Escenario de inflacion baja": f"{resultados_mex['promedios']['Positivo']:.2f}%",
                "Escenario de inflación alta": f"{resultados_mex['promedios']['Negativo']:.2f}%"
                }
        
            # --- LLAMADA A LOS COMPONENTES REUTILIZABLES ---
            components.display_kpi_card("Promedios Proyectados", kpis_inflacion)

            st.write("")

                # Crear y mostrar graficas (2/3)

            components.display_projection_chart(
                title=f"Proyección de inflación a {resultados_mex['anos_proyectados']} años",
                x_axis_label="Años [1]",
                y_axis_label="Inflación anualizada [%]",
                historico_data=resultados_mex["df_historico"]['inflacion'],
                proy_base=resultados_mex['escenario_base'],
                proy_positivo=resultados_mex['escenario_positivo'],
                proy_negativo=resultados_mex['escenario_negativo']
                )
            
            st.write("")

            # Tabla comparativa de escenarios (3/3)

            components.display_summary_table(
                title="Comparativa de Escenarios",
                dataframe=resultados_mex['tabla_escenarios'],
                format_str="{:.2f}"
            )

            st.write("")
            
            # Crear y mostrar la tabla resumen (3/3)

            nombres_col = {
                'inflacion': 'Inflación anual [%]',
                'tasa_interes': 'Tasa de interés [%]',
                'tipo_cambio': 'Tipo de cambio [log]'
            }

            components.display_data_table(expander_title="Datos históricos utilizados", dataframe=resultados_mex['df_historico'], column_rename_map=nombres_col) 


        elif submit_button_mex:
            st.error("Ocurrió un error al generar la proyección.")
        else:
            st.info("Ingresa los parámetros en el formulario y haz clic en 'Generar Proyección' para ver los resultados.")


def render_tab_diagnosticos():
    theme.render_header("Diagnósticos del Modelo")

    if 'resultados_mex' in st.session_state and st.session_state['resultados_mex'] is not None:
        resultados_mex = st.session_state['resultados_mex']

        # Pruebas hechas (1/3)

        components.display_model_diagnostics_card(resultados_mex)

        st.write("")

        # Sección de Análisis de Residuos (2/3)
        
        components.display_residuals_analysis(resultados_mex)
    
        st.write("")

        # Resumen estadístico (3/3)
        
        with st.expander("Ver Resumen Estadístico Completo"):
            st.text(resultados_mex['resumen_texto'])

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
        page_title="Proyección de la inflación para México",
        tabs_config=tabs_config
    )
     

