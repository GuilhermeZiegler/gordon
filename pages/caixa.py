import streamlit as st
import pandas as pd
from datetime import datetime
import time

from components.auth import exigir_permissao
exigir_permissao("caixa")

from components.card_caixa_resumo import card_caixa_resumo
from utils.caixa_utils import (
    carregar_caixa,
    salvar_caixa,
    carregar_produtos,
    garantir_estrutura_caixa,
    obter_caixa_aberto,
    atualizar_historico_caixa,
    registrar_venda_no_caixa,
    listar_vendas_estornaveis,
    calcular_estornado_venda,
    registrar_estorno,
)

from utils.agendamentos_utils import (
    CATEGORIAS_AGENDAMENTO,
    PERIODICIDADES,
    criar_agendamento,
    pagar_agendamento,
    cancelar_agendamento,
    importar_agendamentos_excel,
    listar_pendentes,
)


caixa_atual = obter_caixa_aberto()

caixa_aberto = caixa_atual is not None
if caixa_aberto:
    caixa_atual = garantir_estrutura_caixa(caixa_atual)

    st.session_state.caixa_atual = caixa_atual
    st.session_state.caixa_aberto = True
else:
    st.session_state.caixa_aberto = False
    st.session_state.caixa_atual = None

st.header("Caixa")
if not caixa_aberto:

    st.subheader("🔓 Abrir Caixa do Dia")
    caixa_existente = carregar_caixa()

    with st.form("form_abrir_caixa"):

        saldo_inicial = st.number_input(
            "Saldo Inicial (R$):",
            min_value=0.0,
            step=0.01,
            value=0.0
        )

        if st.form_submit_button(
            "✅ Abrir Caixa",
            use_container_width=True,
            type="primary"
        ):

            novo_caixa = {
                "saldo_inicial": saldo_inicial,
                "data_abertura": datetime.now().strftime(
                    "%d/%m/%Y %H:%M:%S"
                ),
                "data_fechamento": "",
                "status": "aberto",
                "vendas_mesa": 0.0,
                "vendas_balcao": 0.0,
                "vendas_delivery": 0.0,
                "vendas_takeaway": 0.0,
                "reembolso": 0.0,
                "pagamentos": [],
                "entradas": [],
                "saidas": [],
                "vendas_metodo": {},
                "fiados": (
                    caixa_existente.get("fiados", [])
                    if caixa_existente
                    else []
                ),
                "estornos": []
            }

            salvar_caixa(novo_caixa)
            atualizar_historico_caixa(novo_caixa)

            st.session_state.caixa_atual = novo_caixa
            st.session_state.caixa_aberto = True

            st.success("✅ Caixa aberto com sucesso!")

            time.sleep(0.5)
            st.rerun()


