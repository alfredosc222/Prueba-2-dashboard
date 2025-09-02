# analisis_sp500.py

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

@st.cache_data
def generar_proyeccion_sp500(ticker, start_date, anos_proyeccion, num_simulaciones):
    """
    Ejecuta la simulación de Monte Carlo para un ticker y devuelve un diccionario con los resultados.
    """
    print(f"--- EJECUTANDO CÁLCULO PESADO: SIMULACIÓN MONTE CARLO ---")
    
    # --- 1. Carga de Datos y Cálculo de Parámetros ---
    try:
        sp500_data = yf.download(ticker, start=start_date, auto_adjust=True)
        if sp500_data.empty:
            st.error("No se pudieron descargar los datos.")
            return None
        precios = sp500_data['Close'].dropna()
        if isinstance(precios, pd.DataFrame):
            precios = precios.iloc[:, 0]
        rendimientos_log = np.log(precios / precios.shift(1)).dropna()
        mu = rendimientos_log.mean()
        sigma = rendimientos_log.std()
    except Exception as e:
        st.error(f"Error en la carga de datos: {e}")
        return None

    # --- 2. Simulación de Monte Carlo ---
    np.random.seed(42)
    dias_proyeccion = anos_proyeccion * 252
    ultimo_precio = float(precios.iloc[-1])
    simulaciones = np.zeros((dias_proyeccion, num_simulaciones))

    for i in range(num_simulaciones):
        precio_actual = ultimo_precio
        for d in range(dias_proyeccion):
            shock = np.random.normal(0, 1)
            precio_actual *= np.exp((mu - 0.5 * sigma**2) + sigma * shock)
            simulaciones[d, i] = precio_actual
    
    idx_futuro = pd.bdate_range(start=precios.index[-1] + pd.Timedelta(days=1), periods=dias_proyeccion)
    df_simulaciones = pd.DataFrame(simulaciones, index=idx_futuro)

    # --- 3. Cálculo de Rendimientos Anuales y Promedios ---
    rendimiento_hist_anual = precios.resample('YE').last().pct_change().dropna() * 100

    escenario_base_precios = df_simulaciones.quantile(0.50, axis=1)
    escenario_pos_precios = df_simulaciones.quantile(0.95, axis=1)
    escenario_neg_precios = df_simulaciones.quantile(0.05, axis=1)
    
    punto_de_inicio = pd.Series(precios.iloc[-1], index=[precios.index[-1]])

    rendimiento_proy_base = pd.concat([punto_de_inicio, escenario_base_precios]).resample('YE').last().pct_change().dropna() * 100
    rendimiento_proy_pos = pd.concat([punto_de_inicio, escenario_pos_precios]).resample('YE').last().pct_change().dropna() * 100
    rendimiento_proy_neg = pd.concat([punto_de_inicio, escenario_neg_precios]).resample('YE').last().pct_change().dropna() * 100
    
    rendimiento_hist_anual.index = rendimiento_hist_anual.index.year
    rendimiento_proy_base.index = rendimiento_proy_base.index.year
    rendimiento_proy_pos.index = rendimiento_proy_pos.index.year
    rendimiento_proy_neg.index = rendimiento_proy_neg.index.year

    # Parámetros anualizados para diagnósticos
    mu_anualizado = mu * 252
    sigma_anualizado = sigma * np.sqrt(252)
    
    # Datos de distribución final
    precios_finales = df_simulaciones.iloc[-1]
    percentiles_finales = precios_finales.quantile([0.10, 0.25, 0.50, 0.75, 0.90])


    promedios = { "Historico": rendimiento_hist_anual.mean(),
                "Base": rendimiento_proy_base.mean(), 
                "Positivo": rendimiento_proy_pos.mean(), 
                "Negativo": rendimiento_proy_neg.mean() 
            }

    # --- 5. Empaquetar y Devolver Resultados ---
    resultados_sp = {
        "historico_anual": rendimiento_hist_anual,
        "anos_proyectados": anos_proyeccion,
        "base_anual": rendimiento_proy_base,
        "positivo_anual": rendimiento_proy_pos,
        "negativo_anual": rendimiento_proy_neg,
        "rendimientos_log_diarios": rendimientos_log,
        "mu_anualizado": mu_anualizado,
        "sigma_anualizado": sigma_anualizado,
        "precios_finales": precios_finales,
        "percentiles": percentiles_finales,
        "promedios": promedios
    }
    
    return resultados_sp