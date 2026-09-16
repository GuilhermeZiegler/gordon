import streamlit as st
import pandas as pd
import os
from datetime import datetime
import time
import pickle

from components.auth import exigir_permissao
exigir_permissao("mesas")


from components.card_mesa import card_mesa
from components.comanda import renderizar_comanda
from components.card_descontos import (
    renderizar_card_item,
    renderizar_resumo_mesa,
    renderizar_cabecalho_pedido,
    renderizar_titulo_acoes,
    renderizar_estilo_cards
)

from utils.db import ler_tabela
from utils.staff_utils import carregar_funcionarios
from utils.mesas_utils import (
    COLUNAS_MESAS,
    filtrar_pedidos_por_sessao,
    carregar_mesas,
    salvar_mesas,
    carregar_pedidos,
    atualizar_valor_mesa,
    resetar_estado_mesa,
    salvar_pedidos,
    adicionar_historico_mesa,
    obter_itens_mesa,
    aplicar_cortesia_item,
    remover_cortesia_item,
    aplicar_desconto_item,
    remover_desconto_item,
    aplicar_devolucao_item,
    remover_devolucao_item,
    obter_id_venda_mesa,
    reabrir_mesa
)

from utils.pedidos_utils import sincronizar_historico_pedido, gerar_id_pedido, gerar_cod_item
from utils.caixa_utils import registrar_venda_no_caixa, substituir_venda_no_caixa
from utils.caixa_utils import carregar_historico_caixa

from pages.configuracoes import carregar_config

if 'mesas' not in st.session_state:
    st.session_state.mesas = carregar_mesas()

    if st.session_state.mesas.empty:
        st.session_state.mesas = pd.DataFrame(columns=COLUNAS_MESAS)

if 'pedidos' not in st.session_state:
    st.session_state.pedidos = carregar_pedidos()

if 'editar_data' not in st.session_state:
    st.session_state.editar_data = {}

if 'fechar_mesa' not in st.session_state:
    st.session_state.fechar_mesa = None

if 'comanda_mesa' not in st.session_state:
    st.session_state.comanda_mesa = None

if 'funcionarios' not in st.session_state:
    st.session_state.funcionarios = carregar_funcionarios()

if 'estado_mesa' not in st.session_state:
    st.session_state.estado_mesa = {}

if 'confirmar_devolucao' not in st.session_state:
    st.session_state.confirmar_devolucao = None

if 'reabrir_mesa' not in st.session_state:
    st.session_state.reabrir_mesa = None


st.header("Mesas")
max_mesas = carregar_config().get("max_mesas", 50)

aba1, aba2, aba3 = st.tabs(["Gerenciar", "Fechadas", "Comandas"])


