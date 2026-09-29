import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import re
import tempfile
from datetime import datetime
from difflib import SequenceMatcher
from itertools import cycle
from databricks import sql
import xlsxwriter
import plotly.express as px
import base64
from html import escape
from xhtml2pdf import pisa
from jinja2 import Template
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from asammdf import MDF

# =============================================================================
# INSTALAÇÃO DE DEPENDÊNCIAS (CALAMINE)
# =============================================================================
from python_calamine import CalamineWorkbook


# =============================================================================
# CONFIGURAÇÕES DA PÁGINA E UI
# =============================================================================

def obter_imagem_b64_segura(filename):
    # Resolve o caminho absoluto baseado em onde o script está rodando
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(base_dir, filename)
    
    # Pixel transparente caso a imagem não seja encontrada
    pixel_vazio = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    
    if os.path.exists(filepath):
        try:
            with open(filepath, "rb") as f:
                data = f.read()
            encoded = base64.b64encode(data).decode()
            ext = filename.split('.')[-1].lower()
            mime = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
            return f"data:{mime};base64,{encoded}"
        except Exception:
            return pixel_vazio
    return pixel_vazio

def inject_custom_css():
    st.markdown("""
        <style>
        /* =========================================================
           BASE DA APLICAÇÃO
        ========================================================= */
        .stApp, .main {
            background-color: #243782 !important;
        }

        .block-container {
            padding-top: 3rem !important;
            padding-bottom: 2rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 100% !important;
        }

        .stApp p,
        .stApp h1,
        .stApp h2,
        .stApp h3,
        .stApp h4,
        .stApp h5,
        .stApp h6,
        .stApp li,
        .stApp label,
        .stApp span {
            color: #FAFAFA !important;
        }

        .stApp .tdas-signal-legend,
        .stApp .tdas-signal-legend span {
            color: #243782 !important;
        }

        .stApp [data-testid="stMarkdownContainer"]:has(.tdas-signal-legend) {
            margin-top: -1rem !important;
            padding-top: 0 !important;
        }

        header,
        [data-testid="stHeader"],
        [data-testid="stDecoration"] {
            display: none !important;
        }

        /* =========================================================
           CABEÇALHO
        ========================================================= */
        .header-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #FFFFFF !important;
            padding: 15px 20px;
            border-radius: 12px;
            margin-bottom: 40px;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.16);
        }

        .header-container * {
            color: #243782 !important;
        }

        .header-container .subtitulo {
            color: #545454 !important;
        }

        /* =========================================================
           INPUTS, SELECTS E TEXTAREA
        ========================================================= */
        [data-baseweb="select"] > div,
        [data-baseweb="base-input"],
        [data-baseweb="textarea"],
        [data-testid="stDataFrame"] {
            background-color: #FFFFFF !important;
            border: 1px solid #D6DFF4 !important;
            border-radius: 8px !important;
        }

        [data-baseweb="select"] *,
        [data-baseweb="base-input"] *,
        [data-baseweb="textarea"] *,
        [data-testid="stDataFrame"] * {
            color: #243782 !important;
            font-weight: 600 !important;
        }

        input,
        textarea {
            color: #243782 !important;
            -webkit-text-fill-color: #243782 !important;
            caret-color: #243782 !important;
        }

        input::placeholder,
        textarea::placeholder {
            color: #7585B4 !important;
            -webkit-text-fill-color: #7585B4 !important;
            opacity: 1 !important;
        }

        /* =========================================================
           DROPDOWNS ABERTOS
           Compatível com o menu virtualizado do Streamlit 1.38+
        ========================================================= */

        /* O dropdown é renderizado em um portal fora de .stApp. */
        body > div[data-baseweb="popover"],
        div[data-baseweb="popover"],
        [data-testid="stSelectboxVirtualDropdown"] {
            background: transparent !important;
        }

        body > div[data-baseweb="popover"] > div,
        body > div[data-baseweb="popover"] > div > div,
        div[data-baseweb="popover"] > div,
        div[data-baseweb="popover"] > div > div,
        [data-testid="stSelectboxVirtualDropdown"],
        [data-testid="stSelectboxVirtualDropdown"] > div,
        [data-baseweb="menu"],
        [data-baseweb="menu"] > div,
        div[role="listbox"],
        ul[role="listbox"] {
            background-color: #FFFFFF !important;
            color: #243782 !important;
            -webkit-text-fill-color: #243782 !important;
        }

        body > div[data-baseweb="popover"] > div,
        div[data-baseweb="popover"] > div,
        [data-testid="stSelectboxVirtualDropdown"] {
            border: 1px solid #CBD6F2 !important;
            border-radius: 10px !important;
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22) !important;
            overflow: hidden !important;
        }

        [data-baseweb="menu"],
        div[role="listbox"],
        ul[role="listbox"],
        [data-testid="stSelectboxVirtualDropdown"] {
            max-height: 310px !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
        }

        body > div[data-baseweb="popover"] *,
        div[data-baseweb="popover"] *,
        [data-testid="stSelectboxVirtualDropdown"] * {
            color: #243782 !important;
            -webkit-text-fill-color: #243782 !important;
        }

        body > div[data-baseweb="popover"] input,
        div[data-baseweb="popover"] input,
        [data-testid="stSelectboxVirtualDropdown"] input {
            background-color: #FFFFFF !important;
            color: #243782 !important;
            -webkit-text-fill-color: #243782 !important;
            caret-color: #243782 !important;
        }

        body > div[data-baseweb="popover"] li,
        body > div[data-baseweb="popover"] [role="option"],
        div[data-baseweb="popover"] li,
        div[data-baseweb="popover"] [role="option"],
        [data-testid="stSelectboxVirtualDropdown"] li,
        [data-testid="stSelectboxVirtualDropdown"] [role="option"] {
            min-height: 38px !important;
            padding: 8px 12px !important;
            background-color: #FFFFFF !important;
            color: #243782 !important;
            -webkit-text-fill-color: #243782 !important;
            border-radius: 6px !important;
        }

        body > div[data-baseweb="popover"] li:hover,
        body > div[data-baseweb="popover"] [role="option"]:hover,
        div[data-baseweb="popover"] li:hover,
        div[data-baseweb="popover"] [role="option"]:hover,
        [data-testid="stSelectboxVirtualDropdown"] li:hover,
        [data-testid="stSelectboxVirtualDropdown"] [role="option"]:hover {
            background-color: #EAF0FF !important;
        }

        body > div[data-baseweb="popover"] [aria-selected="true"],
        div[data-baseweb="popover"] [aria-selected="true"],
        [data-testid="stSelectboxVirtualDropdown"] [aria-selected="true"] {
            background-color: #DDE7FF !important;
            color: #162A6B !important;
            -webkit-text-fill-color: #162A6B !important;
            font-weight: 700 !important;
        }

        /* Scrollbar do dropdown */
        [data-baseweb="menu"]::-webkit-scrollbar,
        div[role="listbox"]::-webkit-scrollbar,
        [data-testid="stSelectboxVirtualDropdown"]::-webkit-scrollbar {
            width: 8px !important;
        }

        [data-baseweb="menu"]::-webkit-scrollbar-thumb,
        div[role="listbox"]::-webkit-scrollbar-thumb,
        [data-testid="stSelectboxVirtualDropdown"]::-webkit-scrollbar-thumb {
            background-color: #AEBCE3 !important;
            border-radius: 999px !important;
        }

        /* =========================================================
           CALENDÁRIO
        ========================================================= */
        [data-baseweb="calendar"],
        [data-baseweb="datepicker"] {
            background-color: #FFFFFF !important;
        }

        [data-baseweb="calendar"] {
            border: 1px solid #D5DEF5 !important;
            border-radius: 12px !important;
            box-shadow: 0 12px 26px rgba(0, 0, 0, 0.18) !important;
        }

        [data-baseweb="calendar"] *,
        [data-baseweb="datepicker"] * {
            color: #243782 !important;
            -webkit-text-fill-color: #243782 !important;
        }

        [data-baseweb="calendar"] button:hover {
            background-color: #E8EEFF !important;
            border-radius: 999px !important;
        }

        [data-baseweb="calendar"] [aria-selected="true"],
        [data-baseweb="calendar"] button[aria-selected="true"],
        [data-baseweb="calendar"] [aria-label*="selected"],
        [data-baseweb="calendar"] [aria-label*="Selected"] {
            background-color: #243782 !important;
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            border-radius: 999px !important;
        }

        [data-baseweb="calendar"] [aria-selected="true"] *,
        [data-baseweb="calendar"] button[aria-selected="true"] *,
        [data-baseweb="calendar"] [aria-label*="selected"] *,
        [data-baseweb="calendar"] [aria-label*="Selected"] * {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
        }

        /* =========================================================
           MULTISELECT
        ========================================================= */
        span[data-baseweb="tag"] {
            background-color: #00D2F2 !important;
            border: none !important;
            border-radius: 6px !important;
        }

        span[data-baseweb="tag"] * {
            color: #243782 !important;
            -webkit-text-fill-color: #243782 !important;
            font-weight: 700 !important;
        }

        /* =========================================================
           FILE UPLOADER — MAIOR CONTRASTE E VISIBILIDADE
        ========================================================= */
        .stApp [data-testid="stFileUploadDropzone"] {
            background: #F2F6FF !important;
            background-color: #F2F6FF !important;
            border: 2px dashed #6F84C4 !important;
            border-radius: 12px !important;
            box-shadow: inset 0 0 0 1px rgba(36, 55, 130, 0.04) !important;
        }

        .stApp [data-testid="stFileUploadDropzone"]:hover {
            background: #EAF1FF !important;
            background-color: #EAF1FF !important;
            border-color: #00BFD8 !important;
            box-shadow: 0 0 0 3px rgba(0, 210, 242, 0.12) !important;
        }

        /* Todo o conteúdo do dropzone fica azul e totalmente visível. */
        .stApp [data-testid="stFileUploadDropzone"] *,
        .stApp [data-testid="stFileUploadDropzoneInstructions"],
        .stApp [data-testid="stFileUploadDropzoneInstructions"] * {
            color: #243782 !important;
            -webkit-text-fill-color: #243782 !important;
            opacity: 1 !important;
            visibility: visible !important;
        }

        .stApp [data-testid="stFileUploadDropzone"] small,
        .stApp [data-testid="stFileUploadDropzoneInstructions"] small {
            color: #5F72AA !important;
            -webkit-text-fill-color: #5F72AA !important;
        }

        /* Ícone da nuvem; o seletor fica preso ao dropzone e não afeta o X. */
        .stApp [data-testid="stFileUploadDropzone"] svg,
        .stApp [data-testid="stFileUploadDropzone"] svg path {
            color: #516AAE !important;
            fill: #516AAE !important;
            stroke: #516AAE !important;
            opacity: 1 !important;
        }

        /* Botão Browse files compacto, azul e visível. */
        .stApp [data-testid="stFileUploadDropzone"] button,
        .stApp [data-testid="stFileUploadDropzone"] button[kind="secondary"],
        .stApp [data-testid="stFileUploadDropzone"] button[data-testid="stBaseButton-secondary"] {
            width: auto !important;
            min-width: 126px !important;
            max-width: 180px !important;
            min-height: 40px !important;
            height: 40px !important;
            padding: 0 16px !important;
            flex: 0 0 auto !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            background: #243782 !important;
            background-color: #243782 !important;
            border: 1px solid #243782 !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 10px rgba(36, 55, 130, 0.20) !important;
            transform: none !important;
        }

        .stApp [data-testid="stFileUploadDropzone"] button:hover {
            background: #1A2C69 !important;
            background-color: #1A2C69 !important;
            border-color: #1A2C69 !important;
            box-shadow: 0 6px 14px rgba(36, 55, 130, 0.28) !important;
            transform: none !important;
        }

        .stApp [data-testid="stFileUploadDropzone"] button,
        .stApp [data-testid="stFileUploadDropzone"] button * {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            opacity: 1 !important;
            visibility: visible !important;
            font-weight: 700 !important;
            white-space: nowrap !important;
            margin: 0 !important;
        }

        /* Linha do arquivo carregado */
        .stApp [data-testid="stFileUploaderFile"],
        .stApp [data-testid="stUploadedFile"] {
            margin-top: 8px !important;
            padding: 8px 12px !important;
            background-color: rgba(255, 255, 255, 0.06) !important;
            border: 1px solid rgba(255, 255, 255, 0.16) !important;
            border-radius: 10px !important;
        }

        .stApp [data-testid="stFileUploaderFile"] p,
        .stApp [data-testid="stFileUploaderFile"] span,
        .stApp [data-testid="stUploadedFile"] p,
        .stApp [data-testid="stUploadedFile"] span {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
        }

        .stApp [data-testid="stFileUploaderFile"] svg,
        .stApp [data-testid="stUploadedFile"] svg {
            color: #D5DFFF !important;
        }

        /* Botão X: mantém o ícone original e remove o quadrado. */
        .stApp [data-testid="stFileUploaderDeleteBtn"] button,
        .stApp [data-testid="stFileUploaderFile"] button,
        .stApp [data-testid="stUploadedFile"] button {
            width: 2rem !important;
            min-width: 2rem !important;
            height: 2rem !important;
            min-height: 2rem !important;
            padding: 0 !important;
            background-color: transparent !important;
            border: none !important;
            border-radius: 50% !important;
            box-shadow: none !important;
            transform: none !important;
        }

        .stApp [data-testid="stFileUploaderDeleteBtn"] button:hover,
        .stApp [data-testid="stFileUploaderFile"] button:hover,
        .stApp [data-testid="stUploadedFile"] button:hover {
            background-color: rgba(255, 255, 255, 0.12) !important;
            transform: none !important;
        }

        .stApp [data-testid="stFileUploaderDeleteBtn"] button svg,
        .stApp [data-testid="stFileUploaderFile"] button svg,
        .stApp [data-testid="stUploadedFile"] button svg {
            width: 18px !important;
            height: 18px !important;
            color: #D6DFFF !important;
        }

        /* Barra de upload: trilho discreto e preenchimento ciano. */
        .stApp [data-testid="stFileUploader"] [data-baseweb="progress-bar"] [role="progressbar"] {
            height: 6px !important;
            background-color: rgba(255, 255, 255, 0.24) !important;
            border-radius: 999px !important;
            overflow: hidden !important;
        }

        .stApp [data-testid="stFileUploader"] [data-baseweb="progress-bar"] [role="progressbar"] > div {
            background-color: #00D2F2 !important;
            border-radius: 999px !important;
        }

        /* Fallback para versões que usam stProgressBar. */
        .stApp [data-testid="stFileUploader"] [data-testid="stProgressBar"] > div {
            height: 6px !important;
            background-color: rgba(255, 255, 255, 0.24) !important;
            border-radius: 999px !important;
            overflow: hidden !important;
        }

        .stApp [data-testid="stFileUploader"] [data-testid="stProgressBar"] > div > div {
            background-color: #00D2F2 !important;
            border-radius: 999px !important;
        }

        /* Aviso após o upload terminar */
        .upload-success-card {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 10px;
            margin-bottom: 18px;
            padding: 12px 15px;
            background-color: rgba(0, 210, 242, 0.10);
            border: 1px solid rgba(0, 210, 242, 0.50);
            border-radius: 10px;
        }

        .upload-success-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 30px;
            height: 30px;
            flex: 0 0 30px;
            background-color: #00D2F2;
            color: #243782 !important;
            -webkit-text-fill-color: #243782 !important;
            border-radius: 50%;
            font-weight: 900;
        }

        .upload-success-title {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            font-weight: 800;
        }

        .upload-success-description {
            color: #CFDAFF !important;
            -webkit-text-fill-color: #CFDAFF !important;
            font-size: 0.86rem;
        }

        /* =========================================================
           ABAS
        ========================================================= */
        .stApp [data-testid="stTabs"] button {
            background-color: transparent !important;
            border: none !important;
        }

        .stApp [data-testid="stTabs"] button * {
            color: #B3C2FF !important;
            font-size: 1.1rem !important;
            font-weight: 700 !important;
        }

        .stApp [data-testid="stTabs"] button[aria-selected="true"] * {
            color: #FFFFFF !important;
        }

        .stApp div[data-baseweb="tab-highlight"] {
            background-color: #FFFFFF !important;
        }

        /* =========================================================
           BOTÕES DO STEP 3 E DOWNLOADS
           Escopo restrito: não interfere no botão do file uploader.
        ========================================================= */
        div[data-testid="stButton"] > button,
        div[data-testid="stButton"] button[data-testid^="stBaseButton"],
        div[data-testid="stDownloadButton"] > button,
        div[data-testid="stDownloadButton"] > a,
        div[data-testid="stDownloadButton"] button[data-testid^="stBaseButton"],
        div[data-testid="stDownloadButton"] a[data-testid^="stBaseButton"] {
            width: 100% !important;
            min-height: 3.15rem !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            border-radius: 10px !important;
            font-weight: 800 !important;
            letter-spacing: 0.15px !important;
            text-decoration: none !important;
            box-shadow: 0 5px 13px rgba(0, 0, 0, 0.16) !important;
            transition: transform 0.16s ease, box-shadow 0.16s ease,
                        background-color 0.16s ease, border-color 0.16s ease !important;
        }

        div[data-testid="stButton"] > button:hover,
        div[data-testid="stDownloadButton"] > button:hover,
        div[data-testid="stDownloadButton"] > a:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 8px 18px rgba(0, 0, 0, 0.21) !important;
        }

        /* Primário e downloads: fundo branco e texto azul. */
        div[data-testid="stButton"] > button[kind="primary"],
        div[data-testid="stButton"] button[data-testid="stBaseButton-primary"],
        div[data-testid="stDownloadButton"] > button,
        div[data-testid="stDownloadButton"] > a,
        div[data-testid="stDownloadButton"] button[data-testid^="stBaseButton"],
        div[data-testid="stDownloadButton"] a[data-testid^="stBaseButton"] {
            background: #FFFFFF !important;
            background-color: #FFFFFF !important;
            border: 1px solid #D5DFF7 !important;
            color: #243782 !important;
            -webkit-text-fill-color: #243782 !important;
        }

        div[data-testid="stButton"] > button[kind="primary"] *,
        div[data-testid="stButton"] button[data-testid="stBaseButton-primary"] *,
        div[data-testid="stDownloadButton"] button *,
        div[data-testid="stDownloadButton"] a * {
            color: #243782 !important;
            -webkit-text-fill-color: #243782 !important;
            visibility: visible !important;
            opacity: 1 !important;
            font-weight: 800 !important;
            margin: 0 !important;
        }

        div[data-testid="stButton"] > button[kind="primary"]:hover,
        div[data-testid="stButton"] button[data-testid="stBaseButton-primary"]:hover,
        div[data-testid="stDownloadButton"] > button:hover,
        div[data-testid="stDownloadButton"] > a:hover {
            background: #EEF3FF !important;
            background-color: #EEF3FF !important;
            border-color: #AFC0ED !important;
        }

        /* Secundário do Step 3: outline claro e texto branco. */
        div[data-testid="stButton"] > button[kind="secondary"],
        div[data-testid="stButton"] button[data-testid="stBaseButton-secondary"] {
            background: rgba(255, 255, 255, 0.035) !important;
            background-color: rgba(255, 255, 255, 0.035) !important;
            border: 2px solid #B9C8F3 !important;
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
        }

        div[data-testid="stButton"] > button[kind="secondary"] *,
        div[data-testid="stButton"] button[data-testid="stBaseButton-secondary"] * {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            visibility: visible !important;
            opacity: 1 !important;
            font-weight: 750 !important;
        }

        div[data-testid="stButton"] > button[kind="secondary"]:hover,
        div[data-testid="stButton"] button[data-testid="stBaseButton-secondary"]:hover {
            background: rgba(255, 255, 255, 0.11) !important;
            background-color: rgba(255, 255, 255, 0.11) !important;
            border-color: #FFFFFF !important;
        }

        /* =========================================================
           TOGGLES
        ========================================================= */
        div[data-testid="stToggle"] {
            display: flex !important;
            align-items: center !important;
            min-height: 68px !important;
            padding: 13px 16px !important;
            background-color: rgba(255, 255, 255, 0.06) !important;
            border: 1px solid rgba(179, 194, 255, 0.18) !important;
            border-radius: 10px !important;
        }

        div[data-testid="stToggle"] label {
            width: 100% !important;
        }

        div[data-testid="stToggle"] p {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            font-weight: 700 !important;
            margin-bottom: 0 !important;
        }

        [data-testid="stToggle"] [data-checked="true"] > div {
            background-color: #00D2F2 !important;
        }

        [data-testid="stToggle"] [data-checked="true"] > div > div {
            background-color: #FFFFFF !important;
        }

        [data-testid="stToggle"] [data-checked="false"] > div {
            background-color: #7889BC !important;
        }

        [data-testid="stToggle"] [data-checked="false"] > div > div {
            background-color: #FFFFFF !important;
        }


        /* =========================================================
           OVERRIDE FINAL DO FILE UPLOADER
           Compatível com versões que usam "Upload" ou "Uploader"
        ========================================================= */

        .stApp section[data-testid="stFileUploadDropzone"],
        .stApp section[data-testid="stFileUploaderDropzone"],
        .stApp div[data-testid="stFileUploadDropzone"],
        .stApp div[data-testid="stFileUploaderDropzone"] {
            background: #F2F6FF !important;
            background-color: #F2F6FF !important;
            border: 2px dashed #6F84C4 !important;
            border-radius: 12px !important;
        }

        .stApp section[data-testid="stFileUploadDropzone"] p,
        .stApp section[data-testid="stFileUploadDropzone"] span,
        .stApp section[data-testid="stFileUploadDropzone"] small,
        .stApp section[data-testid="stFileUploaderDropzone"] p,
        .stApp section[data-testid="stFileUploaderDropzone"] span,
        .stApp section[data-testid="stFileUploaderDropzone"] small,
        .stApp div[data-testid="stFileUploadDropzone"] p,
        .stApp div[data-testid="stFileUploadDropzone"] span,
        .stApp div[data-testid="stFileUploadDropzone"] small,
        .stApp div[data-testid="stFileUploaderDropzone"] p,
        .stApp div[data-testid="stFileUploaderDropzone"] span,
        .stApp div[data-testid="stFileUploaderDropzone"] small,
        .stApp [data-testid="stFileUploadDropzoneInstructions"] *,
        .stApp [data-testid="stFileUploaderDropzoneInstructions"] * {
            color: #243782 !important;
            -webkit-text-fill-color: #243782 !important;
            opacity: 1 !important;
            visibility: visible !important;
        }

        .stApp section[data-testid="stFileUploadDropzone"] small,
        .stApp section[data-testid="stFileUploaderDropzone"] small,
        .stApp div[data-testid="stFileUploadDropzone"] small,
        .stApp div[data-testid="stFileUploaderDropzone"] small,
        .stApp [data-testid="stFileUploadDropzoneInstructions"] small,
        .stApp [data-testid="stFileUploaderDropzoneInstructions"] small {
            color: #5F72AA !important;
            -webkit-text-fill-color: #5F72AA !important;
        }

        .stApp section[data-testid="stFileUploadDropzone"] button,
        .stApp section[data-testid="stFileUploaderDropzone"] button,
        .stApp div[data-testid="stFileUploadDropzone"] button,
        .stApp div[data-testid="stFileUploaderDropzone"] button,
        .stApp section[data-testid="stFileUploadDropzone"] button[data-testid="stBaseButton-secondary"],
        .stApp section[data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"] {
            width: auto !important;
            min-width: 126px !important;
            max-width: 180px !important;
            min-height: 40px !important;
            height: 40px !important;
            padding: 0 16px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            flex: 0 0 auto !important;
            background: #00D2F2 !important;
            background-color: #00D2F2 !important;
            border: 1px solid #00BFD8 !important;
            border-radius: 8px !important;
            color: #243782 !important;
            -webkit-text-fill-color: #243782 !important;
            box-shadow: 0 4px 10px rgba(0, 191, 216, 0.24) !important;
            opacity: 1 !important;
            visibility: visible !important;
            transform: none !important;
        }

        .stApp section[data-testid="stFileUploadDropzone"] button *,
        .stApp section[data-testid="stFileUploaderDropzone"] button *,
        .stApp div[data-testid="stFileUploadDropzone"] button *,
        .stApp div[data-testid="stFileUploaderDropzone"] button * {
            color: #243782 !important;
            -webkit-text-fill-color: #243782 !important;
            font-weight: 800 !important;
            opacity: 1 !important;
            visibility: visible !important;
            white-space: nowrap !important;
        }

        .stApp section[data-testid="stFileUploadDropzone"] button:hover,
        .stApp section[data-testid="stFileUploaderDropzone"] button:hover,
        .stApp div[data-testid="stFileUploadDropzone"] button:hover,
        .stApp div[data-testid="stFileUploaderDropzone"] button:hover {
            background: #16DCFF !important;
            background-color: #16DCFF !important;
            border-color: #00BFD8 !important;
            color: #243782 !important;
            -webkit-text-fill-color: #243782 !important;
            transform: none !important;
        }

        </style>
    """, unsafe_allow_html=True)

