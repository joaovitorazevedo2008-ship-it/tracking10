import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
import re

# Tenta importar a biblioteca de leitura de PDF
try:
    from pypdf import PdfReader
    has_pypdf = True
except ImportError:
    has_pypdf = False

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

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("### 📖 Guia do Sistema")
    st.markdown("**1️⃣ Upload de Booking:** Faça upload do PDF para preencher automaticamente processo (DC...), transbordo, destino e ETA.")
    st.markdown("**2️⃣ Atualização:** Insira o contêiner e o status.")
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
    colunas_padrao = ["Processo", "Container", "Armador Detectado", "Status", "Porto de Transbordo", "Data Transbordo", "Destino Final", "ETA Destino", "DOOR/RAMP", "E-mail Pronto", "Alerta ETA"]
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

def calcular_alerta_eta(eta_str):
    if not eta_str or eta_str == "DD/MM/AAAA":
        return "A Confirmar"
    try:
        data_eta = datetime.strptime(eta_str.strip(), "%d/%m/%Y").date()
        hoje = date.today()
        if data_eta < hoje:
            return "🚨 Vencido"
        elif data_eta == hoje:
            return "⚠️ Vence Hoje"
        else:
            return "✅ No Prazo"
    except ValueError:
        return "A Confirmar"

df_tracking = carregar_dados()

st.title("⚓ GESTÃO DE RASTREAMENTO LOGÍSTICO")

# --- DASHBOARD EXECUTIVO INTERATIVO ---
if not df_tracking.empty:
    df_ultimos = df_tracking.drop_duplicates(subset=['Container'], keep='last')
    total_cargas = len(df_ultimos)
    em_transito = len(df_ultimos[df_ultimos['Status'].isin(["Em trânsito", "A caminho do destino final"])])
    liberadas = len(df_ultimos[df_ultimos['Status'].isin(["Liberado na Alfândega", "Disponível para Retirada", "Chegada confirmada"])])
    
    st.markdown("### 📊 Visão Geral da Operação (Clique para listar os processos)")
    col_m1, col_m2, col_m3 = st.columns(3)
    
    if "filtro_dashboard" not in st.session_state:
        st.session_state["filtro_dashboard"] = "Todos"

    with col_m1:
        if st.button(f"📦 Ver Todos os Processos ({total_cargas})", use_container_width=True):
            st.session_state["filtro_dashboard"] = "Todos"
    with col_m2:
        if st.button(f"🚢 Ver Em Trânsito ({em_transito})", use_container_width=True):
            st.session_state["filtro_dashboard"] = "Transito"
    with col_m3:
        if st.button(f"✨ Ver Liberados/Disponíveis ({liberadas})", use_container_width=True):
            st.session_state["filtro_dashboard"] = "Liberados"
            
    st.markdown("<br>", unsafe_allow_html=True)

aba1, aba2, aba3 = st.tabs(["🚀 1. Automação por Booking e Atualização", "📋 2. Histórico Consolidado e Filtros", "✏️ 3. Edição Rápida"])