with aba1:
    df_abertas = st.session_state.mesas[
        st.session_state.mesas['status'] == 'aberta'
    ].copy()

    mesas_abertas = len(df_abertas)
    total_mesas_cadastradas = len(st.session_state.mesas)

    col_info1, col_info2, col_info3 = st.columns(3)

    with col_info1:
        st.metric(
            "Mesas Abertas",
            f"{mesas_abertas}/{max_mesas}",
            delta=f"{max_mesas - mesas_abertas} disponíveis"
        )

    with col_info2:
        st.metric(
            "📌 Total de Mesas",
            total_mesas_cadastradas
        )

    with col_info3:
        valor_total_soma = (
            df_abertas['valor_total'].sum()
            if 'valor_total' in df_abertas.columns
            else 0
        )

        ticket_medio = (
            valor_total_soma / mesas_abertas
            if mesas_abertas > 0
            else 0
        )

        st.metric(
            "🎫 Ticket Médio",
            f"R$ {ticket_medio:,.2f}"
        )

    st.divider()

    with st.container(border=True):

        col_abrir, col_buscar = st.columns([3, 1])

        with col_abrir:

            if mesas_abertas < max_mesas:

                col_mesa, col_garcom, col_clientes, col_btn = st.columns(
                    [2, 2, 1, 1]
                )

                with col_mesa:

                    ids_abertos = df_abertas['id_mesa'].tolist()
                    numeros_ocupados = []

                    for id_mesa in ids_abertos:
                        try:
                            num = int(id_mesa.replace('MESA-', ''))
                            numeros_ocupados.append(num)
                        except:
                            pass

                    numeros_disponiveis = [
                        i
                        for i in range(1, max_mesas + 1)
                        if i not in numeros_ocupados
                    ]

                    if numeros_disponiveis:
                        numero_mesa = st.selectbox(
                            "Mesa:",
                            numeros_disponiveis,
                            format_func=lambda x: f"MESA-{x:d}"
                        )

                with col_garcom:

                    funcionarios = st.session_state.funcionarios

                    nomes_funcionarios = [
                        f.get('nome', '')
                        for f in funcionarios
                        if f.get('cargo') == 'Garçom'
                    ]

                    garcom_selecionado = st.selectbox(
                        "Garçom:",
                        [""] + nomes_funcionarios,
                        format_func=lambda x: x if x else "Selecione..."
                    )

                with col_clientes:

                    qtd_clientes = st.number_input(
                        "Clientes:",
                        min_value=1,
                        step=1,
                        value=1
                    )

                with col_btn:

                    st.write("")
                    st.write("")

                    if st.button(
                        "🆕 Abrir",
                        use_container_width=True,
                        type="primary"
                    ):

                        novo_id = f"MESA-{numero_mesa:d}"

                        if novo_id in st.session_state.mesas['id_mesa'].values:

                            idx_existente = st.session_state.mesas[
                                st.session_state.mesas['id_mesa'] == novo_id
                            ].index[0]

                            if st.session_state.mesas.loc[
                                idx_existente,
                                'status'
                            ] == 'fechada':

                                st.session_state.mesas.loc[
                                    idx_existente,
                                    'status'
                                ] = 'aberta'

                                st.session_state.mesas.loc[
                                    idx_existente,
                                    'garcom'
                                ] = garcom_selecionado

                                st.session_state.mesas.loc[
                                    idx_existente,
                                    'qtd_clientes'
                                ] = qtd_clientes

                                st.session_state.mesas.loc[
                                    idx_existente,
                                    'aberto_em'
                                ] = datetime.now().strftime(
                                    "%d/%m/%Y %H:%M:%S"
                                )

                                st.session_state.mesas.loc[
                                    idx_existente,
                                    'fechado_em'
                                ] = ''

                                st.session_state.mesas.loc[
                                    idx_existente,
                                    'valor_total'
                                ] = 0.0

                                st.session_state.mesas.loc[
                                    idx_existente,
                                    'valor_pedidos'
                                ] = 0.0

                                st.session_state.mesas.loc[
                                    idx_existente,
                                    'valor_10'
                                ] = 0.0

                                st.session_state.mesas.loc[
                                    idx_existente,
                                    'valor_com_desconto'
                                ] = 0.0

                                st.session_state.mesas.loc[
                                    idx_existente,
                                    'ticket_medio'
                                ] = 0.0

                                st.session_state.mesas.loc[
                                    idx_existente,
                                    'cover'
                                ] = 0.0

                                st.session_state.mesas.loc[
                                    idx_existente,
                                    'incluir_10'
                                ] = False

                                st.session_state.mesas.loc[
                                    idx_existente,
                                    'desconto_valor'
                                ] = 0.0

                                st.session_state.mesas.loc[
                                    idx_existente,
                                    'id_venda_caixa'
                                ] = ''

                                resetar_estado_mesa(novo_id)

                                if salvar_mesas(
                                    st.session_state.mesas
                                ):

                                    st.session_state.pedidos = (
                                        st.session_state.pedidos[
                                            st.session_state.pedidos[
                                                'id_mesa'
                                            ] != novo_id
                                        ]
                                    )

                                    salvar_pedidos(
                                        st.session_state.pedidos
                                    )

                                    time.sleep(0.3)
                                    st.rerun()

                            else:

                                st.error(
                                    f"❌ Mesa {novo_id} já está aberta!"
                                )

                        else:

                            nova_mesa = pd.DataFrame([{
                                'id_mesa': novo_id,
                                'status': 'aberta',
                                'garcom': garcom_selecionado,
                                'qtd_clientes': qtd_clientes,
                                'aberto_em': datetime.now().strftime(
                                    "%d/%m/%Y %H:%M:%S"
                                ),
                                'fechado_em': '',
                                'valor_pedidos': 0.0,
                                'valor_10': 0.0,
                                'valor_total': 0.0,
                                'valor_com_desconto': 0.0,
                                'ticket_medio': 0.0,
                                'cover': 0.0,
                                'incluir_10': False,
                                'desconto_valor': 0.0,
                                'id_venda_caixa': ''
                            }])

                            st.session_state.mesas = pd.concat(
                                [
                                    st.session_state.mesas,
                                    nova_mesa
                                ],
                                ignore_index=True
                            )

                            resetar_estado_mesa(novo_id)

                            if salvar_mesas(
                                st.session_state.mesas
                            ):

                                st.session_state.pedidos = (
                                    st.session_state.pedidos[
                                        st.session_state.pedidos[
                                            'id_mesa'
                                        ] != novo_id
                                    ]
                                )

                                salvar_pedidos(
                                    st.session_state.pedidos
                                )

                                time.sleep(0.3)
                                st.rerun()

            else:

                st.error(
                    f"❌ Limite máximo de {max_mesas} mesas abertas atingido!"
                )

        with col_buscar:

            mesas_disponiveis = (
                ["Todas"] +
                df_abertas['id_mesa'].tolist()
            )

            mesa_busca = st.selectbox(
                "🔍 Buscar:",
                mesas_disponiveis,
                key="mesa_busca_select"
            )

            if mesa_busca == "Todas":
                df_filtrado = df_abertas.copy()
            else:
                df_filtrado = df_abertas[
                    df_abertas['id_mesa'] == mesa_busca
                ].copy()

    if 'df_filtrado' not in locals():
        df_filtrado = df_abertas.copy()

    if not df_filtrado.empty:

        df_filtrado = df_filtrado.sort_values('id_mesa')

        num_colunas = 3
        mesas_list = df_filtrado.to_dict('records')

        for i in range(0, len(mesas_list), num_colunas):

            cols = st.columns(num_colunas)

            for idx, row in enumerate(
                mesas_list[i:i + num_colunas]
            ):

                with cols[idx]:

                    with st.container():

                        st.session_state.mesas = atualizar_valor_mesa(
                            row['id_mesa'],
                            st.session_state.mesas,
                            st.session_state.pedidos
                        )

                        mesa_atual = st.session_state.mesas[
                            st.session_state.mesas['id_mesa'] == row['id_mesa']
                        ].iloc[0]

                        card_mesa(mesa_atual)

                        col_acao1, col_acao2 = st.columns(2)

                        with col_acao1:

                            if st.button(
                                "✏️ Editar",
                                key=f"editar_{row['id_mesa']}",
                                use_container_width=True
                            ):

                                st.session_state.editar_data[
                                    row['id_mesa']
                                ] = {
                                    'garcom': mesa_atual['garcom'],
                                    'clientes': mesa_atual['qtd_clientes'],
                                    'cover': mesa_atual.get(
                                        'cover',
                                        0.0
                                    ),
                                    'valor': mesa_atual['valor_total'],
                                    'incluir_10': mesa_atual.get(
                                        'incluir_10',
                                        False
                                    )
                                }

                                st.rerun()

                        with col_acao2:

                            if st.button(
                                "🧾 Fechar",
                                key=f"fechar_{row['id_mesa']}",
                                use_container_width=True
                            ):

                                st.session_state.fechar_mesa = row['id_mesa']
                                st.rerun()

                        if st.session_state.editar_data.get(
                            row['id_mesa']
                        ):

                            st.divider()
                            st.markdown("**✏️ Editar Mesa**")

                            edit_data = st.session_state.editar_data[
                                row['id_mesa']
                            ]

                            incluir_10_atual = edit_data.get(
                                'incluir_10',
                                False
                            )

                            col_edit1, col_edit2 = st.columns(2)

                            with col_edit1:

                                funcionarios = (
                                    st.session_state.funcionarios
                                )

                                nomes_funcionarios = [
                                    f.get('nome', '')
                                    for f in funcionarios
                                    if f.get('cargo') == 'Garçom'
                                ]

                                novo_garcom = st.selectbox(
                                    "Garçom:",
                                    [""] + nomes_funcionarios,
                                    index=(
                                        0
                                        if edit_data['garcom']
                                        not in nomes_funcionarios
                                        else nomes_funcionarios.index(
                                            edit_data['garcom']
                                        ) + 1
                                    ),
                                    key=f"edit_garcom_select_{row['id_mesa']}",
                                    format_func=lambda x:
                                    x if x else "Selecione um garçom..."
                                )

                                novos_clientes = st.number_input(
                                    "Quantidade de Clientes:",
                                    min_value=0,
                                    step=1,
                                    value=int(edit_data['clientes']),
                                    key=f"edit_clientes_{row['id_mesa']}"
                                )

                            with col_edit2:

                                novo_cover = st.number_input(
                                    "Cover (R$):",
                                    min_value=0.0,
                                    step=0.01,
                                    value=float(edit_data['cover']),
                                    key=f"edit_cover_{row['id_mesa']}"
                                )

                                incluir_10_edit = st.radio(
                                    "10% Garçom",
                                    ["Não", "Sim"],
                                    index=(
                                        0
                                        if not incluir_10_atual
                                        else 1
                                    ),
                                    key=f"edit_radio_10_{row['id_mesa']}",
                                    horizontal=True
                                )

                                incluir_10_flag = (
                                    incluir_10_edit == "Sim"
                                )

                                pedidos_mesa = (
                                    filtrar_pedidos_por_sessao(
                                        row['id_mesa'],
                                        st.session_state.pedidos,
                                        mesa_atual['aberto_em'],
                                        datetime.now().strftime(
                                            "%d/%m/%Y %H:%M:%S"
                                        )
                                    )
                                )

                                subtotal = (
                                    pedidos_mesa["subtotal"].sum()
                                    if not pedidos_mesa.empty
                                    else 0
                                )

                                valor_com_10 = (
                                    subtotal * 1.10
                                    if incluir_10_flag
                                    else subtotal
                                )

                                cover_total_edit = (
                                    novo_cover * novos_clientes
                                )

                            col_edit_btn1, col_edit_btn2 = st.columns(2)

                            with col_edit_btn1:

                                if st.button(
                                    "💾 Salvar",
                                    key=f"salvar_edit_{row['id_mesa']}",
                                    use_container_width=True
                                ):

                                    idx_mesa = st.session_state.mesas[
                                        st.session_state.mesas[
                                            'id_mesa'
                                        ] == row['id_mesa']
                                    ].index

                                    if not idx_mesa.empty:

                                        idx_mesa = idx_mesa[0]

                                        st.session_state.mesas.loc[
                                            idx_mesa,
                                            'garcom'
                                        ] = novo_garcom

                                        st.session_state.mesas.loc[
                                            idx_mesa,
                                            'qtd_clientes'
                                        ] = novos_clientes

                                        st.session_state.mesas.loc[
                                            idx_mesa,
                                            'cover'
                                        ] = novo_cover

                                        st.session_state.mesas.loc[
                                            idx_mesa,
                                            'incluir_10'
                                        ] = incluir_10_flag

                                        st.session_state.mesas = (
                                            atualizar_valor_mesa(
                                                row['id_mesa'],
                                                st.session_state.mesas,
                                                st.session_state.pedidos
                                            )
                                        )

                                        if salvar_mesas(
                                            st.session_state.mesas
                                        ):

                                            del st.session_state.editar_data[
                                                row['id_mesa']
                                            ]

                                            time.sleep(0.3)
                                            st.rerun()

                            with col_edit_btn2:

                                if st.button(
                                    "❌ Cancelar",
                                    key=f"cancel_edit_{row['id_mesa']}",
                                    use_container_width=True
                                ):

                                    if row['id_mesa'] in (
                                        st.session_state.editar_data
                                    ):

                                        del st.session_state.editar_data[
                                            row['id_mesa']
                                        ]

                                    st.rerun()

                        if st.session_state.fechar_mesa == row['id_mesa']:

                            caixa_aberto = st.session_state.get(
                                'caixa_aberto',
                                False
                            )

                            if not caixa_aberto:

                                st.error(
                                    "❌ Caixa não está aberto. "
                                    "Abra o caixa antes de fechar a mesa."
                                )

                            else:

                                pedidos_abertos_mesa = (
                                    st.session_state.pedidos[
                                        (
                                            st.session_state.pedidos[
                                                'id_mesa'
                                            ].astype(str).str.strip()
                                            ==
                                            str(row['id_mesa']).strip()
                                        )
                                        &
                                        (
                                            st.session_state.pedidos[
                                                'status'
                                            ] == 'enviado'
                                        )
                                    ]
                                )

                                if not pedidos_abertos_mesa.empty:

                                    st.error(
                                        f"❌ Não é possível fechar a mesa "
                                        f"{row['id_mesa']} enquanto houver "
                                        f"pedidos em aberto!"
                                    )

                                    st.warning(
                                        f"⚠️ Existem "
                                        f"{len(pedidos_abertos_mesa)} "
                                        f"pedido(s) em aberto para esta mesa"
                                    )

                                    if st.button(
                                        "🔄 Atualizar",
                                        key=f"atualizar_fechar_{row['id_mesa']}"
                                    ):
                                        st.rerun()

                                else:

                                    fechado_em = datetime.now().strftime(
                                        "%d/%m/%Y %H:%M:%S"
                                    )

                                    pedidos_mesa = (
                                        filtrar_pedidos_por_sessao(
                                            row['id_mesa'],
                                            st.session_state.pedidos,
                                            mesa_atual['aberto_em'],
                                            fechado_em
                                        )
                                    )

                                    if (
                                        pedidos_mesa.empty
                                        and mesa_atual.get(
                                            'cover',
                                            0.0
                                        ) == 0
                                    ):

                                        idx_mesa = st.session_state.mesas[
                                            st.session_state.mesas[
                                                'id_mesa'
                                            ] == row['id_mesa']
                                        ].index

                                        if not idx_mesa.empty:

                                            idx_mesa = idx_mesa[0]

                                            st.session_state.mesas.loc[
                                                idx_mesa,
                                                'status'
                                            ] = 'fechada'

                                            st.session_state.mesas.loc[
                                                idx_mesa,
                                                'fechado_em'
                                            ] = datetime.now().strftime(
                                                "%d/%m/%Y %H:%M:%S"
                                            )

                                            salvar_mesas(
                                                st.session_state.mesas
                                            )

                                            resetar_estado_mesa(
                                                row['id_mesa']
                                            )

                                            st.session_state.fechar_mesa = None

                                            st.success(
                                                f"✅ Mesa {row['id_mesa']} "
                                                f"liberada "
                                                f"(sem pedidos e sem cover)."
                                            )

                                            time.sleep(0.3)
                                            st.rerun()

                                    if (
                                        not pedidos_mesa.empty
                                        and 'status'
                                        in pedidos_mesa.columns
                                    ):

                                        pedidos_fechados = (
                                            pedidos_mesa[
                                                pedidos_mesa['status']
                                                == 'fechado'
                                            ].copy()
                                        )

                                    else:

                                        pedidos_fechados = pd.DataFrame()

                                    tem_pedidos = (
                                        not pedidos_fechados.empty
                                    )

                                    incluir_10 = mesa_atual.get(
                                        'incluir_10',
                                        False
                                    )

                                    valor_pedidos = (
                                        pedidos_fechados[
                                            'subtotal'
                                        ].sum()
                                        if not pedidos_fechados.empty
                                        else 0.0
                                    )

                                    valor_com_desconto = (
                                        pedidos_fechados[
                                            'valor_com_desconto'
                                        ].fillna(
                                            pedidos_fechados[
                                                'subtotal'
                                            ]
                                        ).sum()
                                        if not pedidos_fechados.empty
                                        else 0.0
                                    )

                                    desconto_valor = (
                                        valor_pedidos
                                        - valor_com_desconto
                                    )

                                    cover_unitario = mesa_atual.get(
                                        'cover',
                                        0.0
                                    )

                                    qtd_clientes = mesa_atual[
                                        'qtd_clientes'
                                    ]

                                    cover_total = (
                                        cover_unitario
                                        * qtd_clientes
                                    )

                                    taxa_garcom = (
                                        valor_com_desconto * 0.10
                                        if incluir_10
                                        and valor_com_desconto > 0
                                        else 0
                                    )

                                    valor_total = (
                                        valor_com_desconto
                                        + cover_total
                                        + taxa_garcom
                                    )

                                    id_venda_existente = obter_id_venda_mesa(
                                        row['id_mesa'],
                                        mesa_atual['aberto_em']
                                    )

                                    st.divider()

                                    if id_venda_existente:
                                        st.info(
                                            f"🔁 Reabertura — venda original "
                                            f"será substituída: `{id_venda_existente}`"
                                        )

                                    metodo_pagamento = st.selectbox(
                                        "Método de Pagamento:",
                                        [
                                            "Pix",
                                            "Débito",
                                            "Crédito",
                                            "Dinheiro",
                                            "Voucher",
                                            "Fiado"
                                        ],
                                        key=f"metodo_pagamento_{row['id_mesa']}"
                                    )

                                    cliente_fiado = ""

                                    if metodo_pagamento == "Fiado":

                                        cliente_fiado = st.text_input(
                                            "👤 Nome do Cliente "
                                            "(identificação):",
                                            placeholder="Ex: João Silva",
                                            key=f"cliente_fiado_{row['id_mesa']}"
                                        )

                                    col_fechar_ok, col_fechar_cancel = (
                                        st.columns(2)
                                    )

                                    with col_fechar_ok:

                                        if st.button(
                                            "✅ FECHAR",
                                            key=f"confirm_fechar_{row['id_mesa']}",
                                            use_container_width=True
                                        ):

                                            idx_mesa = st.session_state.mesas[
                                                st.session_state.mesas[
                                                    'id_mesa'
                                                ] == row['id_mesa']
                                            ].index

                                            if not idx_mesa.empty:

                                                idx_mesa = idx_mesa[0]

                                                fechado_em = (
                                                    datetime.now().strftime(
                                                        "%d/%m/%Y %H:%M:%S"
                                                    )
                                                )

                                                st.session_state.mesas.loc[
                                                    idx_mesa,
                                                    'fechado_em'
                                                ] = fechado_em

                                                st.session_state.mesas.loc[
                                                    idx_mesa,
                                                    'status'
                                                ] = 'fechada'

                                                st.session_state.mesas.loc[
                                                    idx_mesa,
                                                    'valor_pedidos'
                                                ] = valor_pedidos

                                                st.session_state.mesas.loc[
                                                    idx_mesa,
                                                    'valor_com_desconto'
                                                ] = valor_com_desconto

                                                st.session_state.mesas.loc[
                                                    idx_mesa,
                                                    'desconto_valor'
                                                ] = desconto_valor

                                                st.session_state.mesas.loc[
                                                    idx_mesa,
                                                    'valor_10'
                                                ] = taxa_garcom

                                                st.session_state.mesas.loc[
                                                    idx_mesa,
                                                    'valor_total'
                                                ] = valor_total

                                                st.session_state.mesas.loc[
                                                    idx_mesa,
                                                    'ticket_medio'
                                                ] = (
                                                    round(
                                                        valor_total
                                                        / qtd_clientes,
                                                        2
                                                    )
                                                    if qtd_clientes > 0
                                                    else 0.0
                                                )

                                                if salvar_mesas(
                                                    st.session_state.mesas
                                                ):

                                                    mesa_historico = {
                                                        'id_mesa': row['id_mesa'],
                                                        'garcom': mesa_atual['garcom'],
                                                        'qtd_clientes': mesa_atual['qtd_clientes'],
                                                        'aberto_em': mesa_atual['aberto_em'],
                                                        'fechado_em': fechado_em,
                                                        'valor_pedidos': valor_pedidos,
                                                        'valor_total': valor_total,
                                                        'valor_com_desconto': valor_com_desconto,
                                                        'desconto_valor': desconto_valor,
                                                        'cover': cover_unitario,
                                                        'valor_10': taxa_garcom,
                                                        'incluir_10': incluir_10
                                                    }

                                                    adicionar_historico_mesa(
                                                        mesa_historico
                                                    )

                                                    if metodo_pagamento == "Fiado":

                                                        if not cliente_fiado.strip():

                                                            st.error(
                                                                "⚠️ Informe "
                                                                "o nome do "
                                                                "cliente para "
                                                                "fiado."
                                                            )

                                                            st.stop()

                                                        descricao = (
                                                            f"FIADO - {cliente_fiado} - "
                                                            f"Mesa {row['id_mesa']} - "
                                                            f"{mesa_atual['garcom']}"
                                                        )

                                                    else:

                                                        descricao = (
                                                            f"Mesa {row['id_mesa']} - "
                                                            f"{mesa_atual['garcom']}"
                                                        )

                                                    if id_venda_existente:

                                                        substituir_venda_no_caixa(
                                                            id_venda_existente,
                                                            'Mesa',
                                                            valor_total,
                                                            metodo_pagamento,
                                                            descricao
                                                        )

                                                    else:

                                                        _, id_venda_novo = registrar_venda_no_caixa(
                                                            'Mesa',
                                                            valor_total,
                                                            metodo_pagamento,
                                                            descricao
                                                        )

                                                        st.session_state.mesas.loc[
                                                            idx_mesa,
                                                            'id_venda_caixa'
                                                        ] = id_venda_novo

                                                        salvar_mesas(
                                                            st.session_state.mesas
                                                        )

                                                    resetar_estado_mesa(
                                                        row['id_mesa']
                                                    )

                                                    st.session_state.fechar_mesa = None
                                                    st.session_state.comanda_mesa = row['id_mesa']

                                                    st.success(
                                                        f"✅ Mesa "
                                                        f"{row['id_mesa']} "
                                                        f"fechada! Total: "
                                                        f"R$ {valor_total:.2f}"
                                                    )

                                                    time.sleep(0.3)
                                                    st.rerun()

                                    with col_fechar_cancel:

                                        if st.button(
                                            "❌ CANCELAR",
                                            key=f"cancel_fechar_{row['id_mesa']}",
                                            use_container_width=True
                                        ):

                                            st.session_state.fechar_mesa = None
                                            st.rerun()

        st.divider()
        st.subheader("📋 Gerenciar Mesa")

        renderizar_estilo_cards()

        mesa_itens = st.selectbox(
            "Mesa:",
            df_filtrado['id_mesa'].tolist(),
            key="mesa_itens_select"
        )

        mesa_info = st.session_state.mesas[
            st.session_state.mesas['id_mesa'] == mesa_itens
        ].iloc[0]

        pedidos_mesa = filtrar_pedidos_por_sessao(
            mesa_itens,
            st.session_state.pedidos,
            mesa_info['aberto_em'],
            datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        )

        if pedidos_mesa.empty or 'status' not in pedidos_mesa.columns:
            st.info("Nenhum item encontrado para esta mesa.")
        else:
            pedidos_mesa = pedidos_mesa[
                pedidos_mesa['status'] != 'cancelado'
            ]

        if not pedidos_mesa.empty:

            pedidos_ids = (
                pedidos_mesa['id_pedido']
                .drop_duplicates()
                .tolist()
            )

            pedido_selecionado = st.selectbox(
                "Pedido:",
                pedidos_ids,
                key=f"pedido_itens_{mesa_itens}"
            )

            itens_pedido = pedidos_mesa[
                pedidos_mesa['id_pedido'] == pedido_selecionado
            ].copy()

            st.html(
                renderizar_cabecalho_pedido(
                    pedido_selecionado,
                    mesa_itens,
                    len(itens_pedido)
                )
            )

            total_itens = len(itens_pedido)

            valor_pedidos = pd.to_numeric(
                itens_pedido['subtotal'],
                errors='coerce'
            ).fillna(0).sum()

            valor_com_desconto = pd.to_numeric(
                itens_pedido.get(
                    'valor_com_desconto',
                    itens_pedido['subtotal']
                ),
                errors='coerce'
            ).fillna(
                pd.to_numeric(
                    itens_pedido['subtotal'],
                    errors='coerce'
                ).fillna(0)
            ).sum()

            desconto_valor = max(
                0,
                valor_pedidos - valor_com_desconto
            )

            st.html(
                renderizar_resumo_mesa(
                    total_itens,
                    valor_pedidos,
                    desconto_valor,
                    valor_com_desconto
                )
            )

            selecionados = []

            for _, item in itens_pedido.iterrows():

                cod_item = str(item['cod_item'])

                if bool(item.get('cortesia', False)):
                    estado = 'cortesia'
                elif str(item.get('desconto_tipo', '')) == 'devolucao':
                    estado = 'devolucao'
                elif float(item.get('desconto_item', 0) or 0) > 0:
                    estado = 'desconto'
                else:
                    estado = ''

                with st.container(border=True):

                    col_check, col_card = st.columns([0.08, 0.92])

                    with col_check:

                        if st.checkbox(
                            "",
                            key=f"selecionar_item_{pedido_selecionado}_{cod_item}"
                        ):
                            selecionados.append(cod_item)

                    with col_card:

                        st.html(
                            renderizar_card_item(
                                nome_produto=item['nome_prod'],
                                cod_item=cod_item,
                                quantidade=item['quantidade'],
                                preco_unitario=item['preco_unitario'],
                                subtotal=item['subtotal'],
                                valor_com_desconto=item.get(
                                    'valor_com_desconto',
                                    item['subtotal']
                                ),
                                estado=estado
                            )
                        )

            st.markdown(
                f"""
                <div class="gerenciar-selecao">
                    {len(selecionados)} item(ns) selecionado(s)
                </div>
                """,
                unsafe_allow_html=True
            )

            if selecionados:

                itens_selecionados = itens_pedido[
                    itens_pedido['cod_item'].astype(str).isin(selecionados)
                ].copy()

                estados_selecionados = []

                for _, item in itens_selecionados.iterrows():

                    if bool(item.get('cortesia', False)):
                        estados_selecionados.append('cortesia')
                    elif str(item.get('desconto_tipo', '')) == 'devolucao':
                        estados_selecionados.append('devolucao')
                    elif float(item.get('desconto_item', 0) or 0) > 0:
                        estados_selecionados.append('desconto')
                    else:
                        estados_selecionados.append('')

                st.html(
                    renderizar_titulo_acoes(len(selecionados))
                )

                col_acao1, col_acao2, col_acao3, col_acao4 = st.columns(4)

                with col_acao1:

                    if all(
                        estado == 'cortesia'
                        for estado in estados_selecionados
                    ):

                        if st.button(
                            "↩ Retirar cortesia",
                            key=f"retirar_cortesia_sel_{pedido_selecionado}",
                            use_container_width=True
                        ):

                            for cod_item in selecionados:
                                st.session_state.pedidos = remover_cortesia_item(
                                    st.session_state.pedidos,
                                    pedido_selecionado,
                                    cod_item
                                )

                            salvar_pedidos(st.session_state.pedidos)

                            for cod_item in selecionados:

                                filtro = (
                                    (
                                        st.session_state.pedidos['id_pedido'].astype(str)
                                        == str(pedido_selecionado)
                                    )
                                    &
                                    (
                                        st.session_state.pedidos['cod_item'].astype(str)
                                        == str(cod_item)
                                    )
                                )

                                if filtro.any():
                                    sincronizar_historico_pedido(
                                        st.session_state.pedidos[filtro].iloc[0].to_dict()
                                    )

                            st.session_state.mesas = atualizar_valor_mesa(
                                mesa_itens,
                                st.session_state.mesas,
                                st.session_state.pedidos
                            )

                            salvar_mesas(st.session_state.mesas)
                            st.rerun()

                    else:

                        if st.button(
                            "🎁 Cortesia",
                            key=f"cortesia_sel_{pedido_selecionado}",
                            use_container_width=True
                        ):

                            for cod_item in selecionados:
                                st.session_state.pedidos = aplicar_cortesia_item(
                                    st.session_state.pedidos,
                                    pedido_selecionado,
                                    cod_item
                                )

                            salvar_pedidos(st.session_state.pedidos)

                            for cod_item in selecionados:

                                filtro = (
                                    (
                                        st.session_state.pedidos['id_pedido'].astype(str)
                                        == str(pedido_selecionado)
                                    )
                                    &
                                    (
                                        st.session_state.pedidos['cod_item'].astype(str)
                                        == str(cod_item)
                                    )
                                )

                                if filtro.any():
                                    sincronizar_historico_pedido(
                                        st.session_state.pedidos[filtro].iloc[0].to_dict()
                                    )

                            st.session_state.mesas = atualizar_valor_mesa(
                                mesa_itens,
                                st.session_state.mesas,
                                st.session_state.pedidos
                            )

                            salvar_mesas(st.session_state.mesas)
                            st.rerun()

                with col_acao2:

                    if all(
                        estado == 'devolucao'
                        for estado in estados_selecionados
                    ):

                        if st.button(
                            "↩ Retirar devolução",
                            key=f"retirar_devolucao_sel_{pedido_selecionado}",
                            use_container_width=True
                        ):

                            for cod_item in selecionados:
                                st.session_state.pedidos = remover_devolucao_item(
                                    st.session_state.pedidos,
                                    pedido_selecionado,
                                    cod_item
                                )

                            salvar_pedidos(st.session_state.pedidos)

                            for cod_item in selecionados:

                                filtro = (
                                    (
                                        st.session_state.pedidos['id_pedido'].astype(str)
                                        == str(pedido_selecionado)
                                    )
                                    &
                                    (
                                        st.session_state.pedidos['cod_item'].astype(str)
                                        == str(cod_item)
                                    )
                                )

                                if filtro.any():
                                    sincronizar_historico_pedido(
                                        st.session_state.pedidos[filtro].iloc[0].to_dict()
                                    )

                            st.session_state.mesas = atualizar_valor_mesa(
                                mesa_itens,
                                st.session_state.mesas,
                                st.session_state.pedidos
                            )

                            salvar_mesas(st.session_state.mesas)
                            st.rerun()

                    else:

                        if st.button(
                            "↩ Devolução",
                            key=f"devolucao_sel_{pedido_selecionado}",
                            use_container_width=True
                        ):

                            for cod_item in selecionados:
                                st.session_state.pedidos = aplicar_devolucao_item(
                                    st.session_state.pedidos,
                                    pedido_selecionado,
                                    cod_item
                                )

                            salvar_pedidos(st.session_state.pedidos)

                            for cod_item in selecionados:

                                filtro = (
                                    (
                                        st.session_state.pedidos['id_pedido'].astype(str)
                                        == str(pedido_selecionado)
                                    )
                                    &
                                    (
                                        st.session_state.pedidos['cod_item'].astype(str)
                                        == str(cod_item)
                                    )
                                )

                                if filtro.any():
                                    sincronizar_historico_pedido(
                                        st.session_state.pedidos[filtro].iloc[0].to_dict()
                                    )

                            st.session_state.mesas = atualizar_valor_mesa(
                                mesa_itens,
                                st.session_state.mesas,
                                st.session_state.pedidos
                            )

                            salvar_mesas(st.session_state.mesas)
                            st.rerun()

                with col_acao3:

                    if all(
                        estado == 'desconto'
                        for estado in estados_selecionados
                    ):

                        if st.button(
                            "↩ Retirar desconto",
                            key=f"retirar_desconto_sel_{pedido_selecionado}",
                            use_container_width=True
                        ):

                            for cod_item in selecionados:
                                st.session_state.pedidos = remover_desconto_item(
                                    st.session_state.pedidos,
                                    pedido_selecionado,
                                    cod_item
                                )

                            salvar_pedidos(st.session_state.pedidos)

                            for cod_item in selecionados:

                                filtro = (
                                    (
                                        st.session_state.pedidos['id_pedido'].astype(str)
                                        == str(pedido_selecionado)
                                    )
                                    &
                                    (
                                        st.session_state.pedidos['cod_item'].astype(str)
                                        == str(cod_item)
                                    )
                                )

                                if filtro.any():
                                    sincronizar_historico_pedido(
                                        st.session_state.pedidos[filtro].iloc[0].to_dict()
                                    )

                            st.session_state.mesas = atualizar_valor_mesa(
                                mesa_itens,
                                st.session_state.mesas,
                                st.session_state.pedidos
                            )

                            salvar_mesas(st.session_state.mesas)
                            st.rerun()

                    else:

                        with st.popover(
                            "✂️ Desconto",
                            use_container_width=True
                        ):

                            tipo_desconto = st.radio(
                                "Tipo:",
                                ["Percentual (%)", "Valor Fixo (R$)"],
                                horizontal=True,
                                key=f"tipo_desconto_sel_{pedido_selecionado}"
                            )

                            valor_base = pd.to_numeric(
                                itens_selecionados['subtotal'],
                                errors='coerce'
                            ).fillna(0).sum()

                            if tipo_desconto == "Percentual (%)":

                                desconto = st.number_input(
                                    "%",
                                    min_value=0.0,
                                    max_value=100.0,
                                    value=10.0,
                                    step=1.0,
                                    key=f"pct_desconto_sel_{pedido_selecionado}"
                                )

                                valor_final = valor_base * (1 - desconto / 100)

                                st.caption(
                                    f"💰 Final: R$ {valor_final:.2f}"
                                )

                                if st.button(
                                    "Aplicar %",
                                    key=f"ap_pct_sel_{pedido_selecionado}",
                                    use_container_width=True
                                ):

                                    if desconto > 0:

                                        for cod_item in selecionados:
                                            st.session_state.pedidos = aplicar_desconto_item(
                                                st.session_state.pedidos,
                                                pedido_selecionado,
                                                cod_item,
                                                desconto,
                                                tipo='percentual'
                                            )

                                        salvar_pedidos(st.session_state.pedidos)

                                        for cod_item in selecionados:

                                            filtro = (
                                                (
                                                    st.session_state.pedidos['id_pedido'].astype(str)
                                                    == str(pedido_selecionado)
                                                )
                                                &
                                                (
                                                    st.session_state.pedidos['cod_item'].astype(str)
                                                    == str(cod_item)
                                                )
                                            )

                                            if filtro.any():
                                                sincronizar_historico_pedido(
                                                    st.session_state.pedidos[filtro].iloc[0].to_dict()
                                                )

                                        st.session_state.mesas = atualizar_valor_mesa(
                                            mesa_itens,
                                            st.session_state.mesas,
                                            st.session_state.pedidos
                                        )

                                        salvar_mesas(st.session_state.mesas)
                                        st.rerun()

                            else:

                                desconto = st.number_input(
                                    "R$",
                                    min_value=0.0,
                                    max_value=float(valor_base),
                                    value=min(5.00, float(valor_base)),
                                    step=0.50,
                                    key=f"fix_desconto_sel_{pedido_selecionado}"
                                )

                                valor_final = valor_base - desconto

                                st.caption(
                                    f"💰 Final: R$ {valor_final:.2f}"
                                )

                                if st.button(
                                    "Aplicar R$",
                                    key=f"ap_fix_sel_{pedido_selecionado}",
                                    use_container_width=True
                                ):

                                    if desconto > 0:

                                        for cod_item in selecionados:
                                            st.session_state.pedidos = aplicar_desconto_item(
                                                st.session_state.pedidos,
                                                pedido_selecionado,
                                                cod_item,
                                                desconto,
                                                tipo='valor'
                                            )

                                        salvar_pedidos(st.session_state.pedidos)

                                        for cod_item in selecionados:

                                            filtro = (
                                                (
                                                    st.session_state.pedidos['id_pedido'].astype(str)
                                                    == str(pedido_selecionado)
                                                )
                                                &
                                                (
                                                    st.session_state.pedidos['cod_item'].astype(str)
                                                    == str(cod_item)
                                                )
                                            )

                                            if filtro.any():
                                                sincronizar_historico_pedido(
                                                    st.session_state.pedidos[filtro].iloc[0].to_dict()
                                                )

                                        st.session_state.mesas = atualizar_valor_mesa(
                                            mesa_itens,
                                            st.session_state.mesas,
                                            st.session_state.pedidos
                                        )

                                        salvar_mesas(st.session_state.mesas)
                                        st.rerun()

                with col_acao4:

                    if len(selecionados) == 1:

                        with st.popover(
                            "➕",
                            use_container_width=True
                        ):

                            item_origem = itens_selecionados.iloc[0]

                            qtd_repetir = st.number_input(
                                "Quantidade:",
                                min_value=1,
                                step=1,
                                value=int(item_origem['quantidade']),
                                key=f"qtd_repetir_{pedido_selecionado}_{item_origem['cod_item']}"
                            )

                            st.caption(
                                f"🔁 {qtd_repetir}x {item_origem['nome_prod']}"
                            )

                            if st.button(
                                "Adicionar",
                                key=f"btn_repetir_{pedido_selecionado}_{item_origem['cod_item']}",
                                use_container_width=True,
                                type="primary"
                            ):

                                novo_id_pedido = gerar_id_pedido(st.session_state.pedidos)
                                agora_repetir = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

                                for _ in range(int(qtd_repetir)):

                                    novo_cod_item = gerar_cod_item()

                                    novo_pedido = {
                                        'id_pedido': novo_id_pedido,
                                        'id_item': 1,
                                        'cod_item': novo_cod_item,
                                        'id_mesa': mesa_itens,
                                        'cod_prod': item_origem.get('cod_prod', ''),
                                        'nome_prod': item_origem.get('nome_prod', ''),
                                        'quantidade': 1,
                                        'preco_unitario': item_origem.get('preco_unitario', 0.0),
                                        'preco_final': item_origem.get('preco_final', 0.0),
                                        'desconto_tipo': item_origem.get('desconto_tipo', 'Nenhum'),
                                        'desconto_valor': item_origem.get('desconto_valor', 0.0),
                                        'subtotal': item_origem.get('preco_final', 0.0),
                                        'valor_com_desconto': item_origem.get('preco_final', 0.0),
                                        'observacao': item_origem.get('observacao', ''),
                                        'criado_em': agora_repetir,
                                        'status': 'enviado',
                                        'categoria': item_origem.get('categoria', ''),
                                        'tipo_venda': item_origem.get('tipo_venda', 'menu'),
                                        'item_individual': f"{item_origem.get('cod_prod', '')}_{novo_cod_item}",
                                        'origem_venda': item_origem.get('origem_venda', 'mesa'),
                                        'taxa_entrega': item_origem.get('taxa_entrega', 0.0),
                                        'taxa_embalagem': item_origem.get('taxa_embalagem', 0.0),
                                        'id_cliente': item_origem.get('id_cliente', ''),
                                        'metodo_pagamento': item_origem.get('metodo_pagamento', '')
                                    }

                                    st.session_state.pedidos = pd.concat(
                                        [st.session_state.pedidos, pd.DataFrame([novo_pedido])],
                                        ignore_index=True
                                    )

                                    sincronizar_historico_pedido(novo_pedido)

                                salvar_pedidos(st.session_state.pedidos)

                                st.session_state.mesas = atualizar_valor_mesa(
                                    mesa_itens,
                                    st.session_state.mesas,
                                    st.session_state.pedidos
                                )

                                salvar_mesas(st.session_state.mesas)

                                st.success(f"✅ {qtd_repetir}x {item_origem['nome_prod']} adicionado!")
                                time.sleep(0.5)
                                st.rerun()

        else:

            st.info("💤 Nenhuma mesa aberta no momento.")
            st.caption(
                "Clique em 'Abrir Mesa' para criar uma nova mesa."
    )
            
