import streamlit as st
import sqlite3
from datetime import datetime

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


def conectar():
    return sqlite3.connect(DB)


def iniciar_banco():
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cargas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dc TEXT UNIQUE NOT NULL,
                container TEXT,
                booking TEXT,
                origem TEXT NOT NULL,
                destino TEXT NOT NULL,
                armador TEXT,
                status TEXT NOT NULL,
                eta TEXT
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


def buscar(referencia):
    referencia = referencia.strip().upper()

    with conectar() as conn:
        return conn.execute("""
            SELECT * FROM cargas
            WHERE UPPER(dc) = ?
               OR UPPER(container) = ?
               OR UPPER(booking) = ?
        """, (referencia, referencia, referencia)).fetchall()


def historico(dc):
    with conectar() as conn:
        return conn.execute("""
            SELECT data, descricao, local
            FROM eventos
            WHERE dc = ?
            ORDER BY data DESC, id DESC
        """, (dc,)).fetchall()


iniciar_banco()

st.markdown("""
<style>
.stApp {
    background-color: #0b1220;
    color: #f1f5f9;
}
.block-container {
    max-width: 1100px;
    padding-top: 2rem;
}
div[data-testid="stMetric"] {
    background: #172338;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #263852;
}
</style>
""", unsafe_allow_html=True)

st.title("🚢 DC LCL TRACKING")
st.caption("International Freight • Shipment Visibility")

pagina = st.sidebar.radio(
    "MENU",
    ["Rastreamento", "Administração"]
)

if pagina == "Rastreamento":

    st.subheader("Rastreie sua carga")
    st.write(
        "Pesquise pelo código DC, contêiner ou booking."
    )

    with st.form("consulta"):
        referencia = st.text_input(
            "Referência",
            placeholder="Ex.: DC100001"
        )
        consultar = st.form_submit_button(
            "🔎 RASTREAR",
            use_container_width=True
        )

    if consultar:
        if not referencia.strip():
            st.warning("Digite uma referência.")
        else:
            resultados = buscar(referencia)

            if not resultados:
                st.error("Nenhuma carga encontrada.")
            else:
                if len(resultados) > 1:
                    st.info(
                        f"{len(resultados)} cargas encontradas. "
                        "O contêiner ou booking pode ser compartilhado."
                    )

                for carga in resultados:
                    (
                        id_carga, dc, container, booking,
                        origem, destino, armador, status, eta
                    ) = carga

                    st.divider()
                    st.header(f"📦 {dc}")

                    a, b, c = st.columns(3)
                    a.metric("STATUS", status)
                    b.metric("ORIGEM", origem)
                    c.metric("DESTINO", destino)

                    a, b, c = st.columns(3)
                    a.write("**Contêiner**")
                    a.write(container or "Não informado")
                    b.write("**Booking**")
                    b.write(booking or "Não informado")
                    c.write("**ETA**")
                    c.write(eta or "Não informado")

                    st.write(
                        f"**Armador / agente:** "
                        f"{armador or 'Não informado'}"
                    )

                    dados_armador = identificar_armador(container, armador)
                    st.write(f"**Empresa associada ao prefixo:** {dados_armador['nome']}")
                    st.link_button(
                        "🌐 Rastrear no site do armador / consultar prefixo",
                        dados_armador["url"],
                        use_container_width=True,
                    )

                    st.subheader("Histórico da carga")
                    eventos = historico(dc)

                    if not eventos:
                        st.info("Nenhum evento registrado.")
                    else:
                        for data, descricao, local in eventos:
                            st.markdown(
                                f"**● {descricao}**  \n"
                                f"📅 {data}  \n"
                                f"📍 {local or 'Local não informado'}"
                            )
                            st.divider()

    st.caption(
        "O sistema consulta os registros cadastrados. "
        "A integração com APIs de armadores será adicionada depois."
    )

