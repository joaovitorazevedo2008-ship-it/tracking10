import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Rastreamento de Contêineres", page_icon="⚓", layout="wide")

# --- SISTEMA DE LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("LOGIN TRACKING")
    st.markdown("Por favor, insira suas credenciais para acessar o sistema.")
    
    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        btn_login = st.form_submit_button("Entrar")
        
        if btn_login:
            if usuario == "DCLOG" and senha == "DCTRACKING":
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos!")
    
    st.stop()
# ------------------------

ARQUIVO_DADOS = "dados_tracking_prefixos.csv"

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
    colunas_padrao = ["Processo", "Container", "Armador Detectado", "Link de Rastreio", "Status", "Porto de Transbordo", "Data Transbordo", "Destino Final", "ETA Destino", "E-mail Pronto"]
    if os.path.exists(ARQUIVO_DADOS):
        df = pd.read_csv(ARQUIVO_DADOS)
        # Adiciona colunas novas caso seja um arquivo antigo
        for col in colunas_padrao:
            if col not in df.columns:
                df[col] = ""
        return df
    else:
        return pd.DataFrame(columns=colunas_padrao)

def salvar_dados(df):
    df.to_csv(ARQUIVO_DADOS, index=False)

df_tracking = carregar_dados()

col_titulo, col_sair = st.columns([8, 1])
with col_titulo:
    st.title("⚓ RASTREAMENTO DE CONTÊINERES")
with col_sair:
    st.write("") 
    if st.button("🚪 Sair"):
        st.session_state["autenticado"] = False
        st.rerun()

st.markdown("Gerencie suas cargas, atualize informações e gere relatórios instantâneos de rastreamento.")

aba1, aba2, aba3 = st.tabs(["🔍 Consulta e E-mail", "📋 Painel e Histórico", "✏️ Editar Informações"])

with aba1:
    st.subheader("Insira os dados da carga")
    
    with st.form("form_prefixo"):
        col1, col2 = st.columns(2)
        with col1:
            processo_input = st.text_input("Nº do Processo / Referência")
            container_input = st.text_input("Nº do Contêiner (Ex: MSCU1234567)")
            porto_transbordo_input = st.text_input("Porto de Transbordo (Opcional)")
            data_transbordo_input = st.text_input("Data de Chegada no Transbordo (Opcional)")
        with col2:
            status_input = st.selectbox("Status Atual", [
                "Em trânsito", 
                "Liberado na Alfândega", 
                "Disponível para Retirada", 
                "Embarcado",
                "Em desova no porto de transbordo"
            ])
            destino_final
