import os
import pandas as pd
import streamlit as st
from datetime import datetime

from utils.db import ler_tabela, escrever_tabela, inserir_linha, deletar_linhas


def gerar_id_pedido(pedidos_df=None, historico_path=None):
    from utils.db import obter_proximo_id

    id_hist = obter_proximo_id("historico_pedidos", "id_pedido", "PED-")
    id_ativos = obter_proximo_id("pedidos", "id_pedido", "PED-")

    proximo = max(id_hist, id_ativos)

    return f"PED-{proximo:04d}"


_TABELAS_CACHE = {"produtos", "insumos", "ficha_tecnica", "funcionarios"}


def carregar_pkl(caminho=None, colunas=None):
    if caminho is None:
        return pd.DataFrame(columns=colunas or [])

    nome_tabela = os.path.basename(str(caminho)).replace(".pkl", "")

    try:
        if nome_tabela in _TABELAS_CACHE:
            from utils.db import ler_tabela_cache
            df = ler_tabela_cache(nome_tabela)
        else:
            df = ler_tabela(nome_tabela)
    except Exception:
        df = pd.DataFrame(columns=colunas or [])

    if 'cod_item' not in df.columns:
        df['cod_item'] = ''

    if 'id_item' not in df.columns:
        df['id_item'] = ''

    if colunas:
        for coluna in colunas:
            if coluna not in df.columns:
                df[coluna] = ''

    return df


def salvar_pkl(df, caminho=None):
    if caminho is None:
        return False

    nome_tabela = os.path.basename(str(caminho)).replace(".pkl", "")

    try:
        escrever_tabela(nome_tabela, df)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {str(e)}")
        return False


def carregar_historico_pedidos_hoje(caminho_historico=None, colunas=None):
    df = ler_tabela("historico_pedidos")

    if df.empty or 'criado_em' not in df.columns:
        if colunas:
            return pd.DataFrame(columns=colunas)
        return pd.DataFrame()

    datas = pd.to_datetime(
        df['criado_em'],
        format='%d/%m/%Y %H:%M:%S',
        errors='coerce'
    )

    df = df[datas.dt.date == datetime.now().date()].copy()

    if colunas:
        for coluna in colunas:
            if coluna not in df.columns:
                df[coluna] = ''

    return df


def sincronizar_historico_pedido(pedido_historico, caminho_historico=None, colunas=None):
    id_pedido = pedido_historico.get('id_pedido')
    id_item = pedido_historico.get('id_item')

    if id_pedido is None or id_item is None:
        return False

    from utils.db import executar

    try:
        executar(
            'DELETE FROM "historico_pedidos" WHERE "id_pedido" = :p AND "id_item" = :i',
            {"p": str(id_pedido), "i": int(id_item)}
        )
        inserir_linha("historico_pedidos", pedido_historico)
        return True
    except Exception as e:
        st.error(f"Erro ao sincronizar: {str(e)}")
        return False


def gerar_cod_item():
    pedidos = st.session_state.get("pedidos")

    if pedidos is None or pedidos.empty:
        ids_existentes = []
    else:
        ids_existentes = pd.to_numeric(
            pedidos.get('cod_item', pd.Series(dtype=str))
            .astype(str)
            .str.extract(r'ID_(\d+)')[0],
            errors='coerce'
        ).dropna().tolist()

    ids_carrinho = pd.to_numeric(
        pd.Series(st.session_state.pedido_atual)
        .apply(lambda x: str(x.get('cod_item', '')).replace('ID_', '')),
        errors='coerce'
    ).dropna().tolist()

    maior_id = max(ids_existentes + ids_carrinho, default=0)

    return f"ID_{int(maior_id) + 1:03d}"


def renderizar_seletor_cliente(chave_prefixo):
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