with aba2:

    df_historico = st.session_state.mesas[
        st.session_state.mesas['status'] == 'fechada'
    ].copy()

    if not df_historico.empty:

        total_fechadas = len(df_historico)

        valor_total_historico = (
            df_historico['valor_total'].sum()
        )

        valor_com_desconto_historico = (
            df_historico['valor_com_desconto'].sum()
            if 'valor_com_desconto' in df_historico.columns
            else valor_total_historico
        )

        ticket_medio_historico = (
            df_historico['ticket_medio'].mean()
            if not df_historico.empty
            else 0
        )

        col_hist1, col_hist2, col_hist3 = st.columns(3)

        with col_hist1:
            st.metric(
                "Total de Mesas Fechadas",
                total_fechadas
            )

        with col_hist2:
            st.metric(
                "💰 Valor Bruto (R$)",
                f"R$ {valor_total_historico:,.2f}"
            )

        with col_hist3:
            st.metric(
                "🎫 Valor Real (R$)",
                f"R$ {valor_com_desconto_historico:,.2f}"
            )

        st.divider()

        df_exibicao = df_historico[
            [
                'id_mesa',
                'garcom',
                'qtd_clientes',
                'aberto_em',
                'fechado_em',
                'valor_total',
                'valor_com_desconto',
                'cover',
                'ticket_medio'
            ]
        ].copy()

        if 'valor_10' in df_historico.columns:
            df_exibicao['valor_10'] = (
                df_historico['valor_10'].fillna(0)
            )
        else:
            df_exibicao['valor_10'] = 0.0

        if 'desconto_valor' in df_historico.columns:
            df_exibicao['desconto_valor'] = (
                df_historico['desconto_valor']
            )
        else:
            df_exibicao['desconto_valor'] = 0.0

        st.dataframe(
            df_exibicao,
            use_container_width=True,
            hide_index=True
        )

        st.divider()
        st.markdown("**🔓 Reabrir Mesa**")

        mesas_fechadas_ids = df_historico['id_mesa'].tolist()

        mesa_reabrir = st.selectbox(
            "Selecione a mesa para reabrir:",
            mesas_fechadas_ids,
            key="mesa_reabrir_select"
        )

        if st.button(
            "🔓 Reabrir Mesa",
            use_container_width=True,
            type="primary",
            key="btn_reabrir_mesa"
        ):
            st.session_state.reabrir_mesa = mesa_reabrir
            st.rerun()

        if st.session_state.reabrir_mesa == mesa_reabrir:

            st.warning(
                f"⚠️ Confirma a reabertura da mesa **{mesa_reabrir}**?\n\n"
                f"• A mesa voltará ao status **aberta**\n"
                f"• Os valores e pedidos serão mantidos\n"
                f"• Ao fechar novamente, a venda no caixa "
                f"será **substituída**"
            )

            col_conf1, col_conf2 = st.columns(2)

            with col_conf1:
                if st.button(
                    "✅ Confirmar",
                    use_container_width=True,
                    key="confirmar_reabrir_mesa"
                ):
                    st.session_state.mesas, sucesso = reabrir_mesa(
                        st.session_state.mesas,
                        mesa_reabrir
                    )

                    if sucesso:
                        if salvar_mesas(st.session_state.mesas):
                            resetar_estado_mesa(mesa_reabrir)
                            st.session_state.reabrir_mesa = None
                            st.success(
                                f"✅ Mesa {mesa_reabrir} reaberta!"
                            )
                            time.sleep(0.5)
                            st.rerun()
                    else:
                        st.error("❌ Não foi possível reabrir a mesa.")
                        st.session_state.reabrir_mesa = None
                        st.rerun()

            with col_conf2:
                if st.button(
                    "❌ Cancelar",
                    use_container_width=True,
                    key="cancelar_reabrir_mesa"
                ):
                    st.session_state.reabrir_mesa = None
                    st.rerun()

        st.divider()

        if st.button(
            "🗑️ Limpar Histórico",
            use_container_width=True
        ):

            st.warning(
                """
                ⚠️ **ATENÇÃO - CONFIRMAÇÃO NECESSÁRIA**

                Você está prestes a:
                1. **Limpar o histórico de mesas fechadas**
                2. **Manter as mesas abertas intactas**

                ✅ **As mesas abertas continuarão abertas** – apenas o histórico de mesas fechadas será removido.

                Deseja continuar?
                """
            )

            col_conf1, col_conf2 = st.columns(2)

            with col_conf1:

                if st.button(
                    "✅ Sim, limpar histórico",
                    use_container_width=True
                ):

                    st.session_state.mesas = (
                        st.session_state.mesas[
                            st.session_state.mesas['status']
                            == 'aberta'
                        ].copy()
                    )

                    st.session_state.estado_mesa = {}

                    if salvar_mesas(
                        st.session_state.mesas
                    ):

                        st.success(
                            "✅ Histórico limpo com sucesso!"
                        )

                        time.sleep(0.3)
                        st.rerun()

            with col_conf2:

                if st.button(
                    "❌ Cancelar",
                    use_container_width=True
                ):
                    st.rerun()

    else:

        st.info("💤 Nenhuma servida.")


