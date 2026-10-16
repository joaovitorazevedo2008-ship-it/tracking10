
import streamlit as st
import sqlite3
import re
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

BIC_URL = "https://www.bic-code.org/pt/codigos-bic/"

ARMADORES = {
    "MAEU": {
        "nome": "Maersk",
        "url": "https://www.maersk.com/tracking/"
    },
    "MSCU": {
        "nome": "MSC",
        "url": "https://www.msc.com/en/track-a-shipment"
    },
    "CMAU": {
        "nome": "CMA CGM",
        "url": "https://www.cma-cgm.com/ebusiness/tracking"
    },
    "CMDU": {
        "nome": "CMA CGM",
        "url": "https://www.cma-cgm.com/ebusiness/tracking"
    },
    "HLCU": {
        "nome": "Hapag-Lloyd",
        "url": "https://www.hapag-lloyd.com/pt/online-business/track/track.html"
    },
    "COSU": {
        "nome": "COSCO Shipping",
        "url": "https://elines.coscoshipping.com/ebusiness/cargoTracking"
    },
    "EISU": {
        "nome": "Evergreen",
        "url": "https://www.shipmentlink.com/"
    },
    "ONEY": {
        "nome": "Ocean Network Express (ONE)",
        "url": "https://ecomm.one-line.com/one-ecom/manage-shipment/cargo-tracking"
    },
    "OOLU": {
        "nome": "OOCL",
        "url": "https://www.oocl.com/"
    },
    "YMLU": {
        "nome": "Yang Ming",
        "url": "https://www.yangming.com/"
    },
    "ZIMU": {
        "nome": "ZIM",
        "url": "https://www.zim.com/tools/track-a-shipment"
    },
    "HMMU": {
        "nome": "HMM",
        "url": "https://www.hmm21.com/"
    },
    "WHLU": {
        "nome": "Wan Hai Lines",
        "url": "https://www.wanhai.com/"
    },
    "PCIU": {
        "nome": "Pacific International Lines",
        "url": "https://www.pilship.com/"
    },
    "APLU": {
        "nome": "APL",
        "url": "https://www.cma-cgm.com/ebusiness/tracking"
    },
    "ANNU": {
        "nome": "ANL",
        "url": "https://www.cma-cgm.com/ebusiness/tracking"
    },
    "SUDU": {
        "nome": "Hamburg Süd / Maersk",
        "url": "https://www.maersk.com/tracking/"
    },
    "SKLU": {
        "nome": "Safmarine / Maersk",
        "url": "https://www.maersk.com/tracking/"
    },
    "GESU": {
        "nome": "Gold Star Line",
        "url": "https://www.gsl.com.hk/"
    },
    "SITU": {
        "nome": "SITC",
        "url": "https://www.sitc.com/"
    },
    "TGHU": {
        "nome": "Textainer",
        "url": BIC_URL
    },
    "FCIU": {
        "nome": "Florens",
        "url": BIC_URL
    },
    "TEMU": {
        "nome": "Triton",
        "url": BIC_URL
    },
    "CAIU": {
        "nome": "CAI",
        "url": BIC_URL
    },
    "SEGU": {
        "nome": "Seaco",
        "url": BIC_URL
    },
}


def identificar_armador(container):
    container = (container or "").strip().upper()
    prefixo = container[:4]

    return ARMADORES.get(
        prefixo,
        {
            "nome": "Prefixo não identificado",
            "url": BIC_URL
        }
    )


