import streamlit as st
import pandas as pd
from theme import theme
from paginas import components

def render():
    theme.render_title("Resumen de las proyecciones")
    st.info("Para que los datos aparezcan en esta sección, debes generar su proyección correspondiente")

    st.write("")

    col_mex, col_usa, col_sp, col_embi, col_beta, col_apalancamiento, col_bonos = st.columns(7)

    with col_mex:
      
        if 'resultados_mex' in st.session_state and st.session_state['resultados_mex'] is not None:
            promedios_mex = st.session_state['resultados_mex']['promedios']

            kpis_inflacion = {
                "Base": f"{promedios_mex['Base']:.2f}%",
                "Positivo": f"{promedios_mex['Positivo']:.2f}%",
                "Negativo": f"{promedios_mex['Negativo']:.2f}%"
            }
            
            # --- LLAMADA A LOS COMPONENTES REUTILIZABLES ---
            components.display_kpi_resumen("Resumen: Inflación México", kpis_inflacion)            

        else:
            st.write("Aún no se ha generado la proyección para México.")

        if 'resultados_mex' in st.session_state and st.session_state['resultados_mex'] is not None:
            resultados_mex = st.session_state['resultados_mex']

            df_para_descarga = pd.DataFrame({
                'Base': resultados_mex['escenario_base'],
                'Positivo':resultados_mex['escenario_positivo'],
                'Negativo': resultados_mex['escenario_negativo']
            })
            
            components.display_download_button(df_descarga=df_para_descarga, nombre_archivo='proyeccion_MEX.csv',)


        else:
            st.warning("Debes generar una proyección en la pestaña 'Proyección' para poder descargar los datos.")


    with col_usa:
                   
        if 'resultados_usa' in st.session_state and st.session_state['resultados_usa'] is not None:
            promedios_usa = st.session_state['resultados_usa']['promedios']
            
            kpis_inflacion = {
                "Base": f"{promedios_usa['Base']:.2f}%",
                "Positivo": f"{promedios_usa['Positivo']:.2f}%",
                "Negativo": f"{promedios_usa['Negativo']:.2f}%"
            }
            
            # --- LLAMADA A LOS COMPONENTES REUTILIZABLES ---
            components.display_kpi_resumen("Resumen: Inflación Estados Unidos", kpis_inflacion)
        else:
            st.write("Aún no se ha generado la proyección para Estados Unidos.")


        if 'resultados_usa' in st.session_state and st.session_state['resultados_usa'] is not None:
            resultados_usa = st.session_state['resultados_usa']

            df_para_descarga = pd.DataFrame({
                'Base': resultados_usa['escenario_base'],
                'Positivo':resultados_usa['escenario_positivo'],
                'Negativo': resultados_usa['escenario_negativo']
            })
            
            components.display_download_button(df_descarga=df_para_descarga, nombre_archivo='proyeccion_USA.csv',)


        else:
            st.warning("Debes generar una proyección en la pestaña 'Proyección' para poder descargar los datos.")


    with col_sp:
            
        if 'resultados_sp' in st.session_state and st.session_state['resultados_sp'] is not None:
            promedios_sp = st.session_state['resultados_sp']['promedios']
        
            kpis_promedios = {
                "Base": f"{promedios_sp['Base']:.2f}%",
                "Positivo": f"{promedios_sp['Positivo']:.2f}%",
                "Negativo": f"{promedios_sp['Negativo']:.2f}%"
            }
            
            components.display_kpi_resumen("Resumen: Valor promedio S&P 500", kpis_promedios)

        else:
            st.write("Aún no se ha generado la simulación para el S&P 500.")

        if 'resultados_sp' in st.session_state and st.session_state['resultados_sp'] is not None:
            resultados_sp = st.session_state['resultados_sp']

            df_para_descarga = pd.DataFrame({
                'Base': resultados_sp["base_anual"],
                'Positivo':resultados_sp['positivo_anual'],
                'Negativo': resultados_sp['negativo_anual']
            })
            
            components.display_download_button(df_descarga=df_para_descarga, nombre_archivo='proyeccion_S&P500.csv',)

        else:
            st.warning("Debes generar una proyección en la pestaña 'Proyección' para poder descargar los datos.")




    with col_embi:
        if 'resultados_embi' in st.session_state and st.session_state['resultados_embi'] is not None:
            promedios_embi = st.session_state['resultados_embi']['promedios']


            kpis_promedios = {
                "embi base": f"{promedios_embi['Base']:.2f}%",
                "embi alto": f"{promedios_embi['Positivo']:.2f}%",
                "embi bajo": f"{promedios_embi['Negativo']:.2f}%"
            }
            
            components.display_kpi_resumen("Resumen: Valor de D/(D+E)", kpis_promedios)

        else:
            st.write("Aún no se ha generado la simulación para D/(D+E).")

        if 'resultados_embi' in st.session_state and st.session_state['resultados_embi'] is not None:
            resultados_embi = st.session_state['resultados_embi']

            df_para_descarga = pd.DataFrame({
                'embi base': resultados_embi['escenario_base'],
                'embi alto':resultados_embi['escenario_positivo'],
                'embi bajo': resultados_embi['escenario_negativo']
            })
            
            components.display_download_button(df_descarga=df_para_descarga, nombre_archivo='proyeccion_EMBI.csv',)

        else:
            st.warning("Debes generar una proyección en la pestaña 'Proyección' para poder descargar los datos.")
            
            
    with col_beta:
            
        if 'resultados_beta' in st.session_state and st.session_state['resultados_beta'] is not None:
            promedios_beta = st.session_state['resultados_beta']['promedios']


            kpis_promedios = {
                "Base": f"{promedios_beta['Base_anual']:.2f}%",
                "Positivo": f"{promedios_beta['Positivo_anual']:.2f}%",
                "Negativo": f"{promedios_beta['Negativo_anual']:.2f}%"
            }
            
            components.display_kpi_resumen("Resumen: Valor de beta desapalancada", kpis_promedios)

        else:
            st.write("Aún no se ha generado la simulación para la beta desapalancada.")

        if 'resultados_beta' in st.session_state and st.session_state['resultados_beta'] is not None:
            resultados_beta = st.session_state['resultados_beta']

            df_para_descarga = pd.DataFrame({
                'Base': resultados_beta['base'],
                'Positivo':resultados_beta['positivo'],
                'Negativo': resultados_beta['negativo']
            })
            
            components.display_download_button(df_descarga=df_para_descarga, nombre_archivo='proyeccion_beta_des.csv',)

        else:
            st.warning("Debes generar una proyección en la pestaña 'Proyección' para poder descargar los datos.")


    with col_apalancamiento:
        if 'resultados_apalancamiento' in st.session_state and st.session_state['resultados_apalancamiento'] is not None:
            promedios_apalancamiento = st.session_state['resultados_apalancamiento']['promedios']


            kpis_promedios = {
                "Apalancamiento base": f"{promedios_apalancamiento['Base_anual']:.2f}%",
                "Apalancamiento alto": f"{promedios_apalancamiento['Positivo_anual']:.2f}%",
                "Apalancamiento bajo": f"{promedios_apalancamiento['Negativo_anual']:.2f}%"
            }
            
            components.display_kpi_resumen("Resumen: Valor de D/(D+E)", kpis_promedios)

        else:
            st.write("Aún no se ha generado la simulación para D/(D+E).")

        if 'resultados_apalancamiento' in st.session_state and st.session_state['resultados_apalancamiento'] is not None:
            resultados_apalancamiento = st.session_state['resultados_apalancamiento']

            df_para_descarga = pd.DataFrame({
                'Apalancamiento base': resultados_apalancamiento['base'],
                'Apalancamiento alto':resultados_apalancamiento['positivo'],
                'Apalancamiento bajo': resultados_apalancamiento['negativo']
            })
            
            components.display_download_button(df_descarga=df_para_descarga, nombre_archivo='proyeccion_D/(D+E).csv',)

        else:
            st.warning("Debes generar una proyección en la pestaña 'Proyección' para poder descargar los datos.")

    
    with col_bonos:
        if 'resultados_bonos' in st.session_state and st.session_state['resultados_bonos'] is not None:
            promedios_bonos = st.session_state['resultados_bonos']['promedios']


            kpis_promedios = {
                "bonos base": f"{promedios_bonos['Base']:.2f}%",
                "bonos alto": f"{promedios_bonos['Positivo']:.2f}%",
                "bonos bajo": f"{promedios_bonos['Negativo']:.2f}%"
            }
            
            components.display_kpi_resumen("Resumen: Valor de D/(D+E)", kpis_promedios)

        else:
            st.write("Aún no se ha generado la simulación para D/(D+E).")

        if 'resultados_bonos' in st.session_state and st.session_state['resultados_bonos'] is not None:
            resultados_bonos = st.session_state['resultados_bonos']

            df_para_descarga = pd.DataFrame({
                'bonos base': resultados_bonos['escenario_base'],
                'bonos alto':resultados_bonos['escenario_positivo'],
                'bonos bajo': resultados_bonos['escenario_negativo']
            })
            
            components.display_download_button(df_descarga=df_para_descarga, nombre_archivo='proyeccion_bonos_20_EUA.csv',)

        else:
            st.warning("Debes generar una proyección en la pestaña 'Proyección' para poder descargar los datos.")
