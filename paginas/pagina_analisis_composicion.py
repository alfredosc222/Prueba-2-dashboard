import streamlit as st
from modulos.logica_cbs import get_processed_data
from theme import theme
from paginas import components
from paginas.components_cbs import CbsVisualizer 


def render_tab_CAPEX(segment_key: str) -> None:

    """
    Renderiza la pestaña de diagnósticos visuales con gráfico sunburst optimizado.
    """

    SESSION_KEY = f'df_{segment_key}_capex'

    if SESSION_KEY not in st.session_state or st.session_state[SESSION_KEY] is None:
        st.warning(f"⚠️ Primero debes cargar datos en la pestaña 'Estructura de costos'.")
        return
    
    df_procesado = get_processed_data(st.session_state[SESSION_KEY])

    visualizer = CbsVisualizer(df_procesado, key_prefix=f'{segment_key}_capex')

    visualizer.render_interactive_dashboard()


def render_tab_OPEX(segment_key: str) -> None:

    """
    Renderiza la pestaña de diagnósticos visuales con gráfico sunburst optimizado.
    """

    SESSION_KEY = f'df_{segment_key}_opex'

    if SESSION_KEY not in st.session_state or st.session_state[SESSION_KEY] is None:
        st.warning(f"⚠️ Primero debes cargar datos en la pestaña 'Estructura de costos'.")
        return
    
    df_procesado = get_processed_data(st.session_state[SESSION_KEY])

    visualizer = CbsVisualizer(df_procesado, key_prefix=f'{segment_key}_opex')

    visualizer.render_interactive_dashboard()


def render_tab_DECEX(segment_key: str) -> None:
    """
    Renderiza la pestaña de descripción del proyecto.
    
    Esta función muestra información general sobre la generación de proyecciones.
    """
    theme.render_header("Descripcion del CBS")


def render(segment_key: str) -> None:

    tabs_config = {

        "CapEx": {
            "icon": "bi-gear-wide-connected", 
            "render_func": lambda: render_tab_CAPEX(segment_key)
        },
        "OpEx": {
            "icon": " bi-wrench-adjustable-circle", 
            "render_func": lambda: render_tab_OPEX(segment_key)
        },
        "DecEx": {
            "icon": "bi-box-arrow-right", 
            "render_func": lambda: render_tab_DECEX(segment_key)
        },
    }
    
    components.render_analysis_page(
        page_title=f"Análisis de composición",
        tabs_config=tabs_config
    )


