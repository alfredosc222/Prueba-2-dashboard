import streamlit as st
import pandas as pd
from typing import Any
import numpy as np

# --- FUNCIÓN AUXILIAR PARA CREAR LA RUTA CORRECTA ---
def generar_ruta_desde_id(id_jerarquico: str) -> str:
    """
    Convierte un ID como '1.1.1' en una ruta jerárquica como '1/1.1/1.1.1'.
    """
    if not isinstance(id_jerarquico, str):
        return ""
    partes = id_jerarquico.split('.')
    rutas_acumuladas = ['.'.join(partes[:i + 1]) for i in range(len(partes))]
    return '/'.join(rutas_acumuladas)


@st.cache_data
def load_and_prepare_data(source: Any) -> pd.DataFrame:
    """Carga y prepara los datos desde un archivo local o uno subido por el usuario."""
    try:
        df = pd.read_excel(source)
    except Exception as e:
        st.error(f"❌ Error al leer el archivo: {e}")
        return pd.DataFrame()

    required_cols = ['ID_Jerarquico', 'Descripcion', 'Resumen', 'Costo']
    if not all(col in df.columns for col in required_cols):
        st.error(f"El archivo debe contener las columnas: {', '.join(required_cols)}")
        return pd.DataFrame()

    df['ID_Jerarquico'] = df['ID_Jerarquico'].astype(str)
    df['Costo'] = pd.to_numeric(df['Costo'], errors='coerce').fillna(0)
    
    # Creamos la ruta en el formato de texto correcto: 'Nivel1/Nivel2/...'
    df['ruta_jerarquica'] = df['ID_Jerarquico'].apply(generar_ruta_desde_id)
    
    df['Nivel'] = df['ID_Jerarquico'].str.count('\\.') + 1
    return df

## OPTIMIZACIÓN: PASO 2 - SE REEMPLAZA EL BUCLE .iterrows() POR OPERACIONES VECTORIZADAS.
## Esta versión es órdenes de magnitud más rápida en DataFrames grandes.
def calculate_aggregate_costs(df: pd.DataFrame) -> pd.DataFrame:
    """
    [VERSIÓN CORREGIDA Y DEFINITIVA]
    Calcula costos agregados de forma robusta, inspirada en la lógica original.
    Guarda los resultados en 'Costo_Total', preservando 'Costo' para los gráficos.
    """
    df_agg = df.copy()

    # 1. Crear la columna 'Costo_Total' que contendrá los valores acumulados.
    #    Se inicia con los costos originales de los nodos hoja.
    df_agg['Costo_Total'] = df_agg['Costo']

    # 2. Identificar los nodos que son padres y poner su 'Costo_Total' inicial a 0.
    all_parent_ids = set(
        id_str.rpartition('.')[0] for id_str in df_agg['ID_Jerarquico'] if '.' in id_str
    )
    is_parent = df_agg['ID_Jerarquico'].isin(all_parent_ids)
    df_agg.loc[is_parent, 'Costo_Total'] = 0

    # 3. Iterar por niveles, desde el más profundo hacia arriba, para acumular costos.
    for level in sorted(df_agg['Nivel'].unique(), reverse=True):
        if level <= 1:
            continue

        # Seleccionar los hijos del nivel actual
        children = df_agg[df_agg['Nivel'] == level].copy()
        
        # Encontrar el ID de su padre
        children['parent_id'] = children['ID_Jerarquico'].str.rpartition('.')[0]
        
        # Sumar los costos de los hijos, agrupando por padre.
        # Se usa 'Costo_Total' porque en niveles intermedios, ya contendrá sumas previas.
        summed_costs = children.groupby('parent_id')['Costo_Total'].sum()
        
        # 4. Mapear estas sumas a los padres en el DataFrame principal.
        update_map = df_agg['ID_Jerarquico'].map(summed_costs)

        # 5. Sumar los costos de los hijos al 'Costo_Total' de los padres.
        #    .add() es una operación segura. .fillna(0) evita errores con nodos que no son padres.
        df_agg['Costo_Total'] = df_agg['Costo_Total'].add(update_map.fillna(0))

    # 6. Asegurar que la columna 'Costo' original (usada por Plotly) tenga 0 en los padres.
    df_agg.loc[is_parent, 'Costo'] = 0
    
    # 7. Calcular la Importancia usando la columna final y correcta 'Costo_Total'.
    total_project_cost = df_agg.loc[df_agg['Nivel'] == 1, 'Costo_Total'].sum()

    if total_project_cost > 0:
        df_agg['Importancia (%)'] = (df_agg['Costo_Total'] / total_project_cost) * 100
    else:
        df_agg['Importancia (%)'] = 0
        
    return df_agg

