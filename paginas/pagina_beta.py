import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from modulos.Montecarlo import ejecutar_simulacion_beta_mejorada
from theme import theme
from paginas import components

def render_tab_metodologia():
    theme.render_header("Metodología del Análisis")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        with st.container(border=True):
            theme.render_subheader("Simulación de Monte Carlo", align="center")
            st.markdown("""
            En lugar de buscar un único pronóstico, este método genera miles de posibles trayectorias futuras para la beta. Esto nos permite no solo ver el resultado más probable, sino también entender el **rango completo de posibilidades** y la incertidumbre inherente a cualquier proyección a largo plazo.
            """)

        with st.container(border=True):
            theme.render_subheader("Volatilidad (`σ`)", align="center")
            st.markdown("""
            La volatilidad, o el "ruido" aleatorio de la simulación, se extrae directamente de los datos históricos. Se calcula como la **desviación estándar de los cambios anuales** de la beta. Una volatilidad más alta en el pasado resultará en un "abanico" de proyecciones más amplio.
            """)

    with col2:
        with st.container(border=True):
            theme.render_subheader("Modelo de Reversión a la Media", align="center")
            st.markdown("""
            A diferencia de los precios de las acciones, la beta de un sector no crece indefinidamente. Tiende a moverse alrededor de un promedio. Este modelo captura ese comportamiento a través de dos componentes:
            
            1.  **Atracción a la Meta:** En cada paso, la beta es "atraída" hacia una meta de largo plazo definida por el usuario.
            2.  **Shock Aleatorio:** Se añade un componente aleatorio basado en la volatilidad histórica (`σ`).
            """)

        with st.container(border=True):
            theme.render_subheader("Parámetros de Convergencia", align="center")
            st.markdown("""
            El usuario controla la dinámica de largo plazo a través de dos parámetros clave:
            - **Metas de Convergencia:** Los valores finales a los que cada escenario (Base, Positivo, Negativo) tenderá.
            - **Velocidad (`θ`):** Un parámetro que define qué tan rápido o lento se produce la convergencia hacia esas metas.
            """)

