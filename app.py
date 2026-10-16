import streamlit as st
import sqlite3
import re
from datetime import datetime
from io import BytesIO

try:
    import pdfplumber
except ImportError:
    pdfplumber = None
try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None
try:
    from pdf2image import convert_from_bytes
except ImportError:
    convert_from_bytes = None

st.set_page_config(
    page_title="DC LCL Tracking",
    page_icon="🚢",
    layout="wide"
)

DB = "tracking.db"

# Biblioteca inicial de códigos de contêiner e portais oficiais.
# O prefixo identifica o código registrado do equipamento; não confirma
# necessariamente qual armador está transportando a carga.
BIC_URL = "https://www.bic-code.org/pt/codigos-bic/"
ARMADORES = {
    "MAEU": {"nome": "Maersk", "url": "https://www.maersk.com/tracking/"},
    "MSCU": {"nome": "MSC", "url": "https://www.msc.com/en/track-a-shipment"},
    "CMAU": {"nome": "CMA CGM", "url": "https://www.cma-cgm.com/ebusiness/tracking"},
    "CMDU": {"nome": "CMA CGM", "url": "https://www.cma-cgm.com/ebusiness/tracking"},
    "HLCU": {"nome": "Hapag-Lloyd", "url": "https://www.hapag-lloyd.com/pt/online-business/track/track.html"},
    "COSU": {"nome": "COSCO Shipping", "url": "https://elines.coscoshipping.com/ebusiness/cargoTracking"},
    "EISU": {"nome": "Evergreen", "url": "https://www.shipmentlink.com/"},
    "ONEY": {"nome": "Ocean Network Express (ONE)", "url": "https://ecomm.one-line.com/one-ecom/manage-shipment/cargo-tracking"},
    "OOLU": {"nome": "OOCL", "url": "https://www.oocl.com/eng/ourservices/eservices/trackandtrace/Pages/default.aspx"},
    "YMLU": {"nome": "Yang Ming", "url": "https://www.yangming.com/"},
    "ZIMU": {"nome": "ZIM", "url": "https://www.zim.com/tools/track-a-shipment"},
    "HMMU": {"nome": "HMM", "url": "https://www.hmm21.com/"},
    "WHLU": {"nome": "Wan Hai Lines", "url": "https://www.wanhai.com/"},
    "PCIU": {"nome": "Pacific International Lines (PIL)", "url": "https://www.pilship.com/"},
    "APLU": {"nome": "APL", "url": "https://www.cma-cgm.com/ebusiness/tracking"},
    "ANNU": {"nome": "ANL", "url": "https://www.cma-cgm.com/ebusiness/tracking"},
    "SUDU": {"nome": "Hamburg Süd / Maersk", "url": "https://www.maersk.com/tracking/"},
    "SKLU": {"nome": "Safmarine / Maersk", "url": "https://www.maersk.com/tracking/"},
    "GESU": {"nome": "Gold Star Line", "url": "https://www.gsl.com.hk/"},
    "SITU": {"nome": "SITC", "url": "https://www.sitc.com/"},
    "TRIU": {"nome": "Triton (equipamento)", "url": BIC_URL},
    "TGHU": {"nome": "Textainer (equipamento)", "url": BIC_URL},
    "FCIU": {"nome": "Florens (equipamento)", "url": BIC_URL},
    "TEMU": {"nome": "Triton (equipamento)", "url": BIC_URL},
    "CAIU": {"nome": "CAI (equipamento)", "url": BIC_URL},
    "SEGU": {"nome": "Seaco (equipamento)", "url": BIC_URL},
    "BEAU": {"nome": "Beacon (equipamento)", "url": BIC_URL},
}


def identificar_armador(container, armador_cadastrado=None):
    nome_cadastrado = (armador_cadastrado or "").strip().casefold()
    if nome_cadastrado:
        for dados in ARMADORES.values():
            if dados["nome"].casefold() == nome_cadastrado:
                return dados
        # Se o cadastro tem nome de armador não mapeado, não inventa um link.
        return {"nome": armador_cadastrado.strip(), "url": BIC_URL}

    container = (container or "").strip().upper()
    prefixo = container[:4]
    return ARMADORES.get(
        prefixo,
        {"nome": "Prefixo não identificado automaticamente", "url": BIC_URL},
    )



def extrair_texto_documento(arquivo):
    """Extrai texto de PDF pesquisável ou imagem; OCR depende do Tesseract."""
    nome = (arquivo.name or "").lower()
    dados = arquivo.getvalue()

    if nome.endswith(".pdf"):
        if pdfplumber is None:
            raise RuntimeError("Dependência pdfplumber ausente. Instale requirements.txt.")
        paginas = []
        with pdfplumber.open(BytesIO(dados)) as pdf:
            for pagina in pdf.pages:
                paginas.append(pagina.extract_text() or "")
        texto = "\n".join(paginas)
        if texto.strip():
