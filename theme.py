# theme.py

import streamlit as st


class AppTheme:
    _colors = {
    "primario": "#006D77",
    "texto_principal": "#1E293B",
    "texto_secundario": "#4E6B73",
    "fondo_claro": "#F5F9FA",
    "fondo_subpestañas": "#FFFFFF",
    "color_mouse": "#DFECEF",
    "exito": "#83C5BE",  # Verde agua pastel
    "peligro": "#E29578", # Coral apagado
    "historico": "#264653"
    }




 #
    estilo_subpestanas = {
        "container": {"padding": "0!important", "background-color":_colors["fondo_subpestañas"], "border-radius": "5px"},
        "icon": {"color": _colors["texto_secundario"], "font-size": "20px"}, 
        "nav-link": {"font-size": "16px","text-align": "center","margin":"0px 2px","--hover-color": _colors["color_mouse"]},
        "nav-link-selected": {"background-color": _colors["primario"],"font-weight": "bold","color": "white"},
    }

    estilo_menu = {
        "container": {"padding": "0!important", "background-color": "#fafafa", "border-radius": "5px"},
        "icon": {"color": _colors["texto_secundario"], "font-size": "20px"}, 
        "nav-link": {"font-size": "16px","text-align": "center","margin":"0px 5px","--hover-color":_colors["color_mouse"]},
        "nav-link-selected": {"background-color": _colors["primario"],"font-weight": "bold","color": "white"},
        "menu-title": {"color":_colors["texto_secundario"], "text-align": "center", "font-weight": "600", "font-size": "18px"},
    }


    # --- Tipos de letra por nivel jerarquico ---

    # Nivel 0: Encabezado principal de la app
    @staticmethod
    def render_main_title(title, align="left"):
        main_title_html = f"""
        <div style="margin-bottom: 20px;">
            <h1 style="color: {AppTheme._colors['primario']};
                       font-family: 'Poppins', sans-serif;
                       font-size: 48px;
                       font-weight: 600;
                       letter-spacing: 1px;
                       margin-bottom: 0px;
                       text-align: {align};">
                {title}
            </h1>
        </div>
        """
        st.markdown(main_title_html, unsafe_allow_html=True)

    # Nivel 1: Título principal de página
    @staticmethod
    def render_title(text, align="justify"):
        title_html = f"""
        <h1 style="color: {AppTheme._colors['primario']};
                   font-family: 'Poppins', sans-serif;
                   font-size: 36px;
                   font-weight: 700;
                   margin-bottom: 25px;
                   text-align: {align};">
            {text}
        </h1>
        """
        st.markdown(title_html, unsafe_allow_html=True)

    # Nivel 2: Encabezado de sección principal
    @staticmethod
    def render_header(text, align="justify"):
        header_html = f"""
        <h2 style="color: {AppTheme._colors['texto_principal']};
                   font-family: 'Poppins', sans-serif;
                   font-size: 28px;
                   font-weight: 600;
                   line-height: 1.3;
                   margin-top: 20px;
                   margin-bottom: 10px;
                   text-align: {align};">
            {text}
        </h2>
        """
        st.markdown(header_html, unsafe_allow_html=True)

    # Nivel 3: Subtítulo dentro de una sección o tarjeta
    @staticmethod
    def render_subheader(text, align="justify"):
        subheader_html = f"""
        <h3 style="color: {AppTheme._colors['texto_principal']};
                   font-family: 'Poppins', sans-serif;
                   font-size: 20px;
                   font-weight: 600;
                   margin-bottom: 5px;
                   text-align: {align};">
            {text}
        </h3>
        """
        st.markdown(subheader_html, unsafe_allow_html=True)

    # Nivel 4: Etiqueta para un formulario o grupo de widgets
    @staticmethod
    def render_label(text, align="justify"):
        label_html = f"""
        <h4 style="color: {AppTheme._colors['texto_secundario']};
                   font-family: 'Poppins', sans-serif;
                   font-size: 16px;
                   font-weight: 500;
                   margin-bottom: 5px;
                   text-align: {align};">
            {text}
        </h4>
        """
        st.markdown(label_html, unsafe_allow_html=True)

    # Nivel 5: Texto normal
    @staticmethod
    def render_text(text, align="justify"):
        text_html = f"""
        <p style="color: {AppTheme._colors['texto_principal']};
                  font-family: 'Poppins', sans-serif;
                  font-size: 16px;
                  font-weight: 400;
                  line-height: 1.6;
                  text-align: {align};">
            {text}
        </p>
        """
        st.markdown(text_html, unsafe_allow_html=True)

    # Nivel 6: Texto pequeño para notas o pies de foto
    @staticmethod
    def render_caption(text, align="justify"):
        caption_html = f"""
        <p style="color: {AppTheme._colors['texto_secundario']};
                  font-family: 'Poppins', sans-serif;
                  font-size: 14px;
                  font-style: italic;
                  line-height: 1.4;
                  text-align: {align};">
            {text}
        </p>
        """
        st.markdown(caption_html, unsafe_allow_html=True)

    
    @staticmethod
    def render_sidebar_subheader(text, align="justify"):
        """
        Genera el HTML para un subtítulo DENTRO de la barra lateral.
        """
        subheader_html = f"""
        <h3 style="color: {AppTheme._colors['texto_principal']}; font-size: 18px; font-weight: 600;margin-bottom: 5px;text-align: {align};">{text}</h3>"""
        st.sidebar.markdown(subheader_html, unsafe_allow_html=True)



    @staticmethod # KPIs
    def render_metric(label, value, formato=None):

        if formato == '$':
            formatted_value = f"${value:,.2f}"
        elif formato == '%':
            formatted_value = f"{value}%"
        else:
            formatted_value = str(value)

        metric_html = f"""
        <div style="text-align: center;">
            <span style="font-size: 18px; color: {AppTheme._colors['texto_secundario']};">{label}</span>
            <p style="font-size: 28px; font-weight: bold; color: {AppTheme._colors['texto_principal']};">{formatted_value}</p>
        </div>
        """
        st.markdown(metric_html, unsafe_allow_html=True)



    @staticmethod
    def render_justified_text(text):
        """Renderiza un párrafo de texto con justificación completa."""
        st.markdown(f"<p style='text-align: justify;'>{text}</p>", unsafe_allow_html=True)

    # --- FUNCIÓN AUXILIAR PARA COLORES ---
    @classmethod
    def get_color(cls, name):
        """Método para acceder a un color por su nombre."""
        return cls._colors.get(name, "#000000") # Devuelve negro si el color no se encuentra
    
 
    

        
# Crear una instancia única del tema para importar en otros archivos
theme = AppTheme()