def extrair_texto_documento(arquivo):
    nome = arquivo.name.lower()
    dados = arquivo.getvalue()

    if nome.endswith(".pdf"):
        if pdfplumber is None:
            raise RuntimeError(
                "Instale pdfplumber no requirements.txt."
            )

        with pdfplumber.open(BytesIO(dados)) as pdf:
            texto = "\n".join(
                pagina.extract_text() or ""
                for pagina in pdf.pages
            )

        if texto.strip():
            return texto

        if (
            pytesseract is not None
            and convert_from_bytes is not None
        ):
            imagens = convert_from_bytes(dados)
            return "\n".join(
                pytesseract.image_to_string(
                    imagem,
                    lang="eng"
                )
                for imagem in imagens
            )

        raise RuntimeError(
            "PDF digitalizado. Verifique as dependências de OCR."
        )

    if nome.endswith(
        (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff")
    ):
        if Image is None or pytesseract is None:
            raise RuntimeError(
                "Instale Pillow e pytesseract."
            )

        imagem = Image.open(BytesIO(dados))

        try:
            return pytesseract.image_to_string(
                imagem,
                lang="eng"
            )
        except Exception:
            return pytesseract.image_to_string(imagem)

    raise RuntimeError(
        "Envie um PDF, PNG, JPG ou WEBP."
    )


def extrair_campos_carga(texto):
    import re

    texto = texto.replace("\r", "\n")
    texto = re.sub(r"[ \t]+", " ", texto)
    linhas = [
        re.sub(r"\s+", " ", linha).strip()
        for linha in texto.splitlines()
        if linha.strip()
    ]
    completo = "\n".join(linhas)

    def capturar(padroes):
        for padrao in padroes:
            m = re.search(
                padrao,
                completo,
                re.IGNORECASE | re.MULTILINE
            )
            if m:
                return m.group(1).strip(" :-;,")
        return ""

    booking = capturar([
        r"\bBooking(?:\s*(?:No\.?|Number|#))?\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-\/]{5,})"
    ])

    # Procura datas identificadas explicitamente como ETD e ETA.
    etd = capturar([
        r"\bETD\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"\bETD\s*[:\-]?\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2})",
        r"\bEstimated Departure(?: Date)?\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
    ])

    eta = capturar([
        r"\bETA\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"\bETA\s*[:\-]?\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2})",
        r"\bEstimated Arrival(?: Date)?\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
    ])

    # Portos identificados por rótulos explícitos.
    transbordo = capturar([
        r"(?:Port of Transshipment|Transshipment Port|Transhipment Port|Porto de Transbordo)\s*[:\-]?\s*([A-Z][A-Z ,\-\/]{2,})"
    ])

    porto_final = capturar([
        r"(?:Final Destination|Final Port|Port of Discharge|Destination Port|Porto Final|Destino Final)\s*[:\-]?\s*([A-Z][A-Z ,\-\/]{2,})"
    ])

    # Analisa a tabela de rota: From / To / By / ETD / ETA.
    # Exemplo: SANTOS, SP -> SINGAPORE, SG -> TOKYO, JP.
    portos_rota = []

    for linha in linhas:
        if re.search(
            r"\b(?:From|To|Vessel|Voyage|ETD|ETA|Booking|Commodity)\b",
            linha,
            re.IGNORECASE
        ):
            continue

        encontrados = re.findall(
            r"\b([A-Z][A-Z .'-]{2,},\s*[A-Z]{2,3})"
            r"(?:\s*\([A-Z0-9]{4,6}\))?",
            linha
        )

        for porto in encontrados:
            porto = porto.strip()
            if porto not in portos_rota:
                portos_rota.append(porto)

    # Alternativa para tabelas extraídas como texto contínuo.
    if not portos_rota:
        encontrados = re.findall(
            r"\b([A-Z][A-Z .'-]{2,},\s*[A-Z]{2,3})"
            r"(?:\s*\([A-Z0-9]{4,6}\))?",
            completo
        )
        for porto in encontrados:
            porto = porto.strip()
            if porto not in portos_rota:
                portos_rota.append(porto)

    if not porto_final and portos_rota:
        porto_final = portos_rota[-1]

    if not transbordo and len(portos_rota) >= 3:
        transbordo = portos_rota[-2]

    # Fallback para datas em tabelas que não rotulam cada data.
    datas = re.findall(
        r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
        r"\d{4}[/-]\d{1,2}[/-]\d{1,2})\b",
        completo
    )

    if not etd and datas:
        etd = datas[0]

    if not eta and len(datas) >= 2:
        eta = datas[-1]

    referencia_dc = capturar([
        r"\b(?:DC Reference|DC Ref(?:erence)?|Referência DC|Código DC)\s*[:#\-]?\s*(DC[A-Z0-9\-]{3,})"
    ])

    return {
        "referencia_dc": referencia_dc,
        "booking": booking,
        "transbordo": transbordo,
        "porto_final": porto_final,
        "etd": etd,
        "eta": eta
    }



