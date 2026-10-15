import streamlit as st
import pandas as pd
import os

# Configuração inicial da página
st.set_page_config(page_title="Rastreamento de Contêineres", page_icon="⚓", layout="wide", initial_sidebar_state="expanded")

# --- DESIGN CUSTOMIZADO E DIDÁTICO (AZUL, AMARELO E BRANCO) ---
st.markdown("""
    <style>
    /* Cor de fundo principal Branca */
    .stApp {
        background-color: #FFFFFF;
    }
    
    /* Textos Gerais em Azul Escuro */
    .stApp, p, span, div, label {
        color: #003366 !important;
    }
    
    /* Títulos em Azul Escuro */
    h1, h2, h3, h4, h5 {
        color: #003366 !important;
        font-weight: 800 !important;
    }

    /* Botão Principal (Amarelo com texto Azul) */
    button[kind="primary"] {
        background-color: #FFC000 !important;
        color: #003366 !important;
        border: none !important;
        font-weight: 900 !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        transition: 0.3s;
    }
    button[kind="primary"]:hover {
        background-color: #FFD633 !important;
        transform: scale(1.02);
        box-shadow: 0px 4px 15px rgba(255, 192, 0, 0.4);
    }
    
    /* Botão Secundário (Azul Escuro com texto Branco) */
    button[kind="secondary"] {
        background-color: #003366 !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        transition: 0.3s;
    }
    button[kind="secondary"]:hover {
        background-color: #004C99 !important;
        color: #FFFFFF !important;
        transform: scale(1.02);
        box-shadow: 0px 4px 15px rgba(0, 51, 102, 0.3);
    }

    /* Campos de Input (Borda Azul, Fundo Branco) */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        border: 1px solid #003366 !important;
        border-radius: 6px !important;
        background-color: #F8FAFC !important;
        color: #003366 !important;
    }

    /* Abas Superiores */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #FFFFFF;
        border-bottom: 2px solid #FFC000;
    }
    .stTabs [data-baseweb="tab"] {
        color: #003366;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #003366 !important;
        color: #FFFFFF !important;
        border-radius: 8px 8px 0 0 !important;
    }

    /* Cartão do Formulário */
    [data-testid="stForm"] {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0px 4px 10px rgba(0, 51, 102, 0.1);
        border: 1px solid #E2E8F0;
        border-left: 5px solid #003366;
    }

    /* Barra Lateral (Sidebar) Azul Escura */
    [data-testid="stSidebar"] {
        background-color: #003366 !important;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    
    /* Alertas Sucesso/Info com detalhe amarelo */
    [data-testid="stAlert"] {
        background-color: #F8FAFC !important;
        border-left: 5px solid #FFC000 !important;
        color: #003366 !important;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)
# --------------------------------------------------

# --- SISTEMA DE LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown("<h1 style='text-align: center; color: #003366;'>⚓ LOGIN TRACKING</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Bem-vindo(a)! Insira suas credenciais para continuar.</p>", unsafe_allow_html=True)
    
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

# --- BARRA LATERAL (TUTORIAL DIDÁTICO) ---
with st.sidebar:
    st.title("⚓ DC Tracking")
    st.markdown("---")
    st.markdown("### 📖 Como usar?")
    st.markdown("**1️⃣ Busca Inteligente:** Digite o número do contêiner e tecle `ENTER`. O sistema preenche o histórico se já existir.")
    st.markdown("**2️⃣ Preencha os Dados:** Atualize datas, status e destinos conforme a situação atual da carga.")
    st.markdown("**3️⃣ Geração de E-mail:** Escolha se quer apenas registrar no sistema ou se deseja gerar o texto pronto para enviar ao cliente.")
    st.markdown("---")
    st.info("💡 **Dica:** Passe o mouse sobre os ícones de interrogação (?) nos campos para ajuda.")
    st.write("")
    st.write("")
    if st.button("🚪 Sair do Sistema"):
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
    elif prefixo in ["HLCU", "HLXU", "HLBU", "AZLU", "CACU", "CASU", "CMUU", "CPSU", "CSQU", "DALU"]:
        return "Hapag-Lloyd", f"https://www.hapag-lloyd.com/en/online-business/track/track-by-container.html?container={container.strip()}"
    elif prefixo in ["CMAU", "CGMU", "CGHU", "CMNU", "ECMU", "AMCU", "TGHU"]:
        return "CMA CGM", f"https://www.cma-cgm.com/ebusiness/tracking/search?SearchBy=Container&SearchValue={container.strip()}"
    elif prefixo in ["ONEU", "NYKU", "TCLU"]:
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
        return df.fillna("")
    else:
        return pd.DataFrame(columns=colunas_padrao)

def salvar_dados(df):
    df.to_csv(ARQUIVO_DADOS, index=False)

df_tracking = carregar_dados()

st.title("Gestão de Rastreamento - Painel Principal")

aba1, aba2, aba3 = st.tabs(["🚀 1. Atualizar Carga / Gerar E-mail", "📋 2. Histórico Geral", "✏️ 3. Edição Rápida de Dados"])

with aba1:
    st.markdown("### 🔍 Etapa 1: Identificação do Contêiner")
    container_input = st.text_input("Digite o Nº do Contêiner e aperte ENTER", help="Exemplo: MSCU1234567. O sistema buscará automaticamente o armador e o histórico desta carga.").strip().upper()
    
    def_proc = ""
    def_porto = ""
    def_data_t = ""
    def_dest = ""
    def_eta = "DD/MM/AAAA"
    def_door = ""
    def_status = "Embarcado"
    
    status_opcoes = [
        "Embarcado",
        "Em trânsito", 
        "Em desova no porto de transbordo",
        "A caminho do destino final",
        "Liberado na Alfândega", 
        "Disponível para Retirada"
    ]
    
    if container_input:
        filtro = df_tracking[df_tracking['Container'] == container_input]
        if not filtro.empty:
            ultimo_reg = filtro.iloc[-1]
            def_proc = str(ultimo_reg.get("Processo", ""))
            def_porto = str(ultimo_reg.get("Porto de Transbordo", ""))
            def_data_t = str(ultimo_reg.get("Data Transbordo", ""))
            def_dest = str(ultimo_reg.get("Destino Final", ""))
            
            eta_salvo = str(ultimo_reg.get("ETA Destino", ""))
            if eta_salvo: def_eta = eta_salvo
                
            door_salvo = str(ultimo_reg.get("DOOR/RAMP", ""))
            if door_salvo: def_door = door_salvo
            
            status_salvo = str(ultimo_reg.get("Status", ""))
            if status_salvo in status_opcoes: def_status = status_salvo
            
            st.success(f"✨ Histórico localizado! Preenchemos os campos abaixo com base na última atualização deste contêiner.")

    idx_status = status_opcoes.index(def_status)

    with st.form("form_dados_carga"):
        st.markdown("### 📝 Etapa 2: Preenchimento de Dados")
        
        col1, col2 = st.columns(2)
        with col1:
            processo_input = st.text_input("Nº do Processo / Referência", value=def_proc, help="O número interno do processo na empresa.")
            porto_transbordo_input = st.text_input("Porto de Transbordo", value=def_porto, help="Opcional. Preencha apenas se houver transbordo.")
            data_transbordo_input = st.text_input("Data no Transbordo", value=def_data_t, help="Data de chegada no porto de transbordo.")
            
        with col2:
            status_input = st.selectbox("Status Atual da Carga", status_opcoes, index=idx_status, help="Selecione em que fase logística a carga se encontra agora.")
            destino_final_input = st.text_input("Destino Final", value=def_dest, help="Ex: Itajaí, Curitiba, etc.")
            eta_input = st.text_input("Previsão de Chegada (ETA)", value=def_eta, help="Formato DD/MM/AAAA. Deixe em branco se a confirmar.")
            door_ramp_input = st.text_input("Modalidade (DOOR/RAMP)", value=def_door, help="Opcional. Informe a modalidade caso aplicável.")
            
        st.markdown("### 🚀 Etapa 3: Ação")
        st.markdown("Escolha se deseja apenas salvar os dados no sistema ou se também quer o texto do e-mail pronto para o cliente.")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            btn_analisar = st.form_submit_button("Salvar Somente")
        with col_btn2:
            btn_email = st.form_submit_button("Gerar E-mail p/ Cliente", type="primary")
    
    if btn_analisar or btn_email:
        if container_input:
            armador_encontrado, link_direto = identificar_armador(container_input)
            
            local_destino = f" ({destino_final_input})" if destino_final_input else ""
            modalidade = f" na modalidade {door_ramp_input}" if door_ramp_input else ""
            
            eta_txt = eta_input if eta_input and eta_input != "DD/MM/AAAA" else "a confirmar"
            frase_eta = f"A previsão de chegada ao destino final{local_destino} é {eta_txt}{modalidade}."
            
            frase_transbordo = ""
            if porto_transbordo_input:
                data_t = f" para o dia {data_transbordo_input}" if data_transbordo_input else ""
                frase_transbordo = f" Lembramos que a carga possui transbordo previsto no porto de {porto_transbordo_input}{data_t}."

            if status_input == "Embarcado":
                corpo_email = f"Prezado cliente,\n\nInformamos que a carga referente ao processo {processo_input} (Contêiner: {container_input.upper()}) foi embarcada no porto de Santos.\n{frase_eta}{frase_transbordo}"
            elif status_input == "Em trânsito":
                corpo_email = f"Prezado cliente,\n\nInformamos que a carga referente ao processo {processo_input} (Contêiner: {container_input.upper()}), embarcada no porto de Santos, encontra-se em trânsito marítimo.\n{frase_eta}{frase_transbordo}"
            elif status_input == "Em desova no porto de transbordo":
                corpo_email = f"Prezado cliente,\n\nInformamos que a carga referente ao processo {processo_input} (Contêiner: {container_input.upper()}) chegou ao porto de transbordo e encontra-se em etapa de desova/movimentação.\n{frase_eta}"
            elif status_input == "A caminho do destino final":
                corpo_email = f"Prezado cliente,\n\nInformamos que a carga referente ao processo {processo_input} (Contêiner: {container_input.upper()}) encontra-se a caminho do destino final{local_destino}.\n{frase_eta}"
            elif status_input == "Liberado na Alfândega":
                corpo_email = f"Prezado cliente,\n\nInformamos que a carga referente ao processo {processo_input} (Contêiner: {container_input.upper()}) encontra-se liberada na alfândega.\nA carga segue para a próxima etapa logística{modalidade}."
            elif status_input == "Disponível para Retirada":
                corpo_email = f"Prezado cliente,\n\nInformamos que a carga referente ao processo {processo_input} (Contêiner: {container_input.upper()}) encontra-se disponível para retirada{local_destino}{modalidade}."

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
            
            st.info(f"⛴️ **Armador Identificado:** {armador_encontrado} | [Abrir site oficial do rastreamento]({link_direto})")
            
            if btn_email:
                st.text_area("📋 Texto Pronto para Copiar:", value=corpo_email, height=150)
            
            st.markdown("---")
            st.subheader("🕒 Linha do Tempo desta Carga")
            if processo_input:
                historico_ref = df_tracking[(df_tracking['Container'] == container_input.upper()) | (df_tracking['Processo'] == processo_input)]
            else:
                historico_ref = df_tracking[df_tracking['Container'] == container_input.upper()]
            st.dataframe(historico_ref, use_container_width=True)
            
        else:
            st.error("⚠️ Por favor, informe o número do contêiner antes de prosseguir.")

with aba2:
    st.subheader("Visualização da Base Completa")
    st.markdown("Abaixo estão todos os contêineres e processos atualizados recentemente.")
    if df_tracking.empty:
        st.info("Nenhum registro encontrado.")
    else:
        st.dataframe(df_tracking, use_container_width=True)
        if st.button("🗑️ Limpar Todos os Registros"):
            if os.path.exists(ARQUIVO_DADOS):
                os.remove(ARQUIVO_DADOS)
            st.rerun()

with aba3:
    st.subheader("Edição Rápida")
    st.markdown("Dê um **duplo clique** na célula que deseja alterar e digite a nova informação. Depois, clique no botão **Salvar Modificações** para guardar permanentemente.")
    
    if df_tracking.empty:
        st.info("Não há dados para editar.")
    else:
        df_editado = st.data_editor(df_tracking, use_container_width=True, num_rows="dynamic")
        if st.button("💾 Salvar Modificações", type="primary"):
            salvar_dados(df_editado)
            st.success("Dados salvos e atualizados no banco!")
            st.rerun()
