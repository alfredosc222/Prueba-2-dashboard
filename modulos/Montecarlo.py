import streamlit as st
import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class SimuladorBetaDesapalancadaMejorado:
    """
    Simulador avanzado para proyección de beta desapalancada usando Monte Carlo
    con reversión a la media y múltiples mejoras metodológicas.
    """

    def __init__(self, df_historico, col_name, anos_proyeccion, num_simulaciones, 
                 params_convergencia, beta_sectorial=None, configuracion_avanzada=None):
        self.df_historico = df_historico
        self.col_name = col_name
        self.anos_proyeccion = anos_proyeccion
        self.num_simulaciones = num_simulaciones
        self.params = params_convergencia
        self.beta_sectorial = beta_sectorial  # MEJORA 1: Beta sectorial como referencia
        self.config_avanzada = configuracion_avanzada or {}
        np.random.seed(42)
        
        # MEJORA 4: Validación con datos históricos
        self.validacion_resultados = {}

    def _calcular_parametros_historicos(self):
        """Calcula parámetros históricos con análisis de estacionariedad."""
        serie = self.df_historico[self.col_name]
        
        # Parámetros básicos
        self.volatilidad_hist = serie.diff().std()
        self.ultimo_valor_hist = serie.iloc[-1]
        self.ultimo_ano_hist = int(serie.index[-1])
        self.media_historica = serie.mean()
        
        # MEJORA 4: Test de estacionariedad
        print("\n--- VALIDACIÓN ESTADÍSTICA ---")
        try:
            adf_result = adfuller(serie.dropna())
            self.validacion_resultados['adf_pvalue'] = adf_result[1]
            self.validacion_resultados['es_estacionaria'] = adf_result[1] < 0.05
            print(f"Test ADF p-value: {adf_result[1]:.4f}")
            print(f"Serie {'ES' if self.validacion_resultados['es_estacionaria'] else 'NO ES'} estacionaria")
        except Exception as e:
            print(f"Warning: No se pudo realizar test ADF: {e}")
            self.validacion_resultados['es_estacionaria'] = None
        
        # MEJORA 4: Calcular velocidad de reversión empírica (half-life)
        self._calcular_half_life_empirico(serie)

    def _calcular_half_life_empirico(self, serie):
        """
        MEJORA 4: Calcula la velocidad de reversión empírica usando half-life.
        Half-life = ln(2) / velocidad_reversion
        """
        try:
            # Calcular desviaciones de la media
            desviaciones = serie - serie.mean()
            desviaciones_lag = desviaciones.shift(1)
            
            # Regresión AR(1): y_t = α + β*y_{t-1} + ε_t
            mask = ~(desviaciones.isna() | desviaciones_lag.isna())
            if mask.sum() > 10:  # Suficientes observaciones
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    desviaciones_lag[mask], desviaciones[mask]
                )
                
                # Velocidad de reversión = -ln(β) si β < 1
                if 0 < slope < 1:
                    velocidad_empirica = -np.log(slope)
                    half_life_meses = np.log(2) / velocidad_empirica if velocidad_empirica > 0 else np.inf
                    
                    self.validacion_resultados['velocidad_empirica'] = velocidad_empirica
                    self.validacion_resultados['half_life_meses'] = half_life_meses
                    self.validacion_resultados['r_squared'] = r_value**2
                    
                    print(f"Velocidad de reversión empírica: {velocidad_empirica:.4f}")
                    print(f"Half-life empírico: {half_life_meses:.1f} períodos")
                    print(f"R-squared del modelo AR(1): {r_value**2:.4f}")
                else:
                    print("Warning: No se detectó reversión a la media clara")
                    self.validacion_resultados['velocidad_empirica'] = None
        except Exception as e:
            print(f"Warning: No se pudo calcular half-life empírico: {e}")

    def _calcular_meta_reversion(self, escenario):
        """
        MEJORA 2: Incorpora factores sectoriales en la meta de reversión.
        Combina beta sectorial con reversión hacia 1.0
        """
        meta_base = self.params[f'meta_{escenario}']
        
        if self.beta_sectorial is not None:
            # Peso para beta sectorial vs reversión hacia 1.0
            peso_sectorial = self.config_avanzada.get('peso_sectorial', 0.7)
            peso_mercado = 1 - peso_sectorial
            
            # Meta combinada: peso*beta_sectorial + (1-peso)*1.0
            meta_sectorial = self.beta_sectorial * peso_sectorial + 1.0 * peso_mercado
            
            # Ajustar según escenario
            if escenario == 'positivo':
                meta_final = meta_sectorial * 0.9  # Beta más conservadora
            elif escenario == 'negativo':
                meta_final = meta_sectorial * 1.1  # Beta más agresiva
            else:
                meta_final = meta_sectorial
                
            print(f"Meta {escenario}: {meta_final:.3f} (sectorial: {self.beta_sectorial:.3f}, peso: {peso_sectorial:.1f})")
            return meta_final
        else:
            return meta_base

    def _calcular_velocidad_adaptativa(self, beta_actual, tiempo, escenario):
        """
        MEJORA 1: Velocidad de reversión adaptativa basada en:
        - Distancia de la meta de reversión
        - Tiempo transcurrido
        - Régimen de mercado (si disponible)
        """
        velocidad_base = self.params[f'velocidad_{escenario}']
        meta_reversion = self._calcular_meta_reversion(escenario)
        
        # Factor 1: Distancia de la meta (mayor distancia = mayor velocidad)
        distancia_normalizada = abs(beta_actual - meta_reversion) / max(0.5, abs(meta_reversion))
        factor_distancia = 1 + distancia_normalizada * self.config_avanzada.get('sensibilidad_distancia', 0.3)
        
        # Factor 2: Tiempo (la reversión puede acelerarse con el tiempo)
        factor_temporal = 1 + (tiempo / self.anos_proyeccion) * self.config_avanzada.get('aceleracion_temporal', 0.1)
        
        # Factor 3: Régimen de mercado (si se proporciona volatilidad de mercado)
        factor_regimen = 1.0
        if 'volatilidad_mercado' in self.config_avanzada:
            vol_mercado = self.config_avanzada['volatilidad_mercado']
            vol_threshold = self.config_avanzada.get('threshold_volatilidad', 0.25)
            if vol_mercado > vol_threshold:
                # En alta volatilidad, la reversión es más rápida
                factor_regimen = self.config_avanzada.get('factor_crisis', 1.5)
        
        velocidad_final = velocidad_base * factor_distancia * factor_temporal * factor_regimen
        
        return min(velocidad_final, 1.0)  # Limitar velocidad máxima

    def _aplicar_modelo_bayesiano(self, beta_proyectada, escenario):
        """
        MEJORA 5: Modelo Bayesiano para combinar información previa
        (beta sectorial) con proyecciones del modelo.
        """
        if self.beta_sectorial is None:
            return beta_proyectada
        
        # Confianzas (pueden ser parámetros configurables)
        confianza_sectorial = self.config_avanzada.get('confianza_sectorial', 0.3)
        confianza_modelo = self.config_avanzada.get('confianza_modelo', 0.7)
        
        # Ajustar beta sectorial según escenario
        if escenario == 'positivo':
            beta_sectorial_ajustada = self.beta_sectorial * 0.95
        elif escenario == 'negativo':
            beta_sectorial_ajustada = self.beta_sectorial * 1.05
        else:
            beta_sectorial_ajustada = self.beta_sectorial
        
        # Combinación bayesiana
        beta_posterior = (confianza_sectorial * beta_sectorial_ajustada + 
                         confianza_modelo * beta_proyectada) / (confianza_sectorial + confianza_modelo)
        
        return beta_posterior

    def _generar_ciclo_economico(self):
        """
        MEJORA 5: Genera un ciclo económico simulado para ajustar las proyecciones.
        """
        if not self.config_avanzada.get('incluir_ciclo_economico', False):
            return np.ones(self.anos_proyeccion)  # Sin efecto cíclico
        
        # Ciclo económico simplificado (onda sinusoidal con ruido)
        periodo_ciclo = self.config_avanzada.get('periodo_ciclo_anos', 7)  # Ciclo de 7 años
        amplitud = self.config_avanzada.get('amplitud_ciclo', 0.15)  # ±15% de variación
        
        tiempo = np.linspace(0, self.anos_proyeccion, self.anos_proyeccion)
        ciclo_base = np.sin(2 * np.pi * tiempo / periodo_ciclo)
        ruido_ciclo = np.random.normal(0, 0.05, self.anos_proyeccion)  # 5% de ruido
        
        factor_ciclico = 1 + amplitud * (ciclo_base + ruido_ciclo)
        
        return np.clip(factor_ciclico, 0.7, 1.3)  # Limitar el rango

    def ejecutar_simulacion(self):
        """Ejecuta la simulación mejorada con todas las mejoras implementadas."""
        print("\n=== INICIANDO SIMULACIÓN BETA DESAPALANCADA MEJORADA ===")
        
        self._calcular_parametros_historicos()
        
        # MEJORA 5: Generar ciclo económico
        factor_ciclo_economico = self._generar_ciclo_economico()
        
        simulaciones = {
            "base": np.zeros((self.anos_proyeccion, self.num_simulaciones)),
            "positivo": np.zeros((self.anos_proyeccion, self.num_simulaciones)),
            "negativo": np.zeros((self.anos_proyeccion, self.num_simulaciones))
        }
        
        print(f"\n--- EJECUTANDO {self.num_simulaciones} SIMULACIONES ---")
        
        for i in range(self.anos_proyeccion):
            for escenario in ["base", "positivo", "negativo"]:
                # Valores del período anterior
                if i > 0:
                    valores_anteriores = simulaciones[escenario][i-1, :]
                else:
                    valores_anteriores = np.full(self.num_simulaciones, self.ultimo_valor_hist)
                
                # MEJORA 1: Velocidad adaptativa para cada simulación
                velocidades = np.array([
                    self._calcular_velocidad_adaptativa(val, i, escenario) 
                    for val in valores_anteriores
                ])
                
                # MEJORA 2: Meta de reversión con factores sectoriales
                meta_reversion = self._calcular_meta_reversion(escenario)
                
                # MEJORA 5: Ajuste por ciclo económico
                factor_ciclo = factor_ciclo_economico[i]
                meta_ajustada = meta_reversion * factor_ciclo
                
                # Shock estocástico
                shock = np.random.normal(0, self.volatilidad_hist, self.num_simulaciones)
                
                # Proceso de reversión mejorado
                betas_proyectadas = (valores_anteriores + 
                                   velocidades * (meta_ajustada - valores_anteriores) + 
                                   shock)
                
                # MEJORA 5: Aplicar modelo Bayesiano
                if self.config_avanzada.get('usar_bayesiano', True):
                    betas_finales = np.array([
                        self._aplicar_modelo_bayesiano(beta, escenario) 
                        for beta in betas_proyectadas
                    ])
                else:
                    betas_finales = betas_proyectadas
                
                # Constraints realistas para beta
                betas_finales = np.clip(betas_finales, 0.1, 3.0)
                simulaciones[escenario][i, :] = betas_finales

        # Generar años futuros
        anos_futuros = range(self.ultimo_ano_hist + 1, self.ultimo_ano_hist + 1 + self.anos_proyeccion)
        
        # Procesar resultados
        resultados = {"historico": self.df_historico[self.col_name]}

        for escenario in ["base", "positivo", "negativo"]:
            # Usar mediana para mayor robustez
            mediana = np.median(simulaciones[escenario], axis=1)
            resultados[escenario] = pd.Series(mediana, index=anos_futuros)
      
        # Calcular estadísticas
        resultados["promedios"] = {
            "Historico": resultados["historico"].mean(),
            **{nombre.capitalize(): serie.mean() for nombre, serie in resultados.items() if nombre != "historico"}
        }   

        resultados['anos_proyectados'] = self.anos_proyeccion
        resultados["ultimo_valor_hist"] = self.ultimo_valor_hist
        resultados["volatilidad_hist"] = self.volatilidad_hist
        
        # MEJORA 4: Incluir resultados de validación
        resultados["validacion_estadistica"] = self.validacion_resultados
        
        # Estadísticas de simulación final
        valores_finales_base = simulaciones["base"][-1, :]
        resultados["valores_finales"] = pd.Series(valores_finales_base)
        resultados["percentiles"] = resultados["valores_finales"].quantile([0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95])
        
        # Información de configuración
        resultados["beta_sectorial_usada"] = self.beta_sectorial
        resultados["configuracion_avanzada"] = self.config_avanzada
        
        print(f"\n✅ SIMULACIÓN COMPLETADA")
        print(f"Beta final promedio (escenario base): {resultados['base'].iloc[-1]:.3f}")
        if self.beta_sectorial:
            print(f"Beta sectorial de referencia: {self.beta_sectorial:.3f}")
        
        return resultados


