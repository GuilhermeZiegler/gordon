
import os
import pickle
import pandas as pd
import streamlit as st
from datetime import datetime


def gerar_id_pedido(
    pedidos_df=None,
    historico_path="data/historico_pedidos.pkl"
):
    max_pedidos = 0

    if pedidos_df is not None and not pedidos_df.empty:
        if isinstance(pedidos_df, list):
            pedidos_df = pd.DataFrame(pedidos_df)

        if isinstance(pedidos_df, pd.DataFrame) and 'id_pedido' in pedidos_df.columns:
            ids = pedidos_df['id_pedido'].astype(str).str.extract(
                r'PED-(\d+)'
            )[0]

            ids = pd.to_numeric(
                ids,
                errors='coerce'
            ).dropna()

            if not ids.empty:
                max_pedidos = int(ids.max())

    max_historico = 0

    if os.path.exists(historico_path):
        with open(historico_path, 'rb') as f:
            historico = pickle.load(f)

        if isinstance(historico, list):
            historico = pd.DataFrame(historico)

        if isinstance(historico, pd.DataFrame) and not historico.empty:
            if 'id_pedido' in historico.columns:
                ids_historico = historico['id_pedido'].astype(str).str.extract(
                    r'PED-(\d+)'
                )[0]

                ids_historico = pd.to_numeric(
                    ids_historico,
                    errors='coerce'
                ).dropna()

                if not ids_historico.empty:
                    max_historico = int(ids_historico.max())

    proximo = max(max_pedidos, max_historico) + 1

    return f"PED-{proximo:04d}"


def carregar_pkl(caminho, colunas=None):
    if os.path.exists(caminho):
        with open(caminho, 'rb') as f:
            df = pickle.load(f)

        if isinstance(df, list):
            df = pd.DataFrame(df)

        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)

        if 'cod_item' not in df.columns:
            df['cod_item'] = ''

        if 'id_item' not in df.columns:
            df['id_item'] = ''

        if colunas:
            for coluna in colunas:
                if coluna not in df.columns:
                    df[coluna] = ''

        return df

    if colunas:
        return pd.DataFrame(columns=colunas)

    return pd.DataFrame()


def salvar_pkl(df, caminho):
    try:
        os.makedirs(
            os.path.dirname(caminho),
            exist_ok=True
        )

        with open(caminho, 'wb') as f:
            pickle.dump(df, f)

        return True

    except Exception as e:
        st.error(f"Erro ao salvar: {str(e)}")
        return False


def carregar_historico_pedidos_hoje(
    caminho_historico="data/historico_pedidos.pkl",
    colunas=None
):
    df = carregar_pkl(
        caminho_historico,
        colunas
    )

    if df.empty or 'criado_em' not in df.columns:
        return pd.DataFrame(
            columns=colunas or []
        )

    datas = pd.to_datetime(
        df['criado_em'],
        format='%d/%m/%Y %H:%M:%S',
        errors='coerce'
    )

    df = df[
        datas.dt.date == datetime.now().date()
    ].copy()

    if colunas:
        for coluna in colunas:
            if coluna not in df.columns:
                df[coluna] = ''

    return df


def sincronizar_historico_pedido(
    pedido_historico,
    caminho_historico="data/historico_pedidos.pkl",
    colunas=None
):
    historico = carregar_pkl(
        caminho_historico,
        colunas
    )

    for coluna in pedido_historico:
        if coluna not in historico.columns:
            historico[coluna] = ''

    nova_linha = pd.DataFrame([
        pedido_historico
    ])

    if not historico.empty:
        mask = (
            (
                historico['id_pedido'].astype(str)
                == str(pedido_historico['id_pedido'])
            ) &
            (
                pd.to_numeric(
                    historico['id_item'],
                    errors='coerce'
                ) ==
                pd.to_numeric(
                    pedido_historico['id_item'],
                    errors='coerce'
                )
            )
        )

        historico = historico.loc[
            ~mask
        ].copy()

    historico = pd.concat(
        [
            historico,
            nova_linha
        ],
        ignore_index=True
    )

    return salvar_pkl(
        historico,
        caminho_historico
    )


def gerar_cod_item():
    ids_existentes = pd.to_numeric(
        st.session_state.pedidos.get(
            'cod_item',
            pd.Series(dtype=str)
        ).astype(str).str.extract(
            r'ID_(\d+)'
        )[0],
        errors='coerce'
    ).dropna().tolist()

    ids_carrinho = pd.to_numeric(
        pd.Series(
            st.session_state.pedido_atual
        ).apply(
            lambda x: str(
                x.get('cod_item', '')
            ).replace('ID_', '')
        ),
        errors='coerce'
    ).dropna().tolist()

    maior_id = max(
        ids_existentes + ids_carrinho,
        default=0
    )

    return f"ID_{int(maior_id) + 1:03d}"


def renderizar_seletor_cliente(chave_prefixo):
    """
    Renderiza o seletor de cliente (busca + seleção + criar novo).
    Retorna (id_cliente, nome_cliente, cliente_dict).
    """
    import streamlit as st
    from utils.clientes_utils import buscar_clientes_por_nome, criar_cliente_minimo

    chave_busca = f"busca_cliente_{chave_prefixo}"
    chave_sel = f"cliente_selecionado_{chave_prefixo}"

    if chave_busca not in st.session_state:
        st.session_state[chave_busca] = ''
    if chave_sel not in st.session_state:
        st.session_state[chave_sel] = None

    busca = st.text_input(
        "👤 Nome do Cliente:",
        value=st.session_state[chave_busca],
        placeholder="Digite o nome do cliente",
        key=f"input_{chave_prefixo}"
    )

    if busca != st.session_state[chave_busca]:
        st.session_state[chave_busca] = busca
        st.session_state[chave_sel] = None

    if st.session_state[chave_sel] is None:
        if busca.strip():
            encontrados = buscar_clientes_por_nome(busca)
            if encontrados:
                st.caption(f"{len(encontrados)} cliente(s) encontrado(s):")
                for cli in encontrados:
                    col_cli, col_btn = st.columns([4, 1])
                    with col_cli:
                        st.write(f"**{cli['nome_cliente']}** — {cli['id_cliente']}")
                    with col_btn:
                        if st.button("Selecionar", key=f"sel_{chave_prefixo}_{cli['id_cliente']}", use_container_width=True):
                            st.session_state[chave_sel] = cli
                            st.rerun()
            else:
                st.info("Nenhum cliente encontrado com esse nome.")

            if st.button(f"➕ Criar novo cliente: {busca}", use_container_width=True, key=f"novo_{chave_prefixo}"):
                novo = criar_cliente_minimo(busca)
                st.session_state[chave_sel] = novo
                st.rerun()
    else:
        cli = st.session_state[chave_sel]
        st.success(f"👤 Cliente selecionado: **{cli['nome_cliente']}** — {cli['id_cliente']}")
        if st.button("🔄 Trocar cliente", key=f"trocar_{chave_prefixo}"):
            st.session_state[chave_sel] = None
            st.session_state[chave_busca] = ''
            st.rerun()

    cli = st.session_state.get(chave_sel)
    if cli:
        return cli['id_cliente'], cli['nome_cliente'], cli
    return '', '', None