with aba3:

    from utils.db import ler_tabela

    df_hist_mesas = ler_tabela("historico_mesas")

    if df_hist_mesas.empty:
        historico_mesas = []
    else:
        historico_mesas = df_hist_mesas.to_dict(orient="records")

    hoje = datetime.now().strftime("%d/%m/%Y")

    comandas_hoje = [
        m
        for m in historico_mesas
        if m.get('fechado_em', '').startswith(hoje)
    ]

    if comandas_hoje:

        comandas_hoje.sort(
            key=lambda x: x.get('fechado_em', ''),
            reverse=True
        )

        opcoes_comandas = [
            f"{m['id_mesa']} - {m['fechado_em']}"
            for m in comandas_hoje
        ]

        comanda_selecionada = st.selectbox(
            "Selecione a comanda:",
            opcoes_comandas,
            key="comanda_historico_select"
        )

        if comanda_selecionada:

            id_mesa_selecionada = (
                comanda_selecionada.split(" - ")[0]
            )

            candidatos = [
                m
                for m in comandas_hoje
                if m['id_mesa'] == id_mesa_selecionada
            ]

            candidatos.sort(key=lambda x: x.get('fechado_em', ''), reverse=True)

            mesa_historico = candidatos[0]

            mesa_df = pd.DataFrame([
                mesa_historico
            ])

            historico_pedidos = ler_tabela("historico_pedidos")

            pedidos_df = historico_pedidos[
                historico_pedidos[
                    'id_mesa'
                ].astype(str).str.strip()
                ==
                str(id_mesa_selecionada).strip()
            ].copy()

            renderizar_comanda(
                id_mesa_selecionada,
                pedidos_df,
                mesa_df
            )

    else:

        st.info(
            "Nenhuma comanda registrada hoje."
        )

        st.caption(
            "As comandas fechadas hoje aparecerão aqui."
        )