elif pagina == "Administração":

    st.subheader("Painel administrativo")

    senha = st.text_input(
        "Senha administrativa",
        type="password"
    )

    senha_configurada = st.secrets.get(
        "ADMIN_PASSWORD", ""
    )

    if not senha_configurada:
        st.warning(
            "Configure ADMIN_PASSWORD nos Secrets "
            "do Streamlit antes de cadastrar cargas."
        )

    elif senha == senha_configurada:

        st.success("Acesso administrativo autorizado.")

        aba1, aba2 = st.tabs([
            "Cadastrar carga",
            "Registrar evento"
        ])

        with aba1:
            with st.form("cadastro"):
                dc = st.text_input(
                    "Código DC *"
                ).strip().upper()

                container = st.text_input(
                    "Número do contêiner"
                ).strip().upper()

                booking = st.text_input(
                    "Booking"
                ).strip().upper()

                origem = st.text_input("Origem")
                destino = st.text_input("Destino")
                armador = st.text_input("Armador ou agente")

                status = st.selectbox(
                    "Status",
                    [
                        "Booking confirmado",
                        "Carga recebida no armazém",
                        "Consolidação",
                        "Embarcado",
                        "Em trânsito",
                        "Chegada ao destino",
                        "Desconsolidação",
                        "Liberado",
                        "Entregue",
                        "Atrasado"
                    ]
                )

                eta = st.text_input(
                    "ETA",
                    placeholder="DD/MM/AAAA"
                )

                salvar = st.form_submit_button(
                    "Salvar carga"
                )

            if salvar:
                if not dc.startswith("DC") or len(dc) <= 2:
                    st.error("O código precisa começar com DC.")
                elif not origem.strip() or not destino.strip():
                    st.error("Preencha origem e destino.")
                else:
                    try:
                        with conectar() as conn:
                            conn.execute("""
                                INSERT INTO cargas (
                                    dc, container, booking,
                                    origem, destino, armador,
                                    status, eta
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                dc, container, booking,
                                origem.strip(), destino.strip(),
                                armador.strip(), status, eta.strip()
                            ))

                            conn.execute("""
                                INSERT INTO eventos (
                                    dc, data, descricao, local
                                ) VALUES (?, ?, ?, ?)
                            """, (
                                dc,
                                datetime.now().strftime("%Y-%m-%d"),
                                "Cadastro inicial: " + status,
                                origem.strip()
                            ))

                        st.success(f"Carga {dc} cadastrada!")
                        st.rerun()

                    except sqlite3.IntegrityError:
                        st.error("Esse código DC já está cadastrado.")

        with aba2:
            with conectar() as conn:
                cargas = conn.execute(
                    "SELECT dc FROM cargas ORDER BY dc"
                ).fetchall()

            if cargas:
                codigos = [c[0] for c in cargas]

                with st.form("evento"):
                    dc_evento = st.selectbox(
                        "Código DC",
                        codigos
                    )

                    descricao = st.text_input(
                        "Descrição da movimentação"
                    )

                    local = st.text_input("Local")

                    data = st.date_input(
                        "Data",
                        value=datetime.now().date()
                    )

                    atualizar_status = st.checkbox(
                        "Atualizar status da carga"
                    )

                    novo_status = st.selectbox(
                        "Novo status",
                        [
                            "Booking confirmado",
                            "Carga recebida no armazém",
                            "Consolidação",
                            "Embarcado",
                            "Em trânsito",
                            "Chegada ao destino",
                            "Desconsolidação",
                            "Liberado",
                            "Entregue",
                            "Atrasado"
                        ]
                    )

                    registrar = st.form_submit_button(
                        "Registrar movimentação"
                    )

                if registrar:
                    if not descricao.strip():
                        st.error("Informe a descrição.")
                    else:
                        with conectar() as conn:
                            conn.execute("""
                                INSERT INTO eventos (
                                    dc, data, descricao, local
                                ) VALUES (?, ?, ?, ?)
                            """, (
                                dc_evento,
                                data.isoformat(),
                                descricao.strip(),
                                local.strip()
                            ))

                            if atualizar_status:
                                conn.execute("""
                                    UPDATE cargas
                                    SET status = ?
                                    WHERE dc = ?
                                """, (novo_status, dc_evento))

                        st.success("Movimentação registrada!")
                        st.rerun()
            else:
                st.info("Cadastre uma carga primeiro.")

    elif senha:
        st.error("Senha incorreta.")
