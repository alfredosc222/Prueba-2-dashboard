import pandas as pd

def preparar_datos_treemap(df):
    """
    Transforma un DataFrame jerárquico de AgGrid a un formato
    compatible con el treemap de Plotly.
    """
    # Esta es una función de ejemplo. La lógica real dependerá de cómo
    # AgGrid devuelve los datos jerárquicos. Por ahora, asumiremos
    # que podemos aplanarlo en una lista de padres, hijos y valores.
    
    # Lógica para aplanar la jerarquía (esto es un placeholder)
    ids = ["Costo Total", "Costos Directos", "Costos Indirectos", "Equipos", "Gestión"]
    labels = ["Costo Total", "Costos Directos", "Costos Indirectos", "Equipos", "Gestión"]
    parents = ["", "Costo Total", "Costo Total", "Costos Directos", "Costos Indirectos"]
    values = [df['Valor'].sum(), 
              df[df['Categoria'] == 'Directo']['Valor'].sum(),
              df[df['Categoria'] == 'Indirecto']['Valor'].sum(),
              500000, # Ejemplo
              150000] # Ejemplo

    return ids, labels, parents, values