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
    
    if prefixo in ["MSCU"]:
        return "MSC", f"https://www.msc.com/en/track-a-shipment?trackingNumber={container.strip()}"
    elif prefixo in ["MRKU", "MAEU", "MSMU"]:
        return "Maersk", f"https://www.maersk.com/tracking/{container.strip()}"
    elif prefixo in ["HLXU", "HLCU"]:
        return "Hapag-Lloyd", f"https://www.hapag-lloyd.com/en/online-business/track/track-by-container.html?container={container.strip()}"
    elif prefixo in ["CMAU", "CGMU", "MEDU", "TGHU"]:
        return "CMA CGM", f"https://www.cma-cgm.com/ebusiness/tracking/search?SearchBy=Container&SearchValue={container.strip()}"
    elif prefixo in ["ONEU", "NYKU", "PONU", "MSKU"]:
        return "ONE (Ocean Network Express)", f"https://ecomm.one-line.com/ecom/CUP_HOM_3301.do?sessLocale=en&bkgNo={container.strip()}"
    elif prefixo in ["COSU", "CBHU", "FCIU"]:
        return "COSCO", f"https://elines.coscoshipping.com/ebusiness/cargoTracking?trackingType=CONTAINER&trackingNumber={container.strip()}"
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
st.markdown(f"### 🔗 [Clique aqui para abrir o rastreio direto no site da {armador_encontrado}]({link_direto})")
aba1, aba2 = st.tabs(["🔍 Consulta Rápida por Prefixo", "📋 Painel e Histórico"])

with aba1:
    st.subheader("Insira os dados da carga")
    
    with st.form("form_prefixo"):
        col1, col2 = st.columns(2)
        with col1:
            processo_input = st.text_input("Nº do Processo / Referência")
            container_input = st.text_input("Nº do Contêiner (Ex: MSCU1234567)")
        with col2:
            status_input = st.selectbox("Status Atual", ["Em trânsito", "Liberado na Alfândega", "Disponível para Retirada", "Embarcado"])
            eta_input = st.text_input("Previsão de Chegada (ETA)", value="DD/MM/AAAA")
            
        btn_analisar = st.form_submit_button("Identificar Armador e Gerar Link")
        
        if btn_analisar:
            if container_input:
                armador_encontrado, link_direto = identificar_armador(container_input)
                
                st.success(f"Armador identificado com sucesso: **{armador_encontrado}**")
                
                # Exibe o botão de redirecionamento direto
                st.markdown(f
