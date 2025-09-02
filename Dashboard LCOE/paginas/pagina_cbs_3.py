import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from typing import Callable, Dict, Any, Optional, Tuple, List
import logging
from pathlib import Path
from modulos.logica_cbs import load_and_prepare_data, get_processed_data, debug_cost_aggregation
from theme import theme
from paginas import components
from paginas import components_cbs
import plotly.express as px
import io
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from paginas.components_cbs import CbsDataManager

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constantes de configuración
THEME_COLORS = theme._colors

DEFAULT_CBS_PATH = "C:\\Users\\alfredo\\Documents\\Proyecto LCOE_completo_POO\\cbs_data_3.xlsx"

DEFAULT_CBS_PATH_2 = "C:\\Users\\alfredo\\Documents\\Proyecto LCOE_completo_POO\\opex.xlsx"



def validate_and_load_data(file_path: str) -> pd.DataFrame:
    """
    Valida y carga datos usando la función cacheada existente.
    
    Args:
        file_path: Ruta al archivo Excel con datos CBS
        
    Returns:
        DataFrame con los datos procesados
    """
    try:
        return load_and_prepare_data(file_path)
    except Exception as e:
        logger.error(f"Error cargando datos CBS: {e}")
        st.error(f"❌ Error al cargar datos: {str(e)}")
        return pd.DataFrame()




# def render_tab_CAPEX() -> None:
#     theme.render_header("Metodología del Análisis")

#     # Inicialización del DataFrame en la sesión
#     if 'df_cbs' not in st.session_state:
#         with st.spinner("Cargando datos iniciales..."):
#             st.session_state.df_cbs = validate_and_load_data(DEFAULT_CBS_PATH)

#     df = st.session_state.df_cbs


#     # 2. "Cláusula de Guarda": Si no hay datos, mostramos el panel de carga y paramos.
#     if df.empty:
#         st.warning("No hay datos cargados. Por favor, sube un archivo para comenzar el análisis.")
#         # Mostramos el panel de carga dentro de un expander para que siempre esté disponible.
#         with st.expander("**Panel de control y carga de archivos**", expanded=True):
#             with st.form("uploader_form_empty", clear_on_submit=True):
#                 new_df = components_cbs.create_enhanced_file_uploader_panel(load_and_prepare_data)
#                 submitted = st.form_submit_button("Subir archivo")
#                 if submitted and new_df is not None:
#                     st.session_state.df_cbs = new_df
#                     st.success("Archivo cargado. Actualizando vista...")
#                     st.rerun()
#         return # Detenemos la ejecución aquí

#     ## Este es el único lugar donde se procesan los datos para toda la pestaña.
#     df_procesado = get_processed_data(df)

#     #st.dataframe(df_procesado)
#     # Mostrar KPIs (1/3) 
         
#     components_cbs.create_kpi_cards("Costos de las categorias principales", df_procesado)

#     st.markdown("")

#     # Mostrar controles y guardado (2/3)
#     with st.expander("**Panel de control y filtros**", expanded=False):
#         col_guardado, col_legendas, col_filtros = st.columns([2, 2, 2])

#         with col_guardado:
#             with st.form("uploader_form", clear_on_submit=True):
#                 new_df = components_cbs.create_enhanced_file_uploader_panel(load_and_prepare_data)
#                 submitted = st.form_submit_button("Subir archivo")
#                 if submitted and new_df is not None:
#                     st.session_state.df_cbs = new_df
#                     st.session_state.control_panel_expanded = True
#                     st.success("Archivo cargado. Actualizando vista...")
#                     st.rerun()
#                 elif submitted and new_df is None:
#                     st.warning("Por favor, selecciona un archivo primero.")

#         if df.empty:
#             st.warning("Sube un archivo para comenzar el análisis.")
#             st.stop

#         with col_legendas:
#             theme.render_subheader("Leyenda", align="center")
#             # Crear la leyenda con HTML para un mejor estilo
#             legend_html = f"""
#             <div style="display: flex; justify-content: center;">
#                 <div style="font-size: 14px; line-height: 1.8;">
#                     <div style="display: flex; align-items: center; margin-bottom: 10px;">
#                         <div style="width: 20px; height: 20px; background-color: rgba(0, 109, 119, 0.1); border: 1px solid #DDD; border-radius: 4px; margin-right: 10px;"></div>
#                         <strong>Niveles con mayor porcentaje de participación:</strong>&nbsp;<span>(> 20%)</span>
#                     </div>
#                     <strong>Hijos (Puntos de Entrada):</strong>
#                     <div style="display: flex; align-items: center; margin-bottom: 5px;">
#                         <div style="width: 4px; height: 20px; background-color: {THEME_COLORS['primario']}; border-radius: 4px; margin-right: 10px;"></div>
#                         <span>Nivel de participación alta (> 20%)</span>
#                     </div>
#                     <div style="display: flex; align-items: center; margin-bottom: 5px;">
#                         <div style="width: 4px; height: 20px; background-color: {THEME_COLORS['historico']}; border-radius: 4px; margin-right: 10px;"></div>
#                         <span>Nivel de participación media (> 10%)</span>
#                     </div>
#                     <div style="display: flex; align-items: center;">
#                         <div style="width: 4px; height: 20px; background-color: {THEME_COLORS['exito']}; border-radius: 4px; margin-right: 10px;"></div>
#                         <span>Nivel de participacion baja (> 5%)</span>
#                     </div>
#                 </div>
#             </div>
#             """
#             st.markdown(legend_html, unsafe_allow_html=True)

#         with col_filtros:
#             theme.render_subheader("Filtros", align="center")
#             col1, col2, col3 = st.columns([1, 4, 1])

