import streamlit as st
import dill
from theme import theme



def render():
    theme.render_main_title("Descripción del proyecto", align="center")
    #theme.render_caption("Selecciona una opción en el menú de la barra lateral o si desea cargar/guardar un trabajo, porfavor use las opciones que se encuentran a la derecha.", align="center")
    
    # --- MOSTRAR MENSAJE GLOBAL DE SESIÓN (SI EXISTE) ---
    if 'mensaje_global' in st.session_state:
        st.success(st.session_state['mensaje_global'])
        del st.session_state['mensaje_global']
    
    st.write("")

    # --- LAYOUT DE DOS COLUMNAS ---
    col_info, col_sesion = st.columns([3, 1], gap="large")

    with col_info:
        theme.render_header("Herramienta Interactiva")
        st.markdown("""
        
        El propósito de esta herramienta es estructurar y evaluar la viabilidad financiera de proyectos undimotrices, aplicando un marco metodológico estandarizado, producto de la investigación académica del autor.

        Para ello, se realiza una evaluación financiera integral centrada en el cálculo del Costo Nivelado de la Energía Eléctrica (LCOE). El modelo se basa en proyecciones de variables macroeconómicas obtenidas de modelos estadísticos y econométricos, permitiendo al usuario definir parámetros clave del proyecto, como el horizonte de análisis. Adicionalmente, la plataforma incluye un análisis de sensibilidad para identificar los factores de mayor impacto en cada etapa del desarrollo del proyecto.
        
        La base central de esta herramienta es su análisis adaptativo, donde el Nivel de Madurez Tecnológica (TRL) actúa como eje para definir la metodología con la que se evaluará la tecnología. Partiendo de que una única fórmula de LCOE es insuficiente para las distintas fases de desarrollo, la plataforma aplica uno de los tres modelos específicos. A su vez, en la etapa avanzada (TRL 7-9), el análisis se complementa con la evaluación del Nivel de Rendimiento Tecnológico (TPL) para medir la competitividad y la preparación comercial, ofreciendo así una visión integral de la viabilidad del proyecto (TRL-TPL-LCOE).
        
        Los modelos propuestos son los siguientes:
        - **TRL 1-3 (Prototipo undimotriz)**: Estimación preliminar basada en costos de componentes, prototipado y pruebas de laboratorio.
        - **TRL 4-6 (Modelo undimotriz - WEC)**: Análisis detallado de un único dispositivo que incluye costos de manufactura, instalación y operación a escala representativa.
        - **TRL 7-9 (Granja de dispositivos undimotrices - WEF)**: Proyección a nivel de granja comercial que incorpora economías de escala, costos de interconexión y operación a largo plazo.
        
        Finalmente, la herramienta incluye módulos para la planificación del despliegue: un componente geoespacial para evaluar el recurso energético y una hoja de ruta con los hitos regulatorios clave en México.
        Le invitamos a iniciar su evaluación. El menú principal está diseñado como un flujo de trabajo para guiarlo en la construcción de un análisis detallado y confiable para su proyecto.
        """)

    with col_sesion:
        # --- CONTENEDOR PARA LA GESTIÓN DE SESIONES ---
        #with st.container(border=False):
            
        # --- LÓGICA PARA CARGAR SESIÓN ---
        with st.form(key="form_cargar_sesion"):
            theme.render_subheader("Cargar Sesión", align="center")
            archivo_cargado = st.file_uploader("Cargar archivo .session", label_visibility="collapsed")
            boton_cargar = st.form_submit_button(label="Cargar sesión", use_container_width=True)

            if boton_cargar and archivo_cargado is not None:
                try:
                    # Limpiar resultados anteriores
                    claves_a_borrar = [key for key in st.session_state.keys() if key.startswith('resultados_')]
                    for key in claves_a_borrar:
                        del st.session_state[key]
                    
                    # Cargar y restaurar
                    datos_sesion_cargada = dill.load(archivo_cargado)
                    st.session_state.update(datos_sesion_cargada)
                    
                    # Guardar mensaje de éxito y refrescar
                    st.session_state['mensaje_global'] = "✅ ¡Sesión cargada exitosamente!"
                    st.rerun()

                except Exception as e:
                    st.error(f"Error al cargar el archivo: {e}")

        st.write("")

        with st.container(border=True):
        # --- LÓGICA PARA GUARDAR SESIÓN ---
            theme.render_subheader("Guardar Sesión Actual", align="center")
            nombre_archivo_sesion = st.text_input("Nombre del archivo:")
            if not nombre_archivo_sesion.endswith('.session'):
                nombre_archivo_sesion += '.session'
                
            sesion_para_guardar = {
                'resultados_mex': st.session_state.get('resultados_mex'),
                'resultados_usa': st.session_state.get('resultados_usa'),
                'resultados_sp': st.session_state.get('resultados_sp'),
                'resultados_embi': st.session_state.get('resultados_embi'),
                'resultados_beta': st.session_state.get('resultados_beta'),
                'resultados_apalancamiento': st.session_state.get('resultados_apalancamiento'),
                'resultados_bonos': st.session_state.get('resultados_bonos'), 
            }
            datos_binarios = dill.dumps(sesion_para_guardar)
            
            st.download_button(
                label="Guardar sesión",
                data=datos_binarios,
                file_name=nombre_archivo_sesion,
                mime="application/octet-stream",
                use_container_width=True
            )