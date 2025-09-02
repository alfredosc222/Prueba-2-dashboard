import streamlit as st
import pandas as pd
import numpy as np
from fredapi import Fred
import requests
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.api import VAR, VECM
from statsmodels.tsa.vector_ar.vecm import coint_johansen


class ModelosEconometricos:
    def __init__(self, api_key, series_ids, processing_config, start_date, anos_proyeccion, 
                 variables_modelo, variable_objetivo, params_escenarios):
        self.api_key = api_key
        self.series_ids = series_ids
        self.processing_config = processing_config
        self.start_date = start_date
        self.anos_proyeccion = anos_proyeccion
        self.variables_modelo = variables_modelo
        self.variable_objetivo = variable_objetivo
        self.params_escenarios = params_escenarios
        self.df = None
        self.df_modelo = None
        self.resultados_modelo = None
        self.usar_vecm = False
        self.series_no_estacionarias = []

    def _obtener_serie_banxico(self, id_serie):
        token = self.api_key.get('banxico')
        if not token:
            st.error("Token de Banxico no proporcionado.")
            return None

        fecha_fin = pd.Timestamp.now().strftime('%Y-%m-%d')
        url = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{id_serie}/datos/{self.start_date}/{fecha_fin}"
        headers = {"Bmx-Token": token}
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            serie_data = data['bmx']['series'][0]['datos']

            df_temp = pd.DataFrame(serie_data)
            df_temp['fecha'] = pd.to_datetime(df_temp['fecha'], format='%d/%m/%Y')
            df_temp.set_index('fecha', inplace=True)
            df_temp['dato'] = pd.to_numeric(df_temp['dato'], errors='coerce')
            return df_temp['dato']
        except Exception as e:
            st.error(f"Error al obtener la serie {id_serie} de Banxico: {e}")
            return None

    def _obtener_serie_fred(self, id_serie):
        api_key = self.api_key.get('fred')
        if not api_key:
            st.error("Clave de API de FRED no proporcionada.")
            return None

        try:
            fred = Fred(api_key=api_key)
            return fred.get_series(id_serie, observation_start=self.start_date)
        except Exception as e:
            st.error(f"Error al obtener la serie '{id_serie}' de FRED: {e}")
            return None

    def _cargar_y_procesar_datos(self):
        if 'banxico' in self.api_key and len(self.api_key['banxico']) == 64:
            print("Detectada API de Banxico. Descargando datos...")
            series_cargadas = {nombre: self._obtener_serie_banxico(id_serie) 
                             for nombre, id_serie in self.series_ids.items()}
        else:
            print("Detectada API de FRED. Descargando datos...")
            series_cargadas = {nombre: self._obtener_serie_fred(id_serie) 
                             for nombre, id_serie in self.series_ids.items()}

        if not all(serie is not None for serie in series_cargadas.values()):
            return 

        df_raw = pd.concat(series_cargadas.values(), axis=1, keys=series_cargadas.keys())
        df_raw.ffill(inplace=True)
        df_mensual = df_raw.resample('MS').mean()

        if (df_mensual.index[-1].month == pd.Timestamp.now().month and 
            df_mensual.index[-1].year == pd.Timestamp.now().year):
            df_mensual = df_mensual.iloc[:-1]

        df_final = pd.DataFrame(index=df_mensual.index)
        
        for nombre_final, config in self.processing_config.items():
            tipo = config['type']
            
            if tipo == 'yoy_pct_change_calculated':
                source_col = config['source_col']
                df_final[nombre_final] = (df_mensual[source_col] / df_mensual[source_col].shift(12) - 1) * 100
            
            elif tipo == 'log':
                source_col = config['source_col']
                df_final[nombre_final] = np.log(df_mensual[source_col])
            
            elif tipo == 'spread':
                col1, col2 = config['source_cols']
                df_final[nombre_final] = df_mensual[col1] - df_mensual[col2]
            
            elif tipo == 'level':
                source_col = config['source_col']
                df_final[nombre_final] = df_mensual[source_col]

        df_final.replace([np.inf, -np.inf], np.nan, inplace=True)
        df_final.dropna(inplace=True)
        self.df = df_final
        print("✅ Datos históricos obtenidos y procesados.")

    def _seleccionar_y_entrenar(self):
        """Realiza las pruebas estadísticas y entrena el modelo."""
        try:
            # 1. Definir el conjunto COMPLETO de variables para el análisis
            variables_del_modelo_final = self.variables_modelo.copy()
            
            if self.variable_objetivo not in variables_del_modelo_final:
                variables_del_modelo_final.insert(0, self.variable_objetivo)

            df_para_analisis = self.df[variables_del_modelo_final]


            # 2. Identificar el tipo de variable objetivo
            self.series_no_estacionarias = []

            # Excluir variable objetivo si es YoY calculada
            config_objetivo = self.processing_config.get(self.variable_objetivo, {})
            variables_para_pruebas = variables_del_modelo_final.copy()

            if config_objetivo.get('type') == 'yoy_pct_change_calculated':
                variables_para_pruebas.remove(self.variable_objetivo)
                print(f"🎯 Variable objetivo '{self.variable_objetivo}' es YoY calculada - EXCLUIDA de pruebas ADF")

            for col in variables_para_pruebas:
                adf_result = adfuller(df_para_analisis[col].dropna())
                p_value = adf_result[1]
                if p_value >= 0.05:
                    self.series_no_estacionarias.append(col)
                print(f"Prueba ADF para {col}: p-value = {p_value:.4f}, {'No estacionaria' if p_value >= 0.05 else 'Estacionaria'}")
            

            # 3. Lógica de cointegración
            if len(self.series_no_estacionarias) >= 2:
                df_coint_test = df_para_analisis[self.series_no_estacionarias]
                johansen_test = coint_johansen(df_coint_test, 0, 1)
                num_rel_coint = sum(johansen_test.lr1 > johansen_test.cvt[:, 1])
            else:
                num_rel_coint = 0

            self.num_relaciones_coint = num_rel_coint
            self.usar_vecm = num_rel_coint > 0
            self.inflacion_como_exogena = False

            # 5. Preparar DataFrame para modelo
            self.df_modelo = df_para_analisis.copy()

            # 4. Diferenciación - NUNCA diferenciar YoY calculadas
            if not self.usar_vecm:
                for col in self.series_no_estacionarias:
                    config_col = None
                    for nombre, conf in self.processing_config.items():
                        if nombre == col:
                            config_col = conf
                            break
                    
                    # NUNCA diferenciar variables YoY calculadas
                    if config_col and config_col.get('type') == 'yoy_pct_change_calculated':
                        print(f"⚠️  SALTANDO diferenciación de {col} (es YoY calculada)")
                        continue
                    
                    self.df_modelo[col] = self.df_modelo[col].diff()
                    print(f"Serie {col} diferenciada para modelo VAR")
     
            self.df_modelo.dropna(inplace=True)
            
            # 5. Entrenar modelo
            if self.usar_vecm:
                var_temp = VAR(self.df_modelo)
                lag_order = var_temp.select_order(maxlags=min(12, len(self.df_modelo)//4))
                p_optimo = lag_order.aic
                
                self.resultados_modelo = VECM(
                    self.df_modelo, 
                    k_ar_diff=max(1, p_optimo-1), 
                    coint_rank=self.num_relaciones_coint, 
                    deterministic='ci'
                ).fit()
                print("✅ Modelo VECM entrenado exitosamente.")
                
            else:
                var_model = VAR(self.df_modelo)
                lag_order = var_model.select_order(maxlags=min(12, len(self.df_modelo)//4))
                p_optimo = lag_order.aic
                self.resultados_modelo = var_model.fit(maxlags=p_optimo, ic='aic')
                print(f"✅ Modelo VAR entrenado exitosamente con {p_optimo} rezagos.")

        except Exception as e:
            print(f"❌ Error durante el entrenamiento del modelo: {e}")
            self.resultados_modelo = None

    def ejecutar_proyeccion(self):
        """Ejecuta la proyección completa sin decoradores problemáticos."""
        
        # 1. Cargar y procesar datos
        self._cargar_y_procesar_datos()
        if self.df is None or self.df.empty:
            st.error("Falló la carga de datos. No se puede continuar.")
            return None

        # 2. Entrenar modelo
        self._seleccionar_y_entrenar()
        if self.resultados_modelo is None:
            st.error("Falló el entrenamiento del modelo. No se puede continuar.")
            return None

        n_periodos = self.anos_proyeccion * 12

        # 3. Generar proyecciones
        try:
            if self.usar_vecm:
                punto_proy, lim_inf, lim_sup = self.resultados_modelo.predict(steps=n_periodos, alpha=0.05)
            else:
                y_input = self.df_modelo.values[-self.resultados_modelo.k_ar:]
                punto_proy, lim_inf, lim_sup = self.resultados_modelo.forecast_interval(
                    y=y_input, steps=n_periodos, alpha=0.05)

            fechas_futuras = pd.date_range(
                start=self.df.index[-1] + pd.DateOffset(months=1), 
                periods=n_periodos, freq="MS")
            
            df_proy_base = pd.DataFrame(punto_proy, index=fechas_futuras, columns=self.df_modelo.columns)
            df_proy_bajas = pd.DataFrame(lim_inf, index=fechas_futuras, columns=self.df_modelo.columns)
            df_proy_altas = pd.DataFrame(lim_sup, index=fechas_futuras, columns=self.df_modelo.columns)
            
            # CORRECCIÓN: Reconstruir niveles solo si la variable objetivo fue diferenciada

            
            if not self.usar_vecm and self.variable_objetivo in self.series_no_estacionarias:
                # Verificar el tipo de variable objetivo
                config_objetivo = self.processing_config.get(self.variable_objetivo, {})
                tipo_objetivo = config_objetivo.get('type')
                
                if tipo_objetivo == 'yoy_pct_change_calculated':
                    print("Reconstruyendo niveles para YoY calculada...")
                    
                    # Para YoY calculada, la reconstrucción es más compleja
                    # Las diferencias proyectadas representan cambios en la tasa YoY, no en niveles
                    ultimo_yoy = self.df[self.variable_objetivo].iloc[-1]
                    
                    idx_objetivo = self.df_modelo.columns.get_loc(self.variable_objetivo)
                    
                    # Las proyecciones son cambios en la tasa YoY
                    # Reconstruir: YoY_proyectada = YoY_anterior + cambio_proyectado
                    df_proy_base.iloc[:, idx_objetivo] = ultimo_yoy + df_proy_base.iloc[:, idx_objetivo].cumsum()
                    df_proy_bajas.iloc[:, idx_objetivo] = ultimo_yoy + df_proy_bajas.iloc[:, idx_objetivo].cumsum()
                    df_proy_altas.iloc[:, idx_objetivo] = ultimo_yoy + df_proy_altas.iloc[:, idx_objetivo].cumsum()
                    
                elif tipo_objetivo == 'yoy_pct_change_official':
                    print("Reconstruyendo niveles para inflación oficial diferenciada...")
                    
                    # Similar al caso anterior
                    ultimo_valor = self.df[self.variable_objetivo].iloc[-1]
                    idx_objetivo = self.df_modelo.columns.get_loc(self.variable_objetivo)
                    
                    df_proy_base.iloc[:, idx_objetivo] = ultimo_valor + df_proy_base.iloc[:, idx_objetivo].cumsum()
                    df_proy_bajas.iloc[:, idx_objetivo] = ultimo_valor + df_proy_bajas.iloc[:, idx_objetivo].cumsum()
                    df_proy_altas.iloc[:, idx_objetivo] = ultimo_valor + df_proy_altas.iloc[:, idx_objetivo].cumsum()
                
                else:
                    # Lógica original para otras variables
                    ultimo_nivel = self.df[self.variable_objetivo].iloc[-1]
                    idx_objetivo = self.df_modelo.columns.get_loc(self.variable_objetivo)
                    
                    df_proy_base.iloc[:, idx_objetivo] = ultimo_nivel + df_proy_base.iloc[:, idx_objetivo].cumsum()
                    df_proy_bajas.iloc[:, idx_objetivo] = ultimo_nivel + df_proy_bajas.iloc[:, idx_objetivo].cumsum()
                    df_proy_altas.iloc[:, idx_objetivo] = ultimo_nivel + df_proy_altas.iloc[:, idx_objetivo].cumsum()

            # Extraer proyecciones de la variable objetivo
            idx_objetivo = self.df_modelo.columns.get_loc(self.variable_objetivo)
            df_proy_nivel = pd.DataFrame({
                'objetivo': df_proy_base.iloc[:, idx_objetivo], 
                'lim_inf': df_proy_bajas.iloc[:, idx_objetivo],
                'lim_sup': df_proy_altas.iloc[:, idx_objetivo]
            })

        except Exception as e:
            st.error(f"Error en la generación de proyecciones: {e}")
            return None

        # 4. CORRECCIÓN: Crear escenarios de manera más coherente
        escenario_base = df_proy_nivel['objetivo'].copy()
        # CORRECCIÓN: Intercambio lógico - límite superior para escenario negativo (inflación alta)
        escenario_negativo = df_proy_nivel['lim_sup'].copy()  # Límite superior = escenario malo para inflación
        escenario_positivo = df_proy_nivel['lim_inf'].copy()  # Límite inferior = escenario bueno para inflación
        
        # Aplicar convergencia a metas de largo plazo
        anos_modelo = self.params_escenarios.get('anos_modelo', 2)
        if anos_modelo * 12 < len(escenario_base):
            fecha_transicion_idx = anos_modelo * 12
            
            escenarios_data = [
                (escenario_base, self.params_escenarios.get('meta_central', 3.0), 
                 self.params_escenarios.get('theta_central', 0.1)),
                (escenario_positivo, self.params_escenarios.get('meta_baja', 2.5), 
                 self.params_escenarios.get('theta_baja', 0.1)),
                (escenario_negativo, self.params_escenarios.get('meta_alta', 4.0), 
                 self.params_escenarios.get('theta_alta', 0.1))
            ]
            
            for escenario, meta, theta in escenarios_data:
                for i in range(fecha_transicion_idx, len(escenario)):
                    valor_previo = escenario.iloc[i-1] if i > 0 else escenario.iloc[0]
                    escenario.iloc[i] = valor_previo + theta * (meta - valor_previo)

        # 5. CORRECCIÓN: Análisis de residuos con formato unificado
        try:
            # Obtener residuos brutos del modelo (independientemente de si es VAR o VECM)
            residuos_brutos = self.resultados_modelo.resid
            
            # Crear índice correcto basado en la longitud de los residuos
            indice_correcto_residuos = self.df_modelo.index[-len(residuos_brutos):]
            
            # Crear DataFrame de residuos con todas las variables
            df_residuos = pd.DataFrame(residuos_brutos, 
                                    index=indice_correcto_residuos, 
                                    columns=self.df_modelo.columns)
            
            # Extraer residuos finales de la variable objetivo
            residuos_finales = df_residuos[self.variable_objetivo]
            
            print(f"✅ Residuos extraídos correctamente. Forma: {residuos_finales.shape}")
            
        except Exception as e:
            print(f"Warning: No se pudieron extraer residuos correctamente: {e}")
            # Crear una serie vacía como fallback
            residuos_finales = pd.Series(dtype=float, name=self.variable_objetivo)

        # 6. Preparación de resultados finales
        promedios = {
            "Base": escenario_base.mean(), 
            "Positivo": escenario_positivo.mean(), 
            "Negativo": escenario_negativo.mean()
        }
        
        tabla_escenarios = pd.DataFrame({
            'Promedio (%)': [promedios['Base'], promedios['Positivo'], promedios['Negativo']],
            'Volatilidad (Desv. Est.)': [escenario_base.std(), escenario_positivo.std(), escenario_negativo.std()],
            'Máximo (%)': [escenario_base.max(), escenario_positivo.max(), escenario_negativo.max()],
            'Mínimo (%)': [escenario_base.min(), escenario_positivo.min(), escenario_negativo.min()]
        }, index=['Base', 'Positivo', 'Negativo'])
        
        resultados = {
            "df_historico": self.df,
            "escenario_base": escenario_base,
            "escenario_positivo": escenario_positivo,
            "escenario_negativo": escenario_negativo,
            "promedios": promedios,
            "tabla_escenarios": tabla_escenarios,
            "modelo_usado": "VECM" if self.usar_vecm else "VAR",
            "anos_proyectados": self.anos_proyeccion,
            "series_no_estacionarias": self.series_no_estacionarias,
            "relaciones_coint": self.num_relaciones_coint,
            "resumen_texto": str(self.resultados_modelo.summary()),
            "residuos": residuos_finales  # Ahora usando el formato correcto
        }

        print(f"✅ Proyección completada. Modelo: {'VECM' if self.usar_vecm else 'VAR'}")
        return resultados


@st.cache_data
def generar_proyeccion_econometrica(api_key, series_ids, processing_config, start_date, 
                                  anos_proyeccion, variables_modelo, variable_objetivo, 
                                  params_escenarios):
    """
    Función wrapper para usar con st.cache_data.
    Esta función SÍ se puede cachear correctamente.
    """
    print("--- EJECUTANDO CÁLCULO ECONOMÉTRICO PESADO ---")
    
    # Crear instancia del modelo
    modelo = ModelosEconometricos(
        api_key=api_key,
        series_ids=series_ids,
        processing_config=processing_config,
        start_date=start_date,
        anos_proyeccion=anos_proyeccion,
        variables_modelo=variables_modelo,
        variable_objetivo=variable_objetivo,
        params_escenarios=params_escenarios,
    )
    
    # Ejecutar proyección
    return modelo.ejecutar_proyeccion()