with aba1:
    st.markdown("### 📄 Automação Inteligente por Booking (PDF)")
    
    if "auto_processo" not in st.session_state: st.session_state["auto_processo"] = ""
    if "auto_destino" not in st.session_state: st.session_state["auto_destino"] = ""
    if "auto_eta" not in st.session_state: st.session_state["auto_eta"] = ""
    if "auto_modalidade" not in st.session_state: st.session_state["auto_modalidade"] = ""
    if "auto_origem" not in st.session_state: st.session_state["auto_origem"] = ""
    if "auto_data_origem" not in st.session_state: st.session_state["auto_data_origem"] = ""

    if has_pypdf:
        arquivo_pdf = st.file_uploader("Faça o upload do Booking em PDF para preenchimento automático", type=["pdf"])
        if arquivo_pdf is not None:
            try:
                leitor = PdfReader(arquivo_pdf)
                texto_pdf = ""
                for pagina in leitor.pages:
                    texto_pdf += pagina.extract_text() or ""
                
                # 1. Extrai Processo no formato DC seguido por números (ex: DC1000873)
                match_dc = re.search(r'DC\d+', texto_pdf.upper())
                if match_dc:
                    st.session_state["auto_processo"] = match_dc.group(0)
                else:
                    match_proc = re.search(r'Booking\s*\|\s*([A-Z0-9/]+)', texto_pdf)
                    if match_proc:
                        st.session_state["auto_processo"] = match_proc.group(1).strip()

                # 2. Extrai Porto de Loading / Origem (Ex: SANTOS)
                match_loading = re.search(r'Porto de Loading\s*\|\s*([A-Z\s,/-]+)', texto_pdf)
                if match_loading:
                    st.session_state["auto_origem"] = match_loading.group(1).strip().split('\n')[0]
                else:
                    # Alternativa baseada no formato do PDF (Ex: SANTOS, SP / EMBRAPORT)
                    if "SANTOS" in texto_pdf.upper():
                        st.session_state["auto_origem"] = "SANTOS"

                # 3. Extrai Destino Final (Ex: INDIANAPOLIS ou Port of Discharge)
                match_dest = re.search(r'Destino Final\s*\|\s*([A-Z\s,]+)', texto_pdf)
                if match_dest:
                    st.session_state["auto_dest"] = match_dest.group(1).strip().split('\n')[0]
                    st.session_state["auto_destino"] = st.session_state["auto_dest"]
                else:
                    match_pod = re.search(r'Port of Discharge\s*\|\s*([A-Z\s,]+)', texto_pdf)
                    if match_pod:
                        st.session_state["auto_destino"] = match_pod.group(1).strip().split('\n')[0]

                # 4. Extrai Datas (ETD e ETA)
                match_datas = re.findall(r'\d{2}/\d{2}/\d{4}', texto_pdf)
                if match_datas:
                    if len(match_datas) >= 2:
                        st.session_state["auto_data_origem"] = match_datas[0]  # ETD
                        st.session_state["auto_eta"] = match_datas[-1]         # ETA
                    else:
                        st.session_state["auto_eta"] = match_datas[0]

                # 5. Extrai Modalidade (Ex: Ramp / Door)
                if "Ramp" in texto_pdf:
                    st.session_state["auto_modalidade"] = "Ramp"
                elif "Door" in texto_pdf:
                    st.session_state["auto_modalidade"] = "Door"

                st.success("✨ Processo, transbordo, destinos e datas extraídos e aplicados com sucesso!")
            except Exception as e:
                st.error(f"Erro ao processar o PDF: {e}")
        st.markdown("---")

    with st.form("form_dados_carga"):
        st.markdown("### 📝 Dados da Carga (Preenchidos pelo Booking ou Manuais)")
        
        col1, col2 = st.columns(2)
        with col1:
            processo_input = st.text_input("Nº do Processo / Referência (Ex: DC1000873)", value=st.session_state["auto_processo"])
            container_input = st.text_input("Nº do Contêiner", value="", help="Formato ex.: HAMU181362 ou MSCU1234567")
            porto_transbordo_input = st.text_input("Porto de Transbordo / Origem", value=st.session_state["auto_origem"])
            data_transbordo_input = st.text_input("Data no Transbordo", value=st.session_state["auto_data_origem"])
            
        with col2:
            status_opcoes = [
                "Embarcado",
                "Em trânsito", 
                "Em desova no porto de transbordo",
                "A caminho do destino final",
                "Chegada confirmada",
                "Liberado na Alfândega", 
                "Em inspeção alfandegária",
                "Disponível para Retirada"
            ]
            status_input = st.selectbox("Status Atual da Carga", status_opcoes, index=0)
            destino_final_input = st.text_input("Destino Final", value=st.session_state["auto_destino"])
            eta_input = st.text_input("Previsão de Chegada (ETA)", value=st.session_state["auto_eta"] if st.session_state["auto_eta"] else "DD/MM/AAAA")
            door_ramp_input = st.text_input("Modalidade (DOOR/RAMP)", value=st.session_state["auto_modalidade"])
            
        st.markdown("<br>", unsafe_allow_html=True)
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            btn_analisar = st.form_submit_button("Salvar Registo")
        with col_btn2:
            btn_email = st.form_submit_button("Salvar e Gerar E-mail p/ Cliente")
    
    if btn_analisar or btn_email:
        if processo_input and container_input:
            armador_encontrado, link_direto = identificar_armador(container_input)
            alerta_status_eta = calcular_alerta_eta(eta_input)
            
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
            elif status_input == "Chegada confirmada":
                corpo_email = f"Prezado cliente,\n\nInformamos que a chegada da carga referente ao processo {processo_input} (Contêiner: {container_input.upper()}) foi confirmada no destino final{local_destino}{modalidade}."
            elif status_input == "Liberado na Alfândega":
                corpo_email = f"Prezado cliente,\n\nInformamos que a carga referente ao processo {processo_input} (Contêiner: {container_input.upper()}) encontra-se liberada na alfândega.\nA carga segue para a próxima etapa logística{modalidade}."
            elif status_input == "Em inspeção alfandegária":
                corpo_email = f"Prezado cliente,\n\nInformamos que a carga referente ao processo {processo_input} (Contêiner: {container_input.upper()}) encontra-se atualmente em inspeção alfandegária.\nSeguimos a monitorizar o processo de perto."
            elif status_input == "Disponível para Retirada":
                corpo_email = f"Prezado cliente,\n\nInformamos que a carga referente ao processo {processo_input} (Contêiner: {container_input.upper()}) encontra-se disponível para retirada{local_destino}{modalidade}."

            nova_linha = {
                "Processo": processo_input.upper(),
                "Container": container_input.upper(),
                "Armador Detectado": armador_encontrado,
                "Status": status_input,
                "Porto de Transbordo": porto_transbordo_input.upper(),
                "Data Transbordo": data_transbordo_input,
                "Destino Final": destino_final_input.upper(),
                "ETA Destino": eta_input,
                "DOOR/RAMP": door_ramp_input.upper(),
                "E-mail Pronto": "Gerado",
                "Alerta ETA": alerta_status_eta
            }
            df_tracking = pd.concat([df_tracking, pd.DataFrame([nova_linha])], ignore_index=True)
            salvar_dados(df_tracking)
            
            st.info(f"⛴️ **Armador Identificado:** {armador_encontrado} | [Aceder ao rastreamento oficial]({link_direto})")
            
            if btn_email:
                st.text_area("📋 Modelo de E-mail Pronto para Copiar:", value=corpo_email, height=150)
            
            st.markdown("---")
            st.subheader("🕒 Histórico Recente do Processo")
            historico_ref = df_tracking[(df_tracking['Container'] == container_input.upper()) | (df_tracking['Processo'].astype(str).str.upper() == processo_input.upper())]
            st.dataframe(historico_ref, use_container_width=True)
            
        else:
            st.error("⚠️ Por favor, preencha o Nº do Processo e o Nº do Contêiner.")

