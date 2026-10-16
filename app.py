
import streamlit as st
import sqlite3
import re
from io import BytesIO
from datetime import datetime

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from PIL import Image, ImageOps, ImageEnhance, ImageFilter
    import pytesseract
except ImportError:
    Image = None
    ImageOps = None
    ImageEnhance = None
    ImageFilter = None
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


def extrair_texto_documento(arquivo):
    nome = arquivo.name.lower()
    dados = arquivo.getvalue()

    if nome.endswith(".pdf"):
        if pdfplumber is None:
            raise RuntimeError("Instale pdfplumber.")

        with pdfplumber.open(BytesIO(dados)) as pdf:
            texto = "\n".join(
                pagina.extract_text() or ""
                for pagina in pdf.pages
            )

        if len(texto.strip()) > 30:
            return texto

        if convert_from_bytes is None:
            raise RuntimeError(
                "Para PDFs digitalizados, instale pdf2image "
                "e poppler-utils."
            )

        imagens = convert_from_bytes(dados)

    else:
        if Image is None or pytesseract is None:
            raise RuntimeError(
                "Instale Pillow e pytesseract."
            )

        imagem = Image.open(BytesIO(dados))
        imagem = ImageOps.exif_transpose(imagem)
        imagens = [imagem]

    if Image is None or pytesseract is None:
        raise RuntimeError("Dependências de OCR ausentes.")

    textos = []

    for imagem in imagens:
        imagem = ImageOps.grayscale(imagem)

        if imagem.width < 1800:
            fator = 1800 / imagem.width
            imagem = imagem.resize((
                1800,
                int(imagem.height * fator)
            ))

        imagem = ImageOps.autocontrast(imagem)
        imagem = ImageEnhance.Contrast(imagem).enhance(2)
        imagem = imagem.filter(ImageFilter.SHARPEN)

        texto = pytesseract.image_to_string(
            imagem,
            lang="eng",
            config="--psm 6"
        )

        if len(texto.strip()) < 20:
          
            texto = pytesseract.image_to_string(
                imagem,
                lang="eng",
                config="--psm 11"
            )


        textos.append(texto)

    resultado = "\n".join(textos)

    if not resultado.strip():
        raise RuntimeError("Nenhum texto foi reconhecido.")

            
    return resultado

def iniciar_banco():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cargas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dc TEXT UNIQUE,
            container TEXT,
            booking TEXT,
            origem TEXT,
            destino TEXT,
            armador TEXT,
            status TEXT DEFAULT 'Em trânsito',
            eta TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dc TEXT,
            data TEXT,
            descricao TEXT,
            local TEXT
        )
    """)

    # Adiciona as colunas novas sem apagar os dados existentes.
    colunas = {
        linha["name"]
        for linha in cursor.execute(
            "PRAGMA table_info(cargas)"
        ).fetchall()
    }

    if "transbordo" not in colunas:
        cursor.execute(
            "ALTER TABLE cargas ADD COLUMN transbordo TEXT"
        )

    if "etd" not in colunas:
        cursor.execute(
            "ALTER TABLE cargas ADD COLUMN etd TEXT"
        )

    conn.commit()
    conn.close()


def conectar_banco():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def limpar_texto(valor):
    if valor is None:
        return ""
    return re.sub(r"\s+", " ", str(valor)).strip()


def encontrar_campo(texto, rotulos):
    """
    Procura um rótulo no texto extraído do documento.
    Retorna o conteúdo encontrado ao lado do rótulo.
    """
    linhas = [
        limpar_texto(linha)
        for linha in texto.splitlines()
        if limpar_texto(linha)
    ]

    for i, linha in enumerate(linhas):
        for rotulo in rotulos:
            padrao = (
                r"(?i)\b"
                + re.escape(rotulo)
                + r"\b\s*[:#\-]?\s*(.*)"
            )

            resultado = re.search(padrao, linha)

            if resultado:
                valor = limpar_texto(resultado.group(1))

                # Evita capturar apenas o próprio nome do campo.
                if valor and valor.lower() not in [
                    rotulo.lower(),
                    "n/a",
                    "na"
                ]:
                    return valor

                # Alguns documentos colocam o valor na linha seguinte.
                if i + 1 < len(linhas):
                    proxima = linhas[i + 1]
                    if len(proxima) < 100:
                        return proxima

    return ""


def extrair_campos_carga(texto):
    """
    Extrai somente os seis campos solicitados.
    Os rótulos variam de acordo com o formato do documento,
    então os valores extraídos precisam ser conferidos.
    """
    campos = {
        "booking": encontrar_campo(texto, [
            "Booking Number",
            "Booking No",
            "Booking",
            "Booking Ref",
            "Booking Reference"
        ]),
        "transbordo": encontrar_campo(texto, [
            "Port of Transshipment",
            "Port of Transhipment",
            "Transshipment Port",
            "Transhipment Port",
            "Porto de Transbordo",
            "Transbordo"
        ]),
        "destino": encontrar_campo(texto, [
            "Final Destination",
            "Port of Discharge",
            "Discharge Port",
            "Porto Final",
            "Porto de Destino",
            "Destination Port"
        ]),
        "etd": encontrar_campo(texto, [
            "ETD",
            "Estimated Time of Departure",
            "Departure Date",
            "Sailing Date"
        ]),
        "eta": encontrar_campo(texto, [
            "ETA",
            "Estimated Time of Arrival",
            "Arrival Date"
        ])
    }

    # Referência DC é preenchida manualmente pelo usuário.
    # Não é inferida automaticamente do documento.
    return campos


def salvar_carga(
    dc,
    booking,
    transbordo,
    destino,
    etd,
    eta
):
    dc = limpar_texto(dc)
    booking = limpar_texto(booking)
    transbordo = limpar_texto(transbordo)
    destino = limpar_texto(destino)
    etd = limpar_texto(etd)
    eta = limpar_texto(eta)

    if not dc:
        raise ValueError("Preencha a Referência DC.")

    conn = conectar_banco()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO cargas (
                dc,
                booking,
                transbordo,
                destino,
                etd,
                eta,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(dc) DO UPDATE SET
                booking = excluded.booking,
                transbordo = excluded.transbordo,
                destino = excluded.destino,
                etd = excluded.etd,
                eta = excluded.eta
        """, (
            dc,
            booking,
            transbordo,
            destino,
            etd,
            eta,
            "Em trânsito"
        ))

        conn.commit()

    finally:
        conn.close()


