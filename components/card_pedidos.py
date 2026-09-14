import streamlit as st
import pandas as pd


def renderizar_formulario_produto_pedido(
    df_produtos,
    versao_obs
):
    col_busca, col_produto = st.columns([1, 2])

    with col_busca:
        busca_produto = st.text_input(
            "🔍 Buscar produto",
            placeholder="Nome ou código..."
        )

    df_filtrado = df_produtos.copy()
    df_filtrado['cod_prod'] = (
        df_filtrado['cod_prod']
        .astype(str)
        .str.strip()
    )

    if 'tipo_venda' in df_filtrado.columns:
        df_filtrado = df_filtrado[
            df_filtrado['tipo_venda'].isin(
                ['menu', 'bar', 'ambos']
            )
        ]

    if busca_produto:
        df_filtrado = df_filtrado[
            df_filtrado['nome'].str.contains(
                busca_produto,
                case=False,
                na=False
            )
            |
            df_filtrado['cod_prod'].str.contains(
                busca_produto,
                case=False,
                na=False
            )
        ]

    if df_filtrado.empty:
        st.info("Nenhum produto encontrado.")
        return None

    df_filtrado['display'] = (
        df_filtrado['cod_prod']
        + " - "
        + df_filtrado['nome']
    )

    with col_produto:
        produto_selecionado_display = st.selectbox(
            "Produto",
            df_filtrado['display'].tolist()
        )

    cod_prod_selecionado = (
        produto_selecionado_display
        .split(" - ")[0]
    )

    produto_data = df_filtrado[
        df_filtrado['cod_prod'] == cod_prod_selecionado
    ].iloc[0]

    cod_prod = produto_data['cod_prod']
    nome_prod = produto_data['nome']
    preco_original = float(produto_data['p_venda'])
    categoria = produto_data.get('categoria', '')
    tipo_venda = produto_data.get('tipo_venda', 'menu')

    st.markdown(
        f"""
        <div class="produto-selecionado">
            <div>
                <div class="produto-selecionado-nome">
                    {nome_prod}
                </div>
                <div class="produto-selecionado-codigo">
                    #{cod_prod}
                </div>
            </div>
            <div class="produto-selecionado-preco">
                R$ {preco_original:.2f}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="produto-secao-titulo">✂️ Desconto</div>',
        unsafe_allow_html=True
    )

    col_desc1, col_desc2 = st.columns([2, 1])

    with col_desc1:
        tipo_desconto = st.radio(
            "Tipo",
            ["Nenhum", "Percentual (%)", "Preço Fixo (R$)"],
            key=f"tipo_desc_{cod_prod}",
            horizontal=True,
            label_visibility="collapsed"
        )

    preco_final = preco_original
    desconto_tipo = "Nenhum"
    desconto_valor = 0.0

    with col_desc2:
        if tipo_desconto == "Percentual (%)":
            pct_desconto = st.number_input(
                "Desconto",
                min_value=0.0,
                max_value=100.0,
                step=0.5,
                value=0.0,
                key=f"desc_pct_{cod_prod}"
            )

            preco_final = preco_original * (
                1 - pct_desconto / 100
            )

            if pct_desconto > 0:
                desconto_tipo = "promo"
                desconto_valor = pct_desconto

        elif tipo_desconto == "Preço Fixo (R$)":
            preco_final = st.number_input(
                "Preço",
                min_value=0.01,
                step=0.01,
                value=float(preco_original),
                key=f"desc_fixo_{cod_prod}"
            )

            desconto_valor = preco_original - preco_final

            if desconto_valor > 0:
                desconto_tipo = "promo"
            else:
                desconto_valor = 0.0

        else:
            st.markdown(
                f"""
                <div class="produto-final">
                    <span>Preço final</span>
                    <strong>R$ {preco_final:.2f}</strong>
                </div>
                """,
                unsafe_allow_html=True
            )

    if tipo_desconto != "Nenhum":
        st.markdown(
            f"""
            <div class="produto-final">
                <span>Preço final</span>
                <strong>R$ {preco_final:.2f}</strong>
            </div>
            """,
            unsafe_allow_html=True
        )

    col_qtd, col_sub = st.columns(2)

    with col_qtd:
        quantidade = st.number_input(
            "Quantidade",
            min_value=1,
            step=1,
            value=1
        )

    with col_sub:
        subtotal = quantidade * preco_final

        st.markdown(
            f"""
            <div class="produto-subtotal">
                <span>Subtotal</span>
                <strong>R$ {subtotal:.2f}</strong>
            </div>
            """,
            unsafe_allow_html=True
        )

    observacao_item = st.text_input(
        "Observação",
        placeholder="Ex: sem cebola, bem passado...",
        key=f"obs_item_{cod_prod}_{versao_obs}"
    )

    adicionar = st.button(
        "➕ Adicionar ao Pedido",
        use_container_width=True,
        type="primary"
    )

    if not adicionar:
        return None

    return {
        'cod_prod': cod_prod,
        'nome_prod': nome_prod,
        'preco_original': preco_original,
        'preco_final': preco_final,
        'categoria': categoria,
        'tipo_venda': tipo_venda,
        'desconto_tipo': desconto_tipo,
        'desconto_valor': desconto_valor,
        'quantidade': quantidade,
        'observacao': observacao_item
    }

def renderizar_card_pedido(
    pedido,
    itens,
    total
):
    linhas = ""

    for item in itens:
        preco_unitario = pd.to_numeric(
            item.get("preco_unitario", 0),
            errors="coerce"
        )

        valor_com_desconto = pd.to_numeric(
            item.get("valor_com_desconto", item.get("subtotal", 0)),
            errors="coerce"
        )

        preco_unitario = 0.0 if pd.isna(preco_unitario) else float(preco_unitario)
        valor_com_desconto = 0.0 if pd.isna(valor_com_desconto) else float(valor_com_desconto)

        desconto_html = ""

        if item.get("desconto_tipo") == "promo":
            desconto_html = """
            <span class="pedido-item-status">✂️ DESCONTO</span>
            """

        observacao_html = ""

        if item.get("observacao") and str(item["observacao"]).strip():
            observacao_html = f"""
            <div class="pedido-item-obs">
                📝 {item["observacao"]}
            </div>
            """

        linhas += f"""
        <div class="pedido-item">
            <div class="pedido-item-top">
                <div>
                    <div class="pedido-item-nome">
                        {item["nome_prod"]}
                    </div>

                    <div class="pedido-item-id">
                        #{item["cod_item"]}
                    </div>
                </div>

                {desconto_html}
            </div>

            <div class="pedido-item-info">
                <div>
                    <span>Qtd.</span>
                    <strong>{item["quantidade"]}x</strong>
                </div>

                <div>
                    <span>Unitário</span>
                    <strong>R$ {preco_unitario:.2f}</strong>
                </div>

                <div class="pedido-item-total">
                    <span>Total</span>
                    <strong>R$ {valor_com_desconto:.2f}</strong>
                </div>
            </div>

            {observacao_html}
        </div>
        """

    return f"""
    <div class="pedido-card">
        <div class="pedido-card-header">
            <div>
                <div class="pedido-card-titulo">
                    Pedido #{pedido}
                </div>

                <div class="pedido-card-qtd">
                    {len(itens)} item(ns)
                </div>
            </div>

            <div class="pedido-card-total">
                R$ {float(total):.2f}
            </div>
        </div>

        <div class="pedido-itens">
            {linhas}
        </div>

        <div class="pedido-card-footer">
            <span>Total do Pedido</span>
            <strong>R$ {float(total):.2f}</strong>
        </div>
    </div>
    """


def renderizar_resumo_pedido(
    quantidade_itens,
    subtotal,
    desconto,
    total
):
    subtotal = pd.to_numeric(subtotal, errors="coerce")
    desconto = pd.to_numeric(desconto, errors="coerce")
    total = pd.to_numeric(total, errors="coerce")

    subtotal = 0.0 if pd.isna(subtotal) else float(subtotal)
    desconto = 0.0 if pd.isna(desconto) else float(desconto)
    total = 0.0 if pd.isna(total) else float(total)

    return f"""
    <div class="pedido-resumo">
        <div class="pedido-resumo-item">
            <span>Itens</span>
            <strong>{quantidade_itens}</strong>
        </div>

        <div class="pedido-resumo-item">
            <span>Subtotal</span>
            <strong>R$ {subtotal:.2f}</strong>
        </div>

        <div class="pedido-resumo-item">
            <span>Desconto</span>
            <strong>R$ {desconto:.2f}</strong>
        </div>

        <div class="pedido-resumo-total">
            <span>Total</span>
            <strong>R$ {total:.2f}</strong>
        </div>
    </div>
    """


def renderizar_card_contexto(
    titulo,
    valor,
    detalhes=None,
    icone="📋"
):
    detalhes_html = ""

    if detalhes:
        detalhes_html = "".join(
            f'<span class="contexto-detalhe">{detalhe}</span>'
            for detalhe in detalhes
            if detalhe
        )

    return f"""
    <div class="pedido-contexto">
        <div class="contexto-icone">{icone}</div>

        <div class="contexto-conteudo">
            <div class="contexto-titulo">{titulo}</div>
            <div class="contexto-valor">{valor}</div>
            <div class="contexto-detalhes">{detalhes_html}</div>
        </div>
    </div>
    """


def renderizar_card_produto(
    nome_produto,
    preco,
    categoria=None
):
    preco = pd.to_numeric(preco, errors="coerce")
    preco = 0.0 if pd.isna(preco) else float(preco)

    categoria_html = ""

    if categoria:
        categoria_html = f"""
        <span class="produto-categoria">
            {categoria}
        </span>
        """

    return f"""
    <div class="produto-card">
        <div>
            <div class="produto-nome">
                {nome_produto}
            </div>

            {categoria_html}
        </div>

        <div class="produto-preco">
            R$ {preco:.2f}
        </div>
    </div>
    """


def renderizar_estilo_pedidos():
    st.markdown(
        """
        <style>
        .pedido-card {
            background: #181818;
            border: 1px solid #303030;
            border-radius: 12px;
            overflow: hidden;
            margin: 10px 0 14px;
        }

        .pedido-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 16px;
            background: #202020;
            border-bottom: 1px solid #303030;
        }

        .pedido-card-titulo {
            color: #f1f3f5;
            font-size: 17px;
            font-weight: 800;
        }

        .pedido-card-qtd {
            color: #858b94;
            font-size: 11px;
            margin-top: 3px;
        }

        .pedido-card-total {
            color: #fff;
            font-size: 17px;
            font-weight: 800;
        }

        .pedido-itens {
            padding: 4px 15px;
        }

        .pedido-item {
            padding: 13px 0;
            border-bottom: 1px solid #292929;
        }

        .pedido-item:last-child {
            border-bottom: none;
        }

        .pedido-item-top {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 10px;
        }

        .pedido-item-nome {
            color: #f1f3f5;
            font-size: 16px;
            font-weight: 700;
            line-height: 1.25;
        }

        .pedido-item-id {
            color: #777;
            font-size: 10px;
            margin-top: 3px;
        }

        .pedido-item-status {
            color: #f39c12;
            font-size: 10px;
            font-weight: 700;
            white-space: nowrap;
        }

        .pedido-item-info {
            display: grid;
            grid-template-columns: auto 1fr auto;
            align-items: end;
            gap: 18px;
            margin-top: 12px;
        }

        .pedido-item-info > div {
            display: flex;
            flex-direction: column;
            gap: 3px;
        }

        .pedido-item-info span {
            color: #777;
            font-size: 9px;
            text-transform: uppercase;
            letter-spacing: .4px;
        }

        .pedido-item-info strong {
            color: #f1f3f5;
            font-size: 14px;
        }

        .pedido-item-total {
            align-items: flex-end;
        }

        .pedido-item-total strong {
            font-size: 16px;
            font-weight: 800;
            white-space: nowrap;
        }

        .pedido-item-obs {
            margin-top: 9px;
            padding-top: 8px;
            border-top: 1px solid #252525;
            color: #9da3ad;
            font-size: 11px;
            line-height: 1.35;
        }

        .pedido-card-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 13px 16px;
            background: #202020;
            border-top: 1px solid #303030;
        }

        .pedido-card-footer span {
            color: #858b94;
            font-size: 12px;
        }

        .pedido-card-footer strong {
            color: #fff;
            font-size: 18px;
            font-weight: 800;
        }

        .pedido-resumo {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            margin: 12px 0;
        }

        .pedido-resumo-item,
        .pedido-resumo-total {
            background: #1e1e1e;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
        }

        .pedido-resumo-item span,
        .pedido-resumo-total span {
            display: block;
            color: #858b94;
            font-size: 10px;
        }

        .pedido-resumo-item strong {
            display: block;
            color: #f1f3f5;
            font-size: 15px;
            margin-top: 3px;
        }

        .pedido-resumo-total {
            border: 1px solid #444;
        }

        .pedido-resumo-total strong {
            display: block;
            color: #fff;
            font-size: 17px;
            margin-top: 3px;
        }

        .pedido-contexto {
            display: flex;
            align-items: center;
            gap: 12px;
            background: #181818;
            border: 1px solid #303030;
            border-radius: 11px;
            padding: 12px 14px;
            margin: 8px 0 14px;
        }

        .contexto-icone {
            font-size: 24px;
            flex-shrink: 0;
        }

        .contexto-conteudo {
            min-width: 0;
        }

        .contexto-titulo {
            color: #858b94;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: .5px;
        }

        .contexto-valor {
            color: #f1f3f5;
            font-size: 16px;
            font-weight: 700;
            margin-top: 2px;
        }

        .contexto-detalhes {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 5px;
        }

        .contexto-detalhe {
            color: #999;
            font-size: 11px;
        }

        .produto-card {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            background: #181818;
            border: 1px solid #303030;
            border-radius: 10px;
            padding: 12px 14px;
            margin: 7px 0;
        }

        .produto-nome {
            color: #f1f3f5;
            font-size: 15px;
            font-weight: 700;
        }

        .produto-categoria {
            display: inline-block;
            color: #858b94;
            font-size: 10px;
            margin-top: 3px;
        }

        .produto-preco {
            color: #fff;
            font-size: 15px;
            font-weight: 700;
            white-space: nowrap;
        }

        @media (max-width: 600px) {
            .pedido-card-header {
                padding: 12px;
            }

            .pedido-item {
                padding: 11px 0;
            }

            .pedido-item-nome {
                font-size: 14px;
            }

            .pedido-item-info {
                gap: 10px;
            }

            .pedido-card-total {
                font-size: 15px;
            }

            .pedido-item-total strong {
                font-size: 15px;
            }

            .pedido-resumo {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )