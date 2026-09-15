import streamlit as st
import pandas as pd
import os
import pickle
from datetime import datetime
import time
import hashlib

from components.auth import exigir_permissao
exigir_permissao("delivery")


from components.card_cozinha import renderizar_card_cozinha

from utils.paths import get_caminhos
from utils.print import gerar_ticket_cozinha, salvar_ticket_arquivo, imprimir_ticket, gerar_ticket_bar, salvar_ticket_bar_arquivo
from utils.pedidos_utils import (
    gerar_id_pedido,
    carregar_pkl,
    salvar_pkl,
    gerar_cod_item,
    carregar_historico_pedidos_hoje,
    sincronizar_historico_pedido,
    renderizar_seletor_cliente
)
from utils.movimentacoes_utils import baixar_por_produto
from utils.caixa_utils import registrar_venda_no_caixa, carregar_historico_caixa
from utils.delivery_utils import criar_registro_delivery, atualizar_status, obter_dados_cliente
from utils.clientes_utils import geocodificar_cliente
from components.card_pedidos import (
    renderizar_card_pedido,
    renderizar_resumo_pedido,
    renderizar_estilo_pedidos
)

_c = get_caminhos()
CAMINHO_PRODUTOS = _c["produtos"]
CAMINHO_MESAS = _c["mesas"]
CAMINHO_PEDIDOS = _c["pedidos"]
CAMINHO_HISTORICO_PEDIDOS = os.path.join("data", "historico_pedidos.pkl")

os.makedirs(os.path.dirname(CAMINHO_PRODUTOS), exist_ok=True)
os.makedirs(os.path.dirname(CAMINHO_MESAS), exist_ok=True)
os.makedirs(os.path.dirname(CAMINHO_PEDIDOS), exist_ok=True)

COLUNAS_PEDIDOS = [
    'id_pedido',
    'id_item',
    'cod_item',
    'id_mesa',
    'cod_prod',
    'nome_prod',
    'quantidade',
    'preco_unitario',
    'preco_final',
    'desconto_tipo',
    'desconto_valor',
    'subtotal',
    'valor_com_desconto',
    'observacao',
    'criado_em',
    'status',
    'categoria',
    'tipo_venda',
    'item_individual',
    'origem_venda',
    'taxa_entrega',
    'taxa_embalagem',
    'id_cliente',
    'metodo_pagamento'
]

if 'produtos' not in st.session_state:
    st.session_state.produtos = carregar_pkl(CAMINHO_PRODUTOS)

if 'mesas' not in st.session_state:
    st.session_state.mesas = carregar_pkl(CAMINHO_MESAS)

if 'pedidos' not in st.session_state:
    st.session_state.pedidos = carregar_historico_pedidos_hoje(
        CAMINHO_HISTORICO_PEDIDOS,
        COLUNAS_PEDIDOS
    )

    if st.session_state.pedidos.empty:
        st.session_state.pedidos = pd.DataFrame(columns=COLUNAS_PEDIDOS)

for coluna in COLUNAS_PEDIDOS:
    if coluna not in st.session_state.pedidos.columns:
        if coluna == 'valor_com_desconto':
            st.session_state.pedidos[coluna] = st.session_state.pedidos.get(
                'subtotal',
                0.0
            )
        elif coluna == 'desconto_tipo':
            st.session_state.pedidos[coluna] = 'Nenhum'
        elif coluna == 'desconto_valor':
            st.session_state.pedidos[coluna] = 0.0
        elif coluna == 'taxa_entrega':
            st.session_state.pedidos[coluna] = 0.0
        elif coluna == 'taxa_embalagem':
            st.session_state.pedidos[coluna] = 0.0
        elif coluna == 'id_cliente':
            st.session_state.pedidos[coluna] = ''
        elif coluna == 'metodo_pagamento':
            st.session_state.pedidos[coluna] = ''
        else:
            st.session_state.pedidos[coluna] = ''

st.session_state.pedidos['valor_com_desconto'] = pd.to_numeric(
    st.session_state.pedidos['valor_com_desconto'],
    errors='coerce'
).fillna(
    pd.to_numeric(
        st.session_state.pedidos['subtotal'],
        errors='coerce'
    ).fillna(0.0)
)

if 'pedido_atual' not in st.session_state:
    st.session_state.pedido_atual = []

if 'confirmar_cancelamento' not in st.session_state:
    st.session_state.confirmar_cancelamento = None

if 'versao_obs' not in st.session_state:
    st.session_state.versao_obs = 0

renderizar_estilo_pedidos()

st.header("Pedidos")

aba1, aba2 = st.tabs(["Novo Pedido", "Cozinha"])


