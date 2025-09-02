
import streamlit as st
import pandas as pd
from typing import Callable, Dict, Any, Optional, Tuple, List
from theme import theme 
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from plotly.subplots import make_subplots
import plotly.graph_objects as go
THEME_COLORS = theme._colors
from modulos import logica_cbs
import numpy as np
from modulos.logica_cbs import load_and_prepare_data, get_processed_data

# Se utiliza para la tarjeta KPI
def create_kpi_cards(title: str, df_procesado: pd.DataFrame) -> None:
    """
    Crea tarjetas KPI para mostrar costos principales desde un DataFrame ya procesado.
    
    Args:
        title: El título para el contenedor de KPIs.
        df_procesado: DataFrame con los costos ya agregados.
    """
    with st.container(border=True):
        theme.render_subheader(title) 
        
        # El DataFrame ya viene con los totales, no hay necesidad de recalcular.
        
        # Mapeo dinámico de KPIs
        kpi_map = {}
        for id_jerarquico in ['1', '1.1', '1.2', '1.3']:
            # Usamos el df_procesado para obtener la descripción
            desc_series = df_procesado[df_procesado['ID_Jerarquico'] == id_jerarquico]['Descripcion']
            if not desc_series.empty:
                kpi_map[id_jerarquico] = desc_series.iloc[0]

        if not kpi_map:
            st.warning("No se encontraron los IDs principales ('1', '1.1', '1.2', '1.3') para los KPIs.")
            return

        cols = st.columns(len(kpi_map))
        
        for i, (id_jerarquico, label) in enumerate(kpi_map.items()):
            cost_series = df_procesado[df_procesado['ID_Jerarquico'] == id_jerarquico]['Costo_Total']
            cost = cost_series.iloc[0] if not cost_series.empty else 0
            
            with cols[i]:
                theme.render_metric(label, cost, formato='$')


# Sirve para el widget de cargar archivo
def create_enhanced_file_uploader_panel(load_function: Callable) -> Optional[pd.DataFrame]:
    """
    MEJORA 11: Panel de carga de archivos más intuitivo y robusto
    """
    theme.render_header("Cargar archivo CBS", align="center")
    
    uploaded_file = st.file_uploader(
        "Selecciona tu archivo Excel",
        type=['xlsx', 'xls'],
        help="El archivo debe contener las columnas: ID_Jerarquico, Descripcion, Resumen, Costo"
    )
    
    if uploaded_file is not None:
        try:
            # Mostrar información del archivo
            file_details = {
                "Nombre": uploaded_file.name,
                "Tamaño": f"{uploaded_file.size / 1024:.1f} KB",
            }
            
            with st.expander("Detalles del archivo", expanded=False):
                for key, value in file_details.items():
                    st.text(f"{key}: {value}")
            
            # Procesar archivo con feedback visual
            with st.spinner("Procesando archivo..."):
                df = load_function(uploaded_file)
                
            if not df.empty:
                st.success(f"Archivo cargado exitosamente: {len(df)} filas procesadas")
                
                # Actualizar session state
                st.session_state.df_cbs = df
                return df
            else:
                st.error("Error al procesar el archivo")
                
        except Exception as e:
            st.error(f"Error al leer el archivo: {str(e)}")
    
    return None




