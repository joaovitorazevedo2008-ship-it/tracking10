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