DB_HOSTNAME = "adb-5678659344564033.13.azuredatabricks.net"
DB_HTTP_PATH = "/sql/1.0/warehouses/f50f8042564c0ed4"
DB_TOKEN = "dapi78bb37615c968c0a0c1b90a91453d398-2" 
TABELA_DB = "`eng_lab`.`t-das-v2`.`dados_iniciais`"

CONFIG = {
    "TIME_COLUMN_NAME": "Time_1Hz",
    "ROWS_TO_SKIP_AFTER_HEADER": 3,
    "FOOTER_ROWS_TO_SKIP": 2,
    "SIMILARITY_THRESHOLD": 0.75
}


def extrair_metadados_mf4(uploaded_file):
    """Extrai somente metadados confiáveis do cabeçalho de um arquivo MF4."""
    if not uploaded_file or not uploaded_file.name.lower().endswith('.mf4'):
        return {}

    arquivo_temporario = None
    mdf = None
    try:
        uploaded_file.seek(0)
        with tempfile.NamedTemporaryFile(suffix='.mf4', delete=False) as arquivo:
            arquivo.write(uploaded_file.getbuffer())
            arquivo_temporario = arquivo.name

        mdf = MDF(arquivo_temporario, load_metadata_only=True)
        data_teste = mdf.start_time.strftime('%Y-%m-%d') if mdf.start_time else ''
        observacao = (
            f"Arquivo MF4: {uploaded_file.name}. "
            f"Aquisição: {mdf.start_time.strftime('%Y-%m-%d %H:%M:%S %z') if mdf.start_time else 'não informada'}. "
            f"Canais disponíveis: {len(mdf.channels_db)}."
        )
        return {
            'test_date': data_teste,
            'observations': observacao,
            'source_file': uploaded_file.name,
            'mf4_version': str(mdf.version),
            'mf4_channel_count': len(mdf.channels_db),
        }
    except Exception as exc:
        st.warning(f"Não foi possível ler os metadados do MF4: {exc}")
        return {}
    finally:
        if mdf is not None:
            try:
                mdf.close()
            except Exception:
                pass
        if arquivo_temporario and os.path.exists(arquivo_temporario):
            os.unlink(arquivo_temporario)

# MAPA PARA O BANCO DE DADOS
MAPA_COLUNAS = {
    'projetos': 'Project', 'motores': 'Engine type', 'transmissoes': 'Transmission',
    'versoes_veiculo': 'Vehicle version', 'marcas': 'Brand', 'mercados': 'Market',
    'test_engineers': 'Test Engineer', 'project_engineers': 'Project Engineer',
    'fases': 'Phase', 'anos_modelo': 'Model Year', 'chassis': 'Chassis'
}

CORES_PADRAO = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A',
    '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52'
]

CORES_FAIXAS = {
    "Phase 1": 'rgba(255, 0, 0, 0.15)',      # Vermelho
    "Phase 2": 'rgba(255, 165, 0, 0.15)',    # Laranja
    "Phase 3": 'rgba(0, 255, 0, 0.15)',      # Verde
    "Idle": 'rgba(0, 0, 255, 0.15)',         # Azul
    "Pre-cond.": 'rgba(0, 255, 255, 0.15)',  # Ciano
    "Ciclos 0–65": 'rgba(255, 0, 255, 0.15)',# Magenta
    "Ciclos 0–16": 'rgba(255, 255, 0, 0.15)',# Amarelo
    "Fase 0": 'rgba(0, 255, 255, 0.15)' 
}

LOGICA_HILL_CLIMBS = {
    "1.1 - General conditions": {
        "T_A_AMB_CWT [°C]": {"sources": {"xF": ["Ambiente"], "xP": ["Ambiente"]}, "axis": "left", "unit": "km/h / ºC"},
        "T_A_AMB [°C]": {"sources": {"xF": ["Ambiente_(teto_carro)"], "xP": ["Ambiente_(teto_carro)"]}, "axis": "left", "unit": "km/h / ºC"},
        "V_VEHICLE_SPEED [km/h]": {"sources": {"xF": ["VehicleSpeedVSOSig"], "xP": ["VITESSE_VEHICULE_ROUES"]}, "axis": "left"},
        "GAS_PEDAL_POSITION [%]": {"sources": {"xF": ["GasPedalPosition"], "xP": ["VOLONTE_COND"]}, "axis": "left", "unit": "%"},
        "GEAR_ENGAGED": {"sources": {"xF": ["GearEngaged"], "xP": ["RAP_BV_ENGAGE_MECA"]}, "axis": "left"}
    },
    "1.2 - General conditions": {
        "N_ENGINE_SPEED [rpm]": {"sources": {"xF": ["EngineSpeed"], "xP": ["REGIME_MOTEUR"]}, "axis": "left", "unit": "rpm"},
        "F_DYNO_FORCE [N]": {"sources": {"xF": ["Força"], "xP": ["Força"]}, "axis": "left", "unit": "N"},
        "N_ELETRO_VENT [rpm]": {"sources": {"xF": ["RPM Eletro"], "xP": ["RPM Eletro"]}, "axis": "left", "unit": "rpm"}
    },
    "2 - Cooling System": {
        "T_WATER_ENGINE [°C]": {"sources": {"xF": ["EngineWaterTemp"], "xP": ["TEMP_EAU_MOT"]}, "axis": "left", "unit": "ºC"},
        "T_OIL_ENGINE [°C]": {"sources": {"xF": [["Óleo_motor_(vareta)"]], "xP": [["Óleo_motor_(vareta)"], ["TEMP_HUILE_MOT"]]}, "axis": "left", "unit": "ºC"},
        "T_C_HT_RAD_I [°C]": {"sources": {"xF": ["Entrada_Radiador_HT"], "xP": ["Entrada_Radiador_HT"]}, "axis": "left", "unit": "ºC"},
        "T_C_HT_RAD_O [°C]": {"sources": {"xF": ["Saida_Radiador_HT"], "xP": ["Saida_Radiador_HT"]}, "axis": "left", "unit": "ºC"},
        "T_OIL_TRANSMISSION [°C]": {"sources": {"xF": ["TransmissionTemperatura"], "xP": ["TEMP_HUILE_BV"]}, "axis": "left", "unit": "ºC"}
    },
    "3 - Torque Comparison": {
        "ENGINE_TORQUE [N.m]": {"sources": {"xF": ["EngineTorque"], "xP": ["COUPLE_REEL"]}, "axis": "left", "unit": "N.m"},
        "ENGINE_TORQUE_REQ [N.m]": {"sources": {"xF": ["EngineTorqueDriverReq"], "xP": ["CPLE_COND_AVT_TRT"]}, "axis": "left", "unit": "N.m"}
    },
    "4 - Intake Air System": {
        "T_A_INTAKE_NOZZLE [°C]": {"sources": {"xF": ["Entrada_Bocal_de_Aspiração"], "xP": ["Entrada_Bocal_de_Aspiração"]}, "axis": "left", "unit": "ºC"},
        "T_A_FILTER_I [°C]": {"sources": {"xF": ["Entrada_Filtro_de_Ar"], "xP": ["Entrada_Filtro_de_Ar"]}, "axis": "left", "unit": "ºC"},
        "T_A_FILTER_O [°C]": {"sources": {"xF": ["Saida_Filtro_de_Ar"], "xP": ["Saida_Filtro_de_Ar"]}, "axis": "left", "unit": "ºC"},
        "T_A_THROTTLE_I [°C]": {"sources": {"xF": ["Entrada_de_Ar_na_borboleta"], "xP": ["Entrada_de_Ar_na_borboleta"]}, "axis": "left", "unit": "ºC"},
        "T_A_TURBO_COMPRESSOR_I [°C]": {"sources": {"xF": ["Entrada_Turbo_Compressor"], "xP": ["Entrada_Turbo_Compressor"]}, "axis": "left", "unit": "ºC"},
        "T_A_TURBO_COMPRESSOR_O [°C]": {"sources": {"xF": ["Saida_Turbo_Compressor"], "xP": ["Saida_Turbo_Compressor"]}, "axis": "left", "unit": "ºC"},
        "T_A_CAN_INTAKE_I [°C]": {"sources": {"xF": ["IntakeAirTemperature"], "xP": ["TEMP_AIR_MOT"]}, "axis": "left", "unit": "km/h / ºC"},
        "T_A_RISE_OF_AMBIENT [°C]": {"calculation": {"type": "difference", "between": ["T_A_TURBO_COMPRESSOR_I [°C]", "T_A_AMB_CWT [°C]"]}, "axis": "left", "unit": "ºC"}
    }
}

