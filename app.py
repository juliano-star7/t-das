import os

import streamlit as st

from modules.channels.page import render_visualizador
from modules.shared.ui import get_img_as_base64, inject_custom_css, render_header
from modules.tdas.page import render_tdas


st.set_page_config(
    layout="wide",
    page_title="Energy Management Aero Thermal - Stellantis",
)

// Set the default theme to light mode


def set_light_theme():
    config_dir = ".streamlit"
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "config.toml")
    theme_config = '''[theme]
base="light"
primaryColor="#243782"
backgroundColor="#ffffff"
secondaryBackgroundColor="#f0f2f6"
textColor="#243782"
font="sans serif"
'''
    if not os.path.exists(config_path):
        with open(config_path, "w", encoding="utf-8") as config_file:
            config_file.write(theme_config)


def render_home():
    st.markdown(
        "<h2 style='text-align:center; color:#fff; margin-bottom:50px; font-weight:700;'>"
        "Selecione a Ferramenta</h2>",
        unsafe_allow_html=True,
    )
    _, channels_column, tdas_column, _ = st.columns([1, 3, 3, 1])

    st.markdown(
        """
        <style>
        div[data-testid="column"]:nth-of-type(2) [data-testid="stButton"] button,
        div[data-testid="column"]:nth-of-type(3) [data-testid="stButton"] button {
            background: rgba(255,255,255,.05) !important;
            border: 1px solid rgba(255,255,255,.2) !important;
            border-top: 5px solid #00E5FF !important;
            border-radius: 12px !important;
            box-shadow: 0 8px 24px rgba(0,0,0,.2) !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: center !important;
            height: 220px !important;
            width: 100% !important;
            transition: transform .3s ease, box-shadow .3s ease, background-color .3s ease !important;
        }
        div[data-testid="column"]:nth-of-type(2) [data-testid="stButton"] button:hover,
        div[data-testid="column"]:nth-of-type(3) [data-testid="stButton"] button:hover {
            transform: translateY(-5px) !important;
            box-shadow: 0 12px 20px rgba(0,0,0,.25) !important;
            background: rgba(255,255,255,.1) !important;
        }
        div[data-testid="column"]:nth-of-type(2) [data-testid="stButton"] button p,
        div[data-testid="column"]:nth-of-type(3) [data-testid="stButton"] button p {
            color: #fff !important;
            font-size: 1.2rem !important;
            font-weight: bold !important;
            text-align: center !important;
        }
        div[data-testid="column"]:nth-of-type(3) [data-testid="stButton"] button::before {
            content: "";
            display: block;
            width: 120px;
            height: 120px;
            background-image: url('data:image/png;base64,IMAGE_BASE64_PLACEHOLDER');
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
            margin: 0 auto 10px auto;
        }
        </style>
        """.replace("IMAGE_BASE64_PLACEHOLDER", get_img_as_base64("t-das.png") or ""),
        unsafe_allow_html=True,
    )

    with channels_column:
        if st.button("📊\n\nVisualizador de Canais", use_container_width=True, key="open_channels"):
            st.session_state["active_module"] = "channels"
            st.rerun()
    with tdas_column:
        if st.button("T-DAS", use_container_width=True, key="open_tdas"):
            st.session_state["active_module"] = "tdas"
            st.rerun()


def render_footer():
    st.markdown("<br><hr style='border-color:rgba(255,255,255,.1);'>", unsafe_allow_html=True)
    st.markdown(
        """<div style='color:#b3c2ff; font-size:.8em; text-align:center;'>
        © DAQ Development<br><br>Desenvolvido por: Fernando Vieira Valentim Junior,
        Lucas Gabriel Alvarenga Costa, Lucio Flavio Oliveira Cardoso e Talita Leal da Silva
        </div>""",
        unsafe_allow_html=True,
    )


def run_app():
    inject_custom_css()
    render_header()

    active_module = st.session_state.get("active_module", "home")
    if active_module == "channels":
        if st.button("⬅️ Voltar ao Menu Principal"):
            st.session_state["active_module"] = "home"
            st.rerun()
        render_visualizador()
    elif active_module == "tdas":
        if st.button("⬅️ Voltar ao Menu Principal"):
            st.session_state["active_module"] = "home"
            st.rerun()
        render_tdas()
    else:
        render_home()

    render_footer()


set_light_theme()

if __name__ == "__main__":
    run_app()