def buscar_carga(referencia):
    referencia = limpar_texto(referencia)

    conn = conectar_banco()
    cursor = conn.cursor()

    carga = cursor.execute("""
        SELECT *
        FROM cargas
        WHERE LOWER(dc) = LOWER(?)
           OR LOWER(COALESCE(booking, '')) = LOWER(?)
        LIMIT 1
    """, (referencia, referencia)).fetchone()

    eventos = []

    if carga:
        eventos = cursor.execute("""
            SELECT data, descricao, local
            FROM eventos
            WHERE dc = ?
            ORDER BY id DESC
        """, (carga["dc"],)).fetchall()

    conn.close()

    return carga, eventos


iniciar_banco()

# =========================
# CONFIGURAÇÃO VISUAL
# =========================

st.markdown("""
<style>
.stApp {
    background-color: #f4f8fc;
    color: #16324f;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

.topo {
    background: linear-gradient(120deg, #063b70, #0878bd);
    padding: 28px;
    border-radius: 14px;
    color: white;
    margin-bottom: 24px;
}

.topo h1 {
    color: white;
    margin-bottom: 4px;
}

.topo p {
    color: #e4f2ff;
    margin-bottom: 0;
}

.cartao {
    background: white;
    border: 1px solid #dce7f1;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 12px;
}

.campo-label {
    color: #56718c;
    font-size: 13px;
    font-weight: 600;
}

.campo-valor {
    color: #123c63;
    font-size: 18px;
    font-weight: 700;
    overflow-wrap: anywhere;
}

.stButton > button {
    background-color: #0878bd;
    color: white;
    border: none;
    border-radius: 8px;
    min-height: 42px;
}

.stButton > button:hover {
    background-color: #065b91;
    color: white;
}

h1, h2, h3 {
    color: #123c63;
}
</style>
""", unsafe_allow_html=True)


# =========================
# CABEÇALHO
# =========================

st.markdown("""
<div class="topo">
    <h1>🚢 DC LCL Tracking</h1>
    <p>
        Acompanhe suas cargas LCL com praticidade e segurança.
    </p>
</div>
""", unsafe_allow_html=True)


# =========================
# FUNÇÕES AUXILIARES
# =========================