def render_tab_proyeccion():
    theme.render_header("Generar Proyección")  

    col_analisis, col_formulario = st.columns([4, 1], gap="large")

    with col_formulario:
        theme.render_header("Parámetros", align="center")
        with st.container(border=False):
            theme.render_caption("Añade o modifica los valores de la Beta para la simulación.", align="center")

            datos_iniciales = {
                'Año': [2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023],
                'Beta': [0.76, 0.71, 0.69, 0.78, 0.68, 0.59, 0.67, 0.70, 0.73, 0.59]
            }
            df_edit_historico = pd.DataFrame(datos_iniciales)

            df_historico_editado = st.data_editor(
                df_edit_historico,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "Año": st.column_config.NumberColumn("Año", help="Año del dato histórico", format="%d", required=True),
                    "Beta": st.column_config.NumberColumn("Beta Desapalancada", help="Valor de la beta corregida por efectivo", format="%.2f", required=True)
                },
                key="editor_beta"
            )

            with st.form(key="form_beta"):
                theme.render_text("<b>Parámetros de simulación</b>", align="center")
                anos_proyeccion_beta = st.number_input("Años a proyectar", 5, 50, 30)
                num_sims_beta = st.number_input("Número de simulaciones", 1000, 10000, 5000, step=500)
                
                theme.render_text("<b>Metas de convergencia</b>", align="center")
                col1, col2 = st.columns(2)
                with col1:
                    meta_base = st.number_input("Meta escenario central", value=0.70, step=0.05)
                    meta_pos = st.number_input("Meta escenario de riesgo bajo", value=0.60, step=0.05)
                with col2:
                    meta_neg = st.number_input("Meta escenario de riesgo alto", value=0.85, step=0.05)

                col_btn_izq, col_btn_centro, col_btn_der = st.columns([1, 3, 1])
                with col_btn_centro:
                    submit_button_beta = st.form_submit_button(label="Iniciar proyección", use_container_width=True)


    with col_analisis:

        if submit_button_beta:
            # 3. Usar los datos de la tabla editada para la simulación
            df_historico_final = df_historico_editado.set_index('Año')
            
            with st.spinner("Ejecutando simulación..."):

                params_convergencia = {'velocidad_base': 0.08, 'velocidad_positivo': 0.06, 'velocidad_negativo': 0.10, 
                                        'meta_base': meta_base, 'meta_positivo': meta_pos, 'meta_negativo': meta_neg
                                        }
                
                config_avanzada = {
                    'peso_sectorial': 0.3,  # Peso de beta sectorial vs reversión a 1.0
                    'sensibilidad_distancia': 0.3,  # Factor de velocidad por distancia
                    'aceleracion_temporal': 0.1,  # Factor de aceleración temporal
                    'volatilidad_mercado': 0.25,  # Volatilidad actual del mercado
                    'threshold_volatilidad': 0.25,  # Umbral para régimen de crisis
                    'factor_crisis': 1.5,  # Factor de velocidad en crisis
                    'confianza_sectorial': 0.3,  # Peso del prior sectorial en Bayesiano
                    'confianza_modelo': 0.7,  # Peso del modelo en Bayesiano
                    'incluir_ciclo_economico': True,  # Incluir efectos cíclicos
                    'periodo_ciclo_anos': 6,  # Duración del ciclo económico
                    'amplitud_ciclo': 0.5,  # Amplitud del ciclo (±15%)
                    'usar_bayesiano': True  # Aplicar ajuste Bayesiano
                }

                resultados = ejecutar_simulacion_beta_mejorada(
                    df_historico=df_historico_editado.set_index('Año'),
                    col_name='Beta',
                    anos_proyeccion=anos_proyeccion_beta,
                    num_simulaciones=num_sims_beta,
                    params_convergencia=params_convergencia,
                    beta_sectorial=None,  
                    configuracion_avanzada=config_avanzada
                )

                st.session_state['resultados_beta'] = resultados
                st.rerun()


        if 'resultados_beta' in st.session_state and st.session_state['resultados_beta'] is not None:
            resultados = st.session_state['resultados_beta']


            st.success("Simulación completada.")

            # Mostrar KPIs (1/3)

            kpis_promedio = {
                "Valor histórico": f"{resultados['promedios']['Historico']:.2f}",
                "Escenario base": f"{resultados['promedios']['Base']:.2f}",
                "Escenario de riesgo bajo": f"{resultados['promedios']['Positivo']:.2f}",
                "Escenario de riesgo alto": f"{resultados['promedios']['Negativo']:.2f}"
                }

            components.display_kpi_card("Rendimiento anual promedio", kpis_promedio)

            st.write("")
            
            # Crear y mostrar grafica (2/3)

            components.display_scenario_bar_chart(
                title="Beta Desapalancada: histórico y proyecciones",
                x_axis_label="Años [1]",
                y_axis_label="Nivel de apalancamiento [1]",
                historico=resultados["historico"],
                base=resultados["base"],
                positivo=resultados["positivo"],
                negativo=resultados["negativo"],
                y_axis_range=[0.0, 0.9],
                color_threshold=0.0,
                nombre_escenarios = ("Valor histórico", "Escenario de riesgo bajo", "Escenario base", "Escenario de riesgo alto")  
            )

            st.write("")

                # --- LLAMADA AL NUEVO COMPONENTE DE DESVIACIÓN ---
            components.display_deviation_chart(
                title="Variacion de la beta desapalancada respecto al 'Escenario base'",
                y_axis_label="Diferencia en Beta (Puntos)",
                base_scenario=resultados['base'],
                positive_scenario=resultados['positivo'],
                negative_scenario=resultados['negativo']
            )

            st.write("")

            # Crear y mostrar la tabla resumen (3/3)

            with st.expander("Ver tabla de valores anuales de beta desapalancada"):
                df_resumen_sp = pd.concat([resultados['historico'], resultados['negativo'], resultados['base'],resultados['positivo']], axis=1)
                df_resumen_sp.columns = ["Histórico", "Negativo", "Base", "Positivo"]   
                st.dataframe(df_resumen_sp.style.format("{:.2f}"))

        elif submit_button_beta:
            st.error("Ocurrió un error al generar la proyección.")
        else:
            st.info("Sube tu archivo de datos y ajusta los parámetros en la barra lateral para generar la proyección.")

def render_tab_diagnosticos():
    theme.render_header("Diagnósticos del Modelo")

    if 'resultados_beta' in st.session_state and st.session_state['resultados_beta'] is not None:
        resultados = st.session_state['resultados_beta']

        # Mostrar KPIs (1/3)

        kpis_interes = {
            "Último valor de beta desapalancada histórica": f"{resultados['ultimo_valor_hist']:.2f}",
            "Volatilidad anual (σ)": f"{resultados['volatilidad_hist']:.4f}",
            }

        components.display_kpi_card("Parámetros de interes", kpis_interes)

        st.write("")

        # Crear y mostrar graficas (2/3)

        components.display_distribution_histogram(
            title="Distribución de valores",
            data=resultados['valores_finales'],
            anos_proyeccion=resultados["anos_proyectados"],
            x_axis_title="Valor de beta desapalancada [1]",
            y_axis_title="Frecuencia [Nº de simulaciones]",
            caption="El modelo asume que los rendimientos diarios se asemejan a una distribución normal (campana de Gauss)."
        )

        st.write("")



        # Crear y mostrar tabla de percentiles (3/3)

        components.display_percentiles_table(
            title="Tabla de percentiles",
            description=f"Valor de la beta desapalancada en el año {pd.Timestamp.now().year + resultados['anos_proyectados']} según diferentes niveles de probabilidad.",
            percentiles_data=resultados['percentiles'],
            column_name="Valor de beta desapalancada [1]",     
        )

    else:
        st.warning("Debes generar una proyección para ver este análisis.")

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
        page_title="Proyección de beta desapalancada",
        tabs_config=tabs_config
    )