# Se define el estilo de la tabla, muy importante
def create_optimized_grid_options(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Configura las opciones optimizadas de AG-Grid con mejor rendimiento.
    
    Args:
        df: DataFrame con datos CBS
        
    Returns:
        Diccionario con configuración de grid
    """

    # Estilo para la columna de Jerarquía (Nivel Jerárquico)
    group_cell_style_js = JsCode(f"""
    function(params) {{
        const level = params.node.level + 1;
        const importance = params.data ? params.data['Importancia (%)'] || 0 : 0;
        const isParentNode = params.node.childrenAfterFilter.length > 0;

        // Estilos base para fuente y color según el nivel
        const baseStyles = {{
            1: {{'fontSize': '20px', 'fontWeight': '600', 'color': '{THEME_COLORS["primario"]}'}},
            2: {{'fontSize': '18px', 'fontWeight': '500', 'color': '{THEME_COLORS["texto_principal"]}'}},
            3: {{'fontSize': '16px', 'fontWeight': '400', 'color': '{THEME_COLORS["texto_principal"]}'}},
            4: {{'fontSize': '15px', 'fontWeight': '400', 'color': '{THEME_COLORS["texto_secundario"]}'}},
            5: {{'fontSize': '14px', 'fontWeight': '400', 'color': '{THEME_COLORS["texto_secundario"]}'}},
            6: {{'fontSize': '13px', 'fontWeight': '400', 'color': '{THEME_COLORS["texto_secundario"]}'}}
        }};
        
        // Estilo de sangría para la jerarquía
        const indentation = {{ paddingLeft: (level > 1 ? (level - 1) * 20 : 0) + 'px' }};
        
        let importanceStyle = {{}};
        if (isParentNode && importance > 20 && level > 2) {{
            // Resalta padres importantes (Nivel 3+) con un fondo sutil
            importanceStyle = {{ 'backgroundColor': 'rgba(0, 109, 119, 0.1)' }};
        }}

        // Combinar todos los estilos
        return Object.assign(indentation, baseStyles[level] || {{}}, importanceStyle);
    }}
    """)

    # Estilo para la columna de Descripción, ahora con el borde de importancia
    description_cell_style_js = JsCode(f"""
    function(params) {{
        const importance = params.data ? params.data['Importancia (%)'] || 0 : 0;
        const isLeafNode = params.node.childrenAfterFilter.length === 0;

        let importanceStyle = {{}};
        if (isLeafNode) {{ // Aplicar solo a los hijos de nivel más bajo
            if (importance > 20) {{
                importanceStyle = {{
                    'borderLeft': '4px solid {THEME_COLORS["primario"]}', 
                    'paddingLeft': '16px',
                    'borderTopLeftRadius': '8px',
                    'borderBottomLeftRadius': '8px'
                }};
            }} else if (importance > 10) {{
                importanceStyle = {{
                    'borderLeft': '4px solid {THEME_COLORS["historico"]}', 
                    'paddingLeft': '16px',
                    'borderTopLeftRadius': '8px',
                    'borderBottomLeftRadius': '8px'
                }};
            }} else if (importance > 5) {{
                importanceStyle = {{
                    'borderLeft': '4px solid {THEME_COLORS["exito"]}', 
                    'paddingLeft': '16px',
                    'borderTopLeftRadius': '8px',
                    'borderBottomLeftRadius': '8px'
                }};
            }}
        }}

        // Se retorna el estilo de importancia para que se aplique a la celda
        return importanceStyle;
    }}
    """)

    value_getter_js = JsCode(f"""
    function(params) {{
        if (!params.node.data) return '';
        return params.node.data.ID_Jerarquico || '';
    }}
    """)

    gb = GridOptionsBuilder.from_dataframe(df)
     
    # Formateador de costo optimizado
    cost_formatter = JsCode("""
    function(params) {
        if (params.value != null) {
            return '$' + params.value.toLocaleString('en-US', {
                minimumFractionDigits: 2, 
                maximumFractionDigits: 2 
            });
        }
        return '$0.00';
    }
    """)
    
    # Configuración de columnas
    gb.configure_column(
        "Costo_Total", 
        headerName="Costo", 
        type=["numericColumn"], 
        valueFormatter=cost_formatter, 
        aggFunc='sum', 
        minWidth=150,
        maxWidth=200,
        flex=1,
        cellStyle={
            'textAlign': 'right', 
            'fontWeight': '600', 
        },
        
    )
    
    gb.configure_column(
        "Descripcion", 
        headerName="Descripción", 
        flex=1,
        minWidth=250, 
        maxWidth=350, 
        wrapText=True, 
        autoHeight=True,
        cellStyle=description_cell_style_js,
         
    )
    
    gb.configure_column(
        "Resumen", 
        headerName="Resumen", 
        flex=2, 
        minWidth=500, 
        maxWidth=850, 
        wrapText=True, 
        autoHeight=True, 
        cellStyle={ 
            'fontSize': '14px',
            'lineHeight': '2.0'
        },
    )

    
    # Ocultar columnas auxiliares
    for col in ["ruta_jerarquica", "Nivel", "ID_Jerarquico", "Importancia (%)","Costo"]:
        gb.configure_column(col, hide=True)
    
    # Configuración principal del grid
    gb.configure_grid_options(
        suppressAggFuncInHeader=True, 
        treeData=True, 
        getDataPath=JsCode("data => data.ruta_jerarquica.split('/')"),
        autoGroupColumnDef={
            "headerName": "Nivel Jerárquico", 
            "minWidth": 300,
            "maxWidth": 350, 
            "flex": 1,
            "cellRendererParams": {"suppressCount": True},
            "valueGetter": value_getter_js,
            "cellStyle": group_cell_style_js, # Se reutiliza el JS consolidado
            
        },
        groupDefaultExpanded=2,
        rowBuffer=50,
        animateRows=False, # Mejora el rendimiento
        #rowSelection='multiple',
        enableRangeSelection=True
    )

    return gb.build()








class CbsDataManager:
    """
    Gestiona la visualización de la tabla de datos del CBS, KPIs y controles.
    """
    def __init__(self, df_procesado: pd.DataFrame, session_key: str):
        self.df_procesado = df_procesado
        self.session_key = session_key
        self.THEME_COLORS = theme._colors

    def render(self, key: str):

        self.render_kpis()

        filtros = self._render_control_panel()

        # 3. Aplicar filtros y renderizar la tabla
        if filtros:
            mask = (self.df_procesado['Importancia (%)'] >= filtros['min_importance']) & \
                   (self.df_procesado['Nivel'].isin(filtros['selected_levels']))
            df_filtrado = self.df_procesado[mask]
            
            self.render_grid(df_filtrado, key=key)  

    def _build_grid_options(self, df_for_grid: pd.DataFrame) -> Dict[str, Any]:
        """
        Método privado que encapsula la compleja configuración de AG-Grid.
        Reemplaza a create_optimized_grid_options.
        """

        
        gb = GridOptionsBuilder.from_dataframe(df_for_grid)

        group_cell_style_js = JsCode(f"""
        function(params) {{
            const level = params.node.level + 1;
            const importance = params.data ? params.data['Importancia (%)'] || 0 : 0;
            const isParentNode = params.node.childrenAfterFilter.length > 0;

            // Estilos base para fuente y color según el nivel
            const baseStyles = {{
                1: {{'fontSize': '20px', 'fontWeight': '600', 'color': '{self.THEME_COLORS["primario"]}'}},
                2: {{'fontSize': '18px', 'fontWeight': '500', 'color': '{self.THEME_COLORS["texto_principal"]}'}},
                3: {{'fontSize': '16px', 'fontWeight': '400', 'color': '{self.THEME_COLORS["texto_principal"]}'}},
                4: {{'fontSize': '15px', 'fontWeight': '400', 'color': '{self.THEME_COLORS["texto_secundario"]}'}},
                5: {{'fontSize': '14px', 'fontWeight': '400', 'color': '{self.THEME_COLORS["texto_secundario"]}'}},
                6: {{'fontSize': '13px', 'fontWeight': '400', 'color': '{self.THEME_COLORS["texto_secundario"]}'}}
            }};
            
            // Estilo de sangría para la jerarquía
            const indentation = {{ paddingLeft: (level > 1 ? (level - 1) * 20 : 0) + 'px' }};
            
            let importanceStyle = {{}};
            if (isParentNode && importance > 20 && level > 2) {{
                // Resalta padres importantes (Nivel 3+) con un fondo sutil
                importanceStyle = {{ 'backgroundColor': 'rgba(0, 109, 119, 0.1)' }};
            }}

            // Combinar todos los estilos
            return Object.assign(indentation, baseStyles[level] || {{}}, importanceStyle);
        }}
        """)
        
        # Estilo para la columna de Descripción, ahora con el borde de importancia
        description_cell_style_js = JsCode(f"""
        function(params) {{
            const importance = params.data ? params.data['Importancia (%)'] || 0 : 0;
            const isLeafNode = params.node.childrenAfterFilter.length === 0;

            let importanceStyle = {{}};
            if (isLeafNode) {{ // Aplicar solo a los hijos de nivel más bajo
                if (importance > 20) {{
                    importanceStyle = {{
                        'borderLeft': '4px solid {self.THEME_COLORS["primario"]}', 
                        'paddingLeft': '16px',
                        'borderTopLeftRadius': '8px',
                        'borderBottomLeftRadius': '8px'
                    }};
                }} else if (importance > 10) {{
                    importanceStyle = {{
                        'borderLeft': '4px solid {self.THEME_COLORS["historico"]}', 
                        'paddingLeft': '16px',
                        'borderTopLeftRadius': '8px',
                        'borderBottomLeftRadius': '8px'
                    }};
                }} else if (importance > 5) {{
                    importanceStyle = {{
                        'borderLeft': '4px solid {self.THEME_COLORS["exito"]}', 
                        'paddingLeft': '16px',
                        'borderTopLeftRadius': '8px',
                        'borderBottomLeftRadius': '8px'
                    }};
                }}
            }}

            // Se retorna el estilo de importancia para que se aplique a la celda
            return importanceStyle;
        }}
        """)

        value_getter_js = JsCode(f"""
        function(params) {{
            if (!params.node.data) return '';
            return params.node.data.ID_Jerarquico || '';
        }}
        """)

        
        gb = GridOptionsBuilder.from_dataframe(self.df_procesado)
        
        # Formateador de costo optimizado
        cost_formatter = JsCode("""
        function(params) {
            if (params.value != null) {
                return '$' + params.value.toLocaleString('en-US', {
                    minimumFractionDigits: 2, 
                    maximumFractionDigits: 2 
                });
            }
            return '$0.00';
        }
        """)
        
        # Configuración de columnas
        gb.configure_column(
            "Costo_Total", 
            headerName="Costo", 
            type=["numericColumn"], 
            valueFormatter=cost_formatter, 
            aggFunc='sum', 
            minWidth=150,
            maxWidth=200,
            flex=1,
            cellStyle={
                'textAlign': 'right', 
                'fontWeight': '600', 
            },
            
        )
        
        gb.configure_column(
            "Descripcion", 
            headerName="Descripción", 
            flex=1,
            minWidth=250, 
            maxWidth=350, 
            wrapText=True, 
            autoHeight=True,
            cellStyle=description_cell_style_js,
            
        )
        
        gb.configure_column(
            "Resumen", 
            headerName="Resumen", 
            flex=2, 
            minWidth=500, 
            maxWidth=850, 
            wrapText=True, 
            autoHeight=True, 
            cellStyle={ 
                'fontSize': '14px',
                'lineHeight': '2.0'
            },
        )

        
        # Ocultar columnas auxiliares
        for col in ["ruta_jerarquica", "Nivel", "ID_Jerarquico", "Importancia (%)","Costo"]:
            gb.configure_column(col, hide=True)
        
        # Configuración principal del grid
        gb.configure_grid_options(
            suppressAggFuncInHeader=True, 
            treeData=True, 
            getDataPath=JsCode("data => data.ruta_jerarquica.split('/')"),
            autoGroupColumnDef={
                "headerName": "Nivel Jerárquico", 
                "minWidth": 300,
                "maxWidth": 350, 
                "flex": 1,
                "cellRendererParams": {"suppressCount": True},
                "valueGetter": value_getter_js,
                "cellStyle": group_cell_style_js, # Se reutiliza el JS consolidado
                
            },
            groupDefaultExpanded=2,
            rowBuffer=50,
            animateRows=False, # Mejora el rendimiento
            #rowSelection='multiple',
            enableRangeSelection=True
        )

        return gb.build()
    
    def render_kpis(self):
        """Renderiza las tarjetas KPI. Reemplaza a create_kpi_cards."""
        with st.container(border=True):
            theme.render_subheader("Costos de las Categorías Principales")
            
            # 1. Encontrar todos los nodos de Nivel 1 (los de más alto nivel)
            level_1_nodes = self.df_procesado[self.df_procesado['Nivel'] == 1]
            
            # 2. Encontrar todos los nodos de Nivel 2 (los hijos directos de los de Nivel 1)
            level_2_nodes = self.df_procesado[self.df_procesado['Nivel'] == 2]
            
            # 3. Crear la lista de IDs a mostrar, combinando ambos niveles y ordenándolos
            kpi_ids_to_display = sorted(
                level_1_nodes['ID_Jerarquico'].tolist() + 
                level_2_nodes['ID_Jerarquico'].tolist()
            )       
            
            kpi_map = {}
            for id_jerarquico in kpi_ids_to_display:
                desc_series = self.df_procesado[self.df_procesado['ID_Jerarquico'] == id_jerarquico]['Descripcion']
                if not desc_series.empty:
                    kpi_map[id_jerarquico] = desc_series.iloc[0]

            if not kpi_map:
                st.warning("No se encontraron los IDs principales para los KPIs.")
                return

            cols = st.columns(len(kpi_map))
            for i, (id_jerarquico, label) in enumerate(kpi_map.items()):
                cost_series = self.df_procesado[self.df_procesado['ID_Jerarquico'] == id_jerarquico]['Costo_Total']
                cost = cost_series.iloc[0] if not cost_series.empty else 0
                with cols[i]:
                    theme.render_metric(label, cost, formato='$')

    def render_grid(self, df_filtrado: pd.DataFrame, key: str):
        """Construye las opciones y renderiza la tabla AG-Grid."""

        col1, col2, col3 = st.columns([1, 6, 1])

        with col2:

            if df_filtrado.empty:
                st.warning("No hay datos que coincidan con los filtros aplicados.")
            else:

                with st.spinner("Generando tabla interactiva..."):
                    try:
                        grid_options = self._build_grid_options(df_filtrado)
                        AgGrid(
                            df_filtrado, 
                            gridOptions=grid_options, 
                            theme='material', 
                            allow_unsafe_jscode=True,
                            enable_enterprise_modules=True, 
                            height=800,
                            update_mode='NO_UPDATE',
                            key=key,
                            fit_columns_on_grid_load=True
                        )
                    except Exception as e:
                        st.error(f"Error al generar la tabla: {str(e)}")


    @staticmethod
    def render_file_uploader(load_function: Callable) -> Optional[pd.DataFrame]:
        """
        Renderiza el panel de carga de archivos. Es estático porque no depende de 'self.df'.
        Reemplaza a create_enhanced_file_uploader_panel.
        """

        theme.render_header("Cargar archivo CBS", align="center")
        
        uploaded_file = st.file_uploader(
            "Selecciona tu archivo Excel",
            type=['xlsx', 'xls'],
            help="El archivo debe contener las columnas: ID_Jerarquico, Descripcion, Resumen, Costo"
        )
        
        if uploaded_file is not None:
            try:
                # Mostrar información del archivo
                file_details = {
                    "Nombre": uploaded_file.name,
                    "Tamaño": f"{uploaded_file.size / 1024:.1f} KB",
                }
                
                with st.expander("Detalles del archivo", expanded=False):
                    for key, value in file_details.items():
                        st.text(f"{key}: {value}")
                
                # Procesar archivo con feedback visual
                with st.spinner("Procesando archivo..."):
                    df = load_function(uploaded_file)
                    
                if not df.empty:
                    st.success(f"Archivo cargado exitosamente: {len(df)} filas procesadas")
                    
                    # Actualizar session state
                    #st.session_state.df_cbs = df
                    return df
                else:
                    st.error("Error al procesar el archivo")
                    
            except Exception as e:
                st.error(f"Error al leer el archivo: {str(e)}")
        
        return df if 'df' in locals() and not df.empty else None



    def _render_control_panel(self) -> Optional[Dict]:
        """Renderiza el expander con los controles y devuelve los valores de los filtros."""
        with st.expander("**Panel de control y filtros**", expanded=False):
            col_guardado, col_legendas, col_filtros = st.columns([2, 2, 2])

            with col_guardado:
                with st.form(f"uploader_form_{self.session_key}", clear_on_submit=True):
                    new_df = CbsDataManager.render_file_uploader(load_and_prepare_data)
                    submitted = st.form_submit_button("Subir archivo")
                    
                    if submitted and new_df is not None:
                        st.session_state[self.session_key] = new_df
                        st.session_state.control_panel_expanded = True
                        st.success("Archivo cargado. Actualizando vista...")
                        st.rerun()
                    elif submitted and new_df is None:
                        st.warning("Por favor, selecciona un archivo primero.")

            if self.df_procesado.empty:
                st.warning("Sube un archivo para comenzar el análisis.")
                st.stop

            with col_legendas:
                theme.render_subheader("Leyenda", align="center")
                # Crear la leyenda con HTML para un mejor estilo
                legend_html = f"""
                <div style="display: flex; justify-content: center;">
                    <div style="font-size: 14px; line-height: 1.8;">
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <div style="width: 20px; height: 20px; background-color: rgba(0, 109, 119, 0.1); border: 1px solid #DDD; border-radius: 4px; margin-right: 10px;"></div>
                            <strong>Niveles con mayor porcentaje de participación:</strong>&nbsp;<span>(> 20%)</span>
                        </div>
                        <strong>Hijos (Puntos de Entrada):</strong>
                        <div style="display: flex; align-items: center; margin-bottom: 5px;">
                            <div style="width: 4px; height: 20px; background-color: {self.THEME_COLORS['primario']}; border-radius: 4px; margin-right: 10px;"></div>
                            <span>Nivel de participación alta (> 20%)</span>
                        </div>
                        <div style="display: flex; align-items: center; margin-bottom: 5px;">
                            <div style="width: 4px; height: 20px; background-color: {self.THEME_COLORS['historico']}; border-radius: 4px; margin-right: 10px;"></div>
                            <span>Nivel de participación media (> 10%)</span>
                        </div>
                        <div style="display: flex; align-items: center;">
                            <div style="width: 4px; height: 20px; background-color: {self.THEME_COLORS['exito']}; border-radius: 4px; margin-right: 10px;"></div>
                            <span>Nivel de participacion baja (> 5%)</span>
                        </div>
                    </div>
                </div>
                """
                st.markdown(legend_html, unsafe_allow_html=True)

            with col_filtros:
                theme.render_subheader("Filtros", align="center")
                col1, col2, col3 = st.columns([1, 4, 1])

                with col2:
                    slider_key = f"min_importance_{self.session_key}"
                    min_importance = st.slider(
                        "Importancia mínima",
                        min_value= 0,
                        max_value= 50,
                        value= 0,
                        key=slider_key,
                        step=1,
                        format="%d%%",
                        width=500,
                        help="Desliza para excluir elementos con importancia menor a la seleccionada."
                    )

                    all_levels = sorted(self.df_procesado["Nivel"].unique())

                    levels_key = f"selected_levels_{self.session_key}"

                    if levels_key not in st.session_state:
                        st.session_state[levels_key]= all_levels.copy()

                    is_all_selected = len(st.session_state[levels_key]) == len(all_levels)
                    
                    select_all = st.checkbox("Seleccionar todos los niveles", value=is_all_selected)

                    if select_all != is_all_selected:
                        st.session_state[levels_key] = all_levels.copy() if select_all else []
                        st.rerun()

                    selected_levels = st.segmented_control(
                        "Niveles a mostrar", 
                        options=all_levels,
                        key=levels_key,
                        selection_mode="multi"
                    )

                    if selected_levels != st.session_state[levels_key]:
                        st.session_state[levels_key] = selected_levels
                        st.rerun()
            
        if self.df_procesado.empty:
            st.info("Esperando carga de datos...")
            return

        # Si no hay niveles seleccionados, no se puede filtrar
        if not selected_levels:
            st.warning("Abre el Panel de Control y selecciona al menos un nivel para ver los datos.")
            return None

        # Devolvemos los valores de los filtros en un diccionario
        return {"min_importance": min_importance, "selected_levels": selected_levels}



        






















































class CbsVisualizer:
    """
    Una clase para encapsular toda la lógica de visualización del CBS.
    """
    def __init__(self, df: pd.DataFrame, key_prefix: str):
        """
        El constructor recibe el DataFrame ya procesado.
        """
        self.df = df
        self.key_prefix = key_prefix
        self.COLOR_PALETTE_CATEGORICAL = ["#006D77", "#83C5BE", "#264653", "#E29578", "#FFDD99", "#4E6B73"]
        self.COLOR_SCALE_SEQUENTIAL = [
            "#FFFAE5",  # Arena muy clara (mínimos)
            "#FFF2CC",  # Arena clara
            "#FFE0A3",  # Arena cálida leve
            "#F2D3B0",  # Transición arena → coral suave
            "#E8C2A4",  # Coral arenoso apagado
            "#D6EDEC",  # Agua muy clara
            "#C1E3E2",  # Agua clara
            "#A9D8D7",  # Agua intermedia
            "#92CECC",  # Agua fresca
            "#7AC3C1",  # Verde agua claro
            "#64B9B5",  # Verde agua medio
            "#4DAFA8",  # Verde agua más profundo
            "#3B9C95",  # Verde-azulado medio
            "#2C8881",  # Verde marino
            "#237571",  # Marino medio
            "#1C6360",  # Marino intenso
            "#15514E",  # Marino profundo
            "#0F413F",  # Verde-azulado oscuro
            "#0A3332",  # Marino casi final
            "#006D77"   # Primario (cierre / valores máximos)
        ]

    # --- MÉTODOS PRIVADOS DE AYUDA ---

    def _get_leaf_nodes(self, df_to_filter: pd.DataFrame) -> pd.DataFrame:
        """Identifica y devuelve los nodos hoja de un DataFrame dado."""

        if 'ruta_jerarquica' not in df_to_filter.columns or df_to_filter['ruta_jerarquica'].dropna().empty:
            return df_to_filter
        paths = df_to_filter['ruta_jerarquica'].dropna().astype(str)
        path_components = paths.str.split('/')
        all_parents = path_components.str[:-1].explode().unique()
        leaf_nodes = df_to_filter[~df_to_filter['ID_Jerarquico'].isin(all_parents)]
        return leaf_nodes
    

    def _create_path_hierarchy(self, df_chart: pd.DataFrame) -> pd.DataFrame:
        df_copy = df_chart.copy()
        def safe_split_path(row):
            ruta = row['ruta_jerarquica']
            if isinstance(ruta, str) and ruta.strip():
                path_list = [part.strip() for part in ruta.split('/') if part.strip()]
                return path_list if path_list else [row['ID_Jerarquico']]
            return [row['ID_Jerarquico']]
        df_copy['path_hierarchy'] = df_copy.apply(safe_split_path, axis=1)
        return df_copy
    
    def _expand_path_columns(self, df_with_paths: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
        """
        Expande la columna 'path_hierarchy' en múltiples columnas 'level_n'.
        """
        df_filtered =  df_with_paths[ df_with_paths['path_hierarchy'].apply(lambda x: isinstance(x, list) and len(x) > 0)].copy()
        if df_filtered.empty:
            return pd.DataFrame(), []
        # Usamos int() para asegurar que max_depth no sea un float si hay NaNs
        max_depth = int(df_filtered['path_hierarchy'].str.len().max())
        path_columns = [f'level_{i}' for i in range(max_depth)]
        for i, col_name in enumerate(path_columns):
            df_filtered[col_name] = df_filtered['path_hierarchy'].str[i]
        return df_filtered, path_columns


    # --- MÉTODOS PÚBLICOS PARA RENDERIZAR GRÁFICOS ---

    def render_category_pie_chart(self, level: int, top_n: int = 5):
        """Prepara datos y renderiza el gráfico de dona por categoría."""
        # Preparación de datos (antes 'prepare_category_data')
        df_copy = self.df.copy()
        description_map = df_copy.drop_duplicates(subset=['ID_Jerarquico']).set_index('ID_Jerarquico')['Descripcion']
        df_copy['Categoria'] = df_copy['ID_Jerarquico'].str.split('.').str[:level].str.join('.')
        df_copy['Nivel_Fila'] = df_copy['ID_Jerarquico'].str.count('\\.') + 1
        df_filtered_level = df_copy[df_copy['Nivel_Fila'] >= level]
        df_chart = df_filtered_level.groupby('Categoria').agg(Costo=('Costo', 'sum')).reset_index()
        df_chart['Descripcion'] = df_chart['Categoria'].map(description_map).fillna('N/A')
        df_chart = df_chart.sort_values('Costo', ascending=False)
        
        if len(df_chart) > top_n:
            df_top = df_chart.head(top_n)
            otros_sum = df_chart.iloc[top_n:]['Costo'].sum()
            df_otros = pd.DataFrame([{'Categoria': 'Otros', 'Costo': otros_sum, 'Descripcion': 'Suma del resto'}])
            df_chart = pd.concat([df_top, df_otros], ignore_index=True)

            

        # Creación del gráfico (antes 'create_category_pie_chart')
        if df_chart.empty:
            st.info(f"No hay datos suficientes para mostrar en el Nivel {level}.")
            return
        
        fig = go.Figure(data=[go.Pie(
            labels=df_chart['Categoria'],
            values=df_chart['Costo'],
            customdata=df_chart['Descripcion'],
            hole=0.4,
            marker_colors=self.COLOR_PALETTE_CATEGORICAL,
            textposition='inside',
            textfont_size=16,
            texttemplate="<b>%{label}</b><br>%{customdata}<br>%{percent:.1%}",
            hovertemplate=(
                "<b>%{label}</b>: %{customdata}<br>"
                "Costo: $%{value:,.2f}<br>"
                "Porcentaje: %{percent}<extra></extra>"
            )
        )])

        fig.update_layout(
            height=827, 
            showlegend=False,
            uniformtext_minsize=6, 
            uniformtext_mode='hide'
        )
        st.plotly_chart(fig, use_container_width=True)

    def render_treemap(self, top_n: int, category_prefix: Optional[str] = None):
        """Prepara datos y renderiza el gráfico treemap."""
        # Preparación de datos (antes 'prepare_treemap_data')
        df_to_filter = self.df
        if category_prefix:
            df_to_filter = self.df[self.df['ID_Jerarquico'].str.startswith(category_prefix)]
        leaf_nodes = self._get_leaf_nodes(df_to_filter)
        if leaf_nodes.empty:
            df_chart = pd.DataFrame()
        else:
            df_chart = leaf_nodes.nlargest(min(top_n, len(leaf_nodes)), 'Costo_Total')
        
        # Creación del gráfico (antes 'create_top_n_treemap')
        if df_chart.empty:
            st.info("No hay datos para mostrar en el Treemap con la selección actual.")
            return

        df_with_paths = self._create_path_hierarchy(df_chart)
        df_plot, path_columns = self._expand_path_columns(df_with_paths)

        if df_plot.empty:
            st.info("No se pudo construir la jerarquía para el Treemap.")
            return
        
        # 1. Crear columnas explícitas para el texto y el hover.
        df_plot['text_label'] = np.where(
            df_plot['Costo'] > 0, 
            df_plot['Descripcion'], 
            df_plot['ID_Jerarquico'] # Los padres solo muestran su ID
        )
        df_plot['cost_text'] = np.where(
            df_plot['Costo'] > 0,
            "$" + df_plot['Costo'].round(2).astype(str),
            "" # Los padres no muestran costo en el recuadro
        )

        # Función para envolver el texto e insertar saltos de línea.
        def wrap_text(text, max_words_per_line=2):
            if not isinstance(text, str):
                return text
            words = text.split()
            wrapped_lines = []
            for i in range(0, len(words), max_words_per_line):
                wrapped_lines.append(" ".join(words[i:i+max_words_per_line]))
            return "<br>".join(wrapped_lines)
        
        df_plot['text_label'] = df_plot['text_label'].apply(wrap_text)

        fig = px.treemap(
            df_plot, 
            path=path_columns,
            values='Costo_Total',
            color='Costo_Total',
            hover_name='text_label',
            custom_data=['text_label', 'cost_text'],
            color_continuous_scale=self.COLOR_SCALE_SEQUENTIAL,
            branchvalues='total' 
        )
        
        fig.update_traces(
            marker=dict(cornerradius=10),
            # CORRECCIÓN: Se usa %{hovertext} para mostrar la descripción directamente.
            texttemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}",
            hovertemplate=(
                "<b>%{label}</b><br>" 
                "Costo: %{value:,.2f}"
                "<extra></extra>" 
            )
        )


        fig.update_layout(
            height=750,
            coloraxis_showscale=False,
            margin=dict(t=50, l=25, r=25, b=25),
            coloraxis_colorbar_title_text='Importancia (%)'
        )
        
        st.plotly_chart(fig, use_container_width=True)


    def render_sunburst_chart(self):
        """Prepara datos y renderiza el gráfico sunburst."""

        df_plot = self.df.copy()
        df_plot['parent_id'] = df_plot['ID_Jerarquico'].str.rpartition('.')[0]

        df_plot['Importancia_Color'] = df_plot['Importancia (%)'].replace(0, 0.01)

        fig = px.sunburst(
            df_plot,
            ids='ID_Jerarquico',
            parents='parent_id',
            values='Costo_Total',
            color='Importancia_Color',
            hover_name='Descripcion',
            color_continuous_scale=self.COLOR_SCALE_SEQUENTIAL, # Una escala de color que va bien con importancia
            branchvalues='total'
        )
        
        ## 3. Asignar la columna 'Descripcion' como las etiquetas visibles.
        fig.update_traces(labels=df_plot['Descripcion'])
        
        ## 4. Configurar el hover y el texto interno.
        fig.update_traces(
            textinfo="label+percent parent",
            textfont_size=16,
            hovertemplate=(
                "<b>%{label}</b><br><br>"
                "Costo total: $%{value:,.2f}<br>"
                "Participacion del total: %{color:.2f}%<br>"
                "Participación del nivel superior: %{percentParent:.2%}<extra></extra>"
            ),
            customdata=None,
            maxdepth=3,
            insidetextorientation='radial',
            marker_line_width=1.5,
            marker_line_color='white'
        )
        
        fig.update_layout(
            height=1000,
            uniformtext_minsize=8,

            margin=dict(t=50, l=25, r=25, b=25),

            ## 3. Activar la escala logarítmica en el eje de color.
            coloraxis_autocolorscale=False,

            ## 4. (Opcional) Personalizar la barra de color.
            coloraxis_colorbar={
                'title': 'Participación (%)', # Título de la barra
                'len': 0.75, # Longitud de la barra (75% de la altura)
                'y': 0.5, # Posición vertical (centrada)
                'tickvals': [1, 5, 10, 25, 50, 100], # Marcas que quieres mostrar
                'ticktext': ['1%', '5%', '10%', '25%', '50%', '100%'] # Etiquetas para esas marcas
            }
        )
        
        st.plotly_chart(fig, use_container_width=True)


    # --- MÉTODO PRINCIPAL PARA EL DASHBOARD ---

    def render_interactive_dashboard(self):
        """
        Renderiza el dashboard completo con sus widgets y gráficos.
        Reemplaza la función 'create_interactive_cost_analysis'.
        """
        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                theme.render_header("Costos por nivel jerarquico")

                max_level = int(self.df['ID_Jerarquico'].str.count('\\.').max()) + 1
                level_options = [f"Nivel {i}" for i in range(2, max_level + 1)]

                if level_options:
                    pills_nivel_key = f"pills_nivel_{self.key_prefix}"
                    # Inicializar el estado si no existe
                    if pills_nivel_key not in st.session_state:
                        st.session_state[pills_nivel_key] = level_options[0]

                    # Renderizar el widget. El argumento 'key' se encarga de la magia.
                    st.pills(
                        "Selecciona el nivel de la jerarquía:",
                        options=level_options,
                        key=pills_nivel_key,
                    )
                    
                    # Leer el valor directamente del estado (ahora es seguro)
                    selected_pill = st.session_state[pills_nivel_key]

                if selected_pill:
                    selected_level_int = int(selected_pill.split(" ")[1])
                    self.render_category_pie_chart(level=selected_level_int)
                else:
                    st.info("Por favor, selecciona un nivel para visualizar el gráfico.")
        
        with col2:
            with st.container(border=True):
                theme.render_header("Conceptos más costosos")

                pills_level_2_key = f"pills_level_2_{self.key_prefix}"
                pills_top_n_key = f"pills_top_n_{self.key_prefix}"

                ## 1. Obtener dinámicamente las categorías de Nivel 2 para las Pills
                level_2_nodes = self.df[self.df['Nivel'] == 2]
                level_2_map = dict(zip(level_2_nodes['Descripcion'], level_2_nodes['ID_Jerarquico']))
                level_2_options = ["Todos"] + list(level_2_map.keys())

                # Inicializar el estado si no existe
                if pills_level_2_key not in st.session_state:
                    st.session_state[pills_level_2_key] = level_2_options[0] 

                st.pills(
                    "Filtrar por Categoría de Nivel 2:",
                    options=level_2_options,
                    key=pills_level_2_key
                )

                selected_category_desc = st.session_state[pills_level_2_key]

                ## 2. Widget para el Top N (el que ya tenías)
                pill_options = ["Top 10", "Top 15", "Top 20", "Top 25"]
                
                # Inicializar el estado si no existe
                if pills_top_n_key not in st.session_state:
                    st.session_state[pills_top_n_key] = pill_options[1] # "Top 15"
    
                st.pills(
                    "Número de elementos a mostrar:",
                    options=pill_options,
                    key=pills_top_n_key
                )

                selected_pill_top_n = st.session_state[pills_top_n_key]

                # 3. Comprobar si AMBAS selecciones existen
                if selected_category_desc and selected_pill_top_n:
                    category_prefix = None
                    if selected_category_desc != "Todos":
                        category_prefix = level_2_map[selected_category_desc]    
                    top_n = int(selected_pill_top_n.split(" ")[1])

                    self.render_treemap(top_n=top_n, category_prefix=category_prefix)
                else:
                    st.info("Por favor, selecciona una categoría y un número de elementos para continuar")


        with st.container(border=True):
            theme.render_header("Jerarquía de costos")
            self.render_sunburst_chart()