# -----------------------------------------------------------------------------
# IMPORTANTE: MANTENHA O SEU DICIONÁRIO TEST_MAPPINGS GIGANTE AQUI!
# Estou colocando apenas um resumo para o código rodar, mas você deve usar o completo.
# -----------------------------------------------------------------------------
TEST_MAPPINGS = {
    "Cool Down": {
        "1.1 - General conditions": {
            "T_A_AMB_CWT [°C]": {"sources": {"xF": ["Ambiente"], "xP": ["Ambiente"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_A_AMB [°C]": {"sources": {"xF": ["Ambiente_(teto_carro)"], "xP": ["Ambiente_(teto_carro)"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_WATER_ENGINE [°C]": {"sources": {"xF": ["EngineWaterTemp"], "xP": ["TEMP_EAU_MOT"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_OIL_ENGINE [°C]": {"sources": {"xF": [["Oil Engine"], ["[Óleo_motor_(vareta)]"]], "xP": [["Óleo_motor_(vareta)"], ["TEMP_HUILE_MOT"]]}, "axis": "left", "unit": "km/h / ºC"},
            "V_VEHICLE_SPEED [km/h]": {"sources": {"xF": ["VehicleSpeedVSOSig"], "xP": ["VITESSE_VEHICULE_ROUES"]}, "axis": "left"},
            "GAS_PEDAL_POSITION [%]": {"sources": {"xF": ["GasPedalPosition"], "xP": ["VOLONTE_COND"]}, "axis": "left", "unit": "%"},
            "T_A_INTAKE_NOZZLE [°C]": {"sources": {"xF": ["Entrada_Bocal_de_Aspiração"], "xP": ["Entrada_Bocal_de_Aspiração"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_A_THROTTLE_I [°C]": {"sources": {"xF": ["Entrada_de_Ar_na_borboleta"], "xP": ["Entrada_de_Ar_na_borboleta"]}, "axis": "left", "unit": "km/h / ºC"}
        },
        "1.2 - General conditions": {
            "N_ENGINE_SPEED [rpm]": {"sources": {"xF": ["EngineSpeed"], "xP": ["REGIME_MOTEUR"]}, "axis": "left", "unit": "rpm"},
            "F_DYNO_FORCE [N]": {"sources": {"xF": ["Força"], "xP": ["Força"]}, "axis": "left", "unit": "N"},
            "N_ELETRO_VENT [rpm]": {"sources": {"xF": ["RPM Eletro"], "xP": ["RPM Eletro"]}, "axis": "left", "unit": "rpm"}
        },
        "2 - AC Pressure": {
            "P_R_HIGH_PRESSURE [bar]": {"sources": {"xF": ["Pressão Alta"], "xP": ["Pressão Alta"]}, "axis": "left", "unit": "bar"},
            "P_R_LOW_PRESSURE [bar]": {"sources": {"xF": ["Pressão Baixa"], "xP": ["Pressão Baixa"]}, "axis": "left", "unit": "bar"},
            "P_R_CAN_AC_PRESSURE [bar]": {"sources": {"xF": ["ACPressure"], "xP": [{"name": "pression_refri_2", "transform": "/100"}]}, "axis": "left", "unit": "bar"}
        },
        "3 - AC Performance": {
            "T_R_COMP_I [ºC]": {"sources": {"xF": ["Entrada_Compressor"], "xP": ["Entrada_Compressor"]}, "axis": "left", "unit": "°C"},
            "T_R_COMP_O [ºC]": {"sources": {"xF": ["Saida_Compressor"], "xP": ["Saida_Compressor"]}, "axis": "left", "unit": "°C"},
            "T_R_COND_I [ºC]": {"sources": {"xF": ["Entrada_Condensador"], "xP": ["Entrada_Condensador"]}, "axis": "left", "unit": "°C"},
            "T_R_COND_O [ºC]": {"sources": {"xF": ["Saida_Condensador"], "xP": ["Saida_Condensador"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_HP_I [ºC]": {"sources": {"xF": ["Entrada_IHX_HP"], "xP": ["Entrada_IHX_HP"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_HP_O [ºC]": {"sources": {"xF": ["Saida_IHX_HP"], "xP": ["Saida_IHX_HP"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_LP_I [ºC]": {"sources": {"xF": ["Entrada_IHX_LP"], "xP": ["Entrada_IHX_LP"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_LP_O [ºC]": {"sources": {"xF": ["Saida_IHX_LP"], "xP": ["Saida_IHX_LP"]}, "axis": "left", "unit": "°C"},
            "T_R_TXV_R_I [ºC]": {"sources": {"xF": ["Entrada_TXV"], "xP": ["Entrada_TXV"]}, "axis": "left", "unit": "°C"},
            "T_R_TXV_R_O [ºC]": {"sources": {"xF": ["Saida_TXV"], "xP": ["Saida_TXV"]}, "axis": "left", "unit": "°C"}
        },
        "4 - Cabin Temperatures": {
            "T_A_VENTS_AVG_R1 [°C]": {"sources": {"xF": ["Difusor esquerdo", "Difusor central esquerdo", "Difusor central direito", "Difusor direito"], "xP": ["Difusor esquerdo", "Difusor central esquerdo", "Difusor central direito", "Difusor direito"]}, "axis": "left", "unit": "°C"},
            "T_A_VENT_R2 [°C]": {"sources": {"xF": ["Difusor traseiro"], "xP": ["Difusor traseiro"]}, "axis": "left", "unit": "°C"},
            "T_A_HEAD_AVG_R1 [°C]": {"sources": {"xF": ["Cabeça_motorista_esquerdo", "Cabeça_motorista_direito", "Cabeça_passageiro_esquerdo", "Cabeça_passageiro_direito"], "xP": ["Cabeça_motorista_esquerdo", "Cabeça_motorista_direito", "Cabeça_passageiro_esquerdo", "Cabeça_passageiro_direito"]}, "axis": "left", "unit": "°C"},
            "T_A_HEAD_AVG_R2 [°C]": {"sources": {"xF": ["Cabeça_esquerda_passageiro_esquerdo_2ª_fileira", "Cabeça_direita_passageiro_esquerdo_2ª_fileira", "Cabeça_esquerda_passageiro_direito_2ª_fileira", "Cabeça_direita_passageiro_direito_2ª_fileira"], "xP": ["Cabeça_esquerda_passageiro_esquerdo_2ª_fileira", "Cabeça_direita_passageiro_esquerdo_2ª_fileira", "Cabeça_esquerda_passageiro_direito_2ª_fileira", "Cabeça_direita_passageiro_direito_2ª_fileira"]}, "axis": "left", "unit": "°C"},
            "T_A_HEAD_AVG_R3 [°C]": {"sources": {"xF": ["Cabeça_esquerda_passageiro_esquerdo_3ª_fileira", "Cabeça_direita_passageiro_esquerdo_3ª_fileira", "Cabeça_esquerda_passageiro_direito_3ª_fileira", "Cabeça_direita_passageiro_direito_3ª_fileira"], "xP": ["Cabeça_esquerda_passageiro_esquerdo_3ª_fileira", "Cabeça_direita_passageiro_esquerdo_3ª_fileira", "Cabeça_esquerda_passageiro_direito_3ª_fileira", "Cabeça_direita_passageiro_direito_3ª_fileira"]}, "axis": "left", "unit": "°C"},
            "T_A_HEAD_TOTAL_AVG [°C]": {"calculation": {"type": "mean", "of": ["T_A_HEAD_AVG_R1 [°C]", "T_A_HEAD_AVG_R2 [°C]", "T_A_HEAD_AVG_R3 [°C]"]}, "axis": "left", "unit": "°C"}
        }
    },
    "RFR03": {
        "1.1 - General conditions": {
            "T_A_AMB_CWT [°C]": {"sources": {"xF": ["out_TempExterieure"], "xP": ["out_TempExterieure"]}, "axis": "left", "unit": "°C"},
            "T_A_AMB [°C]": {"sources": {"xF": ["out_TempExterieure"], "xP": ["out_TempExterieure"]}, "axis": "left", "unit": "°C"},
            "T_WATER_ENGINE [°C]": {"sources": {"xF": ["TempEauMot"], "xP": ["TempEauMot"]}, "axis": "left", "unit": "°C"},
            "T_OIL_ENGINE [°C]": {"sources": {"xF": [["Oil Engine"], ["[Óleo_motor_(vareta)]"]], "xP": [["Óleo_motor_(vareta)"], ["TEMP_HUILE_MOT"]]}, "axis": "left", "unit": "km/h / ºC"},
            "V_VEHICLE_SPEED [km/h]": {"sources": {"xF": ["VitesseVehicule001Kmh"], "xP": ["VitesseVehicule001Kmh"]}, "axis": "left", "unit": "km/h"},
            "GAS_PEDAL_POSITION [%]": {"sources": {"xF": ["VolonteConducteur"], "xP": ["VolonteConducteur"]}, "axis": "left", "unit": "%"},
            "T_A_INTAKE_NOZZLE [°C]": {"sources": {"xF": ["Entrada_Bocal_de_Aspiração"], "xP": ["Entrada_Bocal_de_Aspiração"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_A_THROTTLE_I [°C]": {"sources": {"xF": ["Entrada_de_Ar_na_borboleta"], "xP": ["Entrada_de_Ar_na_borboleta"]}, "axis": "left", "unit": "km/h / ºC"}
        },
        "1.2 - General conditions": {
            "N_ENGINE_SPEED [rpm]": {"sources": {"xF": ["EngineSpeed"], "xP": ["REGIME_MOTEUR"]}, "axis": "left", "unit": "rpm"},
            "F_DYNO_FORCE [N]": {"sources": {"xF": ["Força"], "xP": ["Força"]}, "axis": "left", "unit": "N"},
            "N_ELETRO_VENT [rpm]": {"sources": {"xF": ["BLOWER_SPEED"], "xP": ["BLOWER_SPEED"]}, "axis": "left", "unit": "rpm"},
            "BLOWER_TEMPERATURE [°C]": {"sources": {"xF": ["BLOWER_TEMPERATURE"], "xP": ["BLOWER_TEMPERATURE"]}, "axis": "left", "unit": "°C"},
            "BLOWER_SPEED": {"sources": {"xF": ["BLOWER_SPEED"], "xP": ["BLOWER_SPEED"]}, "axis": "left", "unit": "V"}
        },
        "2 - AC Pressure": {
            "P_R_HIGH_PRESSURE [bar]": {"sources": {"xF": ["Pressão Alta"], "xP": ["Pressão Alta"]}, "axis": "left", "unit": "bar"},
            "P_R_LOW_PRESSURE [bar]": {"sources": {"xF": ["Pressão Baixa"], "xP": ["Pressão Baixa"]}, "axis": "left", "unit": "bar"},
            "P_R_CAN_AC_PRESSURE [bar]": {"sources": {"xF": ["ACPressure"], "xP": [{"name": "pression_refri_2", "transform": "/100"}]}, "axis": "left", "unit": "bar"}
        },
        "3 - AC Performance": {
            "T_R_COMP_I [ºC]": {"sources": {"xF": ["Entrada_Compressor"], "xP": ["Entrada_Compressor"]}, "axis": "left", "unit": "°C"},
            "T_R_COMP_O [ºC]": {"sources": {"xF": ["Saida_Compressor"], "xP": ["Saida_Compressor"]}, "axis": "left", "unit": "°C"},
            "T_R_COND_I [ºC]": {"sources": {"xF": ["Entrada_Condensador"], "xP": ["Entrada_Condensador"]}, "axis": "left", "unit": "°C"},
            "T_R_COND_O [ºC]": {"sources": {"xF": ["Saida_Condensador"], "xP": ["Saida_Condensador"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_HP_I [ºC]": {"sources": {"xF": ["Entrada_IHX_HP"], "xP": ["Entrada_IHX_HP"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_HP_O [ºC]": {"sources": {"xF": ["Saida_IHX_HP"], "xP": ["Saida_IHX_HP"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_LP_I [ºC]": {"sources": {"xF": ["Entrada_IHX_LP"], "xP": ["Entrada_IHX_LP"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_LP_O [ºC]": {"sources": {"xF": ["Saida_IHX_LP"], "xP": ["Saida_IHX_LP"]}, "axis": "left", "unit": "°C"},
            "T_R_TXV_R_I [ºC]": {"sources": {"xF": ["Entrada_TXV"], "xP": ["Entrada_TXV"]}, "axis": "left", "unit": "°C"},
            "T_R_TXV_R_O [ºC]": {"sources": {"xF": ["Saida_TXV"], "xP": ["Saida_TXV"]}, "axis": "left", "unit": "°C"}
        },
        "4 - Cabin Temperatures": {
            "T_A_VENTS_AVG_R1 [°C]": {"sources": {"xF": ["Difusor esquerdo", "Difusor central esquerdo", "Difusor central direito", "Difusor direito"], "xP": ["Difusor esquerdo", "Difusor central esquerdo", "Difusor central direito", "Difusor direito"]}, "axis": "left", "unit": "°C"},
            "T_A_VENT_R2 [°C]": {"sources": {"xF": ["Difusor traseiro"], "xP": ["Difusor traseiro"]}, "axis": "left", "unit": "°C"},
            "T_A_HEAD_AVG_R1 [°C]": {"sources": {"xF": ["Cabeça_motorista_esquerdo", "Cabeça_motorista_direito", "Cabeça_passageiro_esquerdo", "Cabeça_passageiro_direito"], "xP": ["Cabeça_motorista_esquerdo", "Cabeça_motorista_direito", "Cabeça_passageiro_esquerdo", "Cabeça_passageiro_direito"]}, "axis": "left", "unit": "°C"},
            "T_A_HEAD_AVG_R2 [°C]": {"sources": {"xF": ["Cabeça_esquerda_passageiro_esquerdo_2ª_fileira", "Cabeça_direita_passageiro_esquerdo_2ª_fileira", "Cabeça_esquerda_passageiro_direito_2ª_fileira", "Cabeça_direita_passageiro_direito_2ª_fileira"], "xP": ["Cabeça_esquerda_passageiro_esquerdo_2ª_fileira", "Cabeça_direita_passageiro_esquerdo_2ª_fileira", "Cabeça_esquerda_passageiro_direito_2ª_fileira", "Cabeça_direita_passageiro_direito_2ª_fileira"]}, "axis": "left", "unit": "°C"},
            "T_A_HEAD_AVG_R3 [°C]": {"sources": {"xF": ["Cabeça_esquerda_passageiro_esquerdo_3ª_fileira", "Cabeça_direita_passageiro_esquerdo_3ª_fileira", "Cabeça_esquerda_passageiro_direito_3ª_fileira", "Cabeça_direita_passageiro_direito_3ª_fileira"], "xP": ["Cabeça_esquerda_passageiro_esquerdo_3ª_fileira", "Cabeça_direita_passageiro_esquerdo_3ª_fileira", "Cabeça_esquerda_passageiro_direito_3ª_fileira", "Cabeça_direita_passageiro_direito_3ª_fileira"]}, "axis": "left", "unit": "°C"},
            "T_A_HEAD_TOTAL_AVG [°C]": {"calculation": {"type": "mean", "of": ["T_A_HEAD_AVG_R1 [°C]", "T_A_HEAD_AVG_R2 [°C]", "T_A_HEAD_AVG_R3 [°C]"]}, "axis": "left", "unit": "°C"}
        }
    },
    "CDS01": {
        "1.1 - General conditions": {
            "V_VEHICLE_SPEED [km/h]": {"sources": {"xF": ["CAN_VEH_Spd_Veh"], "xP": ["CAN_VEH_Spd_Veh"]}, "axis": "left", "unit": "km/h"},
            "GAS_PEDAL_POSITION [%]": {"sources": {"xF": ["CAN_VEH_Pos_AccelPedal"], "xP": ["CAN_VEH_Pos_AccelPedal"]}, "axis": "left", "unit": "%"},
            "GEAR_ENGAGED": {"sources": {"xF": ["CAN_VEH_St_GearLever"], "xP": ["CAN_VEH_St_GearLever"]}, "axis": "left"},
            "T_A_AMB [°C]": {"sources": {"xF": ["T_Air_BatHV_Ambient"], "xP": ["T_Air_BatHV_Ambient"]}, "axis": "left", "unit": "°C"},
            "T_A_CABIN [°C]": {"sources": {"xF": ["T_Air_Cab"], "xP": ["T_Air_Cab"]}, "axis": "left", "unit": "°C"}
        },
        "1.2 - General conditions": {
            "N_ENGINE_SPEED [rpm]": {"sources": {"xF": ["Spd_FrontEMotor"], "xP": ["Spd_FrontEMotor"]}, "axis": "left", "unit": "rpm"},
            "N_ELETRO_VENT [rpm]": {"sources": {"xF": ["Spd_FrontFan"], "xP": ["Spd_FrontFan"]}, "axis": "left", "unit": "rpm"},
            "BLOWER_SPEED": {"sources": {"xF": ["Spd_Air_CabBlower_Out"], "xP": ["Spd_Air_CabBlower_Out"]}, "axis": "left", "unit": "rpm"}
        },
        "2 - AC Pressure": {
            "P_R_HIGH_PRESSURE [bar]": {"sources": {"xF": ["P_Re_CabCond_In"], "xP": ["P_Re_CabCond_In"]}, "axis": "left", "unit": "bar"},
            "P_R_LOW_PRESSURE [bar]": {"sources": {"xF": ["P_Re_CabEvap_Out"], "xP": ["P_Re_CabEvap_Out"]}, "axis": "left", "unit": "bar"},
            "P_R_CAN_AC_PRESSURE [bar]": {"sources": {"xF": ["P_Re_ReComp_Out"], "xP": ["P_Re_ReComp_Out"]}, "axis": "left", "unit": "bar"}
        },
        "3 - AC Performance": {
            "T_R_COMP_I [ºC]": {"sources": {"xF": ["T_Re_ReComp_In"], "xP": ["T_Re_ReComp_In"]}, "axis": "left", "unit": "°C"},
            "T_R_COMP_O [ºC]": {"sources": {"xF": ["T_Re_ReComp_Out"], "xP": ["T_Re_ReComp_Out"]}, "axis": "left", "unit": "°C"},
            "T_R_COND_I [ºC]": {"sources": {"xF": ["T_Re_CabCond_In"], "xP": ["T_Re_CabCond_In"]}, "axis": "left", "unit": "°C"},
            "T_R_COND_O [ºC]": {"sources": {"xF": ["T_Re_CabCond_Out"], "xP": ["T_Re_CabCond_Out"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_HP_I [ºC]": {"sources": {"xF": ["T_Re_EvapCond_In"], "xP": ["T_Re_EvapCond_In"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_HP_O [ºC]": {"sources": {"xF": ["T_Re_EvapCond_Out"], "xP": ["T_Re_EvapCond_Out"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_LP_I [ºC]": {"sources": {"xF": ["T_Re_CabEvap_In"], "xP": ["T_Re_CabEvap_In"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_LP_O [ºC]": {"sources": {"xF": ["T_Re_CabEvap_Out"], "xP": ["T_Re_CabEvap_Out"]}, "axis": "left", "unit": "°C"},
            "T_R_TXV_R_I [ºC]": {"sources": {"xF": ["T_Re_CabCond_In"], "xP": ["T_Re_CabCond_In"]}, "axis": "left", "unit": "°C"},
            "T_R_TXV_R_O [ºC]": {"sources": {"xF": ["T_Re_CabCond_Out"], "xP": ["T_Re_CabCond_Out"]}, "axis": "left", "unit": "°C"}
        },
        "4 - Cabin Temperatures": {
            "T_A_VENTS_AVG_R1 [°C]": {"sources": {"xF": ["T_Air_Vent_Head_FL", "T_Air_Vent_Head_FR", "T_Air_Vent_Head_FCL", "T_Air_Vent_Head_FCR"], "xP": ["T_Air_Vent_Head_FL", "T_Air_Vent_Head_FR", "T_Air_Vent_Head_FCL", "T_Air_Vent_Head_FCR"]}, "axis": "left", "unit": "°C"},
            "T_A_VENT_R2 [°C]": {"sources": {"xF": ["T_Air_Vent_Head_Rear"], "xP": ["T_Air_Vent_Head_Rear"]}, "axis": "left", "unit": "°C"},
            "T_A_HEAD_AVG_R1 [°C]": {"sources": {"xF": ["T_Air_Cab_Head_FL_L", "T_Air_Cab_Head_FL_R", "T_Air_Cab_Head_FR"], "xP": ["T_Air_Cab_Head_FL_L", "T_Air_Cab_Head_FL_R", "T_Air_Cab_Head_FR"]}, "axis": "left", "unit": "°C"},
            "T_A_HEAD_AVG_R2 [°C]": {"sources": {"xF": ["T_Air_Cab_Head_RL"], "xP": ["T_Air_Cab_Head_RL"]}, "axis": "left", "unit": "°C"},
            "T_A_CABIN_AVG [°C]": {"sources": {"xF": ["T_Air_Cab"], "xP": ["T_Air_Cab"]}, "axis": "left", "unit": "°C"}
        }
    },
    "US City": {
        "1.1 - General conditions": {
            "T_A_AMB_CWT [°C]": {"sources": {"xF": ["Ambiente"], "xP": ["Ambiente"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_A_AMB [°C]": {"sources": {"xF": ["Ambiente_(teto_carro)"], "xP": ["Ambiente_(teto_carro)"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_WATER_ENGINE [°C]": {"sources": {"xF": ["EngineWaterTemp"], "xP": ["TEMP_EAU_MOT"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_OIL_ENGINE [°C]": {"sources": {"xF": [["Óleo_motor_(vareta)"]], "xP": [["Óleo_motor_(vareta)"], ["TEMP_HUILE_MOT"]]}, "axis": "left", "unit": "km/h / ºC"},
            "V_VEHICLE_SPEED [km/h]": {"sources": {"xF": ["VehicleSpeedVSOSig"], "xP": ["VITESSE_VEHICULE_ROUES"]}, "axis": "left"},
            "GAS_PEDAL_POSITION [%]": {"sources": {"xF": ["GasPedalPosition"], "xP": ["VOLONTE_COND"]}, "axis": "left", "unit": "%"},
            "T_A_INTAKE_NOZZLE [°C]": {"sources": {"xF": ["Entrada_Bocal_de_Aspiração"], "xP": ["Entrada_Bocal_de_Aspiração"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_A_THROTTLE_I [°C]": {"sources": {"xF": ["Entrada_de_Ar_na_borboleta"], "xP": ["Entrada_de_Ar_na_borboleta"]}, "axis": "left", "unit": "km/h / ºC"}
        },
        "1.2 - General conditions": {
            "N_ENGINE_SPEED [rpm]": {"sources": {"xF": ["EngineSpeed"], "xP": ["REGIME_MOTEUR"]}, "axis": "left", "unit": "rpm"},
            "F_DYNO_FORCE [N]": {"sources": {"xF": ["Força"], "xP": ["Força"]}, "axis": "left", "unit": "N"},
            "N_ELETRO_VENT [rpm]": {"sources": {"xF": ["RPM Eletro"], "xP": ["RPM Eletro"]}, "axis": "left", "unit": "rpm"}
        },
        "2 - AC Pressure": {
            "P_R_HIGH_PRESSURE [bar]": {"sources": {"xF": ["Pressão Alta"], "xP": ["Pressão Alta"]}, "axis": "left", "unit": "bar"},
            "P_R_LOW_PRESSURE [bar]": {"sources": {"xF": ["Pressão Baixa"], "xP": ["Pressão Baixa"]}, "axis": "left", "unit": "bar"},
            "P_R_CAN_AC_PRESSURE [bar]": {"sources": {"xF": ["ACPressure"], "xP": [{"name": "pression_refri_2", "transform": "/100"}]}, "axis": "left", "unit": "bar"}
        },
        "3 - AC Performance": {
            "T_R_COMP_I [ºC]": {"sources": {"xF": ["Entrada_Compressor"], "xP": ["Entrada_Compressor"]}, "axis": "left", "unit": "°C"},
            "T_R_COMP_O [ºC]": {"sources": {"xF": ["Saida_Compressor"], "xP": ["Saida_Compressor"]}, "axis": "left", "unit": "°C"},
            "T_R_COND_I [ºC]": {"sources": {"xF": ["Entrada_Condensador"], "xP": ["Entrada_Condensador"]}, "axis": "left", "unit": "°C"},
            "T_R_COND_O [ºC]": {"sources": {"xF": ["Saida_Condensador"], "xP": ["Saida_Condensador"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_HP_I [ºC]": {"sources": {"xF": ["Entrada_IHX_HP"], "xP": ["Entrada_IHX_HP"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_HP_O [ºC]": {"sources": {"xF": ["Saida_IHX_HP"], "xP": ["Saida_IHX_HP"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_LP_I [ºC]": {"sources": {"xF": ["Entrada_IHX_LP"], "xP": ["Entrada_IHX_LP"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_LP_O [ºC]": {"sources": {"xF": ["Saida_IHX_LP"], "xP": ["Saida_IHX_LP"]}, "axis": "left", "unit": "°C"},
            "T_R_TXV_R_I [ºC]": {"sources": {"xF": ["Entrada_TXV"], "xP": ["Entrada_TXV"]}, "axis": "left", "unit": "°C"},
            "T_R_TXV_R_O [ºC]": {"sources": {"xF": ["Saida_TXV"], "xP": ["Saida_TXV"]}, "axis": "left", "unit": "°C"}
        },
        "4 - Cabin Temperatures": {
            "T_A_VENTS_AVG_R1 [°C]": {"sources": {"xF": ["Difusor esquerdo", "Difusor central esquerdo", "Difusor central direito", "Difusor direito"], "xP": ["Difusor esquerdo", "Difusor central esquerdo", "Difusor central direito", "Difusor direito"]}, "axis": "left", "unit": "°C"},
            "T_A_VENT_R2 [°C]": {"sources": {"xF": ["Difusor traseiro"], "xP": ["Difusor traseiro"]}, "axis": "left", "unit": "°C"},
            "T_A_HEAD_AVG_R1 [°C]": {"sources": {"xF": ["Cabeça_motorista_esquerdo", "Cabeça_motorista_direito", "Cabeça_passageiro_esquerdo", "Cabeça_passageiro_direito"], "xP": ["Cabeça_motorista_esquerdo", "Cabeça_motorista_direito", "Cabeça_passageiro_esquerdo", "Cabeça_passageiro_direito"]}, "axis": "left", "unit": "°C"},
            "T_A_HEAD_AVG_R2 [°C]": {"sources": {"xF": ["Cabeça_esquerda_passageiro_esquerdo_2ª_fileira", "Cabeça_direita_passageiro_esquerdo_2ª_fileira", "Cabeça_esquerda_passageiro_direito_2ª_fileira", "Cabeça_direita_passageiro_direito_2ª_fileira"], "xP": ["Cabeça_esquerda_passageiro_esquerdo_2ª_fileira", "Cabeça_direita_passageiro_esquerdo_2ª_fileira", "Cabeça_esquerda_passageiro_direito_2ª_fileira", "Cabeça_direita_passageiro_direito_2ª_fileira"]}, "axis": "left", "unit": "°C"},
            "T_A_HEAD_AVG_R3 [°C]": {"sources": {"xF": ["Cabeça_esquerda_passageiro_esquerdo_3ª_fileira", "Cabeça_direita_passageiro_esquerdo_3ª_fileira", "Cabeça_esquerda_passageiro_direito_3ª_fileira", "Cabeça_direita_passageiro_direito_3ª_fileira"], "xP": ["Cabeça_esquerda_passageiro_esquerdo_3ª_fileira", "Cabeça_direita_passageiro_esquerdo_3ª_fileira", "Cabeça_esquerda_passageiro_direito_3ª_fileira", "Cabeça_direita_passageiro_direito_3ª_fileira"]}, "axis": "left", "unit": "°C"},
            "T_A_HEAD_TOTAL_AVG [°C]": {"calculation": {"type": "mean", "of": ["T_A_HEAD_AVG_R1 [°C]", "T_A_HEAD_AVG_R2 [°C]", "T_A_HEAD_AVG_R3 [°C]"]}, "axis": "left", "unit": "°C"}
        }
    },
    "Heavy Urban": {
        "1.1 - General conditions": {
            "T_A_AMB_CWT [°C]": {"sources": {"xF": ["Ambiente"], "xP": ["Ambiente"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_A_AMB [°C]": {"sources": {"xF": ["Ambiente_(teto_carro)"], "xP": ["Ambiente_(teto_carro)"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_WATER_ENGINE [°C]": {"sources": {"xF": ["EngineWaterTemp"], "xP": ["TEMP_EAU_MOT"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_OIL_ENGINE [°C]": {"sources": {"xF": [["Óleo_motor_(vareta)"]], "xP": [["Óleo_motor_(vareta)"], ["TEMP_HUILE_MOT"]]}, "axis": "left", "unit": "km/h / ºC"},
            "V_VEHICLE_SPEED [km/h]": {"sources": {"xF": ["VehicleSpeedVSOSig"], "xP": ["VITESSE_VEHICULE_ROUES"]}, "axis": "left"},
            "GAS_PEDAL_POSITION [%]": {"sources": {"xF": ["GasPedalPosition"], "xP": ["VOLONTE_COND"]}, "axis": "left", "unit": "%"},
            "T_A_INTAKE_NOZZLE [°C]": {"sources": {"xF": ["Entrada_Bocal_de_Aspiração"], "xP": ["Entrada_Bocal_de_Aspiração"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_A_THROTTLE_I [°C]": {"sources": {"xF": ["Entrada_de_Ar_na_borboleta"], "xP": ["Entrada_de_Ar_na_borboleta"]}, "axis": "left", "unit": "km/h / ºC"}
        },
        "1.2 - General conditions": {
            "N_ENGINE_SPEED [rpm]": {"sources": {"xF": ["EngineSpeed"], "xP": ["REGIME_MOTEUR"]}, "axis": "left", "unit": "rpm"},
            "F_DYNO_FORCE [N]": {"sources": {"xF": ["Força"], "xP": ["Força"]}, "axis": "left", "unit": "N"},
            "N_ELETRO_VENT [rpm]": {"sources": {"xF": ["RPM Eletro"], "xP": ["RPM Eletro"]}, "axis": "left", "unit": "rpm"}
        },
        "2 - AC Pressure": {
            "P_R_HIGH_PRESSURE [bar]": {"sources": {"xF": ["Pressão Alta"], "xP": ["Pressão Alta"]}, "axis": "left", "unit": "bar"},
            "P_R_LOW_PRESSURE [bar]": {"sources": {"xF": ["Pressão Baixa"], "xP": ["Pressão Baixa"]}, "axis": "left", "unit": "bar"},
            "P_R_CAN_AC_PRESSURE [bar]": {"sources": {"xF": ["ACPressure"], "xP": [{"name": "pression_refri_2", "transform": "/100"}]}, "axis": "left", "unit": "bar"}
        },
        "3 - AC Performance": {
            "T_R_COMP_I [ºC]": {"sources": {"xF": ["Entrada_Compressor"], "xP": ["Entrada_Compressor"]}, "axis": "left", "unit": "°C"},
            "T_R_COMP_O [ºC]": {"sources": {"xF": ["Saida_Compressor"], "xP": ["Saida_Compressor"]}, "axis": "left", "unit": "°C"},
            "T_R_COND_I [ºC]": {"sources": {"xF": ["Entrada_Condensador"], "xP": ["Entrada_Condensador"]}, "axis": "left", "unit": "°C"},
            "T_R_COND_O [ºC]": {"sources": {"xF": ["Saida_Condensador"], "xP": ["Saida_Condensador"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_HP_I [ºC]": {"sources": {"xF": ["Entrada_IHX_HP"], "xP": ["Entrada_IHX_HP"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_HP_O [ºC]": {"sources": {"xF": ["Saida_IHX_HP"], "xP": ["Saida_IHX_HP"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_LP_I [ºC]": {"sources": {"xF": ["Entrada_IHX_LP"], "xP": ["Entrada_IHX_LP"]}, "axis": "left", "unit": "°C"},
            "T_R_IHX_LP_O [ºC]": {"sources": {"xF": ["Saida_IHX_LP"], "xP": ["Saida_IHX_LP"]}, "axis": "left", "unit": "°C"},
            "T_R_TXV_R_I [ºC]": {"sources": {"xF": ["Entrada_TXV"], "xP": ["Entrada_TXV"]}, "axis": "left", "unit": "°C"},
            "T_R_TXV_R_O [ºC]": {"sources": {"xF": ["Saida_TXV"], "xP": ["Saida_TXV"]}, "axis": "left", "unit": "°C"}
        },
        "4 - Cabin Temperatures": {
            "T_A_VENTS_AVG_R1 [°C]": {"sources": {"xF": ["Difusor esquerdo", "Difusor central esquerdo", "Difusor central direito", "Difusor direito"], "xP": ["Difusor esquerdo", "Difusor central esquerdo", "Difusor central direito", "Difusor direito"]}, "axis": "left", "unit": "°C"},
            "T_A_VENT_R2 [°C]": {"sources": {"xF": ["Difusor traseiro"], "xP": ["Difusor traseiro"]}, "axis": "left", "unit": "°C"},
            "T_A_HEAD_AVG_R1 [°C]": {"sources": {"xF": ["Cabeça_motorista_esquerdo", "Cabeça_motorista_direito", "Cabeça_passageiro_esquerdo", "Cabeça_passageiro_direito"], "xP": ["Cabeça_motorista_esquerdo", "Cabeça_motorista_direito", "Cabeça_passageiro_esquerdo", "Cabeça_passageiro_direito"]}, "axis": "left", "unit": "°C"},
            "T_A_HEAD_AVG_R2 [°C]": {"sources": {"xF": ["Cabeça_esquerda_passageiro_esquerdo_2ª_fileira", "Cabeça_direita_passageiro_esquerdo_2ª_fileira", "Cabeça_esquerda_passageiro_direito_2ª_fileira", "Cabeça_direita_passageiro_direito_2ª_fileira"], "xP": ["Cabeça_esquerda_passageiro_esquerdo_2ª_fileira", "Cabeça_direita_passageiro_esquerdo_2ª_fileira", "Cabeça_esquerda_passageiro_direito_2ª_fileira", "Cabeça_direita_passageiro_direito_2ª_fileira"]}, "axis": "left", "unit": "°C"},
            "T_A_HEAD_AVG_R3 [°C]": {"sources": {"xF": ["Cabeça_esquerda_passageiro_esquerdo_3ª_fileira", "Cabeça_direita_passageiro_esquerdo_3ª_fileira", "Cabeça_esquerda_passageiro_direito_3ª_fileira", "Cabeça_direita_passageiro_direito_3ª_fileira"], "xP": ["Cabeça_esquerda_passageiro_esquerdo_3ª_fileira", "Cabeça_direita_passageiro_esquerdo_3ª_fileira", "Cabeça_esquerda_passageiro_direito_3ª_fileira", "Cabeça_direita_passageiro_direito_3ª_fileira"]}, "axis": "left", "unit": "°C"},
            "T_A_HEAD_TOTAL_AVG [°C]": {"calculation": {"type": "mean", "of": ["T_A_HEAD_AVG_R1 [°C]", "T_A_HEAD_AVG_R2 [°C]", "T_A_HEAD_AVG_R3 [°C]"]}, "axis": "left", "unit": "°C"}
        }
    },
    "TVM": {
        "1.1 - General conditions": {
            "T_A_AMB_CWT [°C]": {"sources": {"xF": ["Ambiente"], "xP": ["Ambiente"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_A_AMB [°C]": {"sources": {"xF": ["Ambiente_(teto_carro)"], "xP": ["Ambiente_(teto_carro)"]}, "axis": "left", "unit": "km/h / ºC"},
            "V_VEHICLE_SPEED [km/h]": {"sources": {"xF": ["VehicleSpeedVSOSig"], "xP": ["VITESSE_VEHICULE_ROUES"]}, "axis": "left", "unit": "km/h"},
            "GAS_PEDAL_POSITION [%]": {"sources": {"xF": ["GasPedalPosition"], "xP": ["VOLONTE_COND"]}, "axis": "left", "unit": "%"},
            "GEAR_ENGAGED": {"sources": {"xF": ["GearEngaged"], "xP": ["RAP_BV_ENGAGE_MECA"]}, "axis": "left", "unit": ""}
        },
        "1.2 - General conditions": {
            "N_ENGINE_SPEED [rpm]": {"sources": {"xF": ["EngineSpeed"], "xP": ["REGIME_MOTEUR"]}, "axis": "left", "unit": "rpm"},
            "F_DYNO_FORCE [N]": {"sources": {"xF": ["Força"], "xP": ["Força"]}, "axis": "left", "unit": "N"},
            "N_ELETRO_VENT [rpm]": {"sources": {"xF": ["RPM Eletro"], "xP": ["RPM Eletro"]}, "axis": "left", "unit": "rpm"}
        },
        "2 - Cooling System": {
            "T_WATER_ENGINE [°C]": {"sources": {"xF": ["EngineWaterTemp"], "xP": ["TEMP_EAU_MOT"]}, "axis": "left", "unit": "ºC"},
            "T_OIL_ENGINE [°C]": {"sources": {"xF": [["Óleo_motor_(vareta)"]], "xP": [["Óleo_motor_(vareta)"], ["TEMP_HUILE_MOT"]]}, "axis": "left", "unit": "ºC"},
            "T_C_HT_RAD_I [°C]": {"sources": {"xF": ["Entrada_Radiador_HT"], "xP": ["Entrada_Radiador_HT"]}, "axis": "left", "unit": "ºC"},
            "T_C_HT_RAD_O [°C]": {"sources": {"xF": ["Saida_Radiador_HT"], "xP": ["Saida_Radiador_HT"]}, "axis": "left", "unit": "ºC"},
            "T_OIL_TRANSMISSION [°C]": {"sources": {"xF": ["TransmissionTemperatura"], "xP": ["TEMP_HUILE_BV"]}, "axis": "left", "unit": "ºC"},
            "T_C_WTOC_I [°C]": {"sources": {"xF": ["Saída_WTOC"], "xP": ["Saída_WTOC"]}, "axis": "left", "unit": "ºC"},
        },
        "3 - Torque Comparison": {
            "ENGINE_TORQUE [N.m]": {"sources": {"xF": ["EngineTorque"], "xP": ["COUPLE_REEL"]}, "axis": "left", "unit": "N.m"},
            "ENGINE_TORQUE_REQ [N.m]": {"sources": {"xF": ["EngineTorqueDriverReq"], "xP": ["CPLE_COND_AVT_TRT"]}, "axis": "left", "unit": "N.m"}
        },
        "4 - Intake Air System": {
            "T_A_INTAKE_NOZZLE [°C]": {"sources": {"xF": ["Entrada_Bocal_de_Aspiração"], "xP": ["Entrada_Bocal_de_Aspiração"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_A_FILTER_I [°C]": {"sources": {"xF": ["Entrada_Filtro_de_Ar"], "xP": ["Entrada_Filtro_de_Ar"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_A_FILTER_O [°C]": {"sources": {"xF": ["Saida_Filtro_de_Ar"], "xP": ["Saida_Filtro_de_Ar"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_A_THROTTLE_I [°C]": {"sources": {"xF": ["Entrada_de_Ar_na_borboleta"], "xP": ["Entrada_de_Ar_na_borboleta"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_A_TURBO_COMPRESSOR_I [°C]": {"sources": {"xF": ["Entrada_Turbo_Compressor"], "xP": ["Entrada_Turbo_Compressor"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_A_TURBO_COMPRESSOR_O [°C]": {"sources": {"xF": ["Saida_Turbo_Compressor"], "xP": ["Saida_Turbo_Compressor"]}, "axis": "left", "unit": "km/h / ºC"},
            "T_A_CAN_INTAKE_I [°C]": {"sources": {"xF": ["IntakeAirTemperature"], "xP": ["TEMP_AIR_MOT"]}, "axis": "left", "unit": "km/h / ºC"},
        },
        "5 - Safety Points": {
            "T_S_FUEL_TANK_1 [°C]": {"sources": {"xF": ["Ponto_1_-_Tanque_de_combustível​"], "xP": ["Ponto_1_-_Tanque_de_combustível​"]}, "axis": "left", "unit": "ºC"},
            "T_S_FUEL_TANK_2 [°C]": {"sources": {"xF": ["Ponto_2_-_Tanque_de_combustível​"], "xP": ["Ponto_2_-_Tanque_de_combustível​"]}, "axis": "left", "unit": "ºC"},
        },
        "6 - Underbody (Exhaust)": {
            "T_S_EXHAUST_PIPE_BEFORE_FLEXIBLE [°C]": {"sources": {"xF": ["Tubulação_antes_do_Flexível​​"], "xP": ["Tubulação_antes_do_Flexível​​"]}, "axis": "left", "unit": "ºC"},
            "T_S_FLEXIBLE​": {"sources": {"xF": ["Pele_do_Flexível​​"], "xP": ["Pele_do_Flexível​"]}, "axis": "left", "unit": "ºC"},
            "T_S_PRIMARY_EXHAUST_PIPE​": {"sources": {"xF": ["Tubulação_antes_do_1°_Gancho​​"], "xP": ["Tubulação_antes_do_1°_Gancho​​"]}, "axis": "left", "unit": "ºC"},
            "T_S_CENTRAL_MUFFLER​": {"sources": {"xF": ["Muffler_Central_(face_superior)​​​"], "xP": ["Muffler_Central_(face_superior)​​"]}, "axis": "left", "unit": "ºC"},
            "T_S_CENTRAL_EXHAUST_PIPE​": {"sources": {"xF": ["Curva_antes_do_tanque_(lado_tanque)​​​​"], "xP": ["Curva_antes_do_tanque_(lado_tanque)​​"]}, "axis": "left", "unit": "ºC"},
            "T_S_POSTERIOR_MUFFLER​": {"sources": {"xF": ["Centro_do_Muffler_Posterior_(face_superior)​​​​"], "xP": ["Centro_do_Muffler_Posterior_(face_superior)​​"]}, "axis": "left", "unit": "ºC"},
            "T_EG_REAR_EXHAUST_PIPE​": {"sources": {"xF": ["Gás_De_Saida_​​"], "xP": ["Gás_De_Saida_​​"]}, "axis": "left", "unit": "ºC"}
        },
        "7 - Underhood": {
            "T_S_ENGINE_HEAD_COVER​": {"sources": {"xF": ["Tampa_do_cabeçote​​​"], "xP": ["Tampa_do_cabeçote​​"]}, "axis": "left", "unit": "ºC"},
            "T_S_ENGINE_BLOCK​": {"sources": {"xF": ["Bloco_motor​​​"], "xP": ["Bloco_motor​​"]}, "axis": "left", "unit": "ºC"},
            "T_S_HOT_END_UP​": {"sources": {"xF": ["Hot_end_Up​"], "xP": ["Hot_end_Up​"]}, "axis": "left", "unit": "ºC"},
            "T_S_HOT_END_MID​": {"sources": {"xF": ["Hot_end_Mid​"], "xP": ["Hot_end_Mid​"]}, "axis": "left", "unit": "ºC"},
            "T_S_HOT_END_DOWN​": {"sources": {"xF": ["Hot_end_down​"], "xP": ["Hot_end_down​"]}, "axis": "left", "unit": "ºC"},
            "T_S_GEARBOX​": {"sources": {"xF": ["Pele_Caixa_de_marchas​​​​"], "xP": ["Pele_Caixa_de_marchas​​"]}, "axis": "left", "unit": "ºC"},
            "T_S_BATTERY_FRONT​": {"sources": {"xF": ["bateria_externo_1​​"], "xP": ["bateria_externo_1​​​"]}, "axis": "left", "unit": "ºC"},
            "T_S_ECU_ENGINE_SIDE​": {"sources": {"xF": ["ECU_lado_motor​​​"], "xP": ["ECU_lado_motor​​"]}, "axis": "left", "unit": "ºC"},
        }
    },

    "Ubatuba_30": LOGICA_HILL_CLIMBS,
    "Ubatuba_transiente": LOGICA_HILL_CLIMBS,
    "Campos_do_Jordao_75": LOGICA_HILL_CLIMBS,
    "Campos_do_Jordao_90": LOGICA_HILL_CLIMBS,
    "Campos_do_Jordao_transiente": LOGICA_HILL_CLIMBS,
    "Topo_do_mundo": LOGICA_HILL_CLIMBS
}

# -----------------------------------------------------------------------------
HTML_TEMPLATE_REPORT = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="utf-8" />
    <style>
        /* 1. REGRA DA CAPA (EM PÉ / PORTRAIT) */
        @page {
            size: a4 portrait;
            margin: 1.5cm;
            @frame footer {
                -pdf-frame-content: footer_content_capa;
                bottom: 0.5cm;
                margin-left: 1.5cm;
                margin-right: 1.5cm;
                height: 1cm;
            }
        }
        
        /* 2. REGRA DOS GRÁFICOS (DEITADO / LANDSCAPE) */
        @page landscape_page {
            size: a4 landscape;
            margin: 1cm;
            @frame footer {
                -pdf-frame-content: footer_content_graph;
                bottom: 0.5cm;
                margin-left: 1cm;
                margin-right: 1cm;
                height: 1cm;
            }
        }

        /* 3. REGRA DA TABELA CPIT (EM PÉ / PORTRAIT COM NÚMERO DE PÁGINA) */
        @page portrait_page {
            size: a4 portrait;
            margin: 1.5cm;
            @frame footer {
                -pdf-frame-content: footer_content_graph;
                bottom: 0.5cm;
                margin-left: 1.5cm;
                margin-right: 1.5cm;
                height: 1cm;
            }
        }
        
        body { font-family: Helvetica, sans-serif; color: #333; }
        div, table, td, span { text-align: left; }
        
        /* --- ESTILOS DA CAPA --- */
        .header-table { width: 100%; border-collapse: collapse; border: 1.5px solid #003366; margin-bottom: 20px; }
        .header-table td { border: 1px solid #003366; text-align: center; vertical-align: middle; padding: 10px; }
        .col-logo { width: 25%; text-align: center; }
        .col-center { width: 50%; font-size: 9pt; line-height: 1.4; font-weight: bold; text-align: center;}
        .col-info { width: 25%; font-size: 9pt; line-height: 1.8; text-align: center;}
        .logo-img-stellantis { width: 130px; }
        
        .title-table { width: 100%; margin-bottom: 15px; }
        .title-table td { vertical-align: middle; border: none; }
        .col-tdas-logo { width: 20%; text-align: center; }
        .col-tdas-text { width: 80%; text-align: center; }
        .logo-tdas { width: 60px; }
        .title-text { font-size: 14pt; font-weight: bold; text-align: center; }
        .subtitle-text { font-size: 15pt; font-weight: bold; margin-top: 5px; text-align: center; }
        
        .section-title { font-size: 11pt; font-weight: bold; color: #003366; border-left: 4px solid #003366; padding-left: 8px; margin-top: 15px; margin-bottom: 5px; line-height: 1.1; }
        .info-table { width: 100%; border-collapse: collapse; font-size: 9.5pt; }
        .info-table td { padding: 4px 0px; border-bottom: 1px solid #eeeeee; }
        .label-col { font-weight: bold; color: #003366; width: 30%; } 
        .value-col { width: 70%; color: #444; }
        
        .observations-box { margin-top: 5px; border: 1px solid #ddd; border-radius: 4px; padding: 10px; background-color: #fdfdfd; white-space: pre-wrap; font-size: 9pt; color: #555; min-height: 30px; }
        
        /* --- ESTILOS DOS GRÁFICOS --- */
        .graph-title { color: #003366; font-size: 16pt; margin-bottom: 15px; text-align: center; width: 100%; font-weight: bold; }
        .chart-container { text-align: center; width: 100%; }
        .chart-img { max-width: 100%; max-height: 15cm; }
    </style>
</head>
<body>
    <div id="footer_content_capa" style="text-align: center; font-size: 8pt; color: #555; padding-top: 5px;">
        PDT / VEHE / VEPE / EMAT / SATC / TEST
    </div>
    
    <div id="footer_content_graph" style="text-align: center; font-size: 9pt; color: #777; padding-top: 5px;">
        Page <pdf:pagenumber />
    </div>

    <table class="header-table">
        <tr>
            <td class="col-logo"><img src="{{ dados.caminho_logo_uri }}" class="logo-img-stellantis" /></td>
            <td class="col-center">
                STELLANTIS AUTOMOVEIS BRASIL LTDA<br/>
                CLIMATIC WIND TUNEL TESTS - BETIM<br/>
                Avenida Contorno, 3455 – Paulo Camilo<br/>
                CEP 32669-900 – Betim – Minas Gerais – MG
            </td>
            <td class="col-info">
                <strong>Date:</strong> {{ dados.test_date }}<br/><br/>
                <strong>Page:</strong> 1
            </td>
        </tr>
    </table>

    <table class="title-table">
        <tr>
            <td class="col-tdas-logo"><img src="{{ dados.caminho_logo_tdas_uri }}" class="logo-tdas" /></td>
            <td class="col-tdas-text">
                <div class="title-text">{{ dados.titulo_principal }}</div>
                <div class="subtitle-text">{{ dados.test_performed }}</div>
            </td>
        </tr>
    </table>

    <div class="section-title">Test General Information</div>
    <table class="info-table">
        <tr><td class="label-col">Test Date:</td><td class="value-col">{{ dados.test_date }}</td></tr>
    </table>

    <div class="section-title">Test Vehicle Specifications</div>
    <table class="info-table">
        <tr><td class="label-col">Project:</td><td class="value-col">{{ dados.project }}</td></tr>
        <tr><td class="label-col">Brand:</td><td class="value-col">{{ dados.brand }}</td></tr>
        <tr><td class="label-col">Vehicle Version:</td><td class="value-col">{{ dados.vehicle_version }}</td></tr>
        <tr><td class="label-col">Market:</td><td class="value-col">{{ dados.market }}</td></tr>
        <tr><td class="label-col">Engine type:</td><td class="value-col">{{ dados.engine_type }}</td></tr>
        <tr><td class="label-col">Transmission:</td><td class="value-col">{{ dados.transmission }}</td></tr>
        <tr><td class="label-col">Model Year:</td><td class="value-col">{{ dados.model_year }}</td></tr>
        <tr><td class="label-col">Project phase:</td><td class="value-col">{{ dados.project_phase }}</td></tr>
        <tr><td class="label-col">Chassis (VIN):</td><td class="value-col">{{ dados.chassi_vin }}</td></tr>
    </table>

    <div class="section-title">Test Responsible</div>
    <table class="info-table">
        <tr><td class="label-col">Test Engineer:</td><td class="value-col">{{ dados.test_engineer }}</td></tr>
        <tr><td class="label-col">Project Engineer:</td><td class="value-col">{{ dados.project_engineer }}</td></tr>
    </table>

    <div class="section-title">Test Notes & Observations</div>
    <div class="observations-box">{{ dados.observations }}</div>

    {{ graficos_html }}

</body>
</html>
"""

HTML_TEMPLATE_GRAPH_BLOCK = """
    <pdf:nextpage />
    
    <div class="graph-title">{{ nome_grafico }}</div>
    <div class="chart-container">
        <img class="chart-img" src="{{ chart_uri }}" style="max-height: {{ max_height }};" />
    </div>
    
    {{ bloco_comentario }}
"""


HTML_TEMPLATE_CPIT_BLOCK = """
    <pdf:nexttemplate name="portrait_page" />
    <pdf:nextpage />
    
    <h3 style="color: #003366; margin-top: 30px; margin-bottom: 15px; text-align: center; font-size: 16pt;">CPIT Analysis Results</h3>
    <table style="width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 10pt;">
        <thead>
            <tr>
                <th style="background-color: #003366; color: white; padding: 8px; border: 1px solid #999; text-align: center; width: 10%;">Num</th>
                <th style="background-color: #003366; color: white; padding: 8px; border: 1px solid #999; text-align: left; width: 60%;">Item</th>
                <th style="background-color: #003366; color: white; padding: 8px; border: 1px solid #999; text-align: center; width: 30%;">Value</th>
            </tr>
        </thead>
        <tbody>
            {% for row in cpit_rows %}
            <tr>
                <td style="padding: 6px; border: 1px solid #999; text-align: center;">{{ row['Num'] }}</td>
                <td style="padding: 6px; border: 1px solid #999; text-align: left;">
                    {{ row['Item'] }} <span style="color: #003366; font-weight: bold; margin-left: 5px;">{{ row['Unit'] }}</span>
                </td>
                <td style="padding: 6px; border: 1px solid #999; text-align: center; font-weight: bold; color: #333;">{{ row['Value'] }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
"""

# =============================================================================
# FUNÇÕES DE BANCO DE DADOS
# =============================================================================
def get_db_connection():
    return sql.connect(server_hostname=DB_HOSTNAME, http_path=DB_HTTP_PATH, access_token=DB_TOKEN)

def carregar_dados_do_databricks():
    novos_dados = {}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for key, db_col in MAPA_COLUNAS.items():
            query = f"SELECT DISTINCT `{db_col}` FROM {TABELA_DB} WHERE `{db_col}` IS NOT NULL ORDER BY `{db_col}` ASC"
            cursor.execute(query)
            novos_dados[key] = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return novos_dados
    except Exception as e:
        st.error(f"Erro DB: {e}")
        return {k: [] for k in MAPA_COLUNAS.keys()}

def adicionar_item_databricks(json_key, novo_valor):
    """Insere um novo valor na respectiva coluna do Databricks de forma silenciosa."""
    if json_key not in MAPA_COLUNAS: return False
    coluna_db = MAPA_COLUNAS[json_key]
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Escapa aspas simples (caso alguém digite d'Avila, por exemplo) para não quebrar o SQL
        valor_seguro = novo_valor.replace("'", "''") 
        query = f"INSERT INTO {TABELA_DB} (`{coluna_db}`) VALUES ('{valor_seguro}')"
        cursor.execute(query)
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro silencioso ao salvar '{novo_valor}' no Databricks: {e}")
        return False

# =============================================================================
# LÓGICA DE LIMPEZA E PROCESSAMENTO (CORE DO T-DAS) - COMPLETO
# =============================================================================

def clean_name_for_search(name):
    """Limpa nomes de colunas para facilitar o 'match'."""
    name = str(name)
    name = re.split(r'///|//|\s\(', name)[0]
    name = re.sub(r'[^a-zA-Z0-9]+', ' ', name)
    return name.lower().strip()

def find_best_header_row_raw(rows, search_depth=20):
    """Encontra o cabeçalho na lista crua."""
    HEADER_KEYWORDS = ['Time_1Hz', 'Ambiente', 'Força', 'EngineSpeed', 'Pressão', 'Time', 'Tempo']
    best_match_score = -1
    header_row_index = 0
    
    for i, row in enumerate(rows[:search_depth]):
        row_text = ' '.join([str(cell) for cell in row if cell is not None]).lower()
        current_score = sum(1 for keyword in HEADER_KEYWORDS if keyword.lower() in row_text)
        if current_score > best_match_score:
            best_match_score = current_score
            header_row_index = i
            
    return header_row_index if best_match_score > 0 else 0

def clean_number_string(val):
    """
    Limpeza robusta HÍBRIDA (Aceita tanto 1.234 quanto 1,234).
    """
    if val is None: return np.nan
    if isinstance(val, (bytes, bytearray, np.bytes_)):
        s_val = val.decode('utf-8', errors='ignore').strip()
    else:
        s_val = str(val).strip()

    # MF4 pode entregar valores codificados com unidade, por exemplo b'0 V'.
    s_val = re.sub(r"^b['\"](.*)['\"]$", r"\1", s_val).strip()
    
    # Lista de valores nulos comuns
    if not s_val or s_val.upper() in ['NOVALUE', 'NAN', 'N/A', '#REF!', 'NULL', 'None']:
        return np.nan

    try:
        # 1. Tenta conversão direta (padrão Python/Americano: 12.34)
        return float(s_val)
    except ValueError:
        pass

    try:
        # 2. Se falhar, verifica se é formato Brasileiro/Europeu (1.000,00 ou 1,23)
        if ',' in s_val:
            # Se tem ponto E vírgula (ex: 1.200,50), remove o ponto de milhar
            if '.' in s_val:
                s_val = s_val.replace('.', '')
            # Troca vírgula decimal por ponto
            s_val = s_val.replace(',', '.')
            return float(s_val)
    except ValueError:
        pass

    # Aceita valores numéricos acompanhados da unidade do canal, como "0 V".
    match = re.search(r"[-+]?(?:\d+(?:[.,]\d*)?|[.,]\d+)", s_val)
    if match:
        try:
            return float(match.group(0).replace(',', '.'))
        except ValueError:
            pass

    return np.nan


def encontrar_melhor_coluna_velocidade(df):
    candidatos = []
    for col in df.columns:
        c = clean_name_for_search(col)
        if (
            "vehiclespeed" in c
            or "vitesse" in c
            or "vel veic" in c
            or "spd veh" in c
            or "speed veh" in c
        ):
            try:
                s = pd.to_numeric(df[col], errors='coerce').fillna(0)
                v_max = s.max()
                candidatos.append((col, v_max))
            except: continue
     
    if not candidatos: return None
    candidatos.sort(key=lambda x: x[1], reverse=True)
    return candidatos[0][0]

def detectar_fases_cool_down_rolling(df, col_v, t):
    v_series = pd.to_numeric(df[col_v], errors='coerce').fillna(0)
    v_smooth = v_series.rolling(window=30, min_periods=5, center=True).median()
     
    conditions = [(v_smooth < 5), (v_smooth >= 5) & (v_smooth < 80), (v_smooth >= 80)]
    choices = [0, 1, 2]
    raw_class = np.select(conditions, choices, default=-1)
     
    df_temp = pd.DataFrame({'time': t, 'class': raw_class})
    df_temp['group'] = (df_temp['class'] != df_temp['class'].shift()).cumsum()
     
    blocks = df_temp.groupby('group').agg(start=('time', 'min'), end=('time', 'max'), cls=('class', 'first')).reset_index()
     
    fases = []
    for block_position, (_, b) in enumerate(blocks.iterrows()):
        duration = b['end'] - b['start']
        if duration < 45: continue 

        # A desaceleração para o idle pode criar um bloco curto de Phase 1
        # entre a Phase 2 e a Phase 3. Esse bloco é transição, não uma nova fase.
        if block_position + 1 < len(blocks):
            next_block = blocks.iloc[block_position + 1]
            next_duration = next_block['end'] - next_block['start']
            if b['cls'] == 1 and next_block['cls'] == 0 and duration < 120 and next_duration >= 600:
                if fases and fases[-1]['Phase_Name'] == 'Phase 2':
                    fases[-1]['t_fim'] = next_block['start']
                continue
         
        cls = b['cls']
        name, color = None, None
         
        if cls == 1: name, color = "Phase 1", CORES_FAIXAS["Phase 1"]
        elif cls == 2: name, color = "Phase 2", CORES_FAIXAS["Phase 2"]
        elif cls == 0: 
            if duration < 600: name, color = "Idle", CORES_FAIXAS["Idle"]
            else: name, color = "Phase 3", CORES_FAIXAS["Phase 3"]
         
        if name:
            if fases and fases[-1]['Phase_Name'] == name: fases[-1]['t_fim'] = b['end']
            else: fases.append({'Phase_Name': name, 't_inicio': b['start'], 't_fim': b['end'], 'Phase_Color': color})
                 
    return pd.DataFrame(fases)

def detectar_fases_us_city_rolling(df, col_v, t):
    v_series = pd.to_numeric(df[col_v], errors='coerce').fillna(0)
    window_size = 60
    v_min_local = v_series.rolling(window=window_size, min_periods=5, center=True).min()
    v_max_local = v_series.rolling(window=window_size, min_periods=5, center=True).max()
    v_mean_local = v_series.rolling(window=window_size, min_periods=5, center=True).mean()

    is_pre_cond = (v_mean_local > 55) & (v_min_local > 20)
    is_fase_1 = (v_max_local > 45) & (~is_pre_cond)
    is_fase_2 = (v_max_local <= 45) & (v_max_local > 2) & (~is_pre_cond)

    conditions = [is_pre_cond, is_fase_1, is_fase_2]
    choices = [0, 1, 2]
     
    raw_class = np.select(conditions, choices, default=-1)
    smooth_class = pd.Series(raw_class).rolling(window=30, min_periods=1, center=True).median().fillna(-1).astype(int)

    df_temp = pd.DataFrame({'time': t, 'class': smooth_class})
    df_temp['group'] = (df_temp['class'] != df_temp['class'].shift()).cumsum()
     
    blocks = df_temp.groupby('group').agg(start=('time', 'min'), end=('time', 'max'), cls=('class', 'first')).reset_index()
     
    fases = []
    map_names = {
        0: ("Phase 0", CORES_FAIXAS["Pre-cond."]),
        1: ("Phase 1", CORES_FAIXAS["Ciclos 0–65"]),
        2: ("Phase 2", CORES_FAIXAS["Ciclos 0–16"])
    }
     
    for _, b in blocks.iterrows():
        if b['cls'] in map_names and (b['end'] - b['start'] > 30):
            name, color = map_names[b['cls']]
            if fases and fases[-1]['Phase_Name'] == name: fases[-1]['t_fim'] = b['end']
            else: fases.append({'Phase_Name': name, 't_inicio': b['start'], 't_fim': b['end'], 'Phase_Color': color})
                 
    return pd.DataFrame(fases)

def detectar_fases_do_teste(df, tipo_teste):
    if df.empty: return pd.DataFrame()
    col_v = encontrar_melhor_coluna_velocidade(df)
    if not col_v: return pd.DataFrame()
    t_values = df['Time [s]'].values

    if tipo_teste == "US City": return detectar_fases_us_city_rolling(df, col_v, t_values)
    elif tipo_teste == "Cool Down": return detectar_fases_cool_down_rolling(df, col_v, t_values)
    else: return pd.DataFrame()


def carregar_mf4(uploaded_file):
    """Lê um MF4 e devolve uma tabela temporal compatível com o pipeline atual."""
    arquivo_temporario = None
    mdf = None
    try:
        uploaded_file.seek(0)
        with tempfile.NamedTemporaryFile(suffix='.mf4', delete=False) as arquivo:
            arquivo.write(uploaded_file.getbuffer())
            arquivo_temporario = arquivo.name

        mdf = MDF(arquivo_temporario)
        nomes_disponiveis = list(mdf.channels_db)
        termos_relevantes = (
            'speed', 'vehicle', 'pedal', 'engine', 'coolant', 'ambient',
            'temp', 'oil', 'torque', 'gear', 'pressure', 'compressor',
            'condens', 'vent', 'blower', 'hvac', 'ac_', 'head', 'cabin',
            'panel', 'velocidade', 'ambiente', 'umidade', 'radiação',
            'potência', 'força', 'pressão', 'rpm', 'cabeça', 'difusor',
            'habitáculo', 'evap', 'bocal', 'filtro', 'borboleta',
            'radiador', 'aquecedor', 'condensador', 'txv', 'gás',
            'distância', 'consumo', 'média', 'time_1hz'
        )
        canais = [
            nome for nome in nomes_disponiveis
            if nome != 'time' and any(termo in nome.lower() for termo in termos_relevantes)
        ]
        if not canais:
            raise ValueError('Nenhum canal relevante foi encontrado no MF4.')

        # Alguns MF4 possuem canais com o mesmo nome no mesmo grupo. O asammdf
        # exige a referência completa nesses casos: nome, grupo e índice.
        referencias_canais = [
            (nome, grupo, indice)
            for nome in canais
            for grupo, indice in mdf.channels_db.get(nome, ())
        ]

        df = mdf.to_dataframe(
            channels=referencias_canais,
            raster=1.0,
            time_from_zero=True,
            reduce_memory_usage=False
        ).reset_index()
        df.rename(columns={df.columns[0]: 'Time [s]'}, inplace=True)

        aliases = {
            'VeBSWR_CANR_Vehicle_Speed': 'VehicleSpeedVSOSig',
            'VeAPSR_Pct_AccelPedalEffPosition': 'GasPedalPosition',
            'VeENGR_T_EngCoolantTemp': 'EngineWaterTemp',
            'VeESPR_n_EngineSpeed': 'EngineSpeed',
            'VeTRNR_e_ActualGear': 'GearEngaged',
            'VeTHMR_T_EstAmbAirTemp': 'Ambiente_(teto_carro)',
            'VeAATR_T_EstAmbAirTemp': 'Ambiente',
            'VeTMIR_T_TransOilTemp': 'TransmissionTemperatura',
            'AC_HEAD_PRESSURE_SCALED': 'Pressão Alta',
            'Ambiente Teto': 'Ambiente_(teto_carro)',
            'Velocidade': 'VehicleSpeedVSOSig',
            'RPM eletro': 'RPM Eletro',
            'Cabeça Motorista Esqu.': 'Cabeça_motorista_esquerdo',
            'Cabeça Motorista Direito': 'Cabeça_motorista_direito',
            'Cabeça Passag. Esqu.': 'Cabeça_passageiro_esquerdo',
            'Cabeça Passag. Direito': 'Cabeça_passageiro_direito',
            'Cabeça Esqu. Passa.Esqu.2ªFila': 'Cabeça_esquerda_passageiro_esquerdo_2ª_fileira',
            'Cabeça Dir. Passa.Esqu.2ªFila': 'Cabeça_direita_passageiro_esquerdo_2ª_fileira',
            'Cabeça Esqu. Passa.Dir.2ªFila': 'Cabeça_esquerda_passageiro_direito_2ª_fileira',
            'Cabeça Dir. Passa.Dir.2ªFila': 'Cabeça_direita_passageiro_direito_2ª_fileira',
            'Entrada Compressor': 'Entrada_Compressor',
            'Saída Compressor': 'Saida_Compressor',
            'Entrada Condensador': 'Entrada_Condensador',
            'Saída Condensador': 'Saida_Condensador',
            'Entrada TXV': 'Entrada_TXV',
            'Saída TXV': 'Saida_TXV',
            'Entrada Radiador HT': 'Entrada_Radiador_HT',
            'Bocal aspiração': 'Entrada_Bocal_de_Aspiração',
            'Entrada filtro de ar': 'Entrada_Filtro_de_Ar',
            'Saída filtro de ar': 'Saida_Filtro_de_Ar',
            'Borboleta': 'Entrada_de_Ar_na_borboleta',
            'Pressão Baixa': 'Pressão Baixa',
        }
        nomes_originais = []
        for coluna in df.columns[1:]:
            nome_base = re.sub(r'_\d+$', '', str(coluna))
            nomes_originais.append(nome_base)

        source_channels = {
            aliases.get(coluna, coluna): coluna
            for coluna in nomes_originais
        }
        df.rename(columns=aliases, inplace=True)
        df.attrs['source_channels'] = source_channels
        df['Time [s]'] = pd.to_numeric(df['Time [s]'], errors='coerce')
        df = df.dropna(subset=['Time [s]']).reset_index(drop=True)
        return df
    except Exception as exc:
        st.error(f"Erro na leitura do MF4: {exc}")
        return None
    finally:
        if mdf is not None:
            try:
                mdf.close()
            except Exception:
                pass
        if arquivo_temporario and os.path.exists(arquivo_temporario):
            try:
                os.unlink(arquivo_temporario)
            except PermissionError:
                st.warning('O arquivo temporário do MF4 ainda está em uso e será removido pelo sistema.')


def carregar_e_tratar_dados(uploaded_file):
    """
    Versão BLINDADA para US City e arquivos grandes.
    - Reseta o ponteiro do arquivo (seek(0)) a cada tentativa.
    - Tenta codificações diferentes (utf-8, latin1, cp1252).
    - Força separadores comuns se o 'sniffer' falhar.
    """
    try:
        rows = []
        filename = uploaded_file.name.lower()

        if filename.endswith('.mf4'):
            return carregar_mf4(uploaded_file)

        # 1. TENTATIVA EXCEL (Calamine - Mais rápido e seguro para xlsx)
        if filename.endswith(('.xlsx', '.xls', '.xlsm', '.xlsb')):
            try:
                uploaded_file.seek(0) # Reseta ponteiro
                wb = CalamineWorkbook.from_filelike(uploaded_file)
                rows = wb.get_sheet_by_index(0).to_python()
            except Exception as e_excel:
                # Se falhar o Calamine, tenta pandas padrão para Excel
                try:
                    uploaded_file.seek(0)
                    df_temp = pd.read_excel(uploaded_file)
                    rows = df_temp.values.tolist()
                except:
                    pass # Segue para tentar como CSV/Texto se falhar

        # 2. TENTATIVA CSV / TXT (Se não for Excel ou se falhou)
        if not rows:
            separadores = [';', ',', '\t'] # Ordem de preferência
            encodings = ['utf-8', 'latin1', 'cp1252'] # US City as vezes é latin1
            
            df_lido = None
            
            # Loop de Tentativas (Força Bruta inteligente)
            for enc in encodings:
                if df_lido is not None: break
                for sep in separadores:
                    try:
                        uploaded_file.seek(0) # CRUCIAL: Reseta o arquivo para o início
                        # Tenta ler apenas as primeiras linhas para ver se não dá erro
                        df_temp = pd.read_csv(uploaded_file, header=None, sep=sep, encoding=enc, engine='python')
                        
                        # Validação simples: Se leu apenas 1 coluna, provavelmente o separador está errado
                        if df_temp.shape[1] > 1:
                            df_lido = df_temp
                            break
                    except:
                        continue
            
            # Se a força bruta falhou, tenta o 'sniffer' automático (sep=None)
            if df_lido is None:
                try:
                    uploaded_file.seek(0)
                    df_lido = pd.read_csv(uploaded_file, header=None, sep=None, engine='python', encoding='latin1')
                except Exception as e:
                    st.error(f"Erro fatal de leitura: {e}")
                    return None
            
            if df_lido is not None:
                rows = df_lido.values.tolist()

        if not rows: 
            st.error("Arquivo vazio ou formato não reconhecido.")
            return None

        # --- A PARTIR DAQUI A LÓGICA É A MESMA QUE JÁ ESTAVA FUNCIONANDO ---
        
        # Encontrar cabeçalho
        header_idx = find_best_header_row_raw(rows)
        header_row = rows[header_idx]
        data_rows = rows[header_idx + 1:]
        
        columns = [str(c).strip() for c in header_row]
        df = pd.DataFrame(data_rows, columns=columns)
        
        # Cortes de cabeçalho/rodapé
        if CONFIG["ROWS_TO_SKIP_AFTER_HEADER"] > 0:
            df = df.iloc[CONFIG["ROWS_TO_SKIP_AFTER_HEADER"]:]
        if CONFIG["FOOTER_ROWS_TO_SKIP"] > 0:
            df = df.iloc[:-CONFIG["FOOTER_ROWS_TO_SKIP"]]
            
        df.reset_index(drop=True, inplace=True)

        # Limpeza de números (Sua versão corrigida híbrida)
        for col in df.columns:
            df[col] = df[col].apply(clean_number_string)

        # Configura Coluna de Tempo
        time_col_original = CONFIG["TIME_COLUMN_NAME"]
        if time_col_original not in df.columns and "Time" in df.columns:
            time_col_original = "Time"
        
        # Remove linhas vazias
        cols_dados = [c for c in df.columns if c != time_col_original and c != "Time [s]"]
        if cols_dados:
            df = df.dropna(subset=cols_dados, how='all')

        if time_col_original in df.columns:
            df["Time [s]"] = df[time_col_original]
        else:
            df["Time [s]"] = df.index.astype(float)
        
        # Garante float no tempo
        df["Time [s]"] = pd.to_numeric(df["Time [s]"], errors='coerce')
        df = df.dropna(subset=["Time [s]"])
        
        # Reordena
        cols = ["Time [s]"] + [c for c in df.columns if c != "Time [s]"]
        return df[cols]

    except Exception as e:
        st.error(f"Erro no processamento geral: {e}")
        return None
        
def detectar_tipo_veiculo(df):
    """Varre as colunas para saber se é xF ou xP."""
    candidatos = {}
    cols_df_limpas = {str(col): clean_name_for_search(col) for col in df.columns}
    
    # Usa o dicionário global TEST_MAPPINGS
    for test_data in TEST_MAPPINGS.values():
        for chart_data in test_data.values():
            for var_data in chart_data.values():
                if "sources" not in var_data: continue
                for tipo, source_candidates in var_data["sources"].items():
                    if not isinstance(source_candidates, list): continue
                    if not any(isinstance(i, list) for i in source_candidates): source_candidates = [source_candidates]
                    
                    for group in source_candidates:
                        for candidate in group:
                            nome_parcial = candidate['name'] if isinstance(candidate, dict) else candidate
                            if not nome_parcial: continue
                            nome_parcial_limpo = clean_name_for_search(nome_parcial)
                            
                            for col_limpa in cols_df_limpas.values():
                                if nome_parcial_limpo in col_limpa:
                                    candidatos.setdefault(tipo, 0)
                                    candidatos[tipo] += 1
                                    break
                                    
    if not any(candidatos.values()): return "Not detected"
    return max(candidatos, key=candidatos.get)

def filtrar_e_resetar_tempo(df):
    """
    Corta o início do arquivo (Idle) baseado em Velocidade e Pedal,
    usando o MAPA REAL do dicionário, igual ao VSCode.
    """
    if df is None or df.empty: return df
    
    col_tempo = 'Time [s]'
    
    # 1. Encontrar nomes reais das colunas de Velocidade e Pedal usando o TEST_MAPPINGS
    candidatos_v = set()
    candidatos_p = set()
    
    # Varre o dicionário global para achar os nomes esperados (ex: VehicleSpeedVSOSig)
    for test_data in TEST_MAPPINGS.values():
        for chart_data in test_data.values():
            if "V_VEHICLE_SPEED [km/h]" in chart_data:
                src = chart_data["V_VEHICLE_SPEED [km/h]"].get("sources", {})
                for grps in src.values():
                    g = [grps] if not any(isinstance(i, list) for i in grps) else grps
                    for grp in g: 
                        for cand in grp: 
                            c_name = cand['name'] if isinstance(cand, dict) else cand
                            candidatos_v.add(clean_name_for_search(c_name))
                            
            if "GAS_PEDAL_POSITION [%]" in chart_data:
                src = chart_data["GAS_PEDAL_POSITION [%]"].get("sources", {})
                for grps in src.values():
                    g = [grps] if not any(isinstance(i, list) for i in grps) else grps
                    for grp in g: 
                        for cand in grp: 
                            c_name = cand['name'] if isinstance(cand, dict) else cand
                            candidatos_p.add(clean_name_for_search(c_name))

    # 2. Mapeia colunas do DataFrame atual
    df_cols_map = {clean_name_for_search(str(c)): str(c) for c in df.columns}
    
    def find_col_in_df(candidates_set):
        best_col, best_score = None, 0.0
        for cand in candidates_set:
            for dc_clean, dc_real in df_cols_map.items():
                score = SequenceMatcher(None, cand, dc_clean).ratio()
                if score > best_score: 
                    best_score, best_col = score, dc_real
        return best_col if best_score >= CONFIG["SIMILARITY_THRESHOLD"] else None

    col_v = find_col_in_df(candidatos_v)
    col_p = find_col_in_df(candidatos_p)

    # Se não achou as colunas, retorna o DF original sem cortar (causa do timestamp grande)
    if not col_v or not col_p: 
        return df

    try:
        # Garante numérico
        v_series = pd.to_numeric(df[col_v], errors='coerce').fillna(0)
        p_series = pd.to_numeric(df[col_p], errors='coerce').fillna(0)
        
        # Lógica de corte (Carro andando E pedal pressionado)
        cond = (v_series > 0) & (p_series > 0)
        
        # Rolling window para evitar ruído (igual ao script local)
        cond_soma = cond.astype(int).rolling(window=5, min_periods=5).sum()
        
        # Pega o primeiro índice onde a condição foi verdadeira por 5 pontos seguidos
        idx_inicio = cond_soma[cond_soma == 5].first_valid_index()
        
        if idx_inicio is not None:
            df_cortado = df.loc[idx_inicio:].copy()
            # Reseta o tempo para zero
            df_cortado[col_tempo] = df_cortado[col_tempo] - df_cortado[col_tempo].iloc[0]
            df_cortado.reset_index(drop=True, inplace=True)
            return df_cortado
            
    except Exception as e:
        print(f"Erro ao filtrar tempo: {e}")
        pass
        
    return df

def executar_logica_processamento(df_processado, tipo_prova, tipo_veiculo):
    """
    Processamento idêntico ao T-DAS Local, incluindo fallback do Cool Down.
    """
    mapa_da_prova = TEST_MAPPINGS.get(tipo_prova, {})
    df_final = pd.DataFrame()
    df_final["Time [s]"] = df_processado["Time [s]"]
    source_channels = df_processado.attrs.get('source_channels', {})
    output_sources = {}
    
    # Cria dicionário de colunas disponíveis limpas para busca rápida
    colunas_disponiveis = {str(c): clean_name_for_search(str(c)) for c in df_processado.columns if c != "Time [s]"}
    
    # 1. Mapeamento Geral
    for _, mapa_variaveis in mapa_da_prova.items():
        for var_grafico, meta in mapa_variaveis.items():
            if "sources" in meta:
                priority_groups = meta['sources'].get(tipo_veiculo, [])
                if not priority_groups: continue
                if not any(isinstance(i, list) for i in priority_groups): priority_groups = [priority_groups]
                
                col_encontrada = False
                for group in priority_groups:
                    if col_encontrada: break
                    series_do_grupo = {}
                    
                    for candidate in group:
                        col_name = candidate['name'] if isinstance(candidate, dict) else candidate
                        transform = candidate.get('transform') if isinstance(candidate, dict) else None
                        target = clean_name_for_search(col_name)
                        
                        best_match, best_score = None, 0.0
                        for col_real, col_limpa in colunas_disponiveis.items():
                            score = SequenceMatcher(None, target, col_limpa).ratio()
                            if score > best_score: best_score, best_match = score, col_real
                        
                        if best_score >= CONFIG["SIMILARITY_THRESHOLD"]:
                            s_data = df_processado[best_match].apply(clean_number_string)
                            # Tratamento para remover zeros em temperaturas (igual ao local)
                            if "[°C]" in var_grafico or var_grafico.startswith("T_"):
                                s_data = s_data.replace(0, np.nan)
                                
                            if transform == "/100": s_data = s_data / 100
                            series_do_grupo[best_match] = s_data
                    
                    if series_do_grupo:
                        df_final[var_grafico] = pd.DataFrame(series_do_grupo).mean(axis=1)
                        output_sources[var_grafico] = [
                            source_channels.get(coluna, coluna)
                            for coluna in series_do_grupo
                        ]
                        col_encontrada = True
    
    # 2. Cálculos (Mean/Diff)
    for _, mapa_variaveis in mapa_da_prova.items():
        for var_grafico, meta in mapa_variaveis.items():          
            if "calculation" in meta:
                calc = meta["calculation"]
                if calc["type"] == "mean":
                    cols = [c for c in calc.get("of", []) if c in df_final.columns]
                    if cols: df_final[var_grafico] = df_final[cols].mean(axis=1)
                elif calc["type"] == "difference":
                    c = calc.get("between", [])
                    if len(c)==2 and c[0] in df_final.columns and c[1] in df_final.columns:
                        df_final[var_grafico] = df_final[c[0]] - df_final[c[1]]

    # 3. Lógica Específica do COOL DOWN (CRUCIAL PARA FICAR IGUAL AO LOCAL)
    if tipo_prova == "Cool Down":
        mapping_cpit = {
            "T_A_AMB [°C]": ["Ambiente_(teto_carro)", "Ambiente"],
            "T_A_HEAD_AVG_R1 [°C]": ["Cabeça_motorista_esquerdo", "Temp_Cabeca_1"],
            "T_A_HEAD_AVG_R2 [°C]": ["Cabeça_esquerda_passageiro_esquerdo_2ª_fileira", "Temp_Cabeca_2"],
            "P_R_HIGH_PRESSURE [bar]": ["Pressão Alta", "High_Pressure"],
            "T_R_COMP_O [ºC]": ["Saida_Compressor", "Comp_Outlet"]
        }
        for target, candidates in mapping_cpit.items():
            if target not in df_final.columns:
                for cand in candidates:
                    cand_clean = clean_name_for_search(cand)
                    match = None
                    for real_col, real_col_clean in colunas_disponiveis.items():
                        if cand_clean in real_col_clean: 
                            match = real_col
                            break
                    if match:
                        df_final[target] = df_processado[match]
                        output_sources[target] = [source_channels.get(match, match)]
                        break

    # Mantém os canais numéricos relevantes do MF4 para inspeção detalhada.
    # Eles ficam disponíveis no grupo "Raw MF4 Signals" da visualização.
    if tipo_prova == "RFR03":
        mapped_columns = set(df_final.columns)
        for raw_column in df_processado.columns:
            if raw_column == "Time [s]" or raw_column in mapped_columns:
                continue
            converted = df_processado[raw_column].apply(clean_number_string)
            if converted.notna().any():
                df_final[raw_column] = converted
                output_sources[raw_column] = [source_channels.get(raw_column, raw_column)]

    df_final.attrs['source_channels'] = output_sources
    return df_final   

def gerar_imagem_grafico_matplotlib(df_plot, nome_grafico, cols_to_plot, df_fases=None,pontos_marcados=None):
    """Gera imagem estática com fases no fundo (Idêntico ao local)"""
    fig, ax = plt.subplots(figsize=(10, 5.5)) 
    ax.set_prop_cycle(color=CORES_PADRAO)
    
    # 1. Pinta as fases no fundo
    if df_fases is not None and not df_fases.empty:
        for _, row in df_fases.iterrows():
            cor_rgba = row['Phase_Color']
            # Converte 'rgba(255, 0, 0, 0.15)' para tupla do matplotlib
            match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)', cor_rgba)
            if match:
                r, g, b, alpha = map(float, match.groups())
                cor_mpl = (r / 255, g / 255, b / 255, alpha)
            else:
                cor_mpl = (0.5, 0.5, 0.5, 0.1)
            ax.axvspan(row['t_inicio'], row['t_fim'], color=cor_mpl, zorder=0)

    # 2. Plota as linhas das variáveis
    for col in cols_to_plot:
        ax.plot(df_plot["Time [s]"], df_plot[col], label=col, linewidth=1.2, zorder=2)
    
    # ======== DESENHA AS MARCAÇÕES NO PDF ========
    if pontos_marcados:
        for x_pt, y_pt in pontos_marcados:
            ax.plot(x_pt, y_pt, 'x', color='red', markersize=8, markeredgewidth=2, zorder=10)
            ax.annotate(
                f"({x_pt:.1f}s, {y_pt:.1f})", 
                xy=(x_pt, y_pt),
                xytext=(8, 8), 
                textcoords='offset points', 
                fontsize=8, 
                color='black', 
                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.9, edgecolor='red'),
                zorder=10
            )
    # =============================================
    
    
    ax.set_xlabel("Time [s]", fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.6)
    
    # 3. Monta a Legenda Combinada (Linhas + Blocos de Fase)
    handles, labels = ax.get_legend_handles_labels()
    if df_fases is not None and not df_fases.empty:
        fases_unicas = df_fases[['Phase_Name', 'Phase_Color']].drop_duplicates()
        for _, row in fases_unicas.iterrows():
            match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)', row['Phase_Color'])
            if match:
                r, g, b, a = map(float, match.groups())
                cor = (r/255, g/255, b/255, a)
            else:
                cor = (0.8, 0.8, 0.8, 0.15)
            # Cria um quadradinho para a legenda
            patch = mpatches.Patch(color=cor, label=row['Phase_Name'])
            handles.append(patch)
            labels.append(row['Phase_Name'])
            
    ax.legend(handles=handles, labels=labels, loc='upper left', bbox_to_anchor=(1.02, 1.0), fontsize=8, title="Series & Phases")
    
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', dpi=150)
    plt.close(fig) 
    
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def get_image_base64(filename):
    """Lê uma imagem local e converte para base64. Retorna um pixel transparente se falhar."""
    pixel_vazio = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(base_dir, filename)

    if os.path.exists(filepath):
        try:
            with open(filepath, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode("utf-8")
                # Adiciona o prefixo correto dependendo da extensão
                ext = filepath.split('.')[-1].lower()
                mime = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
                return f"data:{mime};base64,{encoded}"
        except Exception as e:
            print(f"Erro ao ler imagem {filepath}: {e}")
            return pixel_vazio
    else:
        return pixel_vazio

def calcular_cpit(df):
    """Calcula os valores da tabela CPIT baseado no tempo (Time [s])."""
    def val_at(col, time_s):
        if col not in df.columns: return "N/A"
        try:
            idx = (df['Time [s]'] - time_s).abs().idxmin()
            return f"{df.loc[idx, col]:.1f}"
        except: return "N/A"

    def val_max(col):
        if col not in df.columns: return "N/A"
        try:
            return f"{df[col].max():.1f}"
        except: return "N/A"

    def val_rise_idle(col):
        if col not in df.columns:
            return "N/A"
        df_fases = st.session_state.get('df_fases', pd.DataFrame())
        if not df_fases.empty:
            idle = df_fases[df_fases['Phase_Name'] == 'Idle']
            if not idle.empty:
                t_start = idle.iloc[0]['t_inicio']
                t_end = idle.iloc[0]['t_fim']
                v_start = val_at(col, t_start)
                mask = (df['Time [s]'] >= t_start) & (df['Time [s]'] <= t_end)
                if not mask.any(): return "N/A"
                v_max_idle = df.loc[mask, col].max()
                if v_start != "N/A":
                    try: return f"{float(v_max_idle) - float(v_start):.1f}"
                    except: return "N/A"
        return "N/A"
    
    dados = [
        {"Num": "1", "Item": "Max Panel Temp @15 min", "Unit": "[°C]", "Value": val_at("T_A_AMB [°C]", 900)},
        {"Num": "2", "Item": "Max Panel Temp @30 min", "Unit": "[°C]", "Value": val_at("T_A_AMB [°C]", 1800)},
        {"Num": "3", "Item": "Max Panel Temp @45 min", "Unit": "[°C]", "Value": val_at("T_A_AMB [°C]", 2700)},
        {"Num": "4", "Item": "Max Panel Temp Rise 20 min idle", "Unit": "[°C]", "Value": val_rise_idle("T_A_AMB [°C]")},
        {"Num": "5", "Item": "1st Row Avg Heads Temp @15 min", "Unit": "[°C]", "Value": val_at("T_A_HEAD_AVG_R1 [°C]", 900)},
        {"Num": "6", "Item": "1st Row Avg Heads Temp @30 min", "Unit": "[°C]", "Value": val_at("T_A_HEAD_AVG_R1 [°C]", 1800)},
        {"Num": "7", "Item": "1st Row Avg Heads Temp @45 min", "Unit": "[°C]", "Value": val_at("T_A_HEAD_AVG_R1 [°C]", 2700)},
        {"Num": "8", "Item": "1st Row Avg Heads Temp @20 min idle", "Unit": "[°C]", "Value": val_rise_idle("T_A_HEAD_AVG_R1 [°C]")},
        {"Num": "9", "Item": "2nd Row Avg Heads Temp @15 min", "Unit": "[°C]", "Value": val_at("T_A_HEAD_AVG_R2 [°C]", 900)},
        {"Num": "10", "Item": "2nd Row Avg Heads Temp @30 min", "Unit": "[°C]", "Value": val_at("T_A_HEAD_AVG_R2 [°C]", 1800)},
        {"Num": "11", "Item": "2nd Row Avg Heads Temp @45 min", "Unit": "[°C]", "Value": val_at("T_A_HEAD_AVG_R2 [°C]", 2700)},
        {"Num": "12", "Item": "2nd Row Avg Heads Temp @20 min idle", "Unit": "[°C]", "Value": val_rise_idle("T_A_HEAD_AVG_R2 [°C]")},
        {"Num": "13", "Item": "Maximum pressure", "Unit": "[bar]", "Value": val_max("P_R_HIGH_PRESSURE [bar]")},
        {"Num": "14", "Item": "Max compressor outlet temp", "Unit": "[°C]", "Value": val_max("T_R_COMP_O [ºC]")}
    ]
    return pd.DataFrame(dados)

def render_tdas():
    inject_custom_css()
    # Cache das listas do DB
    if 'db_lists' not in st.session_state:
        with st.spinner("Carregando banco de dados..."):
            st.session_state['db_lists'] = carregar_dados_do_databricks()

    tab1, tab2 = st.tabs(["1. Setup & Processing", "2. Visualization & Export"])

    def combobox_dinamico(label, lista_db, key_sufix):
        """Cria um selectbox que vira input de texto se o usuário quiser adicionar um novo valor."""
        opcoes = [""] + lista_db + ["➕ Adicionar Novo..."]
    
        # 1. Pega a escolha do dropdown
        escolha = st.selectbox(f"{label}:", options=opcoes, key=f"sel_{key_sufix}")
    
        # 2. Se escolheu adicionar novo, mostra um campo de texto embaixo
        if escolha == "➕ Adicionar Novo...":
            novo_valor = st.text_input(f"Digite o novo {label} (será salvo no banco):", key=f"txt_{key_sufix}")
            return novo_valor.strip() if novo_valor else ""
        
        return escolha

    with tab1:
        st.subheader("Step 1: Select File")
        uploaded_file = st.file_uploader(
            "Browse...",
            type=["csv", "xlsx", "xls", "dat", "mf4"],
            label_visibility="collapsed"
        )

        if uploaded_file is not None:
            tamanho_mb = uploaded_file.size / (1024 * 1024)
            arquivo_id = f"{uploaded_file.name}:{uploaded_file.size}"
            if st.session_state.get('mf4_source_id') != arquivo_id:
                st.session_state['mf4_source_id'] = arquivo_id
                st.session_state['mf4_metadata'] = extrair_metadados_mf4(uploaded_file)
                metadados_mf4 = st.session_state['mf4_metadata']
                if metadados_mf4.get('test_date'):
                    st.session_state['meta_test_date'] = datetime.strptime(
                        metadados_mf4['test_date'], '%Y-%m-%d'
                    ).date()
                if metadados_mf4.get('observations'):
                    st.session_state['meta_observations'] = metadados_mf4['observations']

            st.markdown(
                f"""
                <div class="upload-success-card">
                    <div class="upload-success-icon">✓</div>
                    <div>
                        <div class="upload-success-title">File uploaded successfully</div>
                        <div class="upload-success-description">{uploaded_file.name} · {tamanho_mb:.2f} MB</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.session_state.get('mf4_metadata'):
                st.caption("Metadados disponíveis no MF4 foram preenchidos automaticamente; confirme os campos antes do processamento.")
    
        st.subheader("Step 2: Report Info")
        col_left, col_right = st.columns(2)
    
        with col_left:
            data_selecionada = st.date_input(
                "Test date:",
                value=datetime.now().date(),
                format="YYYY-MM-DD",
                key="meta_test_date"
            )
            test_date = data_selecionada.strftime('%Y-%m-%d') if data_selecionada else ""
            project = combobox_dinamico("Project", st.session_state['db_lists'].get('projetos', []), 'projetos')
            chassis = combobox_dinamico("Chassis", st.session_state['db_lists'].get('chassis', []), 'chassis')
            transmission = combobox_dinamico("Transmission", st.session_state['db_lists'].get('transmissoes', []), 'transmissoes')
            market = combobox_dinamico("Market", st.session_state['db_lists'].get('mercados', []), 'mercados')
            phase = combobox_dinamico("Phase", st.session_state['db_lists'].get('fases', []), 'fases')
            proj_eng = combobox_dinamico("Proj Eng.", st.session_state['db_lists'].get('project_engineers', []), 'project_engineers')

        with col_right:
            test_performed = st.selectbox("Test Performed:", [""] + list(TEST_MAPPINGS.keys()))
            brand = combobox_dinamico("Brand", st.session_state['db_lists'].get('marcas', []), 'marcas')
            engine = combobox_dinamico("Engine", st.session_state['db_lists'].get('motores', []), 'motores')
            version = combobox_dinamico("Version", st.session_state['db_lists'].get('versoes_veiculo', []), 'versoes_veiculo')
            model_year = combobox_dinamico("Model Year", st.session_state['db_lists'].get('anos_modelo', []), 'anos_modelo')
            test_eng = combobox_dinamico("Test Eng.", st.session_state['db_lists'].get('test_engineers', []), 'test_engineers')

        # Mostra o tipo de veículo detectado (ou padrão se não processado ainda)
        v_type = st.session_state.get('detected_type', 'Not detected')
        st.markdown(f"**Vehicle Type:** `{v_type}`")
        observations = st.text_area(
            "Observations:",
            placeholder="Digite observações aqui...",
            key="meta_observations"
        )

        st.subheader("Step 3: Actions")
    
        # Botão principal de processamento
        if st.button("Load and Process Data", type="primary", use_container_width=True):
            if uploaded_file and test_performed != "":
                st.session_state['aguardando_confirmacao'] = True
            else:
                st.warning("Selecione um arquivo e o tipo de teste.")
            
        # 2. Lógica do Poka-Yoke: Exibe o aviso e os botões de Sim/Não
        if st.session_state.get('aguardando_confirmacao', False):
            # Exibe um bloco visual de alerta para o usuário
            st.warning(f"⚠️ **Atenção:** Você está prestes a processar os dados utilizando a lógica do teste **'{test_performed}'**. Tem certeza de que este é o teste correto?")
        
            col_conf_1, col_conf_2 = st.columns(2)
        
            with col_conf_1:
                if st.button("✅ Sim, processar os dados", type="primary", use_container_width=True):
                    # Limpa a tela de confirmação
                    st.session_state['aguardando_confirmacao'] = False
                
                    # --- AQUI COMEÇA SUA LÓGICA DE PROCESSAMENTO ORIGINAL ---
                    with st.spinner("Processing file...."):
                        st.session_state['metadata_ensaio'] = {
                            "test_date": test_date,
                            "project": project,
                            "chassis": chassis,
                            "transmission": transmission,
                            "market": market,
                            "phase": phase,
                            "project_engineer": proj_eng,
                            "test_performed": test_performed,
                            "brand": brand,
                            "engine_type": engine,
                            "vehicle_version": version,
                            "model_year": model_year,
                            "test_engineer": test_eng,
                            "observations": observations if 'observations' in locals() else "" 
                        }
                    
                        valores_digitados = {
                            'projetos': project, 'chassis': chassis, 'transmissoes': transmission,
                            'mercados': market, 'fases': phase, 'project_engineers': proj_eng,
                            'marcas': brand, 'motores': engine, 'versoes_veiculo': version,
                            'anos_modelo': model_year, 'test_engineers': test_eng
                        }
                    
                        for chave_db, valor in valores_digitados.items():
                            if valor: 
                                lista_atual = st.session_state['db_lists'].get(chave_db, [])
                                if valor not in lista_atual:
                                    if adicionar_item_databricks(chave_db, valor):
                                        st.session_state['db_lists'][chave_db].append(valor)
                                        st.session_state['db_lists'][chave_db].sort(key=str)
                    
                        try:
                            df_raw = carregar_e_tratar_dados(uploaded_file)
                        
                            if df_raw is not None:
                                tipo_v = detectar_tipo_veiculo(df_raw)
                                st.session_state['detected_type'] = tipo_v
                            
                                df_raw = filtrar_e_resetar_tempo(df_raw)
                                df_fases = detectar_fases_do_teste(df_raw, test_performed)
                                st.session_state['df_fases'] = df_fases
                            
                                df_clean = executar_logica_processamento(df_raw, test_performed, tipo_v)
                            
                                st.session_state['df_final'] = df_clean
                                st.success(f"Sucesso! Veículo detectado: {tipo_v}. Dados prontos na aba 2.")
                                st.rerun() 
                        except Exception as e:
                            st.error(f"Erro no processamento: {e}")

            with col_conf_2:
                # Botão de escape/cancelamento
                if st.button("❌ Não", type="secondary", use_container_width=True):
                    st.session_state['aguardando_confirmacao'] = False
                    st.rerun()
            
        # Botão de Download do CSV processado
 
        if 'df_final' in st.session_state:
            st.markdown("### 💾 Export Processed Data")
        
            # Cria duas colunas para os botões ficarem lado a lado
            col_dw1, col_dw2 = st.columns(2)
        
            with col_dw1:
                # --- LÓGICA DO EXCEL (Que você já tinha) ---
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    st.session_state['df_final'].to_excel(writer, index=False)
            
                excel_data = output.getvalue()
            
                st.download_button(
                    label="Download Excel (.xlsx)",
                    data=excel_data,
                    file_name=f"TDAS_Clean_{chassis if chassis else 'Data'}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with col_dw2:
                # --- NOVA LÓGICA DO CSV ---
                # Converte o dataframe para CSV (separado por vírgula e encode utf-8)
                csv_data = st.session_state['df_final'].to_csv(index=False).encode('utf-8')
            
                st.download_button(
                    label="Download CSV (.csv)",
                    data=csv_data,
                    file_name=f"TDAS_Clean_{chassis if chassis else 'Data'}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    with tab2:
        if 'df_final' in st.session_state:
            df_plot = st.session_state['df_final']
            prova_atual = test_performed  # Puxando o selectbox da aba 1
        
            if prova_atual and prova_atual in TEST_MAPPINGS:
                st.markdown(f"### View and Export: {prova_atual}")
            
            

                mapas_graficos = dict(TEST_MAPPINGS[prova_atual])
                graficos_padrao = list(mapas_graficos.keys())
                if prova_atual == "RFR03":
                    sinais_mapeados = {
                        sinal
                        for mapa in mapas_graficos.values()
                        for sinal in mapa
                    }
                    sinais_brutos = [
                        coluna for coluna in df_plot.columns
                        if coluna != "Time [s]" and coluna not in sinais_mapeados
                    ]
                    if sinais_brutos:
                        mapas_graficos["Raw MF4 Signals"] = {
                            sinal: {} for sinal in sinais_brutos
                        }

                graficos_disponiveis = list(mapas_graficos.keys())
                graficos_selecionados = st.multiselect(
                    "Selecione os gráficos para exibir/exportar:",
                    options=graficos_disponiveis,
                    default=graficos_padrao
                )

                # ======== CONTROLES DE EXIBIÇÃO ========
                st.markdown("#### Opções de Exibição")
                col_tog1, col_tog2 = st.columns(2)
                
                with col_tog1:
                    mostrar_fases = st.toggle("Show Phases", value=True)
                    
                with col_tog2:
                        # O botão do CPIT só aparece se for Cool Down
                    if prova_atual == "Cool Down":
                            mostrar_cpit = st.toggle("Show CPIT Table", value=True)
                    else:
                            mostrar_cpit = False
                
                st.divider()
                    # =======================================

         
                st.divider()
            
                # Dicionário para guardar as figuras geradas (vamos usar no PDF)
                figuras_plotly = {}
            
                # --- 1. RENDERIZAR GRÁFICOS NA TELA ---
                for nome_grafico in graficos_selecionados:
                    mapa_variaveis = mapas_graficos[nome_grafico]
                    cols_to_plot = [var for var in mapa_variaveis.keys() if var in df_plot.columns]
                
                    if not cols_to_plot:
                        continue
                
                    fig = px.line(
                        df_plot, 
                        x="Time [s]", 
                        y=cols_to_plot,
                        title=nome_grafico,
                        template="plotly_white",
                        color_discrete_sequence=CORES_PADRAO
                    )
                
                    # ======== O SEGREDO DO CLIQUE ========
                    # Plotly não permite seleção em "linhas puras".
                    # Adicionamos marcadores invisíveis (opacity=0) para criar a "área de clique"!
                    fig.update_traces(mode="lines+markers", marker=dict(opacity=0, size=10))
                    source_map = df_plot.attrs.get('source_channels', {})
                    for trace in fig.data:
                        original_names = source_map.get(trace.name, [])
                        if isinstance(original_names, str):
                            original_names = [original_names]
                        original_text = ', '.join(original_names) if original_names else 'não informado'
                        normalized_name = trace.name
                        trace.name = normalized_name
                        trace.hovertemplate = (
                            "Time: %{x:.1f} s<br>Valor: %{y:.2f}"
                            f"<extra>MF4: {original_text}</extra>"
                        )
                    # =====================================

                    fig.update_layout(
                        legend_title_text="Variáveis",
                        xaxis_title="Time [s]",
                        yaxis_title=(
                            cols_to_plot[0]
                            if len(cols_to_plot) == 1
                            else "Valores (unidades originais)"
                        ),
                        hovermode="closest",      # Garante o foco em um único ponto
                        clickmode="event+select", # Habilita o clique nativo
                        height=500,
                        paper_bgcolor="#FFFFFF",
                        plot_bgcolor="#FFFFFF",
                        font=dict(color="#243782"),
                        title_font=dict(color="#243782"),
                        legend=dict(
                            orientation="h",
                            yanchor="top",
                            y=-0.2,
                            xanchor="center",
                            x=0.5,
                            font=dict(color="#243782"),
                            title_font=dict(color="#243782"),
                            bgcolor="rgba(255,255,255,0)"
                        ),
                        showlegend=True,
                        margin=dict(l=55, r=30, t=65, b=105)
                    )

                    fig.update_xaxes(
                        showgrid=True,
                        gridcolor="#DCE3F2",
                        zerolinecolor="#AEBBDA",
                        linecolor="#7D8DBB",
                        tickfont=dict(color="#243782"),
                        title_font=dict(color="#243782")
                    )

                    fig.update_yaxes(
                        showgrid=True,
                        gridcolor="#DCE3F2",
                        zerolinecolor="#AEBBDA",
                        linecolor="#7D8DBB",
                        tickfont=dict(color="#243782"),
                        title_font=dict(color="#243782")
                    )
                
                    # ======== ADICIONA AS FASES NO FUNDO DO GRÁFICO NA TELA ========
                    if mostrar_fases:
                        df_fases = st.session_state.get('df_fases', pd.DataFrame())
                        if not df_fases.empty:
                            for _, row in df_fases.iterrows():
                                fig.add_vrect(
                                    x0=row['t_inicio'], x1=row['t_fim'],
                                    fillcolor=row['Phase_Color'],
                                    opacity=1,
                                    layer="below", line_width=0,
                                    annotation_text=row['Phase_Name'],
                                    annotation_position="top left",
                                    annotation_font_size=11,
                                    annotation_font_color="#555"
                                )
                    # ===============================================================

                    # ======== MARCAÇÃO DE PONTOS INTERATIVA ========
                    # 1. Inicializa a "memória" de pontos para este gráfico
                    if 'pontos_marcados' not in st.session_state:
                        st.session_state['pontos_marcados'] = {}
                    if nome_grafico not in st.session_state['pontos_marcados']:
                        st.session_state['pontos_marcados'][nome_grafico] = []
                
                    key_last_sel = f"last_sel_{nome_grafico}"
                    if key_last_sel not in st.session_state:
                        st.session_state[key_last_sel] = []
                
                    pontos_atuais = st.session_state['pontos_marcados'][nome_grafico]

                    # 2. Desenha as marcações na tela ANTES de renderizar
                    if pontos_atuais:
                        fig.add_scatter(
                            x=[p[0] for p in pontos_atuais],
                            y=[p[1] for p in pontos_atuais],
                            mode='markers+text',
                            marker=dict(color='red', size=10, symbol='x'),
                            text=[f"({p[0]:.1f}s, {p[1]:.1f})" for p in pontos_atuais],
                            textposition="top right",
                            name="Marcações",
                            hoverinfo="skip" 
                        )
                
                    # 3. Renderiza o gráfico e CAPTURA O CLIQUE
                    event = st.plotly_chart(
                        fig,
                        use_container_width=True,
                        theme=None,
                        on_select="rerun",
                        selection_mode="points",
                        key=f"plot_inter_{nome_grafico}"
                    )

                    # 4. Lógica de "Liga/Desliga" Anti-Loop Infinito
                    pontos_clicados = []
                    if event and hasattr(event, 'selection'):
                        pontos_clicados = event.selection.get("points", [])
                    elif isinstance(event, dict) and "selection" in event: # Proteção extra para outras versões
                        pontos_clicados = event["selection"].get("points", [])

                    if pontos_clicados:
                        selecao_atual = [(p["x"], p["y"]) for p in pontos_clicados]
                    
                        # Só processa se a seleção for NOVA (o usuário acabou de clicar de fato)
                        if selecao_atual != st.session_state[key_last_sel]:
                            st.session_state[key_last_sel] = selecao_atual 
                        
                            if selecao_atual:
                                x_click, y_click = selecao_atual[-1]
                            
                                ponto_para_remover = None
                                for p in pontos_atuais:
                                    if abs(p[0] - x_click) < 0.5 and abs(p[1] - y_click) < (abs(y_click) * 0.05 + 0.5): 
                                        ponto_para_remover = p
                                        break
                            
                                if ponto_para_remover:
                                    st.session_state['pontos_marcados'][nome_grafico].remove(ponto_para_remover)
                                else:
                                    st.session_state['pontos_marcados'][nome_grafico].append((x_click, y_click))
                            
                                st.rerun() # Atualiza a tela com o ponto desenhado
                    # ===============================================
                
                    # ======== CAIXA DE COMENTÁRIOS ========
                    st.text_area(
                        f"📝 Análise / Comentários: {nome_grafico}", 
                        key=f"comment_{nome_grafico}",
                        height=80,
                        placeholder="Digite sua análise para este gráfico aqui. Ela aparecerá logo abaixo dele no PDF."
                    )
                    st.divider()
                    # ======================================
                
                    # Guarda a figura para o exportador de PDF não precisar gerar de novo
                    figuras_plotly[nome_grafico] = fig
            

                st.divider()

                 # ======== EXIBE TABELA CPIT NA TELA SE FOR COOL DOWN ========
                if prova_atual == "Cool Down" and mostrar_cpit:
                    st.markdown("#### CPIT Table (Resultados)")
                    df_cpit_tela = calcular_cpit(df_plot)
                    st.dataframe(df_cpit_tela, hide_index=True, use_container_width=True)
                    st.divider()
                # ==============================================================
            
                # Botão para INICIAR o processamento
                if st.button("⚙️ Process PDF Report"):
                    with st.spinner("Generating PDF... It might take a few seconds..."):
                        try:
                            st.info("Step 1: Preparing cover...")
                        
                            logo_stellantis_b64 = get_image_base64("logo_stellantis.png")
                            logo_tdas_b64 = get_image_base64("t-das.png")
                        
                            # Resgata a "Foto" dos dados salva na Aba 1
                            meta = st.session_state.get('metadata_ensaio', {})
                        
                            dados_gerais = {
                                "titulo_principal": "T-DAS Standardized Report",
                                "test_performed": meta.get("test_performed", prova_atual),
                                "test_date": meta.get("test_date", ""),
                                "project": meta.get("project", ""),
                                "engine_type": meta.get("engine_type", ""),
                                "model_year": meta.get("model_year", ""),
                                "project_phase": meta.get("phase", ""),
                                "chassi_vin": meta.get("chassis", ""),
                                "test_engineer": meta.get("test_engineer", ""),
                                "project_engineer": meta.get("project_engineer", ""),
                                "observations": meta.get("observations", ""),
                                "transmission": meta.get("transmission", ""),
                                "vehicle_version": meta.get("vehicle_version", ""),
                                "brand": meta.get("brand", ""),
                                "market": meta.get("market", ""),
                                "caminho_logo_uri": logo_stellantis_b64, 
                                "caminho_logo_tdas_uri": logo_tdas_b64    
                            }

                            st.info("Step 2: Preparing graphs...")
                        
                            template_grafico_bloco = Template(HTML_TEMPLATE_GRAPH_BLOCK)
                        
                            # A MÁGICA ESTÁ AQUI: Inicia a string já ordenando virar a folha!
                            graficos_renderizados_str = "<pdf:nexttemplate name='landscape_page' />\n"
                        
                            for nome_grafico in graficos_selecionados:
                                mapa_variaveis = mapas_graficos[nome_grafico]
                                cols_to_plot = [var for var in mapa_variaveis.keys() if var in df_plot.columns]
                            
                                if not cols_to_plot:
                                    continue
                            
                           
                                # Envia as fases pro PDF só se o botão estiver ativado
                                df_fases_para_pdf = st.session_state.get('df_fases') if mostrar_fases else None
                            
                           
                                # Puxa os pontos marcados deste gráfico específico na memória
                                pontos_deste_grafico = st.session_state.get('pontos_marcados', {}).get(nome_grafico, [])
                            
                                # Gera a imagem com as Fases e os Pontos
                                img_b64 = gerar_imagem_grafico_matplotlib(
                                    df_plot, 
                                    nome_grafico, 
                                    cols_to_plot, 
                                    df_fases_para_pdf,
                                    pontos_marcados=pontos_deste_grafico # <- Argumento novo aqui!
                                )
                                chart_uri = f"data:image/png;base64,{img_b64}"
                            
                                # ======== LÓGICA DO COMENTÁRIO DINÂMICO ========
                                # Puxa o que o engenheiro digitou na tela
                                comentario_atual = st.session_state.get(f"comment_{nome_grafico}", "").strip()
                            
                                if comentario_atual:
                                    altura_maxima = "11cm" # Encolhe a imagem para caber o texto
                                    html_comentario = f"""
                                    <div style="margin-top: 15px; padding: 12px; background-color: #fcfcfc; border: 1px solid #ddd; border-left: 4px solid #003366; font-size: 10pt; text-align: left; white-space: pre-wrap; color: #444;">
                                        <strong>Analysis / Comments:</strong><br/>{comentario_atual}
                                    </div>
                                    """
                                else:
                                    altura_maxima = "15cm" # Se não tem comentário, usa o tamanho máximo
                                    html_comentario = ""
                                # ===============================================
                            
                                # Adiciona o HTML do Gráfico na String já com o comentário
                                graficos_renderizados_str += template_grafico_bloco.render(
                                    nome_grafico=nome_grafico, 
                                    chart_uri=chart_uri,
                                    max_height=altura_maxima,
                                    bloco_comentario=html_comentario
                                )
                        

                            # ======== INJETA A TABELA CPIT NO FINAL DO PDF ========
                            if prova_atual == "Cool Down" and mostrar_cpit:
                                st.info("Calculando tabela CPIT para o relatório...")
                                df_cpit = calcular_cpit(df_plot)
                                cpit_dict_list = df_cpit.to_dict('records')
                            
                                template_cpit = Template(HTML_TEMPLATE_CPIT_BLOCK)
                                html_cpit_renderizado = template_cpit.render(cpit_rows=cpit_dict_list)
                            
                                graficos_renderizados_str += html_cpit_renderizado
                            # ======================================================
                        
                            st.info("Step 3: Preparing PDF...")
                        
                            # Renderiza o Template Principal, injetando os dados da capa e o blocão de gráficos juntos
                            template_principal = Template(HTML_TEMPLATE_REPORT)
                            html_final = template_principal.render(dados=dados_gerais, graficos_html=graficos_renderizados_str)
                        
                            pdf_buffer = io.BytesIO()
                            pisa_status = pisa.CreatePDF(html_final, dest=pdf_buffer)

                            if pisa_status.err:
                                st.error("Erro interno ao montar o PDF com xhtml2pdf.")
                            else:
                                # Salva o PDF pronto na sessão do Streamlit!
                                st.session_state['pdf_pronto'] = pdf_buffer.getvalue()
                                st.success("✅ Success! Click on the button below to download the PDF")
                            
                        except Exception as e:
                            st.error(f"Erro detalhado ao gerar o PDF: {e}")
            
            
                # O Botão de Download fica do LADO DE FORA do botão de processar.
                if 'pdf_pronto' in st.session_state:
                    # 1. Puxa os dados da memória
                    meta = st.session_state.get('metadata_ensaio', {})
                
                    nome_prova = str(meta.get("test_performed", "Prova"))
                    nome_projeto = str(meta.get("project", "Projeto"))
                    nome_motor = str(meta.get("engine_type", "Motor"))
                    nome_chassi = str(meta.get("chassis", "Chassi"))
                    data_teste = str(meta.get("test_date", "Data"))
                
                    # 2. Limpa possíveis caracteres proibidos pelo Windows (como barras)
                    def limpar_string(texto):
                        return texto.replace("/", "-").replace("\\", "-").replace(":", "")

                    nome_prova = limpar_string(nome_prova)
                    nome_projeto = limpar_string(nome_projeto)
                    nome_motor = limpar_string(nome_motor)
                    nome_chassi = limpar_string(nome_chassi)
                
                    # 3. Monta a string final no padrão solicitado pela área
                    # Formato: TDAS - Prova - Projeto - Motor - Chassi - Data
                    nome_arquivo_pdf = f"TDAS - {nome_prova} - {nome_projeto} - {nome_motor} - {nome_chassi} - {data_teste}.pdf"
                
                    st.download_button(
                        label="💾 Baixar Relatório PDF",
                        data=st.session_state['pdf_pronto'],
                        file_name=nome_arquivo_pdf, 
                        mime="application/pdf",
                        type="primary"
                    )  
            else:
                st.warning("Please select a valid 'Test performed' on tab 1")
            
        else:
            st.info("Waiting for data on tab 1.")


