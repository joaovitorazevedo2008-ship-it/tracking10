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
    colunas_padrao = ["Processo", "Container", "Armador Detectado", "Status", "Porto de Transbordo", "Data Transbordo", "Destino Final", "ETA Destino", "DOOR/RAMP", "E-mail Pronto"]
    if os.path.exists(ARQUIVO_DADOS):
        df = pd.read_csv(ARQUIVO_DADOS)
        if "Link de Rastreio" in df.columns:
            df = df.drop(columns=["Link de Rastreio"])
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
                "Embarcado",
                "Em trânsito", 
                "Em desova no porto de transbordo",
                "Liberado na Alfândega", 
                "Disponível para Retirada"
            ])
            destino_final_input = st.text_input("Destino Final")
            eta_input = st.text_input("Previsão de Chegada (ETA) no Destino Final", value="DD/MM/AAAA")
            door_ramp_input = st.text_input("DOOR/RAMP (Opcional)")
            
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            btn_analisar = st.form_submit_button("Identificar Armador")
        with col_btn2:
            btn_email = st.form_submit_button("✉️ Gerar E-mail")
        
        if btn_analisar or btn_email:
            if container_input:
                armador_encontrado, link_direto = identificar_armador(container_input)
                
                # Variáveis auxiliares para montar o texto de forma natural
                texto_transbordo = ""
                if porto_transbordo_input:
                    data_t = f" no dia {data_transbordo_input}" if data_transbordo_input else ""
                    texto_transbordo = f" Lembramos que a carga tem passagem prevista pelo porto de transbordo ({porto_transbordo_input}){data_t}."

                local_destino = f" em {destino_final_input}" if destino_final_input else ""
                modalidade_door = f" (Modalidade: {door_ramp_input})" if door_ramp_input else ""

                # --- LÓGICA DE E-MAILS SEPARADOS POR STATUS ---
                if status_input == "Embarcado":
                    corpo_email = f"""Prezado cliente,

Informamos que a sua carga referente ao processo {processo_input} (Contêiner: {container_input.upper()}) foi embarcada com sucesso na origem. 

A previsão atualizada de chegada (ETA) ao destino final{local_destino} é para a data de {eta_input}{modalidade_door}.{texto_transbordo}

Para acompanhar as movimentações do navio em tempo real, acesse o rastreamento oficial através do link abaixo:
{link_direto}

Qualquer dúvida, a nossa equipe está à disposição!

Atenciosamente,
Equipe DC Logistics Brasil"""

                elif status_input == "Em trânsito":
                    corpo_email = f"""Prezado cliente,

Gostaríamos de atualizar que a carga do processo {processo_input} (Contêiner: {container_input.upper()}) segue sua viagem normalmente e encontra-se em trânsito marítimo.

A nossa estimativa de chegada (ETA){local_destino} permanece para o dia {eta_input}{modalidade_door}.{texto_transbordo}

Pode continuar a acompanhar o status através do link de rastreamento do armador:
{link_direto}

Qualquer necessidade, não hesite em nos contactar.

Atenciosamente,
Equipe DC Logistics Brasil"""

                elif status_input == "Em desova no porto de transbordo":
                    corpo_email = f"""Prezado cliente,

Entramos em contacto para informar que o contêiner {container_input.upper()} (Processo: {processo_input}) chegou ao porto de transbordo e encontra-se em etapa de desova/movimentação.

A previsão de chegada no destino final{local_destino} após esta etapa é {eta_input}{modalidade_door}.

Acompanhe os próximos passos da carga pelo rastreio abaixo:
{link_direto}

Seguimos à disposição para qualquer esclarecimento.

Atenciosamente,
Equipe DC Logistics Brasil"""

                elif status_input == "Liberado na Alfândega":
                    corpo_email = f"""Prezado cliente,

Temos boas notícias! Informamos que a carga referente ao processo {processo_input} (Contêiner: {container_input.upper()}) foi parametrizada e encontra-se devidamente liberada na alfândega.

A carga segue agora o trâmite normal para a próxima etapa logística{modalidade_door}.

Caso queira consultar o histórico no armador, segue o link:
{link_direto}

Nossa equipa continua acompanhando de perto. Qualquer dúvida, estamos à disposição.

Atenciosamente,
Equipe DC Logistics Brasil"""

                elif status_input == "Disponível para Retirada":
                    corpo_email = f"""Prezado cliente,

Gostaríamos de informar que o contêiner {container_input.upper()} (Processo: {processo_input}) concluiu todas as etapas e já se encontra DISPONÍVEL PARA RETIRADA{local_destino}.

Por favor, procedam com as programações de transporte necessárias de acordo com a modalidade contratada{modalidade_door}.

Rastreio para consulta final:
{link_direto}

Agradecemos a confiança em nossos serviços e seguimos à disposição!

Atenciosamente,
Equipe DC Logistics Brasil"""
                # ----------------------------------------------

                nova_linha = {
                    "Processo": processo_input,
                    "Container": container_input.upper(),
                    "Armador Detectado": armador_encontrado,
                    "Status": status_input,
                    "Porto de Transbordo": porto_transbordo_input,
                    "Data Transbordo": data_transbordo_input,
                    "Destino Final": destino_final_input,
                    "ETA Destino": eta_input,
                    "DOOR/RAMP": door_ramp_input,
                    "E-mail Pronto": "Gerado"
                }
                df_tracking = pd.concat([df_tracking, pd.DataFrame([nova_linha])], ignore_index=True)
                salvar_dados(df_tracking)
                
                st.success(f"Armador identificado com sucesso: **{armador_encontrado}**")
                st.markdown(f"### 🔗 [Clique aqui para abrir o rastreio direto no site da {armador_encontrado}]({link_direto})")
                
                if btn_email:
                    st.text_area("Modelo de E-mail Pronto para Copiar:", value=corpo_email, height=350)
                
                st.markdown("---")
                st.subheader("🕒 Histórico de Atualizações desta Carga")
                
                if processo_input:
                    historico_ref = df_tracking[(df_tracking['Container'] == container_input.upper()) | (df_tracking['Processo'] == processo_input)]
                else:
                    historico_ref = df_tracking[df_tracking['Container'] == container_input.upper()]
                
                st.dataframe(historico_ref, use_container_width=True)
                
            else:
                st.error("Por favor, informe o número do contêiner.")

with aba2:
    st.subheader("Histórico de Contêineres Consultados (Geral)")
    if df_tracking.empty:
        st.info("Nenhum contêiner consultado ainda.")
    else:
        st.dataframe(df_tracking, use_container_width=True)
        if st.button("🗑️ Limpar Todo o Histórico"):
            if os.path.exists(ARQUIVO_DADOS):
                os.remove(ARQUIVO_DADOS)
            st.rerun()

with aba3:
    st.subheader("✏️ Editar Informações Salvas")
    st.markdown("Dê um duplo clique em qualquer campo da tabela abaixo para editar. Quando terminar, clique no botão azul para salvar.")
    
    if df_tracking.empty:
        st.info("Ainda não há dados para editar.")
    else:
        df_editado = st.data_editor(df_tracking, use_container_width=True, num_rows="dynamic")
        
        if st.button("💾 Salvar Alterações na Base de Dados", type="primary"):
            salvar_dados(df_editado)
            st.success("Dados atualizados com sucesso!")
            st.rerun()