def conectar():
    return sqlite3.connect(DB)


def iniciar_banco():
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cargas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dc TEXT UNIQUE NOT NULL,
                container TEXT DEFAULT '',
                booking TEXT DEFAULT '',
                origem TEXT DEFAULT '',
                destino TEXT DEFAULT '',
                armador TEXT DEFAULT '',
                status TEXT DEFAULT 'Em trânsito',
                eta TEXT DEFAULT ''
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS eventos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dc TEXT NOT NULL,
                data TEXT NOT NULL,
                descricao TEXT NOT NULL,
                local TEXT
            )
        """)

        colunas = {
            linha[1]
            for linha in conn.execute(
                "PRAGMA table_info(cargas)"
            ).fetchall()
        }

        if "transbordo" not in colunas:
            conn.execute(
                "ALTER TABLE cargas ADD COLUMN transbordo TEXT DEFAULT ''"
            )

        if "etd" not in colunas:
            conn.execute(
                "ALTER TABLE cargas ADD COLUMN etd TEXT DEFAULT ''"
            )


def buscar(referencia):
    with conectar() as conn:
        conn.row_factory = sqlite3.Row

        return conn.execute("""
            SELECT *
            FROM cargas
            WHERE UPPER(dc) = UPPER(?)
               OR UPPER(booking) = UPPER(?)
            ORDER BY id DESC
        """, (referencia.strip(), referencia.strip())).fetchall()


def listar_cargas():
    with conectar() as conn:
        conn.row_factory = sqlite3.Row

        return conn.execute("""
            SELECT *
            FROM cargas
            ORDER BY id DESC
        """).fetchall()


iniciar_banco()

# ==========================================================
# INTERFACE DO DC LCL TRACKING
# ==========================================================

st.markdown("""

<style>
    .stApp {
        background-color: #f4f7fb;
        color: #1f2937;
    }

    h1, h2, h3, h4, p, label,
    .stMarkdown, [data-testid="stCaptionContainer"] {
        color: #1f2937;
    }

    [data-testid="stWidgetLabel"] p {
        color: #1f2937 !important;
    }

    .stTabs [data-baseweb="tab"] {
        color: #334155 !important;
    }

    .stTabs [aria-selected="true"] {
        color: #1261a0 !important;
    }

    div.stButton > button,
    div.stFormSubmitButton > button {
        background-color: #1261a0;
        color: #ffffff !important;
        border: none;
        border-radius: 8px;
    }

    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover {
        background-color: #0b4778;
        color: #ffffff !important;
    }

    input, textarea {
        color: #1f2937 !important;
    }
</style>

