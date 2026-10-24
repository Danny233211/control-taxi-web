# ESTILOS PARA FORZAR LA OCULTACIÓN DE LOS BOTONES FLOTANTES
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden; display: none !important;}
    .stDeployButton {display: none !important;}
    [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    [data-testid="stStatusWidget"] {visibility: hidden !important; display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    div[class*="viewerBadge"] {visibility: hidden !important; display: none !important;}
    a[href*="streamlit.cloud"] {display: none !important;}
    .viewerBadge_container__1QSob {display: none !important;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
