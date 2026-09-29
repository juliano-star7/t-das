import base64
import os
import streamlit as st

def get_img_as_base64(file_path):
    try:
        if not os.path.exists(file_path):
            return None
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None

def inject_custom_css():
    st.markdown("""
        <style>
        .stApp { background-color: #243782; }
        .block-container { padding-top: 5rem !important; padding-bottom: 2rem !important; padding-left: 2rem !important; padding-right: 2rem !important; max-width: 100% !important; }
        p, h1, h2, h3, h4, h5, h6, li, label, div.stMarkdown, span { color: #FAFAFA !important; }
        [data-testid="stHeader"], [data-testid="stDecoration"] { display: none !important; }
        .header-container { display: flex; justify-content: space-between; align-items: center; background-color: #ffffff; padding: 15px 20px; border-radius: 10px; margin-bottom: 40px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); border: none; }
        .header-title { font-family: 'Segoe UI', sans-serif; font-size: 2.2rem; font-weight: 700; color: #243782 !important; margin: 0; text-align: center; flex-grow: 1; }
        [data-baseweb="select"] > div, [data-baseweb="base-input"] { background-color: #ffffff !important; border: 2px solid #243782 !important; border-radius: 6px !important; }
        [data-baseweb="select"] div, [data-baseweb="base-input"] input { color: #243782 !important; font-weight: 600; }
        [data-baseweb="popover"] { background-color: #ffffff !important; }
        [data-baseweb="popover"] li { color: #243782 !important; }
        [data-baseweb="popover"] li:hover { background-color: #f0f2f6 !important; }
        [data-testid="stDataFrame"] { background-color: #ffffff; border-radius: 8px; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25); border: 2px solid #243782; }
        [data-testid="stElementToolbar"], [data-testid="stDataFrame"] th svg { display: none !important; }

        /* Controle de exportação em lote */
        [data-testid="stToggle"] { background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.24); border-left: 4px solid #00E5FF; border-radius: 8px; padding: 8px 12px; }
        [data-testid="stToggle"] label { color: #ffffff !important; font-weight: 600 !important; }
        
        /* Botões Padrão */
        button[kind="secondary"] p { color: #243782 !important; font-weight: 600 !important; }
        button[kind="primary"] p { color: #ffffff !important; font-weight: bold !important; letter-spacing: 0.5px; }
        button[disabled] p { color: #888888 !important; } 
        .stDownloadButton button { margin-top: 15px; font-weight: bold; }
        
        /* --- NOVO: Estilo exclusivo para o botão Salvar Tabela (Form Submit) --- */
        [data-testid="stFormSubmitButton"] button {
            background-color: #00C853 !important; /* Verde vibrante */
            border-color: #00C853 !important;
            transition: all 0.3s ease;
        }
        [data-testid="stFormSubmitButton"] button:hover {
            background-color: #00E676 !important; /* Verde mais claro ao passar o mouse */
            border-color: #00E676 !important;
            box-shadow: 0 4px 12px rgba(0, 200, 83, 0.4) !important;
        }
        [data-testid="stFormSubmitButton"] button p {
            color: #ffffff !important;
            font-size: 1.1rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_header():
    img_esq_b64 = get_img_as_base64("stellantis.png") 
    img_dir_b64 = get_img_as_base64("DAQ.png")
    
    img_esq_html = f'<div style="display: inline-flex; height: 50px; align-items: center;"><img src="data:image/png;base64,{img_esq_b64}" style="max-height: 40px; max-width: 100%; object-fit: contain;"></div>' if img_esq_b64 else '<span style="color:#243782; font-size:12px;">[stellantis.png não encontrado]</span>'
    img_dir_html = f'<div style="display: inline-flex; height: 50px; align-items: center;"><img src="data:image/png;base64,{img_dir_b64}" style="max-height: 40px; max-width: 100%; object-fit: contain;"></div>' if img_dir_b64 else '<span style="color:#243782; font-size:12px;">[DAQ.png não encontrado]</span>'

    header_html = f'<div class="header-container"><div style="flex: 0 0 200px; display: flex; align-items: center; justify-content: flex-start;">{img_esq_html}</div><div class="header-title">Energy Management Aero Thermal</div><div style="flex: 0 0 200px; display: flex; align-items: center; justify-content: flex-end;">{img_dir_html}</div></div>'
    st.markdown(header_html, unsafe_allow_html=True)

# --- FUNÇÃO PARA GERAR PDF (REPORTLAB) ---