""", unsafe_allow_html=True)

st.title("DC LCL TRACKING")
st.caption("Sistema de rastreamento de cargas LCL")

pagina = st.sidebar.radio(
    "Menu",
    ["Rastreamento", "Administração"]
)


# ==========================================================
# RASTREAMENTO PÚBLICO
# ==========================================================

if pagina == "Rastreamento":
    st.subheader("Rastreie sua carga")

    referencia = st.text_input(
        "Referência DC ou número do Booking",
        placeholder="Ex.: DC100001"
    )

    if st.button("Consultar carga"):
        if not referencia.strip():
            st.warning("Digite uma referência.")
        else:
            resultados = buscar(referencia)

            if not resultados:
                st.error("Nenhuma carga encontrada.")
            else:
                for carga in resultados:
                    dc = carga["dc"]

                    st.markdown("---")
                    st.subheader(f"Carga {dc}")

                    st.write(
                        f"**Booking:** "
                        f"{carga['booking'] or 'Não informado'}"
                    )

                    st.write(
                        f"**Porto de transbordo:** "
                        f"{carga['transbordo'] or 'Não informado'}"
                    )

                    st.write(
                        f"**Porto final:** "
                        f"{carga['destino'] or 'Não informado'}"
                    )

                    col1, col2 = st.columns(2)

                    col1.write("**Data de embarque (ETD)**")
                    col1.write(carga["etd"] or "Não informada")

                    col2.write("**Data de chegada (ETA)**")
                    col2.write(carga["eta"] or "Não informada")

                    st.write(
                        f"**Status:** {carga['status']}"
                    )

                    eventos = []

                    with conectar() as conn:
                        eventos = conn.execute("""
                            SELECT data, descricao, local
                            FROM eventos
                            WHERE UPPER(dc) = UPPER(?)
                            ORDER BY id DESC
                        """, (dc,)).fetchall()

                    if eventos:
                        st.markdown("#### Histórico da carga")

                        for data, descricao, local in eventos:
                            st.write(
                                f"**{data}** — {descricao}"
                            )
                            if local:
                                st.caption(local)


# ==========================================================
# ADMINISTRAÇÃO
# ==========================================================

elif pagina == "Administração":
    st.subheader("Painel administrativo")

    try:
        senha_correta = st.secrets["ADMIN_PASSWORD"]
    except Exception:
        senha_correta = "troque-esta-senha"

    senha_digitada = st.text_input(
        "Senha administrativa",
        type="password"
    )

    if senha_digitada != senha_correta:
        st.info(
            "Digite a senha administrativa para acessar o painel."
        )
        st.stop()

    st.success("Acesso administrativo autorizado.")

    aba1, aba2, aba3 = st.tabs([
        "Cadastrar carga",
        "Registrar evento",
        "Importar print/PDF"
    ])

    # ------------------------------------------------------
    # CADASTRAR CARGA
    # ------------------------------------------------------

    with aba1:
        st.write("Cadastre ou revise os dados principais da carga.")

        with st.form("form_carga"):
            dc = st.text_input(
                "Referência DC *",
                placeholder="Ex.: DC100001"
            ).strip().upper()

            booking = st.text_input(
                "Booking"
            ).strip().upper()

            transbordo = st.text_input(
                "Porto de transbordo"
            )

            destino = st.text_input(
                "Porto final *"
            )

            etd = st.text_input(
                "Data de embarque (ETD)",
                placeholder="DD/MM/AAAA"
            )

            eta = st.text_input(
                "Data de chegada (ETA)",
                placeholder="DD/MM/AAAA"
            )

            status = st.selectbox(
                "Status da carga",
                [
                    "Booking confirmado",
                    "Aguardando embarque",
                    "Em trânsito",
                    "Em transbordo",
                    "Chegada ao destino",
                    "Entregue"
                ]
            )

            salvar = st.form_submit_button(
                "Salvar carga"
            )

        if salvar:
            if not dc:
                st.error("Informe a referência DC.")
            elif not destino.strip():
                st.error("Informe o porto final.")
            else:
                try:
                    with conectar() as conn:
                        conn.execute("""
                            INSERT INTO cargas (
                                dc,
                                container,
                                booking,
                                origem,
                                destino,
                                armador,
                                status,
                                eta,
                                transbordo,
                                etd
                            )
                            VALUES (?, '', ?, '', ?, '', ?, ?, ?, ?)
                        """, (
                            dc,
                            booking,
                            destino.strip(),
                            status,
                            eta.strip(),
                            transbordo.strip(),
                            etd.strip()
                        ))

                    st.success(
                        f"Carga {dc} cadastrada com sucesso!"
                    )

                except sqlite3.IntegrityError:
                    st.error(
                        "Esta referência DC já está cadastrada."
                    )

                except sqlite3.Error as erro:
                    st.error(f"Erro no banco de dados: {erro}")

    # ------------------------------------------------------
    # REGISTRAR EVENTO
    # ------------------------------------------------------

    with aba2:
        st.write("Adicione uma atualização ao histórico da carga.")

        with st.form("form_evento"):
            dc_evento = st.text_input(
                "Referência DC"
            ).strip().upper()

            descricao = st.text_input(
                "Descrição do evento",
                placeholder="Ex.: Carga embarcada"
            )

            local = st.text_input(
                "Local",
                placeholder="Ex.: Singapura"
            )

            salvar_evento = st.form_submit_button(
                "Registrar evento"
            )

        if salvar_evento:
            if not dc_evento or not descricao.strip():
                st.error(
                    "Informe a referência DC e a descrição."
                )
            else:
                carga_existe = buscar(dc_evento)

                if not carga_existe:
                    st.error("Referência DC não encontrada.")
                else:
                    from datetime import datetime

                    with conectar() as conn:
                        conn.execute("""
                            INSERT INTO eventos (
                                dc, data, descricao, local
                            )
                            VALUES (?, ?, ?, ?)
                        """, (
                            dc_evento,
                            datetime.now().strftime(
                                "%d/%m/%Y %H:%M"
                            ),
                            descricao.strip(),
                            local.strip()
                        ))

                    st.success("Evento registrado!")

    # ------------------------------------------------------
    # IMPORTAR PRINT OU PDF
    # ------------------------------------------------------

    with aba3:
        st.write(
            "Envie o booking para extrair os seis campos principais."
        )

        arquivo = st.file_uploader(
            "Selecione o PDF ou a imagem",
            type=[
                "pdf", "png", "jpg", "jpeg",
                "webp", "tif", "tiff"
            ]
        )

        if arquivo is not None:
            try:
                texto = extrair_texto_documento(arquivo)
                campos = extrair_campos_carga(texto)

                st.success(
                    "Documento lido. Confira os dados extraídos."
                )

                with st.form("form_importacao"):
                    dc_imp = st.text_input(
                        "Referência DC",
                        value=campos["referencia_dc"]
                    )

                    booking_imp = st.text_input(
                        "Booking",
                        value=campos["booking"]
                    )

                    trans_imp = st.text_input(
                        "Porto de transbordo",
                        value=campos["transbordo"]
                    )

                    destino_imp = st.text_input(
                        "Porto final",
                        value=campos["porto_final"]
                    )

                    etd_imp = st.text_input(
                        "Data de embarque (ETD)",
                        value=campos["etd"]
                    )

                    eta_imp = st.text_input(
                        "Data de chegada (ETA)",
                        value=campos["eta"]
                    )

                    importar = st.form_submit_button(
                        "Cadastrar carga com estes dados"
                    )

                if importar:
                    if not dc_imp.strip():
                        st.error(
                            "Informe uma referência DC. "
                            "Ela é interna e pode não estar no booking."
                        )
                    elif not destino_imp.strip():
                        st.error("Informe o porto final.")
                    else:
                        try:
                            with conectar() as conn:
                                conn.execute("""
                                    INSERT INTO cargas (
                                        dc,
                                        container,
                                        booking,
                                        origem,
                                        destino,
                                        armador,
                                        status,
                                        eta,
                                        transbordo,
                                        etd
                                    )
                                    VALUES (?, '', ?, '', ?, '', ?, ?, ?, ?)
                                """, (
                                    dc_imp.strip().upper(),
                                    booking_imp.strip().upper(),
                                    destino_imp.strip(),
                                    "Booking confirmado",
                                    eta_imp.strip(),
                                    trans_imp.strip(),
                                    etd_imp.strip()
                                ))

                            st.success(
                                f"Carga {dc_imp.strip().upper()} cadastrada!"
                            )

                        except sqlite3.IntegrityError:
                            st.error(
                                "Essa referência DC já existe. "
                                "Use outra referência."
                            )

            except Exception as erro:
                st.error(
                    f"Não foi possível ler o documento: {erro}"
                )

    # ------------------------------------------------------
    # LISTA DE CARGAS
    # ------------------------------------------------------

    st.markdown("---")
    st.subheader("Cargas cadastradas")

    cargas = listar_cargas()

    if cargas:
        for carga in cargas:
            st.write(
                f"**{carga['dc']}** | "
                f"Booking: {carga['booking'] or '-'} | "
                f"Destino: {carga['destino'] or '-'} | "
                f"Status: {carga['status']}"
            )
    else:
        st.info("Nenhuma carga cadastrada.")