## OPTIMIZACIÓN: PASO 1 - NUEVA FUNCIÓN "ORQUESTADORA" CON CACHÉ.
## Esta será la única función que llamaremos desde la página para obtener los datos procesados.
@st.cache_data
def get_processed_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Función principal que toma el df crudo, calcula los costos agregados y cachea el resultado.
    """
    if df.empty:
        return pd.DataFrame()
    
    # Llama a la función de cálculo optimizada.
    df_processed = calculate_aggregate_costs(df)
    return df_processed

def debug_cost_aggregation(df_aggregated: pd.DataFrame, num_checks: int = 5):
    """
    Función de depuración para verificar que los costos de los nodos padre
    corresponden a la suma de sus hijos directos.
    """
    with st.expander("🔬 Verificación de la Suma de Costos Jerárquicos"):
        st.info(f"Se seleccionarán hasta {num_checks} nodos 'padre' al azar para verificar que su costo sea igual a la suma de sus hijos directos.")

        # Identificar todos los IDs que son padres
        parent_ids = set(
            id_str.rpartition('.')[0] for id_str in df_aggregated['ID_Jerarquico'] if '.' in id_str
        )
        
        # Filtrar el DataFrame para obtener solo los nodos que son padres
        parent_nodes = df_aggregated[df_aggregated['ID_Jerarquico'].isin(parent_ids)]

        if parent_nodes.empty:
            st.warning("No se encontraron nodos padre en los datos para verificar.")
            return

        # Seleccionar una muestra aleatoria de padres para no saturar la pantalla
        num_to_sample = min(num_checks, len(parent_nodes))
        parents_to_check = parent_nodes.sample(num_to_sample, random_state=1)

        # Iterar sobre los padres seleccionados para verificarlos
        for _, parent_row in parents_to_check.iterrows():
            parent_id = parent_row['ID_Jerarquico']
            parent_cost_calculated = parent_row['Costo']
            
            st.markdown(f"--- \n#### Verificando Padre: `{parent_id}`")
            
            # Encontrar los hijos directos de este padre
            parent_level = parent_row['Nivel']
            direct_children = df_aggregated[
                df_aggregated['ID_Jerarquico'].str.startswith(parent_id + '.') &
                (df_aggregated['Nivel'] == parent_level + 1)
            ]

            if direct_children.empty:
                st.write("Este nodo no tiene hijos directos en el DataFrame.")
                continue

            # Sumar los costos de los hijos directos
            children_cost_sum = direct_children['Costo'].sum()

            # Mostrar los resultados de la verificación
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    label=f"Costo Calculado para '{parent_id}'",
                    value=f"${parent_cost_calculated:,.2f}"
                )
            with col2:
                st.metric(
                    label="Suma de Costos de Hijos Directos",
                    value=f"${children_cost_sum:,.2f}"
                )
            
            # Comparar y mostrar un mensaje de éxito o error
            if np.isclose(parent_cost_calculated, children_cost_sum):
                st.success(f"✅ ¡Correcto! El costo del padre coincide con la suma de sus hijos.")
            else:
                st.error(f"❌ ¡Error! El costo del padre NO coincide con la suma de sus hijos.")
                st.write("Hijos directos encontrados:")
                st.dataframe(direct_children[['ID_Jerarquico', 'Costo']])