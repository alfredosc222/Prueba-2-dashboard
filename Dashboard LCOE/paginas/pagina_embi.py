import streamlit as st
import pandas as pd
from modulos.modelos_econometricos import generar_proyeccion_econometrica
from theme import theme
from paginas import components

def render_tab_metodologia():
    theme.render_header("Metodología del Análisis")

    with st.container(border=True):
                theme.render_subheader("Índice de Precios al Consumidor (IPC) de Estados Unidos", align="center")
                st.markdown("""
                El Índice de Precios al Consumidor (IPC) de Estados Unidos es un indicador que mide el cambio promedio en los precios que los consumidores urbanos pagan por una canasta de bienes y servicios.

                El cambio porcentual en este índice se usa para medir la tasa de inflación, generalmente comparando un mes con el mismo mes del año anterior. Este indicador refleja los hábitos de compra de la gran mayoría de la población urbana, 
                incluyendo a trabajadores, desempleados y jubilados.

                Para calcularlo, se recopilan mensualmente los precios de miles de productos y servicios como alimentos, ropa, vivienda, combustibles, transporte e impuestos. Los cambios de precios se ponderan según la importancia que tienen en el gasto de los hogares.
                """)




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
            * **Rendimiento efectivo del índice de bonos corporativos con calificación BBB de mercados emergentes de ICE BofA (Variable a Proyectar):** Representa el rendimiento anual promedio que un inversionista podría esperar al invertir en una cartera específica de bonos emitidos por empresas de mercados emergentes que poseen una calificación crediticia "BBB". 
                * *ID de Serie (FRED):* `BAMLEM2BRRBBBCRPIEY`<br><br>
               
            * **Índice de Volatilidad de la Bolsa de Opciones de Chicago (VIX):** Es un índice en tiempo real que representa la expectativa del mercado sobre la volatilidad a 30 días. Se calcula utilizando los precios de las opciones de compra y venta del índice S&P 500, sirviendo como una medida de la incertidumbre o el miedo de los inversionistas.
                * *ID de Serie (FRED):* `VIXCLS`<br><br>

            * **Rendimiento de Mercado de los Bonos del Tesoro de EE. UU. con Vencimiento Constante a 10 Años:** Este indicador representa el rendimiento teórico de un bono del Tesoro de los Estados Unidos si este tuviera un vencimiento exacto de 10 años en cualquier día. 
                No se basa en un solo bono, sino que es un valor interpolado a partir de la curva de rendimiento de todos los bonos del Tesoro, y se presenta como un promedio de los días hábiles.
                * *ID de Serie (FRED):* `GS10`<br><br>        
                       
            * **Índice Nominal Amplio del Dólar Estadounidense:** Es un índice ponderado por el comercio exterior que mide el valor del dólar estadounidense frente a una canasta de monedas de un grupo amplio de los principales socios comerciales de Estados Unidos.
                Al ser "nominal", el índice compara los tipos de cambio directos sin ajustarlos por las diferencias de inflación entre los países.
                * *ID de Serie (FRED):* `DTWEXBGS`<br><br>

            **Para hacer uso del modelo es necesario que el usuario cuente con una clave de API. Si el usuario aún no cuenta con una, puede obtenerla en la siguiente dirección: https://fred.stlouisfed.org/docs/api/api_key.html**
            """, unsafe_allow_html=True)


def render_tab_proyeccion():
    theme.render_header("Generar Proyección")  
    # Dividimos la página en una columna principal y una lateral para el formulario
    col_espacio1, col_analisis, col_espacio2, col_formulario = st.columns([0.5, 5.0, 0.5, 1])

    with col_formulario:
        theme.render_header("Parámetros", align="center")
        with st.form(key="form_embi"):
            fred_api_key = st.text_input("Token de FRED", type="password")
            start_date_embi = st.date_input("Fecha de Inicio", pd.to_datetime("2006-01-01"), min_value=pd.to_datetime("2006-01-01"))
            anos_proyeccion_embi = st.number_input("Años a Proyectar", 5, 50, 30)

            col_metas1, col_metas2 = st.columns(2)
            with col_metas1:
                meta_central = st.number_input("Meta Central (%)", value=2.5, step=0.1)
                meta_baja = st.number_input("Meta Baja (%)", value=1.5, step=0.1)
            with col_metas2:
                meta_alta = st.number_input("Meta Alta (%)", value=4.5, step=0.1)
            
            col_btn_izq, col_btn_centro, col_btn_der = st.columns([1, 3, 1])
            with col_btn_centro:   
                submit_button_embi = st.form_submit_button(label="Generar Proyección", use_container_width=True)

    with col_analisis:
        if submit_button_embi:
            fecha_descarga = start_date_embi - pd.DateOffset(years=1)
            if not fred_api_key:
                st.warning("Por favor, ingresa un Token de FRED válido.")
            else:
                with st.spinner("Ejecutando modelo econométrico..."):
                    
                    config_procesamiento_embi = {
                        "embi": {"type": "level", "source_col": "embi"},
                        "aversion_global": {"type": "level", "source_col": "aversion_global"},
                        "bonos_10": {"type": "level", "source_col": "bonos_10"},
                        "fortaleza_dolar": {"type": "level", "source_col": "fortaleza_dolar"}
                    }

                    variables_modelo_embi = ['embi', 'aversion_global', 'bonos_10', 'fortaleza_dolar']

                    variable_objetivo_embi = 'embi'

                    params_escenarios = {
                        'anos_modelo': 5, 'meta_central': meta_central, 'meta_baja': meta_baja, 'meta_alta': meta_alta,
                        'theta_central': 0.030, 'theta_baja': 0.050, 'theta_alta': 0.015
                    }
                    series_ids = {
                        "embi": "BAMLEM2BRRBBBCRPIEY", 
                        "aversion_global": "VIXCLS", 
                        "bonos_10": "GS10", 
                        "fortaleza_dolar": "DTWEXBGS"
                    }
                        
                    # Llamamos a la función del módulo
                    resultados_embi = generar_proyeccion_econometrica(
                        api_key={"fred": fred_api_key},
                        series_ids=series_ids,
                        processing_config=config_procesamiento_embi,
                        start_date=fecha_descarga.strftime("%Y-%m-%d"),
                        anos_proyeccion=anos_proyeccion_embi,
                        variables_modelo=variables_modelo_embi,
                        variable_objetivo=variable_objetivo_embi,
                        params_escenarios=params_escenarios,
                    )

                    st.session_state['resultados_embi'] = resultados_embi
                    st.rerun()

        if 'resultados_embi' in  st.session_state and  st.session_state['resultados_embi'] is not None:
            resultados_embi = st.session_state['resultados_embi'] # Guarda los resultados obtenidos en la pestaña proyeccion para visualizar diagnostico
            
            st.success("Proyección generada exitosamente.")

            # Mostrar KPIs (1/3)

            kpis_embi = {
                #"Valor histórico": f"{resultados_embi['promedios']['Historico']:.2f}%",
                "Escenario base": f"{resultados_embi['promedios']['Base']:.2f}%",
                "Escenario de riesgo bajo": f"{resultados_embi['promedios']['Positivo']:.2f}%",
                "Escenario de riesgo alto": f"{resultados_embi['promedios']['Negativo']:.2f}%"
                }
            
            # --- LLAMADA A LOS COMPONENTES REUTILIZABLES ---
            components.display_kpi_card("Promedio del índice de mercados emergentes: histórico y proyectado", kpis_embi)

            st.write("")

            # Crear y mostrar graficas (2/3)

            components.display_projection_chart(
                title=f"Proyección a {resultados_embi['anos_proyectados']} años del índice de mercados emergentes",
                x_axis_label="Años [1]",
                y_axis_label="Bonos del tesoro a 20 años [%]",
                historico_data=resultados_embi['df_historico']['embi'],
                proy_base=resultados_embi['escenario_base'],
                proy_positivo=resultados_embi['escenario_positivo'],
                proy_negativo=resultados_embi['escenario_negativo']
                )
            
            st.write("")

            # Tabla comparativa de escenarios (3/3)

            components.display_summary_table(
                title="Comparativa de Escenarios",
                dataframe=resultados_embi['tabla_escenarios'],
                format_str="{:.2f}"
            )

            st.write("")

            # Crear y mostrar la tabla resumen (3/3)


            nombres_col = {
                'embi': 'índide de mercados emergentes [%]',
                'aversion_global': 'índice de volatilidad [1]',
                'bonos_10': 'Bonos del tesoro de Estados Unidos a 10 años [%]',
                'fortaleza_dolar': 'Índice nominal del dolar estadounidense [Base 100]'
            }

            components.display_data_table(expander_title="Datos históricos utilizados", dataframe=resultados_embi['df_historico'], column_rename_map=nombres_col) 

        elif submit_button_embi:
            st.error("Ocurrió un error al generar la proyección.")

        else:
            st.info("Ingresa los parámetros en el formulario y haz clic en 'Generar Proyección' para ver los resultados.")



def render_tab_diagnosticos():
    theme.render_header("Diagnósticos del Modelo")
    if 'resultados_embi' in st.session_state and st.session_state['resultados_embi'] is not None:
        resultados_embi = st.session_state['resultados_embi']

        # Pruebas hechas (1/3)

        components.display_model_diagnostics_card(resultados_embi)

        st.write("")

        # Sección de Análisis de Residuos (2/3)
        
        components.display_residuals_analysis(resultados_embi)
    
        st.write("")

        # Resumen estadístico (3/3)
        
        with st.expander("Ver Resumen Estadístico Completo"):
            st.text(resultados_embi['resumen_texto'])

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
     