with aba2:
    st.subheader("Histórico Consolidado e Processos Filtrados")
    if df_tracking.empty:
        st.info("Nenhum registo encontrado na base de dados.")
    else:
        df_tracking['Processo'] = df_tracking['Processo'].astype(str).str.upper()
        df_tracking['Container'] = df_tracking['Container'].astype(str).str.upper()
        df_tracking['Alerta ETA'] = df_tracking['ETA Destino'].apply(calcular_alerta_eta)
        
        modo_filtro = st.session_state.get("filtro_dashboard", "Todos")
        if modo_filtro == "Transito":
            df_exibicao = df_tracking[df_tracking['Status'].isin(["Em trânsito", "A caminho do destino final"])]
            st.markdown("📌 **Filtro Ativo:** Exibindo apenas cargas em trânsito/viagem.")
        elif modo_filtro == "Liberados":
            df_exibicao = df_tracking[df_tracking['Status'].isin(["Liberado na Alfândega", "Disponível para Retirada", "Chegada confirmada"])]
            st.markdown("📌 **Filtro Ativo:** Exibindo apenas cargas liberadas ou disponíveis.")
        else:
            df_exibicao = df_tracking
            st.markdown("📌 **Filtro Ativo:** Exibindo todos os processos registados.")

        st.dataframe(df_exibicao, use_container_width=True)
        
        col_f1, col_f2 = st.columns([2, 1])
        with col_f2:
            if st.button("🗑️ Limpar Todos os Registros"):
                if os.path.exists(ARQUIVO_DADOS):
                    os.remove(ARQUIVO_DADOS)
                st.rerun()

with aba3:
    st.subheader("Edição Rápida da Base")
    st.markdown("Abaixo constam apenas os registos mais recentes de cada contêiner. Edite diretamente nas células e clique em salvar.")
    
    if df_tracking.empty:
        st.info("Não há dados disponíveis para edição.")
    else:
        df_latest = df_tracking.drop_duplicates(subset=['Container'], keep='last')
        df_editado = st.data_editor(df_latest, use_container_width=True)
        
        if st.button("💾 Salvar Modificações"):
            df_tracking.update(df_editado)
            df_tracking['Alerta ETA'] = df_tracking['ETA Destino'].apply(calcular_alerta_eta)
            salvar_dados(df_tracking)
            st.success("Modificações gravadas com sucesso!")
            st.rerun()