else:

    caixa = st.session_state.get("caixa_atual")

    if not caixa:
        caixa = caixa_atual.copy()
        st.session_state.caixa_atual = caixa

    caixa = garantir_estrutura_caixa(caixa)

    aba_resumo, aba_vendas, aba_movimentacoes, aba_fiados = st.tabs(
        [
            "Dia",
            "Vendas",
            "Movimentações",
            "Fiados"
        ]
    )

    with aba_resumo:

        card_caixa_resumo(caixa)

        st.divider()

        if "confirmar_fechamento_caixa" not in st.session_state:
            st.session_state.confirmar_fechamento_caixa = False

        if not st.session_state.confirmar_fechamento_caixa:
            if st.button(
                "🔒 Fechar Caixa",
                use_container_width=True,
                type="primary"
            ):
                st.session_state.confirmar_fechamento_caixa = True
                st.rerun()

        else:
            total_entradas_especie = sum(
                e.get("valor", 0)
                for e in caixa["entradas"]
                if e.get("metodo") in ["Dinheiro", "Voucher"]
            )

            total_saidas_especie = (
                sum(
                    e.get("valor_estornado", 0)
                    for e in caixa.get("estornos", [])
                    if e.get("metodo") in ["Dinheiro", "Voucher"]
                )
                + sum(
                    p.get("valor", 0)
                    for p in caixa["pagamentos"]
                    if p.get("metodo") in ["Dinheiro", "Voucher"]
                )
                + sum(
                    s.get("valor", 0)
                    for s in caixa["saidas"]
                    if s.get("metodo") in ["Dinheiro", "Voucher"]
                )
            )

            saldo_esperado_especie = (
                caixa["saldo_inicial"]
                + total_entradas_especie
                - total_saidas_especie
            )

            st.warning(
                "⚠️ Confirme o fechamento do caixa."
            )

            st.info(
                f"💰 Saldo esperado em espécie: "
                f"R$ {saldo_esperado_especie:.2f}"
            )

            col_confirmar, col_cancelar = st.columns(2)

            with col_confirmar:
                if st.button(
                    "✅ Confirmar e Fechar",
                    use_container_width=True
                ):
                    fiados_ativos = [
                        f
                        for f in caixa.get("fiados", [])
                        if f.get("status") == "pendente"
                    ]

                    caixa["data_fechamento"] = datetime.now().strftime(
                        "%d/%m/%Y %H:%M:%S"
                    )

                    caixa["status"] = "fechado"

                    atualizar_historico_caixa(caixa)
                    salvar_caixa(caixa)

                    novo_caixa = {
                        "saldo_inicial": 0.0,
                        "data_abertura": "",
                        "data_fechamento": "",
                        "status": "fechado",
                        "vendas_mesa": 0.0,
                        "vendas_balcao": 0.0,
                        "vendas_delivery": 0.0,
                        "vendas_takeaway": 0.0,
                        "reembolso": 0.0,
                        "pagamentos": [],
                        "entradas": [],
                        "saidas": [],
                        "vendas_metodo": {},
                        "fiados": fiados_ativos,
                        "estornos": []
                    }

                    salvar_caixa(novo_caixa)

                    st.session_state.caixa_aberto = False
                    st.session_state.caixa_atual = None
                    st.session_state.confirmar_fechamento_caixa = False

                    st.success(
                        f"✅ Caixa fechado! "
                        f"{len(fiados_ativos)} fiados pendentes mantidos."
                    )

                    time.sleep(0.5)
                    st.rerun()

            with col_cancelar:
                if st.button(
                    "↩️ Cancelar",
                    use_container_width=True
                ):
                    st.session_state.confirmar_fechamento_caixa = False
                    st.rerun()

    with aba_vendas:

        metodo_pagamento = st.selectbox(
            "Pagamento:",
            [
                "Pix",
                "Débito",
                "Crédito",
                "Dinheiro",
                "Voucher",
                "Fiado"
            ],
            key="metodo_pagamento_caixa"
        )

        cliente = ""

        if metodo_pagamento == "Fiado":

            cliente = st.text_input(
                "👤 Nome do Cliente (identificação):",
                placeholder="Ex: João Silva",
                key="cliente_fiado"
            )

        df_produtos = carregar_produtos()

        if not df_produtos.empty:

            df_avulso = df_produtos[
                df_produtos["tipo_venda"] == "caixa"
            ]

            if not df_avulso.empty:

                st.markdown("### Itens")

                opcoes_produtos = (
                    df_avulso["cod_prod"].astype(str)
                    + " - "
                    + df_avulso["nome"]
                )

                col_item, col_qtd, col_btn = st.columns(
                    [2, 1, 1]
                )

                with col_item:

                    produto_selecionado = st.selectbox(
                        "Produto:",
                        opcoes_produtos.tolist(),
                        key="produto_avulso"
                    )

                    cod_prod_selecionado = int(
                        produto_selecionado.split(" - ")[0]
                    )

                    produto_info = df_avulso[
                        df_avulso["cod_prod"].astype(int)
                        == cod_prod_selecionado
                    ].iloc[0]

                    preco_produto = float(
                        produto_info["p_venda"]
                    )

                with col_qtd:

                    quantidade = st.number_input(
                        "Qtd:",
                        min_value=1,
                        step=1,
                        value=1,
                        key="qtd_avulso"
                    )

                with col_btn:

                    st.write("")
                    st.write("")

                    if st.button(
                        "➕ Adicionar",
                        key="add_avulso"
                    ):

                        nome_produto = (
                            produto_selecionado.split(" - ")[1]
                        )

                        if "itens_venda" not in st.session_state:
                            st.session_state.itens_venda = []

                        cod_item = (
                            f"ITEM-"
                            f"{len(st.session_state.itens_venda) + 1:03d}"
                        )

                        st.session_state.itens_venda.append({
                            "cod_item": cod_item,
                            "cod_prod": cod_prod_selecionado,
                            "nome": nome_produto,
                            "quantidade": quantidade,
                            "preco_unitario": preco_produto,
                            "subtotal": (
                                preco_produto * quantidade
                            ),
                            "tipo": "Avulso"
                        })

                        st.rerun()

            else:

                st.warning(
                    "⚠️ Nenhum item avulso disponível. "
                    "Cadastre produtos com tipo_venda = 'caixa'."
                )

        else:

            st.warning("⚠️ Nenhum produto cadastrado.")

        if (
            "itens_venda" in st.session_state
            and st.session_state.itens_venda
        ):

            st.divider()
            st.markdown("### 📋 Itens Adicionados")

            df_itens = pd.DataFrame(
                st.session_state.itens_venda
            )

            st.dataframe(
                df_itens[
                    [
                        "cod_item",
                        "nome",
                        "quantidade",
                        "preco_unitario",
                        "subtotal"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

            valor_total = df_itens["subtotal"].sum()

            st.metric(
                "💰 Total da Venda",
                f"R$ {valor_total:.2f}"
            )

            col_remover, col_limpar = st.columns(2)

            with col_remover:

                opcoes_itens = [
                    f"{item['cod_item']} - {item['nome']}"
                    for item in st.session_state.itens_venda
                ]

                if opcoes_itens:

                    item_remover = st.selectbox(
                        "Remover item:",
                        opcoes_itens,
                        key="remover_item_venda"
                    )

                    if st.button(
                        "🗑️ Remover Item",
                        key="remover_item_btn"
                    ):

                        cod_item_remover = (
                            item_remover.split(" - ")[0]
                        )

                        st.session_state.itens_venda = [
                            item
                            for item in st.session_state.itens_venda
                            if item["cod_item"] != cod_item_remover
                        ]

                        st.rerun()

            with col_limpar:

                if st.button(
                    "🧹 Limpar Todos",
                    key="limpar_itens_venda"
                ):

                    st.session_state.itens_venda = []

                    st.rerun()

        if st.button(
            "✅ Registrar Venda",
            use_container_width=True,
            type="primary"
        ):

            if metodo_pagamento == "Fiado":

                if not cliente.strip():

                    st.error(
                        "⚠️ Informe o nome do cliente para registro de fiado."
                    )

                elif not st.session_state.get("itens_venda"):

                    st.error(
                        "⚠️ Adicione pelo menos um item."
                    )

                else:

                    valor_total = sum(
                        item["subtotal"]
                        for item in st.session_state.itens_venda
                    )

                    descricao = ", ".join(
                        [
                            f"{item['nome']} x{item['quantidade']}"
                            for item in st.session_state.itens_venda
                        ]
                    )

                    registrar_venda_no_caixa(
                        "Avulso",
                        valor_total,
                        "Fiado",
                        f"{cliente.strip()} - {descricao}",
                        itens=st.session_state.itens_venda
                    )

                    st.session_state.itens_venda = []

                    st.success(
                        f"✅ Venda registrada como FIADO para "
                        f"{cliente}! Total: R$ {valor_total:.2f}"
                    )

                    time.sleep(0.5)
                    st.rerun()

            else:

                if not st.session_state.get("itens_venda"):

                    st.error(
                        "⚠️ Adicione pelo menos um item."
                    )

                else:

                    valor_total = sum(
                        item["subtotal"]
                        for item in st.session_state.itens_venda
                    )

                    descricao = ", ".join(
                        [
                            f"{item['nome']} x{item['quantidade']}"
                            for item in st.session_state.itens_venda
                        ]
                    )

                    registrar_venda_no_caixa(
                        "Avulso",
                        valor_total,
                        metodo_pagamento,
                        descricao,
                        itens=st.session_state.itens_venda
                    )

                    st.session_state.itens_venda = []

                    st.success(
                        f"✅ Venda Avulsa registrada! "
                        f"Total: R$ {valor_total:.2f}"
                    )

                    time.sleep(0.5)
                    st.rerun()

        st.divider()
        st.subheader("Vendas do Dia")

        vendas = [
            e for e in caixa["entradas"]
        ]

        if vendas:

            df_vendas = pd.DataFrame(vendas)

            colunas_vendas = [
                c for c in [
                    "id_venda",
                    "categoria",
                    "valor",
                    "metodo",
                    "descricao",
                    "data"
                ] if c in df_vendas.columns
            ]

            df_vendas = df_vendas[colunas_vendas].copy()

            if "id_venda" in df_vendas.columns:
                df_vendas["estornado"] = df_vendas["id_venda"].apply(
                    calcular_estornado_venda
                )
                df_vendas["disponivel"] = (
                    pd.to_numeric(df_vendas["valor"], errors="coerce").fillna(0)
                    - df_vendas["estornado"]
                )
            else:
                df_vendas["estornado"] = 0.0
                df_vendas["disponivel"] = df_vendas["valor"]

            st.dataframe(
                df_vendas,
                column_config={
                    "id_venda": "ID",
                    "categoria": "Categoria",
                    "valor": st.column_config.NumberColumn(
                        "Valor",
                        format="R$ %.2f"
                    ),
                    "metodo": "Método",
                    "descricao": "Descrição",
                    "data": "Data",
                    "estornado": st.column_config.NumberColumn(
                        "Estornado",
                        format="R$ %.2f"
                    ),
                    "disponivel": st.column_config.NumberColumn(
                        "Disponível",
                        format="R$ %.2f"
                    ),
                },
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info("Nenhuma venda registrada hoje.")

    with aba_movimentacoes:

        tipo_movimentacao = st.selectbox(
            "Tipo de Movimentação:",
            ["Entrada", "Saída", "Reembolso", "Pagamento", "Estorno"],
            key="tipo_movimentacao_select"
        )

        if tipo_movimentacao == "Estorno":

            st.subheader("↩️ Estornar Venda")

            periodo_estorno = st.selectbox(
                "Período:",
                [
                    "Hoje",
                    "Últimos 7 dias",
                    "Últimos 30 dias",
                    "Últimos 90 dias",
                    "Tudo"
                ],
                index=1,
                key="periodo_estorno_select"
            )

            vendas_estornaveis = listar_vendas_estornaveis(periodo_estorno)

            vendas_com_disponivel = []
            for v in vendas_estornaveis:
                ja_estornado = calcular_estornado_venda(v["id_venda"])
                disponivel = round(v["valor"] - ja_estornado, 2)
                if disponivel > 0:
                    vendas_com_disponivel.append({
                        **v,
                        "ja_estornado": ja_estornado,
                        "disponivel": disponivel,
                    })

            if not vendas_com_disponivel:

                st.info("Nenhuma venda disponível para estorno.")

            else:

                opcoes = {
                    f"{v['id_venda']} — {v['categoria']} — "
                    f"R$ {v['valor']:.2f} — {v['metodo']} — "
                    f"{v['data']} — Disp: R$ {v['disponivel']:.2f}": v
                    for v in vendas_com_disponivel
                }

                selecionada_label = st.selectbox(
                    "Selecione a venda:",
                    list(opcoes.keys()),
                    key="estorno_venda_select"
                )

                venda = opcoes[selecionada_label]

                col_info1, col_info2, col_info3 = st.columns(3)

                with col_info1:
                    st.metric(
                        "Valor Original",
                        f"R$ {venda['valor']:.2f}"
                    )

                with col_info2:
                    st.metric(
                        "Já Estornado",
                        f"R$ {venda['ja_estornado']:.2f}"
                    )

                with col_info3:
                    st.metric(
                        "Disponível",
                        f"R$ {venda['disponivel']:.2f}"
                    )

                st.divider()

                col_tipo, col_valor = st.columns(2)

                with col_tipo:
                    tipo_estorno = st.radio(
                        "Tipo de Estorno:",
                        ["Total", "Parcial"],
                        horizontal=True,
                        key="tipo_estorno_radio"
                    )

                with col_valor:
                    if tipo_estorno == "Parcial":
                        valor_estornar = st.number_input(
                            "Valor a estornar (R$):",
                            min_value=0.01,
                            max_value=float(venda["disponivel"]),
                            step=0.01,
                            value=float(venda["disponivel"]),
                            key="valor_estorno_input"
                        )
                    else:
                        valor_estornar = float(venda["disponivel"])
                        st.metric(
                            "Valor a estornar",
                            f"R$ {valor_estornar:.2f}"
                        )

                col_metodo, col_class = st.columns(2)

                with col_metodo:
                    metodos = [
                        "Pix", "Débito", "Crédito",
                        "Dinheiro", "Voucher"
                    ]
                    metodo_estorno = st.selectbox(
                        "Método do Estorno:",
                        metodos,
                        index=(
                            metodos.index(venda["metodo"])
                            if venda["metodo"] in metodos
                            else 0
                        ),
                        key="metodo_estorno_select"
                    )

                with col_class:
                    classificacoes = [
                        "cliente_desistiu",
                        "erro_pedido",
                        "cobranca_duplicada",
                        "produto_indisponivel",
                        "outros"
                    ]
                    classificacao = st.selectbox(
                        "Classificação:",
                        classificacoes,
                        key="classificacao_estorno_select"
                    )

                if classificacao == "outros":
                    motivo = st.text_input(
                        "Motivo (livre):",
                        placeholder="Descreva o motivo...",
                        key="motivo_estorno_input"
                    )
                else:
                    motivo = classificacao

                if st.button(
                    "↩️ Confirmar Estorno",
                    use_container_width=True,
                    type="primary"
                ):
                    if not motivo.strip():
                        st.error("⚠️ Informe o motivo do estorno.")
                    else:
                        sucesso, msg = registrar_estorno(
                            venda["id_venda"],
                            valor_estornar,
                            metodo_estorno,
                            motivo.strip(),
                            classificacao
                        )

                        if sucesso:
                            st.success(
                                f"✅ Estorno registrado! ID: {msg}"
                            )
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                st.divider()
            st.subheader("↩️ Estornos do Dia")

            estornos_dia = caixa.get("estornos", [])

            if estornos_dia:
                df_estornos = pd.DataFrame(estornos_dia)
                colunas_est = [
                    c for c in [
                        "id_estorno",
                        "id_venda_original",
                        "valor_estornado",
                        "tipo",
                        "metodo",
                        "classificacao",
                        "motivo",
                        "data"
                    ] if c in df_estornos.columns
                ]
                st.dataframe(
                    df_estornos[colunas_est],
                    column_config={
                        "id_estorno": "ID",
                        "id_venda_original": "Venda",
                        "valor_estornado": st.column_config.NumberColumn(
                            "Valor",
                            format="R$ %.2f"
                        ),
                        "tipo": "Tipo",
                        "metodo": "Método",
                        "classificacao": "Classificação",
                        "motivo": "Motivo",
                        "data": "Data",
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Nenhum estorno registrado hoje.")

        else:

            sub_mov, sub_agd = st.tabs(["📝 Movimentações", "📅 Agendamentos"])

            with sub_mov:
                with st.form("form_movimentacao"):

                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                    with col1:
                        descricao = st.text_input(
                            "Descrição:",
                            placeholder="Ex: Pagamento fornecedor, Troco..."
                        )

                    with col2:
                        st.write("")
                        st.write("")
                        st.caption(f"**{tipo_movimentacao}**")

                    with col3:
                        valor = st.number_input(
                            "Valor (R$):",
                            min_value=0.01,
                            step=0.01
                        )

                    with col4:
                        metodo_mov = st.selectbox(
                            "Pagamento:",
                            ["Pix", "Débito", "Crédito", "Dinheiro", "Voucher"],
                            key="metodo_movimentacao"
                        )

                    funcionario_pagamento = None

                    if tipo_movimentacao == "Pagamento":
                        if 'funcionarios' not in st.session_state:
                            from utils.staff_utils import carregar_funcionarios
                            st.session_state.funcionarios = carregar_funcionarios()
                        funcionarios = st.session_state.funcionarios
                        nomes_funcionarios = [f.get("nome", "") for f in funcionarios]
                        funcionario_pagamento = st.selectbox("Funcionário:", nomes_funcionarios)

                    if st.form_submit_button("➕ Registrar", use_container_width=True):
                        if tipo_movimentacao == "Entrada":
                            caixa["entradas"].append({
                                "categoria": "Manual",
                                "descricao": descricao,
                                "valor": valor,
                                "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                "metodo": metodo_mov
                            })
                        elif tipo_movimentacao == "Saída":
                            caixa["saidas"].append({
                                "descricao": descricao,
                                "valor": valor,
                                "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                "metodo": metodo_mov
                            })
                        elif tipo_movimentacao == "Reembolso":
                            caixa["reembolso"] += valor
                        elif tipo_movimentacao == "Pagamento":
                            caixa["pagamentos"].append({
                                "funcionario": funcionario_pagamento,
                                "valor": valor,
                                "descricao": descricao,
                                "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                "metodo": metodo_mov
                            })

                        atualizar_historico_caixa(caixa)
                        salvar_caixa(caixa)
                        st.session_state.caixa_atual = caixa

                        st.success(f"✅ {tipo_movimentacao} registrada!")
                        time.sleep(0.5)
                        st.rerun()

                st.divider()

                col_entradas, col_saidas = st.columns(2)

                with col_entradas:
                    st.subheader("📥 Entradas")
                    entradas_manuais = [e for e in caixa["entradas"] if e.get("categoria") == "Manual"]
                    if entradas_manuais:
                        st.dataframe(pd.DataFrame(entradas_manuais), use_container_width=True, hide_index=True)
                    else:
                        st.info("Nenhuma entrada manual registrada.")

                with col_saidas:
                    st.subheader("📤 Saídas")
                    if caixa["saidas"]:
                        st.dataframe(pd.DataFrame(caixa["saidas"]), use_container_width=True, hide_index=True)
                    else:
                        st.info("Nenhuma saída registrada.")

            with sub_agd:
                with st.expander("📤 Importar Agendamentos via Excel"):
                    st.markdown("**Formato esperado:**")
                    st.code("descricao | valor | data_vencimento | categoria | fornecedor (opc) | metodo_pagamento (opc) | recorrente (opc: sim/nao) | periodicidade (opc) | observacao (opc)")

                    arquivo_excel = st.file_uploader(
                        "Envie o arquivo Excel (.xlsx)",
                        type=['xlsx'],
                        key="upload_agendamentos_excel"
                    )

                    if arquivo_excel:
                        try:
                            df_upload = pd.read_excel(arquivo_excel)
                            st.write(f"📄 {len(df_upload)} registros encontrados")

                            obrigatorias = ['descricao', 'valor', 'data_vencimento', 'categoria']
                            ausentes = [c for c in obrigatorias if c not in df_upload.columns]

                            if ausentes:
                                st.error(f"❌ Colunas obrigatórias faltando: {', '.join(ausentes)}")
                            else:
                                st.success("✅ Arquivo válido!")
                                st.dataframe(df_upload.head(), use_container_width=True, hide_index=True)

                                if st.button("📥 Importar", use_container_width=True, type="primary", key="btn_importar_agendamentos"):
                                    importados, erros = importar_agendamentos_excel(df_upload)
                                    if importados > 0:
                                        st.success(f"✅ {importados} agendamentos importados!")
                                        time.sleep(0.5)
                                        st.rerun()
                                    if erros:
                                        st.warning(f"⚠️ {len(erros)} erros:")
                                        for erro in erros[:10]:
                                            st.write(f"- {erro}")
                        except Exception as e:
                            st.error(f"❌ Erro ao ler arquivo: {str(e)}")

                with st.expander("➕ Novo Agendamento"):
                    with st.form("form_novo_agendamento"):
                        col1, col2 = st.columns(2)

                        with col1:
                            descricao_novo = st.text_input("Descrição:")
                            valor_novo = st.number_input("Valor (R$):", min_value=0.01, step=0.01, value=1.0)
                            data_venc_novo = st.date_input("Data de Vencimento:", datetime.now())

                        with col2:
                            categoria_novo = st.selectbox("Categoria:", CATEGORIAS_AGENDAMENTO)
                            fornecedor_novo = st.text_input("Fornecedor:")
                            metodo_novo = st.selectbox("Método:", ["Pix", "Débito", "Crédito", "Dinheiro", "Boleto"])

                        col3, col4, col5 = st.columns(3)

                        with col3:
                            recorrente_novo = st.checkbox("Recorrente")

                        with col4:
                            periodicidade_novo = st.selectbox("Periodicidade:", PERIODICIDADES)

                        with col5:
                            st.write("")
                            st.write("")

                        observacao_novo = st.text_input("Observação:")

                        if st.form_submit_button("➕ Criar Agendamento", use_container_width=True, type="primary"):
                            if not descricao_novo.strip():
                                st.error("⚠️ Informe a descrição")
                            else:
                                criar_agendamento(
                                    descricao=descricao_novo.strip(),
                                    valor=valor_novo,
                                    data_vencimento=data_venc_novo.strftime("%d/%m/%Y"),
                                    categoria=categoria_novo,
                                    fornecedor=fornecedor_novo.strip(),
                                    metodo_pagamento=metodo_novo,
                                    recorrente=recorrente_novo,
                                    periodicidade=periodicidade_novo if recorrente_novo else '',
                                    observacao=observacao_novo.strip()
                                )
                                st.success("✅ Agendamento criado!")
                                time.sleep(0.5)
                                st.rerun()

                st.divider()

                pendentes = listar_pendentes()

                if pendentes.empty:
                    st.info("📭 Nenhum agendamento pendente.")
                else:
                    pendentes_display = pendentes.copy()
                    pendentes_display['data_venc_dt'] = pd.to_datetime(
                        pendentes_display['data_vencimento'], format="%d/%m/%Y", errors='coerce'
                    )

                    hoje = pd.Timestamp(datetime.now().date())

                    pendentes_display['situacao'] = pendentes_display['data_venc_dt'].apply(
                        lambda d: '🔴 Vencido' if pd.notna(d) and d.date() <= hoje.date()
                        else '🟡 Vencendo' if pd.notna(d) and (d.date() - hoje.date()).days <= 7
                        else '🟢 Futuro'
                    )

                    pendentes_display = pendentes_display.sort_values('data_venc_dt')

                    st.markdown("**Pendentes**")

                    selecionados = []

                    for _, row in pendentes_display.iterrows():
                        with st.container(border=True):
                            col_chk, col_info, col_btn_pagar, col_btn_cancel = st.columns([0.5, 4, 1, 1])

                            with col_chk:
                                if st.checkbox("", key=f"agd_chk_{row['id_agendamento']}"):
                                    selecionados.append(row['id_agendamento'])

                            with col_info:
                                recorrente_tag = f" 🔁 {row.get('periodicidade', '')}" if row.get('recorrente') else ""
                                st.markdown(f"{row['situacao']} **{row['descricao']}** — R$ {row['valor']:.2f}{recorrente_tag}")
                                st.caption(f"Venc: {row['data_vencimento']} | {row['categoria']} | {row.get('fornecedor', '') or '—'} | {row['metodo_pagamento']}")

                            with col_btn_pagar:
                                if st.button("💰 Pagar", key=f"agd_pagar_{row['id_agendamento']}", use_container_width=True):
                                    st.session_state.pagar_id = row['id_agendamento']
                                    st.rerun()

                            with col_btn_cancel:
                                if st.button("❌", key=f"agd_cancelar_{row['id_agendamento']}", use_container_width=True):
                                    st.session_state.cancelar_id = row['id_agendamento']
                                    st.rerun()

                    if selecionados:
                        if st.button(f"💰 Pagar {len(selecionados)} selecionado(s)", use_container_width=True, type="primary"):
                            total_pago = 0
                            for id_agd in selecionados:
                                sucesso, msg = pagar_agendamento(id_agd)
                                if sucesso:
                                    total_pago += 1

                            if total_pago > 0:
                                st.success(f"✅ {total_pago} agendamento(s) pago(s)!")
                                time.sleep(0.5)
                                st.rerun()

                    if st.session_state.get('pagar_id'):
                        id_pagar = st.session_state.pagar_id
                        registro = pendentes_display[pendentes_display['id_agendamento'] == id_pagar]

                        if not registro.empty:
                            reg = registro.iloc[0]
                            st.warning(f"⚠️ Confirmar pagamento de **{reg['descricao']}** — R$ {reg['valor']:.2f}?")

                            col_conf1, col_conf2 = st.columns(2)

                            with col_conf1:
                                if st.button("✅ Confirmar", use_container_width=True, type="primary", key="conf_pagar"):
                                    sucesso, msg = pagar_agendamento(id_pagar)
                                    if sucesso:
                                        st.session_state.pagar_id = None
                                        st.success(f"✅ {msg}")
                                        time.sleep(0.5)
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {msg}")

                            with col_conf2:
                                if st.button("❌ Cancelar", use_container_width=True, key="canc_pagar"):
                                    st.session_state.pagar_id = None
                                    st.rerun()

                    if st.session_state.get('cancelar_id'):
                        id_cancelar = st.session_state.cancelar_id
                        registro = pendentes_display[pendentes_display['id_agendamento'] == id_cancelar]

                        if not registro.empty:
                            reg = registro.iloc[0]
                            st.warning(f"⚠️ Confirmar cancelamento de **{reg['descricao']}**?")

                            col_conf1, col_conf2 = st.columns(2)

                            with col_conf1:
                                if st.button("✅ Confirmar cancelamento", use_container_width=True, key="conf_cancelar"):
                                    sucesso, msg = cancelar_agendamento(id_cancelar)
                                    if sucesso:
                                        st.session_state.cancelar_id = None
                                        st.success(f"✅ {msg}")
                                        time.sleep(0.5)
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {msg}")

                            with col_conf2:
                                if st.button("❌ Voltar", use_container_width=True, key="canc_cancelar"):
                                    st.session_state.cancelar_id = None
                                    st.rerun()

    with aba_fiados:

        st.subheader("Fiados Pendentes")

        fiados_pendentes = [
            f
            for f in caixa.get("fiados", [])
            if f.get("status") == "pendente"
        ]

        if not fiados_pendentes:

            st.info("✅ Nenhum fiado pendente.")

        else:

            df_fiados = pd.DataFrame(
                fiados_pendentes
            )

            colunas_fiados = [
                c for c in [
                    "id",
                    "cliente",
                    "valor",
                    "data",
                    "itens",
                    "tipo"
                ] if c in df_fiados.columns
            ]

            st.dataframe(
                df_fiados[colunas_fiados],
                column_config={
                    "id": "ID",
                    "cliente": "Cliente",
                    "valor": st.column_config.NumberColumn(
                        "Valor",
                        format="R$ %.2f"
                    ),
                    "data": "Data",
                    "itens": "Itens",
                    "tipo": "Tipo"
                },
                use_container_width=True,
                hide_index=True
            )

            total_fiados = sum(
                f["valor"]
                for f in fiados_pendentes
            )

            st.metric(
                "💳 Total em Fiados",
                f"R$ {total_fiados:.2f}"
            )

            st.divider()

            opcoes_fiados = [
                f"{f['id']} - {f['cliente']} - R$ {f['valor']:.2f}"
                for f in fiados_pendentes
            ]

            fiado_selecionado = st.selectbox(
                "Selecione o fiado para quitar:",
                opcoes_fiados
            )

            if st.button(
                "✅ Quitar Fiado",
                use_container_width=True,
                type="primary"
            ):

                id_fiado = int(
                    fiado_selecionado.split(" - ")[0]
                )

                cliente_nome = ""

                for f in caixa["fiados"]:

                    if f["id"] == id_fiado:

                        cliente_nome = f["cliente"]

                        f["status"] = "pago"

                        f["data_pagamento"] = (
                            datetime.now().strftime(
                                "%d/%m/%Y %H:%M:%S"
                            )
                        )

                        caixa["entradas"].append({
                            "categoria": "Quitação Fiado",
                            "valor": f["valor"],
                            "metodo": "Fiado",
                            "descricao": (
                                f"Quitação - {f['cliente']}"
                            ),
                            "data": datetime.now().strftime(
                                "%d/%m/%Y %H:%M:%S"
                            )
                        })

                        caixa["vendas_balcao"] += f["valor"]

                        caixa["vendas_metodo"] = (
                            caixa.get("vendas_metodo", {})
                        )

                        caixa["vendas_metodo"]["Fiado"] = (
                            caixa["vendas_metodo"].get(
                                "Fiado",
                                0.0
                            )
                            + f["valor"]
                        )

                        break

                atualizar_historico_caixa(caixa)
                salvar_caixa(caixa)

                st.session_state.caixa_atual = caixa

                st.success(
                    f"✅ Fiado de {cliente_nome} "
                    "quitado com sucesso!"
                )

                time.sleep(0.5)
                st.rerun()

        st.divider()

        st.subheader("Fiados Pagos")

        fiados_pagos = [
            f
            for f in caixa.get("fiados", [])
            if f.get("status") == "pago"
        ]

        if fiados_pagos:

            df_pagos = pd.DataFrame(
                fiados_pagos
            )

            colunas_pagos = [
                c for c in [
                    "id",
                    "cliente",
                    "valor",
                    "data",
                    "data_pagamento"
                ] if c in df_pagos.columns
            ]

            st.dataframe(
                df_pagos[colunas_pagos],
                column_config={
                    "id": "ID",
                    "cliente": "Cliente",
                    "valor": st.column_config.NumberColumn(
                        "Valor",
                        format="R$ %.2f"
                    ),
                    "data": "Data Venda",
                    "data_pagamento": "Data Pagamento"
                },
                use_container_width=True,
                hide_index=True
            )

            total_pagos = sum(
                f["valor"]
                for f in fiados_pagos
            )

            st.metric(
                "✅ Total Fiados Pagos",
                f"R$ {total_pagos:.2f}"
            )

        else:

            st.caption(
                "Nenhum fiado pago ainda."
            )