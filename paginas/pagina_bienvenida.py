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
        Esta aplicación proporciona proyecciones económicas y financieras utilizando modelos econométricos y simulaciones de Monte Carlo.

        - **Para iniciar un nuevo análisis:** Selecciona una opción en el menú de la barra lateral.
        - **Para continuar un trabajo anterior:** Usa las opciones de gestión de sesiones a la derecha.
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