#             with col2:
#                 min_importance = st.slider(
#                     "Importancia mínima",
#                     min_value= 0,
#                     max_value= 50,
#                     value= 0,
#                     step=1,
#                     format="%d%%",
#                     width=500,
#                     help="Desliza para excluir elementos con importancia menor a la seleccionada."
#                 )

#                 all_levels = sorted(df_procesado["Nivel"].unique())

#                 if "selected_levels" not in st.session_state:
#                     st.session_state.selected_levels = all_levels.copy()

#                 is_all_selected = len(st.session_state.selected_levels) == len(all_levels)
                
#                 select_all = st.checkbox("Seleccionar todos los niveles", value=is_all_selected)

#                 if select_all != is_all_selected:
#                     st.session_state.selected_levels = all_levels.copy() if select_all else []
#                     st.rerun()

#                 selected_levels = st.segmented_control(
#                     "Niveles a mostrar", 
#                     options=all_levels,
#                     default=st.session_state.selected_levels,
#                     selection_mode="multi"
#                 )

#                 if selected_levels != st.session_state.selected_levels:
#                     st.session_state.selected_levels = selected_levels
#                     st.rerun()
        
#     if df.empty:
#         st.info("Esperando carga de datos...")
#         return

#     # Si no hay niveles seleccionados, se muestra una advertencia.
#     if not selected_levels:
#         st.warning("Abre el Panel de Control y selecciona al menos un nivel para ver los datos.")
#         return

#     mask = (df_procesado['Importancia (%)'] >= min_importance) & \
#             (df_procesado['Nivel'].isin(selected_levels))
#     df_filtrado = df_procesado[mask]

#     st.markdown("")

#     # Tabla jerarquica (3/3)
#     col1, col2, col3 = st.columns([1, 6, 1])

#     with col2:

#         if df_filtrado.empty:
#             st.warning("No hay datos que coincidan con los filtros aplicados.")
#         else:
#             with st.spinner("Generando tabla interactiva..."):
#                 try:
#                     grid_options = components_cbs.create_optimized_grid_options(df_filtrado)
#                     AgGrid(
#                         df_filtrado, 
#                         gridOptions=grid_options, 
#                         theme='material', 
#                         allow_unsafe_jscode=True, 
#                         enable_enterprise_modules=True, 
#                         height=800,
#                         key='cbs_dashboard_pro_grid',
#                         update_mode='NO_UPDATE',
#                         fit_columns_on_grid_load=True
#                     )
#                 except Exception as e:
#                     st.error(f"Error generando tabla: {str(e)}")
#                     logger.error(f"Error en AG-Grid: {e}")

#     #debug_cost_aggregation(df_filtrado)





def render_tab_CAPEX(segment_key: str) -> None:
    theme.render_header("Metodología del Análisis")

    SESSION_KEY = f'df_{segment_key}_capex'
    #PAG_KEY = 'tabla_capex'

    # Inicialización del DataFrame en la sesión
    if SESSION_KEY not in st.session_state:
        st.session_state[SESSION_KEY] = None

    df = st.session_state[SESSION_KEY]


    # 2. "Cláusula de Guarda": Si no hay datos, mostramos el panel de carga y paramos.
    if df is None or df.empty:
        st.warning("No hay datos cargados. Por favor, sube un archivo para comenzar el análisis.")
        # Mostramos el panel de carga dentro de un expander para que siempre esté disponible.
        with st.expander("**Panel de control y carga de archivos**", expanded=True):
            with st.form(f"uploader_form_empty_{SESSION_KEY}", clear_on_submit=True):
                new_df = CbsDataManager.render_file_uploader(load_and_prepare_data)
                submitted = st.form_submit_button("Subir archivo")
                if submitted and new_df is not None:
                    st.session_state[SESSION_KEY] = new_df
                    st.success("Archivo cargado. Actualizando vista...")
                    st.rerun()
        return 

    ## Este es el único lugar donde se procesan los datos para toda la pestaña.
    df_procesado = get_processed_data(df)

    # Crea la instancia y deja que la clase dibuje toda la página
    data_manager = CbsDataManager(df_procesado, session_key=SESSION_KEY)
    data_manager.render(key=f'tabla_{segment_key}_capex')





def render_tab_OPEX(segment_key: str) -> None:
    theme.render_header("Metodología del Análisis")

    SESSION_KEY = f'df_{segment_key}_opex'
    #PAG_KEY = 'tabla_opex'

    # Inicialización del DataFrame en la sesión
    if SESSION_KEY not in st.session_state:
        st.session_state[SESSION_KEY] = None

    df = st.session_state[SESSION_KEY]


    # 2. "Cláusula de Guarda": Si no hay datos, mostramos el panel de carga y paramos.
    if df is None or df.empty:
        st.warning("No hay datos cargados. Por favor, sube un archivo para comenzar el análisis.")
        # Mostramos el panel de carga dentro de un expander para que siempre esté disponible.
        with st.expander("**Panel de control y carga de archivos**", expanded=True):
            with st.form(f"uploader_form_empty_{SESSION_KEY}", clear_on_submit=True):
                new_df = CbsDataManager.render_file_uploader(load_and_prepare_data)
                submitted = st.form_submit_button("Subir archivo")
                if submitted and new_df is not None:
                    st.session_state[SESSION_KEY] = new_df
                    st.success("Archivo cargado. Actualizando vista...")
                    st.rerun()
        return 

    ## Este es el único lugar donde se procesan los datos para toda la pestaña.
    df_procesado = get_processed_data(df)

    # Crea la instancia y deja que la clase dibuje toda la página
    data_manager = CbsDataManager(df_procesado, session_key=SESSION_KEY)
    data_manager.render(key=f'tabla_{segment_key}_opex')



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
        page_title=f"Análisis de estructura de costos",
        tabs_config=tabs_config
    )


