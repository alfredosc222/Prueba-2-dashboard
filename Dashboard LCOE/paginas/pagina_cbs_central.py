# paginas/pagina_cbs_central.py

import streamlit as st
from streamlit_option_menu import option_menu
from theme import theme
from paginas import pagina_cbs_3, pagina_analisis_composicion

def render_cbs_segment(segment_key: str):
    """
    Renderiza la interfaz completa para un segmento específico del CBS.
    Usa el segment_key para aislar el estado de la sesión y los widgets.
    """
    analisis_seleccionado = option_menu(
        menu_title=None,
        options=["Metodología", "Estructura de costos", "Análisis de composición", "Control presupuestal", "Análisis de sensibilidad"],
        icons=['bi-journal-text', 'bi-diagram-3', 'bi-grid-1x2-fill', 'bi-bullseye', 'bi-sliders'],
        orientation="horizontal",
        styles={
             "container": {"padding": "0!important", "background-color": "#fafafa"},
             "icon": {"color": "#607D8B", "font-size": "20px"}, 
             "nav-link": {"font-size": "16px", "text-align": "center", "margin":"0px", "--hover-color": "#eee"},
             "nav-link-selected": {"background-color": "#0a3161"},

        }
    ) 
    
    # 2. Lógica de enrutamiento que pasa el 'segment_key' a las páginas
    if analisis_seleccionado == "Estructura de costos":
        # Le pasamos el identificador único a la página de la tabla
        pagina_cbs_3.render(segment_key=segment_key)

    elif analisis_seleccionado == "Análisis de composición":
        # Le pasamos el identificador único a la página de los gráficos
        pagina_analisis_composicion.render(segment_key=segment_key)
        
    # Aquí podrías añadir los elif para las otras opciones del menú
    # elif analisis_seleccionado == "Metodología":
    #     st.info(f"Metodología para el segmento {segment_key}")