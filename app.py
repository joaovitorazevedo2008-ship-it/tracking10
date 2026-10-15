import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Redirecionador Inteligente de Tracking", page_icon="⚓", layout="wide")

ARQUIVO_DADOS = "dados_tracking_prefixos.csv"

# Função para identificar o armador pelo prefixo do contêiner
def identificar_armador(container):
    if not container or len(container.strip()) < 4:
        return "Desconhecido", "#"
    
    prefixo = container.strip()[:4].upper()
    
    if prefixo in ["MSCU", "MEDU", "MSNU"]:
        return "MSC", f"https://www.msc.com/en/track-a-shipment?trackingNumber={container.strip()}"
    elif prefixo in ["MAEU", "MSKU", "MRKU", "APMU", "PONU", "SEAU", "POCU", "OCLU", "NZSU"]:
        return "Maersk", f"https://www.maersk.com/tracking/{container.strip()}"
    elif prefixo in ["HLCU", "HLXU", "HLBU", "AZLU", "CACU", "CASU", "CMUU", "CPSU", "CSQU", "DALU"]:
        return "Hapag-Lloyd", f"https://www.hapag-lloyd.com/en/online-business/track/track-by-container.html?container={container.strip()}"
    elif prefixo in ["CMAU", "CGMU", "CGHU", "CMNU", "ECMU", "AMCU", "TGHU"]:
        return "CMA CGM", f"https://www.cma-cgm.com/ebusiness/tracking/search?SearchBy=Container&SearchValue={container.strip()}"
    elif prefixo in ["ONEU", "NYKU"]:
        return "ONE (Ocean Network Express)", f"https://ecomm.one-line.com/ecom/CUP_HOM_3301.do?sessLocale=en&bkgNo={container.strip()}"
    elif prefixo in ["COSU", "CSLU", "CSNU", "CBHU", "FCIU"]:
        return "COSCO", f"https://elines.coscoshipping.com/ebusiness/cargoTracking?trackingType=CONTAINER&trackingNumber={container.strip()}"
    elif prefixo in ["EMCU", "EISU", "EGHU"]:
        return "Evergreen", f"https://ct.shipmentlink.com/servlet/CT31_q?cntr_no={container.strip()}"
    elif prefixo in ["ZIMU", "GSLU"]:
        return "ZIM", f"https://www.zim.com/tools/track-a-shipment?consignmentnumber={container.strip()}"
    elif prefixo == "YMLU":
        return "Yang Ming", f"https://www.yangming.com/e-service/track_trace/track_trace_cargo_tracking.aspx?tno={container.strip()}"
    else:
        return "Outro / Não Mapeado", f"https://www.google.com/search?q=tracking+container+{container.strip()}"

def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        return pd.read_csv(ARQUIVO_DADOS)
    else:
        return pd.DataFrame(columns=["Processo", "Container", "Armador Detectado", "Link de Rastreio", "Status", "E-mail Pronto"])

def salvar_dados(df):
    df.to_csv(ARQUIVO_DADOS, index=False)

df_tracking = carregar_dados()

st.title("⚓ Redirecionador Inteligente de Contêineres - Comex")
st.markdown("Digite o número do contêiner e a IA identifica o armador e gera o link direto para a consulta instantânea!")

aba1, aba2 = st.tabs(["🔍 Consulta Rápida por Prefixo", "📋 Painel e Histórico"])

with aba1:
    st.subheader("Insira os dados da carga")
    
    with st.form("form_prefixo"):
        col1, col2 = st.columns(2)
        with col1:
            processo_input = st.text_input("Nº do Processo / Referência")
            container_input = st.text_input("Nº do Contêiner (Ex: MSCU1234567)")
            porto_transbordo_input = st.text_input("Porto de Transbordo (Opcional)")
            data_transbordo_input = st.text_input("Data de Chegada no Transb
