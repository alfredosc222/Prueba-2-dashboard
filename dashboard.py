import streamlit as st
from streamlit_option_menu import option_menu
from theme import theme
from paginas import pagina_bienvenida, pagina_inflacion_mex, pagina_inflacion_usa, pagina_sp500, pagina_embi, pagina_beta, pagina_apalancamiento, pagina_resumen_ve, pagina_bonos_20, pagina_cbs_central
from paginas import components

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    
    /* CSS para la sangría del submenú en la barra lateral */
    .sidebar-submenu {
        margin-left: 1rem; /* Crea la sangría visual */
    }

    /* Regla para Tablets y pantallas más pequeñas (< 992px) */
    @media (max-width: 992px) {
        /* Apila las columnas de st.columns para que no se amontonen */
        div[data-testid="stHorizontalBlock"] {
            flex-direction: column;
        }
        /* Opcional: Centra las columnas apiladas */
        div[data-testid="stHorizontalBlock"] > div {
            width: 100% !important;
            margin: 0 auto;
        }
    }

    /* Regla solo para Teléfonos Móviles (< 600px) */
    @media (max-width: 600px) {
        /* Reduce el tamaño de los títulos principales para que quepan mejor */
        h1 {
            font-size: 28px !important;
        }
        h2 {
            font-size: 22px !important;
        }
        h3 {
            font-size: 18px !important;
        }
    }
    
    /* Regla para Monitores MUY Anchos (> 1800px) */
    @media (min-width: 1800px) {
        /* Limita el ancho del contenedor principal para evitar que el texto
           se estire demasiado, mejorando la legibilidad. */
        .main .block-container {
            max-width: 1600px;
            margin: auto;
        }
    }
    
    /* Regla solo para Desktops y Laptops Estándar */
    @media (min-width: 993px) and (max-width: 1799px) {
        /* Estilos específicos para este rango irían aquí */
        /* Por ejemplo, podrías querer un tamaño de fuente específico */
        body {
            font-size: 16px; /* 1rem, generalmente el tamaño por defecto */
        }
    }
            
</style>
""", unsafe_allow_html=True)


st.set_page_config(page_title="Dashboard de Proyecciones", layout="wide")

# Barra lateral con la navegación principal
with st.sidebar:
    theme.render_main_title("Menú", align="center")
    #st.info("Selecciona el análisis y ajusta los parámetros aquí.")
    
    pagina_seleccionada = option_menu(
        menu_title=None,
        options=["Pagina principal", "Variables Económicas", "CBS", "Flujo de efectivo"],
        icons=["bi-house-door", "bi-columns-gap", "bi-collection", "bi-bar-chart-line"],
        menu_icon="app-indicator",
        default_index=0,
        styles=theme.estilo_menu
    )
    # 2. Submenú condicional para CBS
    if pagina_seleccionada == "CBS":
        st.markdown('<div class="sidebar-submenu">', unsafe_allow_html=True)
        segmento_cbs = option_menu(
            menu_title="Nivel de LCOE",
            options=["Nivel 1-3", "Nivel 4-6", "Nivel 7-9"],
            icons=["bi-layers-half", "bi-layers-half", "bi-layers-half"],
            menu_icon="list-nested",
            default_index=0,
            styles=theme.estilo_menu
        )

        st.markdown('</div>', unsafe_allow_html=True)
        # Guardamos la selección en el estado de la sesión
        st.session_state['segmento_cbs_seleccionado'] = segmento_cbs

#Agregar estado de sesion, si ya se hizo o no la proyeccion

# st.divider()
# theme.render_sidebar_subheader("Estado de la Sesión Actual", align="center")

# # --- Estado de "Variables Económicas" ---

# resultados_variables_economicas = {
#     "Inflación México": "resultados_mex",
#     "Inflación Estados Unidos": "resultados_usa",
#     "S&P 500": "resultados_sp",
#     "EMBI": "resultados_embi",
#     "Beta Desapalancada": "resultados_beta",
#     "D(D+E)": "resultados_apalancamiento",
#     "Bonos del tesoro": "resultados_bonos"  
# }

# components.display_session_status1(resultados_variables_economicas, "Variables Económicas")

# --- CONTENIDO DE CADA PÁGINA ---

# --- PÁGINA DE BIENVENIDA ---
if pagina_seleccionada == "Pagina principal":
    # Llama a la función render de la página de bienvenida
    pagina_bienvenida.render()


# --- PÁGINA DE VARIABLES ECONÓMICAS ---
if pagina_seleccionada == "Variables Económicas":
    theme.render_main_title("Análisis de Variables Económicas", align="center")

    # Creamos el menú horizontal para los análisis específicos
    
    analisis_seleccionado = option_menu(
        menu_title=None,
        options=["Inflación México", "Inflación Estados Unidos", "S&P 500", "EMBI", "Beta Desapalancada", "Deuda Largo Plazo", "Bonos 20 años", "Resumen"],
        icons=['bi-currency-dollar', 'bi-currency-exchange', 'bi-graph-up-arrow', 'bi-globe-americas', 'bi-bar-chart-line', 'bi-cash-stack', 'bi-bank', 'bi-file-earmark-text'], # Iconos de Bootstrap
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "#607D8B", "font-size": "20px"}, 
            "nav-link": {"font-size": "16px", "text-align": "center", "margin":"0px", "--hover-color": "#eee", "display": "flex","height": "100%", "align-items": "center", "justify-content": "center", "width": "auto"},
            "nav-link-selected": {"background-color": "#0a3161"},
        }
    ) 
    
    if analisis_seleccionado == "Inflación México":
        pagina_inflacion_mex.render()
        
    elif analisis_seleccionado == "Inflación Estados Unidos":
        pagina_inflacion_usa.render() 
        
    elif analisis_seleccionado == "S&P 500":
        pagina_sp500.render()

    elif analisis_seleccionado == "EMBI":
        pagina_embi.render()

    elif analisis_seleccionado == "Beta Desapalancada":
        pagina_beta.render()

    elif analisis_seleccionado == "Deuda Largo Plazo":
        pagina_apalancamiento.render()

    elif analisis_seleccionado == "Bonos 20 años":
        pagina_bonos_20.render()

    elif analisis_seleccionado == "Resumen":
        pagina_resumen_ve.render()



# 3. Modifica el enrutador principal para la sección CBS
if pagina_seleccionada == "CBS":
    
    # Obtenemos el segmento seleccionado ("Nivel 1-3", etc.)
    segmento_seleccionado = st.session_state.get('segmento_cbs_seleccionado', "Nivel 1-3")
    
    # Creamos un mapa para convertir el nombre amigable en un 'key' único
    segment_map = {
        "Nivel 1-3": "nivel_1_3",
        "Nivel 4-6": "nivel_4_6",
        "Nivel 7-9": "nivel_7_9"
    }
    segment_key = segment_map.get(segmento_seleccionado)
    
    # Mostramos un título dinámico
    theme.render_main_title(f"Estructura de Desglose de Costos ({segmento_seleccionado})", align="center")

    # Llamamos a nuestra función central reutilizable
    pagina_cbs_central.render_cbs_segment(segment_key)

    