def exibir_valor(rotulo, valor):
    valor = valor if valor else "Não informado"

    st.markdown(
        f"""
        <div class="cartao">
            <div class="campo-label">{rotulo}</div>
            <div class="campo-valor">{valor}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def obter_senha_admin():
    try:
        return st.secrets["ADMIN_PASSWORD"]
    except Exception:
        return "troque-esta-senha"


def registrar_evento(dc, data, descricao, local):
    conn = conectar_banco()

    conn.execute("""
        INSERT INTO eventos (dc, data, descricao, local)
        VALUES (?, ?, ?, ?)
    """, (
        limpar_texto(dc),
        limpar_texto(data),
        limpar_texto(descricao),
        limpar_texto(local)
    ))

    conn.commit()
    conn.close()


# =========================
# MENU
# =========================

pagina = st.radio(
    "Menu principal",
    [
        "Consultar carga",
        "Painel administrativo"
    ],
    horizontal=True
)


# =========================
# CONSULTA PÚBLICA
# =========================

if pagina == "Consultar carga":

    st.subheader("🔎 Rastrear minha carga")

    referencia = st.text_input(
        "Referência DC ou Booking",
        placeholder="Digite sua referência ou número do booking"
    )

    if st.button("Consultar carga", use_container_width=True):
        if not referencia.strip():
            st.warning("Digite uma Referência DC ou Booking.")
        else:
            carga, eventos = buscar_carga(referencia)

            if not carga:
                st.error("Nenhuma carga encontrada com essa referência.")
            else:
                st.success("Carga localizada!")

                st.markdown("### Informações da carga")

                col1, col2 = st.columns(2)

                with col1:
                    exibir_valor(
                        "Referência DC",
                        carga["dc"]
                    )
                    exibir_valor(
                        "Booking",
                        carga["booking"]
                    )
                    exibir_valor(
                        "Porto de transbordo",
                        carga["transbordo"]
                    )

                with col2:
                    exibir_valor(
                        "Porto final",
                        carga["destino"]
                    )
                    exibir_valor(
                        "ETD — Data de saída",
                        carga["etd"]
                    )
                    exibir_valor(
                        "ETA — Data prevista de chegada",
                        carga["eta"]
                    )

                st.markdown("### Status da carga")

                st.info(
                    carga["status"] or "Status não informado"
                )

                if eventos:
                    st.markdown("### Histórico de atualizações")

                    for evento in eventos:
                        st.markdown(
                            f"""
                            <div class="cartao">
                                <strong>{evento['data'] or 'Data não informada'}</strong>
                                <br>
                                {evento['descricao'] or ''}
                                <br>
                                <span style="color:#56718c">
                                    {evento['local'] or ''}
                                </span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                else:
                    st.caption(
                        "Ainda não existem atualizações de histórico "
                        "para esta carga."
                    )


# =========================
# PAINEL ADMINISTRATIVO
# =========================

elif pagina == "Painel administrativo":

    st.subheader("🔐 Acesso administrativo")

    if "admin_autenticado" not in st.session_state:
        st.session_state["admin_autenticado"] = False

    if not st.session_state["admin_autenticado"]:

        senha = st.text_input(
            "Senha de administrador",
            type="password"
        )

        if st.button("Entrar", use_container_width=True):
            senha_correta = obter_senha_admin()

            if senha == senha_correta:
                st.session_state["admin_autenticado"] = True
                st.rerun()
            else:
                st.error("Senha incorreta.")

        st.caption(
            "Configure ADMIN_PASSWORD nos Secrets do Streamlit "
            "antes de publicar o site."
        )

    else:

        if st.button("Sair do painel"):
            st.session_state["admin_autenticado"] = False
            st.rerun()

        aba_importar, aba_manual, aba_eventos, aba_lista = st.tabs([
            "Importar documento",
            "Cadastrar carga",
            "Atualizar histórico",
            "Cargas cadastradas"
        ])

        # -------------------------
        # IMPORTAR DOCUMENTO
        # -------------------------

        with aba_importar:

            st.markdown("### Importar PDF ou imagem")

            st.write(
                "Envie um documento de transporte para tentar "
                "extrair automaticamente os cinco campos do arquivo. "
                "A Referência DC será preenchida por você."
            )

            arquivo = st.file_uploader(
                "Selecione o documento",
                type=["pdf", "png", "jpg", "jpeg", "tif", "tiff"],
                key="arquivo_importacao"
            )

            if arquivo is not None:

                if st.button("Ler documento", use_container_width=True):

                    try:
                        texto_extraido = extrair_texto_documento(
                            arquivo
                        )

                        campos = extrair_campos_carga(
                            texto_extraido
                        )

                        st.session_state["texto_documento"] = (
                            texto_extraido
                        )
                        st.session_state["campos_documento"] = campos

                        st.success(
                            "Documento lido. Confira os campos abaixo."
                        )

                    except Exception as erro:
                        st.error(
                            f"Não foi possível ler o documento: {erro}"
                        )

            if "campos_documento" in st.session_state:

                campos = st.session_state["campos_documento"]

                st.markdown("### Confira os seis campos")

                dc_importacao = st.text_input(
                    "Referência DC (obrigatória)",
                    key="dc_importacao"
                )

                booking_importacao = st.text_input(
                    "Booking",
                    value=campos.get("booking", ""),
                    key="booking_importacao"
                )

                transbordo_importacao = st.text_input(
                    "Porto de transbordo",
                    value=campos.get("transbordo", ""),
                    key="transbordo_importacao"
                )

                destino_importacao = st.text_input(
                    "Porto final",
                    value=campos.get("destino", ""),
                    key="destino_importacao"
                )

                etd_importacao = st.text_input(
                    "ETD — Data de saída",
                    value=campos.get("etd", ""),
                    key="etd_importacao"
                )

                eta_importacao = st.text_input(
                    "ETA — Data de chegada",
                    value=campos.get("eta", ""),
                    key="eta_importacao"
                )

                with st.expander("Ver texto reconhecido no documento"):
                    st.text(
                        st.session_state.get(
                            "texto_documento",
                            ""
                        )
                    )

                if st.button(
                    "Salvar carga importada",
                    use_container_width=True
                ):
                    if not dc_importacao.strip():
                        st.error(
                            "Preencha a Referência DC antes de salvar."
                        )
                    else:
                        try:
                            salvar_carga(
                                dc_importacao,
                                booking_importacao,
                                transbordo_importacao,
                                destino_importacao,
                                etd_importacao,
                                eta_importacao
                            )

                            st.success(
                                "Carga salva com sucesso!"
                            )

                            del st.session_state["campos_documento"]

                            st.rerun()

                        except Exception as erro:
                            st.error(
                                f"Erro ao salvar a carga: {erro}"
                            )

        # -------------------------
        # CADASTRO MANUAL
        # -------------------------

        with aba_manual:

            st.markdown("### Cadastrar carga manualmente")

            with st.form("form_cadastro_manual"):

                dc = st.text_input(
                    "Referência DC *"
                )

                booking = st.text_input(
                    "Booking"
                )

                transbordo = st.text_input(
                    "Porto de transbordo"
                )

                destino = st.text_input(
                    "Porto final"
                )

                etd = st.text_input(
                    "ETD — Data de saída"
                )

                eta = st.text_input(
                    "ETA — Data de chegada"
                )

                enviado = st.form_submit_button(
                    "Salvar cadastro",
                    use_container_width=True
                )

            if enviado:
                if not dc.strip():
                    st.error("A Referência DC é obrigatória.")
                else:
                    try:
                        salvar_carga(
                            dc,
                            booking,
                            transbordo,
                            destino,
                            etd,
                            eta
                        )

                        st.success("Cadastro salvo com sucesso!")

                    except Exception as erro:
                        st.error(f"Erro ao salvar: {erro}")

        # -------------------------
        # HISTÓRICO DA CARGA
        # -------------------------

        with aba_eventos:

            st.markdown("### Registrar atualização")

            conn = conectar_banco()
            cargas = conn.execute("""
                SELECT dc, booking
                FROM cargas
                ORDER BY dc
            """).fetchall()
            conn.close()

            if not cargas:
                st.info("Cadastre uma carga primeiro.")
            else:
                opcoes = [
                    f"{c['dc']} — {c['booking'] or 'Sem booking'}"
                    for c in cargas
                ]

                escolha = st.selectbox(
                    "Selecione a carga",
                    opcoes
                )

                indice = opcoes.index(escolha)
                dc_evento = cargas[indice]["dc"]

                with st.form("form_evento"):

                    data_evento = st.text_input(
                        "Data da atualização",
                        value=datetime.now().strftime("%d/%m/%Y")
                    )

                    descricao_evento = st.text_input(
                        "Descrição",
                        placeholder="Ex.: Carga embarcada"
                    )

                    local_evento = st.text_input(
                        "Local",
                        placeholder="Ex.: Porto de origem"
                    )

                    salvar_evento = st.form_submit_button(
                        "Registrar atualização",
                        use_container_width=True
                    )

                if salvar_evento:
                    if not descricao_evento.strip():
                        st.error("Preencha a descrição.")
                    else:
                        registrar_evento(
                            dc_evento,
                            data_evento,
                            descricao_evento,
                            local_evento
                        )

                        st.success("Atualização registrada!")

        # -------------------------
        # LISTA DE CARGAS
        # -------------------------

        with aba_lista:

            st.markdown("### Cargas cadastradas")

            conn = conectar_banco()
            registros = conn.execute("""
                SELECT
                    dc,
                    booking,
                    transbordo,
                    destino,
                    etd,
                    eta,
                    status
                FROM cargas
                ORDER BY dc
            """).fetchall()
            conn.close()

            if registros:
                st.dataframe(
                    [dict(registro) for registro in registros],
                    use_container_width=True,
                    hide_index=True
                )

                st.caption(
                    f"Total de cargas cadastradas: {len(registros)}"
                )
            else:
                st.info("Nenhuma carga cadastrada ainda.")
