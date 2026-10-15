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
st.markdown("Digite o número do contêiner e a IA identifica o armador e gera o link direto para a consulta instantânea!")

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
                st.markdown(f"### 🔗 [Clique aqui para abrir o rastreio direto no site da {armador_encontrado}]({link_direto})")
                
                # Gera o e-mail pronto para o cliente
                corpo_email = f"""Prezado(a) Cliente,

Gostaríamos de atualizar o status do processo {processo_input}:

• Contêiner: {container_input.upper()}
• Armador: {armador_encontrado}
• Previsão de Chegada (ETA): {eta_input}
• Status Atual: {status_input}

Você pode acompanhar o rastreio oficial clicando no link abaixo:
{link_direto}

Qualquer dúvida, estamos à disposição.
Atenciosamente,
Sua Equipe de Logística"""

                st.text_area("Modelo de E-mail Pronto para Copiar:", value=corpo_email, height=220)
                
                # Salva no histórico
                nova_linha = {
                    "Processo": processo_input,
                    "Container": container_input.upper(),
                    "Armador Detectado": armador_encontrado,
                    "Link de Rastreio": link_direto,
                    "Status": status_input,
                    "E-mail Pronto": "Gerado"
                }
                global df_tracking
                df_tracking = pd.concat([df_tracking, pd.DataFrame([nova_linha])], ignore_index=True)
                salvar_dados(df_tracking)
            else:
                st.error("Por favor, informe o número do contêiner.")

with aba2:
    st.subheader("Histórico de Contêineres Consultados")
    if df_tracking.empty:
        st.info("Nenhum contêiner consultado ainda.")
    else:
        st.dataframe(df_tracking, use_container_width=True)
        if st.button("🗑️ Limpar Histórico"):
            if os.path.exists(ARQUIVO_DADOS):
                os.remove(ARQUIVO_DADOS)
            st.rerun()