with aba1:
    st.subheader("📝 Novo Pedido")

    origem_venda = st.selectbox(
        "Origem da Venda:",
        ["mesa", "takeaway", "delivery"],
        format_func=lambda x: {
            "mesa": "Mesa",
            "takeaway": "Takeaway",
            "delivery": "Delivery"
        }[x],
        key="origem_venda_pedido"
    )

    mesa_selecionada = None
    mesa_info = None
    taxa_entrega = 0.0
    taxa_embalagem = 0.0
    id_cliente = ""
    nome_cliente_pedido = ""
    metodo_pagamento = ""

    if origem_venda == "delivery":
        st.subheader("🚚 Delivery")

        id_cliente, nome_cliente_pedido, _ = renderizar_seletor_cliente("pedido_atual")

        col_delivery1, col_delivery2 = st.columns(2)

        with col_delivery1:
            taxa_entrega = st.number_input(
                "Taxa de entrega (R$)",
                min_value=0.0,
                step=1.0,
                value=10.0,
                format="%.2f",
                key="taxa_entrega_input"
            )

        with col_delivery2:
            taxa_embalagem = st.number_input(
                "Taxa de embalagem (R$)",
                min_value=0.0,
                step=0.50,
                value=0.0,
                format="%.2f",
                key="taxa_embalagem_delivery"
            )

        metodo_pagamento = "iFood"
        st.info(f"💳 Método de pagamento: {metodo_pagamento}")

        st.divider()

    elif origem_venda == "takeaway":
        st.subheader("🛍️ Takeaway")

        id_cliente, nome_cliente_pedido, _ = renderizar_seletor_cliente("pedido_atual")

        col_takeaway1, col_takeaway2 = st.columns(2)

        with col_takeaway1:
            taxa_embalagem = st.number_input(
                "Taxa de embalagem (R$)",
                min_value=0.0,
                step=0.50,
                value=2.00,
                format="%.2f",
                key="taxa_embalagem_takeaway"
            )

        with col_takeaway2:
            metodo_pagamento = st.selectbox(
                "💳 Método de Pagamento:",
                ["Dinheiro", "Pix", "Débito", "Crédito", "Voucher"],
                key="metodo_pagamento_takeaway"
            )

        st.divider()

    if origem_venda == "mesa":
        mesas_abertas = st.session_state.mesas[
            st.session_state.mesas['status'] == 'aberta'
        ].copy()

        if mesas_abertas.empty:
            st.warning("⚠️ Nenhuma mesa aberta. Abra uma mesa primeiro.")
            st.stop()

        lista_mesas = mesas_abertas['id_mesa'].tolist()

        mesa_selecionada = st.selectbox(
            "Selecione a mesa:",
            lista_mesas,
            key="mesa_selecionada_pedido"
        )

        mesa_info = mesas_abertas[
            mesas_abertas['id_mesa'] == mesa_selecionada
        ].iloc[0]

        st.info(
            f"👥 Clientes: {mesa_info['qtd_clientes']} | "
            f"Garçom: {mesa_info['garcom'] if mesa_info['garcom'] else 'Não definido'}"
        )

        id_cliente, nome_cliente_pedido, _ = renderizar_seletor_cliente("pedido_atual")

    st.subheader("Produtos")

    if st.session_state.produtos.empty:
        st.warning(
            "⚠️ Nenhum produto cadastrado. Cadastre produtos na aba Produtos."
        )
    else:
        col_busca, col_produto = st.columns([1, 2])

        with col_busca:
            busca_produto = st.text_input(
                "🔍 Buscar:",
                placeholder="Nome ou código..."
            )

        df_produtos = st.session_state.produtos.copy()
        df_produtos['cod_prod'] = df_produtos['cod_prod'].astype(str).str.strip()

        if 'tipo_venda' in df_produtos.columns:
            df_produtos = df_produtos[
                df_produtos['tipo_venda'].isin(['menu', 'bar'])
            ]

        if busca_produto:
            df_produtos = df_produtos[
                df_produtos['nome'].str.contains(
                    busca_produto,
                    case=False,
                    na=False
                )
                |
                df_produtos['cod_prod'].str.contains(
                    busca_produto,
                    case=False,
                    na=False
                )
            ]

        if not df_produtos.empty:
            df_produtos['display'] = (
                df_produtos['cod_prod'] + " - " + df_produtos['nome']
            )

            produtos_display = df_produtos['display'].tolist()

            with col_produto:
                produto_selecionado_display = st.selectbox(
                    "Produto:",
                    produtos_display
                )

            cod_prod_selecionado = produto_selecionado_display.split(" - ")[0]

            produto_data = df_produtos[
                df_produtos['cod_prod'] == cod_prod_selecionado
            ].iloc[0]

            cod_prod = produto_data['cod_prod']
            nome_prod = produto_data['nome']
            preco_original = float(produto_data['p_venda'])
            categoria = produto_data.get('categoria', '')
            tipo_venda = produto_data.get('tipo_venda', 'menu')

            with st.container():
                st.markdown("**✂️ Desconto**")

                col_desc1, col_desc2, col_desc3 = st.columns([2, 1, 1])

                with col_desc1:
                    tipo_desconto = st.radio(
                        "Tipo:",
                        ["Nenhum", "Percentual (%)", "Preço Fixo (R$)"],
                        key=f"tipo_desc_{cod_prod}",
                        horizontal=True
                    )

                preco_final = preco_original
                desconto_tipo = "Nenhum"
                desconto_valor = 0.0

                with col_desc2:
                    if tipo_desconto == "Percentual (%)":
                        pct_desconto = st.number_input(
                            "%",
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
                            "R$",
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
                        st.caption("Sem desconto")

                with col_desc3:
                    st.metric(
                        "Final",
                        f"R$ {preco_final:.2f}"
                    )

            col_qtd, col_sub, col_obs = st.columns([1, 1, 2])

            with col_qtd:
                quantidade = st.number_input(
                    "Qtd:",
                    min_value=1,
                    step=1,
                    value=1
                )

            with col_sub:
                subtotal = quantidade * preco_final
                st.metric(
                    "Subtotal",
                    f"R$ {subtotal:.2f}"
                )

            with col_obs:
                observacao_item = st.text_input(
                    "Observação:",
                    placeholder="Ex: sem cebola, bem passado...",
                    key=f"obs_item_{cod_prod}_{st.session_state.versao_obs}"
                )

            if st.button(
                "➕ Adicionar ao Pedido",
                use_container_width=True,
                type="primary"
            ):
                for i in range(quantidade):
                    cod_item = gerar_cod_item()

                    st.session_state.pedido_atual.append({
                        'cod_item': cod_item,
                        'cod_prod': cod_prod,
                        'nome_prod': nome_prod,
                        'quantidade': 1,
                        'preco_unitario': preco_original,
                        'preco_final': preco_final,
                        'desconto_tipo': desconto_tipo,
                        'desconto_valor': desconto_valor,
                        'subtotal': preco_final,
                        'valor_com_desconto': preco_final,
                        'observacao': observacao_item,
                        'categoria': categoria,
                        'tipo_venda': tipo_venda,
                        'item_individual': (
                            f"{cod_prod}_{i+1}_"
                            f"{datetime.now().strftime('%H%M%S%f')}"
                        )
                    })

                st.session_state.versao_obs += 1

                st.success(
                    f"✅ {quantidade}x {nome_prod} adicionado ao pedido!"
                )

                time.sleep(1)
                st.rerun()

        else:
            st.info("Nenhum produto encontrado.")

    st.divider()

    st.subheader("Pedido Atual")

    if st.session_state.pedido_atual:
        df_pedido_atual = pd.DataFrame(
            st.session_state.pedido_atual
        )

        df_pedido_atual['subtotal'] = (
            df_pedido_atual['quantidade'] *
            df_pedido_atual['preco_final']
        )

        df_pedido_atual['valor_com_desconto'] = (
            df_pedido_atual['subtotal']
        )

        total_pedido = df_pedido_atual['valor_com_desconto'].sum()

        total_economia = (
            df_pedido_atual['quantidade'] *
            df_pedido_atual['preco_unitario'] -
            df_pedido_atual['valor_com_desconto']
        ).sum()

        itens_card = df_pedido_atual.to_dict('records')

        st.html(
            renderizar_card_pedido(
                pedido="Atual",
                itens=itens_card,
                total=total_pedido
            )
        )

        desconto_total = max(
            0.0,
            (
                df_pedido_atual['quantidade'] *
                df_pedido_atual['preco_unitario']
            ).sum() -
            total_pedido
        )

        st.html(
            renderizar_resumo_pedido(
                quantidade_itens=len(df_pedido_atual),
                subtotal=(
                    df_pedido_atual['quantidade'] *
                    df_pedido_atual['preco_unitario']
                ).sum(),
                desconto=desconto_total,
                total=total_pedido
            )
        )

        col_btn1, col_btn2, col_btn3 = st.columns(3)

        with col_btn1:
            if st.button(
                "✅ Enviar Pedido",
                use_container_width=True):
                
                if origem_venda == "delivery" and not id_cliente:
                    st.error("⚠️ Selecione ou crie um cliente para o delivery.")
                    st.stop()

                if st.session_state.pedido_atual:
                    id_pedido = gerar_id_pedido(
                        st.session_state.pedidos
                    )

                    for numero_item, item in enumerate(
                        st.session_state.pedido_atual,
                        start=1
                    ):
                        cod_item = item.get('cod_item') or gerar_cod_item()

                        agora = datetime.now().strftime(
                            "%d/%m/%Y %H:%M:%S"
                        )

                        novo_pedido = pd.DataFrame([{
                            'id_pedido': id_pedido,
                            'id_item': numero_item,
                            'cod_item': cod_item,
                            'id_mesa': mesa_selecionada,
                            'cod_prod': item['cod_prod'],
                            'nome_prod': item['nome_prod'],
                            'quantidade': item['quantidade'],
                            'preco_unitario': item['preco_unitario'],
                            'preco_final': item['preco_final'],
                            'desconto_tipo': item.get(
                                'desconto_tipo',
                                'Nenhum'
                            ),
                            'desconto_valor': item.get(
                                'desconto_valor',
                                0.0
                            ),
                            'subtotal': item['subtotal'],
                            'valor_com_desconto': item.get(
                                'valor_com_desconto',
                                item['subtotal']
                            ),
                            'observacao': item.get(
                                'observacao',
                                ''
                            ),
                            'criado_em': agora,
                            'status': 'enviado',
                            'categoria': item.get(
                                'categoria',
                                ''
                            ),
                            'tipo_venda': item.get(
                                'tipo_venda',
                                'menu'
                            ),
                            'item_individual': item.get(
                                'item_individual',
                                ''
                            ),
                            'origem_venda': origem_venda,
                            'taxa_entrega': taxa_entrega,
                            'taxa_embalagem': taxa_embalagem,
                            'id_cliente': id_cliente,
                            'metodo_pagamento': metodo_pagamento
                        }])

                        st.session_state.pedidos = pd.concat(
                            [
                                st.session_state.pedidos,
                                novo_pedido
                            ],
                            ignore_index=True
                        )

                        pedido_historico = {
                            'id_pedido': id_pedido,
                            'id_item': numero_item,
                            'cod_item': cod_item,
                            'id_mesa': mesa_selecionada,
                            'cod_prod': item['cod_prod'],
                            'nome_prod': item['nome_prod'],
                            'quantidade': item['quantidade'],
                            'preco_unitario': item['preco_unitario'],
                            'preco_final': item['preco_final'],
                            'desconto_tipo': item.get(
                                'desconto_tipo',
                                'Nenhum'
                            ),
                            'desconto_valor': item.get(
                                'desconto_valor',
                                0.0
                            ),
                            'subtotal': item['subtotal'],
                            'valor_com_desconto': item.get(
                                'valor_com_desconto',
                                item['subtotal']
                            ),
                            'observacao': item.get(
                                'observacao',
                                ''
                            ),
                            'criado_em': agora,
                            'data_fechamento': '',
                            'status': 'enviado',
                            'categoria': item.get(
                                'categoria',
                                ''
                            ),
                            'tipo_venda': item.get(
                                'tipo_venda',
                                'menu'
                            ),
                            'item_individual': item.get(
                                'item_individual',
                                ''
                            ),
                            'origem_venda': origem_venda,
                            'taxa_entrega': taxa_entrega,
                            'taxa_embalagem': taxa_embalagem,
                            'id_cliente': id_cliente,
                            'metodo_pagamento': metodo_pagamento
                        }

                        sincronizar_historico_pedido(
                            pedido_historico,
                            CAMINHO_HISTORICO_PEDIDOS,
                            COLUNAS_PEDIDOS
                        )

                    if origem_venda == "mesa":
                        idx_mesa = st.session_state.mesas[
                            st.session_state.mesas['id_mesa'] == mesa_selecionada
                        ].index[0]

                        st.session_state.mesas.loc[
                            idx_mesa,
                            'valor_total'
                        ] += total_pedido

                        clientes = st.session_state.mesas.loc[
                            idx_mesa,
                            'qtd_clientes'
                        ]

                        if clientes > 0:
                            st.session_state.mesas.loc[
                                idx_mesa,
                                'ticket_medio'
                            ] = round(
                                st.session_state.mesas.loc[
                                    idx_mesa,
                                    'valor_total'
                                ] / clientes,
                                2
                            )

                        salvar_pkl(
                            st.session_state.mesas,
                            CAMINHO_MESAS
                        )

                    if origem_venda == "delivery":
                        cliente_info = obter_dados_cliente(id_cliente)

                        lat_delivery = ''
                        lon_delivery = ''

                        if cliente_info:
                            telefone_delivery = cliente_info.get('telefone_principal', '') or ''
                            partes_end = [
                                cliente_info.get('logradouro', ''),
                                cliente_info.get('numero', ''),
                                cliente_info.get('complemento', '')
                            ]
                            endereco_delivery = ' '.join([p for p in partes_end if p])
                            bairro_cidade = ' - '.join([
                                p for p in [
                                    cliente_info.get('bairro', ''),
                                    cliente_info.get('cidade', ''),
                                    cliente_info.get('estado', '')
                                ] if p
                            ])
                            if bairro_cidade:
                                endereco_delivery = f"{endereco_delivery} ({bairro_cidade})"
                            referencia_delivery = cliente_info.get('referencia', '') or ''

                            lat_delivery = str(cliente_info.get('latitude', '') or '').strip()
                            lon_delivery = str(cliente_info.get('longitude', '') or '').strip()

                            if not lat_delivery or not lon_delivery:
                                email_contato = (
                                    st.session_state.get('config', {})
                                    .get('empresa', {})
                                    .get('email_contato', '')
                                    .strip()
                                )

                                if email_contato:
                                    try:
                                        sucesso_geo = geocodificar_cliente(id_cliente, email_contato)
                                        if sucesso_geo:
                                            cliente_atualizado = obter_dados_cliente(id_cliente)
                                            if cliente_atualizado:
                                                lat_delivery = str(cliente_atualizado.get('latitude', '') or '').strip()
                                                lon_delivery = str(cliente_atualizado.get('longitude', '') or '').strip()
                                    except Exception:
                                        pass
                        else:
                            telefone_delivery = ''
                            endereco_delivery = ''
                            referencia_delivery = ''

                        itens_resumo_delivery = ', '.join([
                            f"{item['quantidade']}x {item['nome_prod']}"
                            for item in st.session_state.pedido_atual
                        ])

                        criar_registro_delivery(
                            id_pedido,
                            id_cliente,
                            nome_cliente_pedido,
                            telefone_delivery,
                            endereco_delivery,
                            referencia_delivery,
                            itens_resumo_delivery,
                            total_pedido,
                            taxa_entrega,
                            lat_delivery,
                            lon_delivery
                        )

                    salvar_pkl(
                        st.session_state.pedidos,
                        CAMINHO_PEDIDOS
                    )

                    itens_cozinha = [
                        item
                        for item in st.session_state.pedido_atual
                        if item.get('tipo_venda', 'menu') == 'menu'
                    ]

                    itens_bar = [
                        item
                        for item in st.session_state.pedido_atual
                        if item.get('tipo_venda') == 'bar'
                    ]

                    if itens_cozinha:
                        ticket = gerar_ticket_cozinha(
                            id_pedido,
                            mesa_selecionada,
                            itens_cozinha
                        )

                        salvar_ticket_arquivo(
                            ticket=ticket,
                            pedido_id=id_pedido,
                            itens=itens_cozinha,
                            mesa=mesa_selecionada
                        )

                        if (
                            'impressora_cozinha' in st.session_state and
                            st.session_state.impressora_cozinha
                        ):
                            sucesso = imprimir_ticket(
                                ticket,
                                st.session_state.impressora_cozinha
                            )

                            if sucesso:
                                st.success(
                                    "🖨️ Ticket da cozinha enviado!"
                                )
                            else:
                                st.error(
                                    "❌ Falha ao imprimir ticket da cozinha."
                                )
                        else:
                            st.info(
                                "ℹ️ Ticket da cozinha salvo em arquivo."
                            )

                    if itens_bar:
                        ticket_bar = gerar_ticket_bar(
                            id_pedido,
                            mesa_selecionada,
                            itens_bar
                        )

                        salvar_ticket_bar_arquivo(
                            ticket=ticket_bar,
                            pedido_id=id_pedido,
                            itens=itens_bar,
                            mesa=mesa_selecionada
                        )

                        if (
                            'impressora_bar' in st.session_state and
                            st.session_state.impressora_bar
                        ):
                            sucesso = imprimir_ticket(
                                ticket_bar,
                                st.session_state.impressora_bar
                            )

                            if sucesso:
                                st.success(
                                    "🖨️ Ticket do bar enviado!"
                                )
                            else:
                                st.error(
                                    "❌ Falha ao imprimir ticket do bar."
                                )
                        else:
                            st.info(
                                "ℹ️ Ticket do bar salvo em arquivo."
                            )

                    if not itens_cozinha and not itens_bar:
                        st.info("ℹ️ Nenhum item para enviar.")

                    st.session_state.pedido_atual = []
                    st.session_state.versao_obs += 1

                    chave_sel = "cliente_selecionado_pedido_atual"
                    chave_busca = "busca_cliente_pedido_atual"
                    if chave_sel in st.session_state:
                        st.session_state[chave_sel] = None
                    if chave_busca in st.session_state:
                        st.session_state[chave_busca] = ''

                    st.success(
                        f"✅ Pedido enviado! Total: R$ {total_pedido:.2f}"
                    )

                    time.sleep(1)
                    st.rerun()

        if st.session_state.pedido_atual:
            st.divider()
            st.markdown("**Alterar Pedido:**")

            opcoes_itens = [
                f"Item {item['cod_item']} - {item['nome_prod']}"
                for item in st.session_state.pedido_atual
            ]

            if opcoes_itens:
                col1, col2 = st.columns(2)

                with col1:
                    item_selecionado = st.selectbox(
                        "Item",
                        opcoes_itens,
                        key="item_selecionado"
                    )

                with col2:
                    st.write("")
                    st.write("")

                    col2_1, col2_2 = st.columns(2)

                    with col2_1:
                        if st.button(
                            "🗑️ Remover",
                            use_container_width=True
                        ):
                            cod_item_selecionado = (
                                item_selecionado
                                .split(" - ")[0]
                                .replace("Item ", "")
                            )

                            st.session_state.pedido_atual = [
                                item
                                for item in st.session_state.pedido_atual
                                if item['cod_item'] != cod_item_selecionado
                            ]

                            st.rerun()

                    with col2_2:
                        if st.button(
                            "🧹 Limpar",
                            use_container_width=True
                        ):
                            st.session_state.pedido_atual = []
                            st.rerun()

with aba2:
    st.subheader("👨‍🍳 Cozinha")

    filtro_status = st.segmented_control(
        "Status do Pedido",
        ["Abertos", "Fechados", "Cancelados"],
        default="Abertos",
        key="filtro_cozinha",
        label_visibility="collapsed"
    )

    if filtro_status == "Abertos":
        pedidos_filtrados = st.session_state.pedidos[
            st.session_state.pedidos['status'] == 'enviado'
        ].copy()

        titulo = "🍽️ Em Aberto"

    elif filtro_status == "Fechados":
        pedidos_filtrados = st.session_state.pedidos[
            st.session_state.pedidos['status'] == 'fechado'
        ].copy()

        titulo = "✅ Fechados"

    else:
        pedidos_filtrados = st.session_state.pedidos[
            st.session_state.pedidos['status'] == 'cancelado'
        ].copy()

        titulo = "🚫 Cancelados"

    st.subheader(titulo)

    if pedidos_filtrados.empty:
        st.info(
            f"Nenhum pedido {filtro_status.lower()} no momento.")
    else:
        if filtro_status == "Abertos":
            pedidos_filtrados = pedidos_filtrados.sort_values('criado_em', ascending=True)
        else:
            pedidos_filtrados = pedidos_filtrados.sort_values('criado_em', ascending=False)


        if 'categoria' not in pedidos_filtrados.columns:
            pedidos_filtrados['categoria'] = ''

        if 'cod_item' not in pedidos_filtrados.columns:
            pedidos_filtrados['cod_item'] = ''

        if 'id_item' not in pedidos_filtrados.columns:
            pedidos_filtrados['id_item'] = ''

        if 'origem_venda' not in pedidos_filtrados.columns:
            pedidos_filtrados['origem_venda'] = 'mesa'

        if 'valor_com_desconto' not in pedidos_filtrados.columns:
            pedidos_filtrados['valor_com_desconto'] = pedidos_filtrados[
                'subtotal'
            ]

        df_exibicao = pedidos_filtrados[
            [
                'id_pedido',
                'id_item',
                'cod_item',
                'id_mesa',
                'nome_prod',
                'quantidade',
                'subtotal',
                'observacao',
                'criado_em',
                'categoria',
                'origem_venda',
                'status'
            ]
        ].copy()

        if 'fechado_em' in pedidos_filtrados.columns:
            df_exibicao['fechado_em'] = pedidos_filtrados['fechado_em']
        else:
            df_exibicao['fechado_em'] = ''

        if filtro_status == "Abertos":
            df_exibicao['tempo_formatado'] = df_exibicao[
                'criado_em'
            ].apply(
                lambda x: f"{int((datetime.now() - datetime.strptime(x, '%d/%m/%Y %H:%M:%S')).total_seconds() / 60)}min"
            )

        column_config = {
            'id_pedido': 'ID Pedido',
            'id_item': 'ID Item',
            'cod_item': 'Cód. Item',
            'id_mesa': 'Mesa',
            'nome_prod': 'Produto',
            'quantidade': 'Qtd',
            'subtotal': st.column_config.NumberColumn(
                'Valor',
                format="R$ %.2f"
            ),
            'observacao': 'Obs',
            'criado_em': 'Criado em',
            'categoria': 'Categoria',
            'origem_venda': 'Origem',
            'status': 'Status'
        }

        if filtro_status == "Abertos":
            column_config['tempo_formatado'] = 'Tempo'
        else:
            column_config['fechado_em'] = 'Fechado em'

        renderizar_card_cozinha(df_exibicao, filtro_status)

        if (
            filtro_status == "Abertos" and
            not pedidos_filtrados.empty
        ):
            st.divider()
            st.subheader("📝 Gerenciar Item")

            pedidos_agrupados = pedidos_filtrados.groupby(
                'id_pedido'
            ).agg({
                'id_mesa': 'first',
                'criado_em': 'first',
                'origem_venda': 'first'
            }).reset_index()
            pedidos_agrupados = pedidos_agrupados.sort_values('criado_em', ascending=True).reset_index(drop=True)
            pedido_selecionado = st.selectbox(
                "Selecione o pedido:",
                pedidos_agrupados['id_pedido'].tolist()
            )

            itens_pedido = pedidos_filtrados[
                pedidos_filtrados['id_pedido'] == pedido_selecionado
            ]

            if not itens_pedido.empty:
                mesa_pedido = itens_pedido['id_mesa'].iloc[0]
                origem_pedido = itens_pedido['origem_venda'].iloc[0]

                if origem_pedido == 'mesa':
                    st.write(f"**Mesa:** {mesa_pedido}")
                else:
                    st.write(
                        f"**Origem:** {origem_pedido.capitalize()}"
                    )

                    if 'id_cliente' in itens_pedido.columns:
                        cliente = itens_pedido['id_cliente'].iloc[0]
                        if cliente:
                            st.write(f"**Cliente:** {cliente}")

                    if 'metodo_pagamento' in itens_pedido.columns:
                        metodo = itens_pedido['metodo_pagamento'].iloc[0]
                        if metodo:
                            st.write(f"**Pagamento:** {metodo}")

                    if 'taxa_embalagem' in itens_pedido.columns:
                        taxa_emb = itens_pedido['taxa_embalagem'].iloc[0]
                        if taxa_emb > 0:
                            st.write(f"**Taxa Embalagem:** R$ {taxa_emb:.2f}")

                    if origem_pedido == 'delivery' and 'taxa_entrega' in itens_pedido.columns:
                        taxa_ent = itens_pedido['taxa_entrega'].iloc[0]
                        if taxa_ent > 0:
                            st.write(f"**Taxa Entrega:** R$ {taxa_ent:.2f}")

                st.write("**Itens do pedido:**")

                for idx, item in itens_pedido.iterrows():
                    obs = (
                        f" (obs: {item['observacao']})"
                        if item.get('observacao')
                        else ""
                    )

                    st.write(
                        f"- **Item {item['id_item']}**: "
                        f"{item['quantidade']}x "
                        f"{item['nome_prod']}{obs}"
                    )

            col_acao1, col_acao2 = st.columns(2)

            with col_acao1:
                st.write("**Fechar Item**")

                cod_item_display = [
                    f"Item {item['id_item']} - {item['nome_prod']}"
                    for _, item in itens_pedido.iterrows()
                ]

                cod_item_selecionado_display = st.multiselect(
                    "Selecione os itens para fechar:",
                    cod_item_display,
                    key="fechar_item_select"
                )

                id_itens_selecionados = [
                    pd.to_numeric(
                        item.split(" - ")[0].replace("Item ", ""),
                        errors='coerce'
                    )
                    for item in cod_item_selecionado_display
                ]

                if st.button(
                    "🛎️ Fechar Item",
                    use_container_width=True,
                    type="primary"
                ):
                    if id_itens_selecionados:
                        mask = (
                            (
                                st.session_state.pedidos['id_pedido'] ==
                                pedido_selecionado
                            )
                            &
                            (
                                pd.to_numeric(
                                    st.session_state.pedidos['id_item'],
                                    errors='coerce'
                                ).isin(id_itens_selecionados)
                            )
                        )

                        if mask.any():
                            data_fechamento = datetime.now().strftime(
                                "%d/%m/%Y %H:%M:%S"
                            )

                            st.session_state.pedidos.loc[
                                mask,
                                'status'
                            ] = 'fechado'

                            st.session_state.pedidos.loc[
                                mask,
                                'fechado_em'
                            ] = data_fechamento

                            for _, item in st.session_state.pedidos.loc[
                                mask
                            ].iterrows():
                                pedido_historico = item.to_dict()
                                pedido_historico['data_fechamento'] = data_fechamento
                                pedido_historico['status'] = 'fechado'

                                sincronizar_historico_pedido(
                                    pedido_historico,
                                    CAMINHO_HISTORICO_PEDIDOS,
                                    COLUNAS_PEDIDOS
                                )

                                baixar_por_produto(
                                    item['id_pedido'],
                                    item['cod_item'],
                                    item['cod_prod'],
                                    item['quantidade'],
                                    item.get('nome_prod', '')
                                )

                            salvar_pkl(
                                st.session_state.pedidos,
                                CAMINHO_PEDIDOS
                            )

                            itens_pedido_atual = st.session_state.pedidos[
                                st.session_state.pedidos['id_pedido'] ==
                                pedido_selecionado
                            ]

                            todos_finalizados = all(
                                status in ['fechado', 'cancelado']
                                for status in itens_pedido_atual['status']
                            )

                            if todos_finalizados:
                                origem = itens_pedido_atual['origem_venda'].iloc[0]

                                if origem in ['takeaway', 'delivery']:
                                    total_pedido = itens_pedido_atual['valor_com_desconto'].sum()
                                    taxa_emb = itens_pedido_atual['taxa_embalagem'].iloc[0] if 'taxa_embalagem' in itens_pedido_atual.columns else 0
                                    metodo_pag = itens_pedido_atual['metodo_pagamento'].iloc[0] if 'metodo_pagamento' in itens_pedido_atual.columns else 'Dinheiro'

                                    if origem == 'takeaway':
                                        total_final = total_pedido + taxa_emb
                                        tipo_venda = 'Takeaway'
                                    else:
                                        taxa_ent = itens_pedido_atual['taxa_entrega'].iloc[0] if 'taxa_entrega' in itens_pedido_atual.columns else 0
                                        total_final = total_pedido + taxa_emb + taxa_ent
                                        tipo_venda = 'Delivery'
                                        if not metodo_pag:
                                            metodo_pag = 'iFood'

                                    registrar_venda_no_caixa(
                                        tipo_venda,
                                        total_final,
                                        metodo_pag,
                                        f"{tipo_venda} - Pedido {pedido_selecionado}"
                                    )

                                    if origem == 'delivery':
                                        atualizar_status(pedido_selecionado, 'pronto')

                                    st.success(
                                        f"✅ Pedido {pedido_selecionado} finalizado! "
                                        f"Total: R$ {total_final:.2f} (Pagamento: {metodo_pag})"
                                    )
                                else:
                                    st.success(
                                        f"✅ Todos os itens do pedido {pedido_selecionado} foram finalizados!"
                                    )
                            else:
                                st.success(
                                    f"✅ {len(id_itens_selecionados)} item(ns) fechado(s)! "
                                    f"Aguardando outros itens."
                                )

                            time.sleep(0.5)
                            st.rerun()

            with col_acao2:
                st.write("**Cancelar Item**")

                cod_item_display_cancel = [
                    f"Item {item['id_item']} - {item['nome_prod']}"
                    for _, item in itens_pedido.iterrows()
                ]

                cod_item_selecionado_cancel_display = st.multiselect(
                    "Selecione os itens para cancelar:",
                    cod_item_display_cancel,
                    key="cancelar_item_select"
                )

                id_itens_selecionados_cancel = [
                    pd.to_numeric(
                        item.split(" - ")[0].replace("Item ", ""),
                        errors='coerce'
                    )
                    for item in cod_item_selecionado_cancel_display
                ]

                if st.button(
                    "❌ Cancelar Item",
                    use_container_width=True
                ):
                    if id_itens_selecionados_cancel:
                        st.session_state.confirmar_cancelamento = (
                            f"{pedido_selecionado}_"
                            f"{'_'.join(map(str, id_itens_selecionados_cancel))}"
                        )

                        st.rerun()

                if st.session_state.get(
                    "confirmar_cancelamento"
                ) == (
                    f"{pedido_selecionado}_"
                    f"{'_'.join(map(str, id_itens_selecionados_cancel))}"
                ):
                    st.warning(
                        f"⚠️ Tem certeza que deseja CANCELAR "
                        f"{len(id_itens_selecionados_cancel)} item(ns) "
                        f"do pedido {pedido_selecionado}?"
                    )

                    col_conf1, col_conf2 = st.columns(2)

                    with col_conf1:
                        if st.button(
                            "✅ Sim, cancelar",
                            use_container_width=True
                        ):
                            mask = (
                                (
                                    st.session_state.pedidos['id_pedido'] ==
                                    pedido_selecionado
                                )
                                &
                                (
                                    pd.to_numeric(
                                        st.session_state.pedidos['id_item'],
                                        errors='coerce'
                                    ).isin(
                                        id_itens_selecionados_cancel
                                    )
                                )
                            )

                            if mask.any():
                                data_fechamento = datetime.now().strftime(
                                    "%d/%m/%Y %H:%M:%S"
                                )

                                st.session_state.pedidos.loc[
                                    mask,
                                    'status'
                                ] = 'cancelado'

                                st.session_state.pedidos.loc[
                                    mask,
                                    'fechado_em'
                                ] = data_fechamento

                                for _, item in st.session_state.pedidos.loc[
                                    mask
                                ].iterrows():
                                    pedido_historico = item.to_dict()
                                    pedido_historico['data_fechamento'] = data_fechamento
                                    pedido_historico['status'] = 'cancelado'

                                    sincronizar_historico_pedido(
                                        pedido_historico,
                                        CAMINHO_HISTORICO_PEDIDOS,
                                        COLUNAS_PEDIDOS
                                    )

                                salvar_pkl(
                                    st.session_state.pedidos,
                                    CAMINHO_PEDIDOS
                                )

                                itens_pedido_atual = st.session_state.pedidos[
                                    st.session_state.pedidos['id_pedido'] ==
                                    pedido_selecionado
                                ]

                                todos_finalizados = all(
                                    status in ['fechado', 'cancelado']
                                    for status in itens_pedido_atual['status']
                                )

                                st.session_state.confirmar_cancelamento = None

                                if todos_finalizados:
                                    origem = itens_pedido_atual['origem_venda'].iloc[0]

                                    if origem in ['takeaway', 'delivery']:
                                        total_pedido = itens_pedido_atual['valor_com_desconto'].sum()
                                        taxa_emb = itens_pedido_atual['taxa_embalagem'].iloc[0] if 'taxa_embalagem' in itens_pedido_atual.columns else 0
                                        metodo_pag = itens_pedido_atual['metodo_pagamento'].iloc[0] if 'metodo_pagamento' in itens_pedido_atual.columns else 'Dinheiro'

                                        if origem == 'takeaway':
                                            total_final = total_pedido + taxa_emb
                                            tipo_venda = 'Takeaway'
                                        else:
                                            taxa_ent = itens_pedido_atual['taxa_entrega'].iloc[0] if 'taxa_entrega' in itens_pedido_atual.columns else 0
                                            total_final = total_pedido + taxa_emb + taxa_ent
                                            tipo_venda = 'Delivery'
                                            if not metodo_pag:
                                                metodo_pag = 'iFood'

                                        registrar_venda_no_caixa(
                                            tipo_venda,
                                            total_final,
                                            metodo_pag,
                                            f"{tipo_venda} - Pedido {pedido_selecionado}"
                                        )

                                        if origem == 'delivery':
                                            atualizar_status(pedido_selecionado, 'pronto')

                                        st.success(
                                            f"✅ Pedido {pedido_selecionado} finalizado! "
                                            f"Total: R$ {total_final:.2f} (Pagamento: {metodo_pag})"
                                        )
                                    else:
                                        st.success(
                                            f"✅ Todos os itens do pedido {pedido_selecionado} foram finalizados!"
                                        )
                                else:
                                    st.success(
                                        f"✅ {len(id_itens_selecionados_cancel)} "
                                        f"item(ns) cancelado(s)! "
                                        f"Aguardando outros itens."
                                    )

                                time.sleep(0.5)
                                st.rerun()

                    with col_conf2:
                        if st.button(
                            "❌ Não",
                            use_container_width=True
                        ):
                            st.session_state.confirmar_cancelamento = None
                            st.rerun()