@st.cache_data
def ejecutar_simulacion_beta_mejorada(df_historico, col_name, anos_proyeccion, num_simulaciones, 
                                    params_convergencia, beta_sectorial=None, configuracion_avanzada=None):
    """
    Función wrapper cacheada para la simulación mejorada de beta desapalancada.
    
    Parámetros adicionales:
    - beta_sectorial: Beta sectorial de Damodaran como referencia (opcional)
    - configuracion_avanzada: Diccionario con configuraciones adicionales
    
    Configuración avanzada puede incluir:
    {
        'peso_sectorial': 0.7,  # Peso de beta sectorial vs reversión a 1.0
        'sensibilidad_distancia': 0.3,  # Factor de velocidad por distancia
        'aceleracion_temporal': 0.1,  # Factor de aceleración temporal
        'volatilidad_mercado': 0.25,  # Volatilidad actual del mercado
        'threshold_volatilidad': 0.25,  # Umbral para régimen de crisis
        'factor_crisis': 1.5,  # Factor de velocidad en crisis
        'confianza_sectorial': 0.3,  # Peso del prior sectorial en Bayesiano
        'confianza_modelo': 0.7,  # Peso del modelo en Bayesiano
        'incluir_ciclo_economico': True,  # Incluir efectos cíclicos
        'periodo_ciclo_anos': 7,  # Duración del ciclo económico
        'amplitud_ciclo': 0.15,  # Amplitud del ciclo (±15%)
        'usar_bayesiano': True  # Aplicar ajuste Bayesiano
    }
    """
    print("--- EJECUTANDO SIMULACIÓN BETA MEJORADA ---")
    
    # Crear instancia del simulador mejorado
    simulador = SimuladorBetaDesapalancadaMejorado(
        df_historico=df_historico,
        col_name=col_name,
        anos_proyeccion=anos_proyeccion,
        num_simulaciones=num_simulaciones,
        params_convergencia=params_convergencia,
        beta_sectorial=beta_sectorial,
        configuracion_avanzada=configuracion_avanzada or {}
    )
    
    # Ejecutar simulación
    return simulador.ejecutar_simulacion()


