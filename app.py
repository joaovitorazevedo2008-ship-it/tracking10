import streamlit as st
import pandas as pd
import os
from datetime import datetime, date

# Configuração inicial da página com tema forçado para claro
st.set_page_config(
    page_title="Rastreamento de Contêineres", 
    page_icon="⚓", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- DESIGN CORPORATIVO FORÇADO (AZUL, AMARELO E BRANCO) ---
st.markdown("""
    <style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #F8FAFC !important;
    }
    
    .stApp p, .stApp span, .stApp div, .stApp label, h1, h2, h3, h4, h5, h6, .stMarkdown {
        color: #002B5B !important;
    }

    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }

    input, textarea, [data-baseweb="input"] input {
        background-color: #002B5B !important;
        color: #FFC000 !important;
        border: 2px solid #FFC000 !important;
        border-radius: 8px !important;
        -webkit-text-fill-color: #FFC000 !important;
        font-weight: 600 !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #002B5B !important;
        color: #FFC000 !important;
        border: 2px solid #FFC000 !important;
        border-radius: 8px !important;
    }
    
    div[data-baseweb="select"] span {
        color: #FFC000 !important;
        -webkit-text-fill-color: #FFC000 !important;
        font-weight: 600 !important;
    }

    .stSelectbox svg {
        fill: #FFC000 !important;
    }

    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
        background-color: #002B5B !important;
        border: 2px solid #FFC000 !important;
        border-radius: 8px !important;
    }
    
    div[data-baseweb="menu"] div, div[data-baseweb="menu"] span, ul[role="listbox"] li, ul[role="listbox"] span, div[role="option"] {
        background-color: #002B5B !important;
        color: #FFC000 !important;
        -webkit-text-fill-color: #FFC000 !important;
        font-weight: 600 !important;
    }

    ul[role="listbox"] li:hover, div[role="option"]:hover {
        background-color: #003F88 !important;
        color: #FFD633 !important;
        -webkit-text-fill-color: #FFD633 !important;
    }

    button[kind="primary"], button[kind="secondary"], .stFormSubmitButton button, div.stButton > button {
        background-color: #002B5B !important;
        color: #FFC000 !important;
        border: 2px solid #FFC000 !important;
        font-weight: 800 !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        transition: all 0.2s ease-in-out;
        -webkit-text-fill-color: #FFC000 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    button[kind="primary"]:hover, button[kind="secondary"]:hover, .stFormSubmitButton button:hover, div.stButton > button:hover {
        background-color: #003F88 !important;
        color: #FFD633 !important;
        -webkit-text-fill-color: #FFD633 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 2px solid #FFC000;
        background-color: #FFFFFF;
        border-radius: 8px 8px 0 0;
        padding: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #002B5B !important;
        font-weight: 700;
    }
    .stTabs [aria-selected="true"] {
        background-color: #002B5B !important;
        color: #FFFFFF !important;
        border-radius: 6px 6px 0 0 !important;
    }
    .stTabs [aria-selected="true"] * {
        color: #FFFFFF !important;
    }

    div[data-testid="stMetric"], .stForm, div[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 20px !important;
        box-shadow: 0px 2px 6px rgba(0, 43, 91, 0.04);
        border-left: 4px solid #FFC000 !important;
    }

    [data-testid="stDataFrame"], [data-testid="stTable"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        padding: 5px;
    }

    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0;
    }
    
    [data-testid="stAlert"] {
        border-left: 5px solid #FFC000 !important;
        background-color: #FFFFFF !important;
        border-radius: 8px;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.02);
    }
    </style>
""", unsafe_allow_html=True)
# --------------------------------------------------

# --- SISTEMA DE LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown("<h1 style='text-align: center; color: #002B5B;'>⚓ LOGIN TRACKING</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #002B5B;'>Ambiente Corporativo Seguro - Insira suas credenciais.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            btn_login = st.form_submit_button("Entrar no Sistema")
            
            if btn_login:
                if usuario == "DCLOG" and senha == "DCTRACKING":
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos!")
    st.stop()
# ------------------------

# --- BARRA LATERAL DIDÁTICA ---
with st.sidebar:
    st.markdown("### 📖 Guia do Sistema")
    st.markdown("**1️⃣ Pesquisa:** Informe a referência para abrir os dados cadastrados ou iniciar um novo registo.")
    st.markdown("**2️⃣ Atualização:** Insira o contêiner (identificação automática do armador), status e prazos.")
    st.markdown("**3️⃣ Comunicação:** Salve e gere e-mails padronizados instantaneamente.")
    st.markdown("---")
    if st.button("🚪 Encerrar Sessão"):
        st.session_state["autenticado"] = False
        st.rerun()
# -----------------------------------------

ARQUIVO_DADOS = "dados_tracking_prefixos.csv"

def identificar_armador(container):
    if not container or len(container.strip()) < 4:
        return "Desconhecido", "#"
    prefixo = container.strip()[:4].upper()
    if prefixo in ["MSCU", "MEDU", "MSNU"]:
        return "MSC", f"https://www.msc.com/en/track-a-shipment?trackingNumber={container.strip()}"
    elif prefixo in ["MAEU", "MSKU", "MRKU", "APMU", "PONU", "SEAU", "POCU", "OCLU", "NZSU"]:
        return "Maersk", f"https://www.maersk.com/tracking/{container.strip()}"
    elif prefixo in ["HLCU", "HLXU", "HLBU", "AZLU", "CACU", "CASU", "CMUU", "CPSU", "CSQU", "DALU", "HAMU"]:
        return "Hapag-Lloyd", f"
