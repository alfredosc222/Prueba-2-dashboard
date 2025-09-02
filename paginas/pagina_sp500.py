import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from modulos.MODULO_SP500 import generar_proyeccion_sp500
from plotly.subplots import make_subplots
from theme import theme
from paginas import components
from streamlit_option_menu import option_menu

def render():
    theme.render_title("Proyección de rendimiento del S&P 500")

    opciones_sp500 = ["Metodología", "Proyección", "Diagnósticos",]
    iconos_sp500 = ['bi-diagram-3', 'bi-graph-up', 'bi-clipboard-pulse']

    pagina_seleccionada = components.render_tabs_menu(opciones_sp500, iconos_sp500)


    if pagina_seleccionada == "Metodología":
        theme.render_header("Descripcion del análisis")

        with st.container(border=True):
                theme.render_subheader("Definición del indicador", align="center")

        col1, col2 = st.columns(2, gap="large")

        with col1:
            with st.container(border=True):
                theme.render_subheader("Modelo utilizado", align="center")
                st.markdown("""
                El pronóstico se basa en el **Movimiento Geométrico Browniano (GBM)**, el estándar en finanzas para modelar el precio de activos. Este modelo asume que los rendimientos del activo siguen un "paseo aleatorio".
                
                La simulación genera miles de trayectorias de precios futuras, donde cada paso diario combina una tendencia central con un shock aleatorio.
                """)

        with col2:
            with st.container(border=True):
                theme.render_subheader("Parámetros clave", align="center")
                st.markdown("""
                El modelo se alimenta de dos parámetros calculados a partir de los datos históricos del **S&P 500 Total Return Index (`^SP500TR`)**:

                - **Deriva (`mu`):** Es el rendimiento diario promedio. Representa la **tendencia** histórica del activo.
                - **Volatilidad (`sigma`):** Es la desviación estándar de los rendimientos. Representa el **riesgo** o la magnitud de la aleatoriedad.
                """)

    elif pagina_seleccionada == "Proyección":
        theme.render_header("Generar y visualizar proyección")

        # Dividimos la página en una columna principal y una lateral para el formulario
        col_analisis, col_formulario = st.columns([6.0, 2.0])

        with col_formulario:
            theme.render_header("Parámetros", align="center") 
            with st.form(key="form_sp500"):
                with st.container(border=False):
                    start_date_sp = st.date_input("Fecha de inicio de datos", pd.to_datetime("2000-01-01")) 

                    col1, col2 = st.columns(2)
                    with col1:
                        num_sims_sp = st.number_input("Número de simulaciones", 100, 5000, 1000, step=100)
                    with col2:
                        anos_proy_sp = st.number_input("Años a simular", 5, 50, 30)
                    
                    col_btn_izq, col_btn_centro, col_btn_der = st.columns([1, 3, 1])
                    with col_btn_centro:
                        submit_button_sp500 = st.form_submit_button(label="Iniciar simulación", use_container_width=True)

        with col_analisis:
            # --- Lógica de Ejecución y Visualización ---
            if submit_button_sp500:
                with st.spinner("Ejecutando simulación..."):
                    
                    # Llamar a la función del módulo con los parámetros del usuario
                    resultados_sp = generar_proyeccion_sp500(
                        ticker='^SP500TR',
                        start_date=start_date_sp,
                        anos_proyeccion=anos_proy_sp,
                        num_simulaciones=num_sims_sp
                    )

                    st.session_state['resultados_sp'] = resultados_sp

                    st.rerun()

            if 'resultados_sp' in st.session_state and st.session_state['resultados_sp'] is not None:
                resultados_sp = st.session_state['resultados_sp']

                promedios = resultados_sp["promedios"]
                rend_hist = resultados_sp["historico_anual"]
                rend_base = resultados_sp["base_anual"]
                rend_pos = resultados_sp["positivo_anual"]
                rend_neg = resultados_sp["negativo_anual"]

                st.success("Simulación completada.")

                # Mostrar KPIs (1/3)

                kpis_promedio = {
                    "Valores historicos": f"{promedios['Historico']:.2f}%",
                    "Escenario base (percentil 50)": f"{promedios['Base']:.2f}%",
                    "Escenario optimista (percentil 95)": f"{promedios['Positivo']:.2f}%",
                    "Escenario pesimista (percentil 5)": f"{promedios['Negativo']:.2f}%"
                 }

                components.display_kpi_card("Rendimiento anual promedio", kpis_promedio)

                st.write("")

                # Crear y mostrar graficas (2/3)

                components.display_scenario_bar_chart(
                    title="Rendimiento Anual S&P 500: Histórico y Proyecciones",
                    x_axis_label="Años [1]",
                    y_axis_label="Rendimiento Anual [%]",
                    historico=resultados_sp["historico_anual"],
                    base=resultados_sp["base_anual"],
                    positivo=resultados_sp["positivo_anual"],
                    negativo=resultados_sp["negativo_anual"]
                )

                st.write("")

                # Crear y mostrar la tabla resumen (3/3)

                with st.expander("Ver Tabla de Rendimientos Anuales"):
                    df_resumen_sp = pd.concat([rend_hist, rend_neg, rend_base, rend_pos], axis=1)
                    df_resumen_sp.columns = ["Histórico", "Negativo", "Base", "Positivo"]   
                    st.dataframe(df_resumen_sp.style.format("{:.2f}%"))

            elif submit_button_sp500:
                st.error("Ocurrió un error al generar la simulación.")
            else:
                st.info("Ajusta los parámetros y haz clic en 'Generar Simulación'.")


    elif pagina_seleccionada == "Diagnósticos":
        theme.render_header("Análisis de la distribución final")

        if 'resultados_sp' in st.session_state and st.session_state['resultados_sp'] is not None:
            resultados_sp = st.session_state['resultados_sp']

            # Mostrar KPIs (1/3)


            kpis_est = {
                "Rendimiento Anualizado Histórico (μ)": f"{resultados_sp['mu_anualizado']:.2%}",
                "Volatilidad Anualizada Histórica (σ)": f"{resultados_sp['sigma_anualizado']:.2%}"
            }

            components.display_kpi_card("Parámetros clave anualizados", kpis_est)
            
            st.write("")

            # Crear y mostrar graficas (2/3)

            components.display_diagnostic_histograms(
                anos_proyeccion=resultados_sp['anos_proyectados'],
                data_distribucion_final=resultados_sp['precios_finales'],
                titulo_distribucion_final="Valores del índice proyectados",
                eje_x_distribucion_final="Valor del S&P 500 puntos]",
                caption_distribucion_final="Muestra el rango de resultados posibles de la simulación.",
                data_rendimientos_historicos=resultados_sp['rendimientos_log_diarios'] * 100,
                titulo_rendimientos_historicos="Distribución de rendimientos diarios históricos",
                eje_x_rendimientos_historicos="Cambio diario [%]",
                caption_rendimientos_historicos="Valida el supuesto de normalidad del modelo (forma de campana)."
            )

            st.write("")

            # Crear y mostrar tabla de percentiles (3/3)

            components.display_percentiles_table(
                title="Tabla de percentiles",
                description=f"Valores específicos del índice S&P 500 en el año {pd.Timestamp.now().year + resultados_sp['anos_proyectados']} según diferentes niveles de probabilidad.",
                percentiles_data=resultados_sp['percentiles'],
                column_name="Valor del Índice (Puntos)",     
            )


        else:
            st.warning("Primero debes generar una proyección en la pestaña anterior.")