# FUNCIÓN DE RETROCOMPATIBILIDAD
@st.cache_data
def ejecutar_simulacion_reversion_media_compatible(df_historico, col_name, anos_proyeccion, 
                                                  num_simulaciones, params_convergencia):
    """
    Función compatible con la interfaz original para transición gradual.
    Usa la clase original sin las mejoras avanzadas.
    """
    # Crear instancia de la clase original (retrocompatible)
    simulador = SimuladorReversionMediaOriginal(
        df_historico=df_historico,
        col_name=col_name,
        anos_proyeccion=anos_proyeccion,
        num_simulaciones=num_simulaciones,
        params_convergencia=params_convergencia
    )
    return simulador.ejecutar_simulacion()


class SimuladorReversionMediaOriginal:
    """Clase original sin mejoras para retrocompatibilidad."""
    
    def __init__(self, df_historico, col_name, anos_proyeccion, num_simulaciones, params_convergencia):
        self.df_historico = df_historico
        self.col_name = col_name
        self.anos_proyeccion = anos_proyeccion
        self.num_simulaciones = num_simulaciones
        self.params = params_convergencia
        np.random.seed(42)

    def _calcular_parametros_historicos(self):
        self.volatilidad_hist = self.df_historico[self.col_name].diff().std()
        self.ultimo_valor_hist = self.df_historico[self.col_name].iloc[-1]
        self.ultimo_ano_hist = int(self.df_historico.index[-1])

    def ejecutar_simulacion(self):
        self._calcular_parametros_historicos()
        
        simulaciones = {
            "base": np.zeros((self.anos_proyeccion, self.num_simulaciones)),
            "positivo": np.zeros((self.anos_proyeccion, self.num_simulaciones)),
            "negativo": np.zeros((self.anos_proyeccion, self.num_simulaciones))
        }
        
        metas = {
            "base": self.params['meta_base'],
            "positivo": self.params['meta_positiva'],
            "negativo": self.params['meta_negativa']
        }

        velocidad = {
            "base": self.params['velocidad_base'],
            "positivo": self.params['velocidad_positiva'],
            "negativo": self.params['velocidad_negativa']
        }

        for i in range(self.anos_proyeccion):
            for escenario in ["base", "positivo", "negativo"]:
                valor_anterior = simulaciones[escenario][i-1, :] if i > 0 else self.ultimo_valor_hist
                shock = np.random.normal(0, self.volatilidad_hist, self.num_simulaciones)
                
                simulaciones[escenario][i, :] = valor_anterior + velocidad[escenario] * (metas[escenario] - valor_anterior) + shock

        anos_futuros = range(self.ultimo_ano_hist + 1, self.ultimo_ano_hist + 1 + self.anos_proyeccion)
        
        resultados = {"historico": self.df_historico[self.col_name]}

        for escenario in ["base", "positivo", "negativo"]:
            mediana = np.median(simulaciones[escenario], axis=1)
            resultados[escenario] = pd.Series(mediana, index=anos_futuros)
      
        resultados["promedios"] = {
            "Historico": resultados["historico"].mean(),
            **{nombre.capitalize(): serie.mean() for nombre, serie in resultados.items() if nombre != "historico"}
        }   

        resultados['anos_proyectados'] = self.anos_proyeccion
        resultados["ultimo_valor_hist"] = self.ultimo_valor_hist
        resultados["volatilidad_hist"] = self.volatilidad_hist
        resultados["valores_finales"] = pd.Series(simulaciones["base"][-1, :])
        resultados["percentiles"] = resultados["valores_finales"].quantile([0.10, 0.25, 0.50, 0.75, 0.90])

        return resultados

