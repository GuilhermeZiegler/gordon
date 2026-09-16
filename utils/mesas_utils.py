import pandas as pd
from datetime import datetime
import streamlit as st

from utils.db import ler_tabela, escrever_tabela, inserir_linha, executar


COLUNAS_MESAS = [
    'id_mesa', 'status', 'garcom', 'qtd_clientes', 'aberto_em', 'fechado_em',
    'valor_pedidos', 'valor_total', 'valor_com_desconto', 'desconto_valor',
    'valor_10', 'ticket_medio', 'cover', 'incluir_10', 'id_venda_caixa'
]


def filtrar_pedidos_por_sessao(mesa_id, pedidos_df, aberto_em_str, fechado_em_str):
    if pedidos_df.empty:
        return pd.DataFrame()

    aberto_dt = datetime.strptime(aberto_em_str, "%d/%m/%Y %H:%M:%S")
    fechado_dt = datetime.strptime(fechado_em_str, "%d/%m/%Y %H:%M:%S")

    pedidos_mesa = pedidos_df[
        pedidos_df["id_mesa"].astype(str).str.strip() == str(mesa_id).strip()
    ].copy()

    if pedidos_mesa.empty:
        return pd.DataFrame()

    pedidos_mesa["criado_dt"] = pd.to_datetime(
        pedidos_mesa["criado_em"],
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce"
    )

    return pedidos_mesa[
        (pedidos_mesa["criado_dt"] >= aberto_dt) &
        (pedidos_mesa["criado_dt"] <= fechado_dt)
    ]


def calcular_valores_mesa(mesa_id, pedidos_df, aberto_em_str, fechado_em_str, apenas_fechados=False):
    pedidos_sessao = filtrar_pedidos_por_sessao(
        mesa_id,
        pedidos_df,
        aberto_em_str,
        fechado_em_str
    )

    if pedidos_sessao.empty:
        return 0.0, 0.0, 0.0

    if apenas_fechados:
        pedidos_sessao = pedidos_sessao[
            pedidos_sessao['status'] == 'fechado'
        ]

    if pedidos_sessao.empty:
        return 0.0, 0.0, 0.0

    valor_pedidos = pd.to_numeric(
        pedidos_sessao.get('subtotal', 0),
        errors='coerce'
    ).fillna(0).sum()

    if 'valor_com_desconto' in pedidos_sessao.columns:
        valor_com_desconto = pd.to_numeric(
            pedidos_sessao['valor_com_desconto'],
            errors='coerce'
        ).fillna(pedidos_sessao['subtotal']).fillna(0).sum()
    else:
        valor_com_desconto = valor_pedidos

    desconto_valor = valor_pedidos - valor_com_desconto

    return float(valor_pedidos), float(valor_com_desconto), float(desconto_valor)


def carregar_mesas():
    df = ler_tabela("mesas")

    if df.empty:
        return pd.DataFrame(columns=COLUNAS_MESAS)

    if 'qtd_clientes' in df.columns:
        df['qtd_clientes'] = pd.to_numeric(
            df['qtd_clientes'],
            errors='coerce'
        ).fillna(0).astype(int)

    for coluna in [
        'cover',
        'valor_pedidos',
        'valor_total',
        'valor_com_desconto',
        'desconto_valor',
        'valor_10',
        'ticket_medio'
    ]:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(
                df[coluna],
                errors='coerce'
            ).fillna(0.0)

    if 'incluir_10' in df.columns:
        df['incluir_10'] = df['incluir_10'].fillna(False)

    if 'id_venda_caixa' not in df.columns:
        df['id_venda_caixa'] = ''

    for coluna in COLUNAS_MESAS:
        if coluna not in df.columns:
            df[coluna] = ''

    return df


def salvar_mesas(df):
    try:
        escrever_tabela("mesas", df)
        return True
    except Exception as e:
        st.error(f"⚠️ Erro ao salvar mesas: {str(e)}")
        return False


def salvar_pedidos(df):
    try:
        escrever_tabela("pedidos", df)
        return True
    except Exception as e:
        st.error(f"⚠️ Erro ao salvar pedidos: {str(e)}")
        return False


def carregar_pedidos():
    return ler_tabela("pedidos")


def calcular_valor_mesa(valor_pedidos, cover_total, desconto_valor, valor_10):
    return valor_pedidos + cover_total - desconto_valor - valor_10


def atualizar_valor_mesa(mesa_id, mesas_df, pedidos_df):
    idx_mesa = mesas_df[mesas_df['id_mesa'] == mesa_id].index

    if idx_mesa.empty:
        return mesas_df

    idx_mesa = idx_mesa[0]
    mesa = mesas_df.loc[idx_mesa]

    pedidos_sessao = filtrar_pedidos_por_sessao(
        mesa_id,
        pedidos_df,
        mesa['aberto_em'],
        datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    )

    if not pedidos_sessao.empty:
        if 'status' in pedidos_sessao.columns:
            pedidos_sessao = pedidos_sessao[
                pedidos_sessao['status'] != 'cancelado'
            ]

        valor_pedidos = pd.to_numeric(
            pedidos_sessao['subtotal'],
            errors='coerce'
        ).fillna(0).sum()

        if 'valor_com_desconto' in pedidos_sessao.columns:
            valor_com_desconto = pd.to_numeric(
                pedidos_sessao['valor_com_desconto'],
                errors='coerce'
            )

            valor_com_desconto = valor_com_desconto.fillna(
                pd.to_numeric(
                    pedidos_sessao['subtotal'],
                    errors='coerce'
                ).fillna(0)
            ).sum()
        else:
            valor_com_desconto = valor_pedidos

        desconto_valor = valor_pedidos - valor_com_desconto
    else:
        valor_pedidos = 0.0
        valor_com_desconto = 0.0
        desconto_valor = 0.0

    cover_total = (
        float(mesa.get('cover', 0) or 0) *
        int(mesa.get('qtd_clientes', 0) or 0)
    )

    incluir_10 = bool(mesa.get('incluir_10', False))

    valor_10 = (
        valor_com_desconto * 0.10
        if incluir_10 and valor_com_desconto > 0
        else 0.0
    )

    valor_total = valor_com_desconto + cover_total + valor_10

    mesas_df.loc[idx_mesa, 'valor_pedidos'] = float(valor_pedidos)
    mesas_df.loc[idx_mesa, 'valor_com_desconto'] = float(valor_com_desconto)
    mesas_df.loc[idx_mesa, 'desconto_valor'] = float(desconto_valor)
    mesas_df.loc[idx_mesa, 'valor_10'] = float(valor_10)
    mesas_df.loc[idx_mesa, 'valor_total'] = float(valor_total)

    qtd_clientes = int(mesa.get('qtd_clientes', 0) or 0)

    mesas_df.loc[idx_mesa, 'ticket_medio'] = (
        round(valor_com_desconto / qtd_clientes, 2)
        if qtd_clientes
        else 0.0
    )

    return mesas_df


def resetar_estado_mesa(mesa_id):
    if 'estado_mesa' in st.session_state:
        if mesa_id in st.session_state.estado_mesa:
            del st.session_state.estado_mesa[mesa_id]


def obter_estatisticas_mesa(mesa_id, pedidos_df, aberto_em_str):
    fechado_em_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    pedidos_sessao = filtrar_pedidos_por_sessao(
        mesa_id,
        pedidos_df,
        aberto_em_str,
        fechado_em_str
    )

    if pedidos_sessao.empty:
        return {
            'total_itens': 0,
            'fechados': 0,
            'abertos': 0,
            'cancelados': 0,
            'cortesias': 0,
            'devolucoes': 0
        }

    cortesia = (
        pedidos_sessao['cortesia'].fillna(False).astype(bool)
        if 'cortesia' in pedidos_sessao.columns
        else pd.Series(False, index=pedidos_sessao.index)
    )

    desconto_tipo = (
        pedidos_sessao['desconto_tipo'].fillna('').astype(str)
        if 'desconto_tipo' in pedidos_sessao.columns
        else pd.Series('', index=pedidos_sessao.index)
    )

    return {
        'total_itens': len(pedidos_sessao),
        'fechados': len(pedidos_sessao[pedidos_sessao['status'] == 'fechado']),
        'abertos': len(pedidos_sessao[pedidos_sessao['status'] == 'enviado']),
        'cancelados': len(pedidos_sessao[pedidos_sessao['status'] == 'cancelado']),
        'cortesias': int(cortesia.sum()),
        'devolucoes': int((desconto_tipo == 'devolucao').sum())
    }


def _limpar_valor(v):
    if v is None:
        return None

    try:
        import numpy as np
        if isinstance(v, np.generic):
            return v.item()
    except ImportError:
        pass

    try:
        if pd.isna(v):
            return None
    except Exception:
        pass

    return v


def adicionar_historico_mesa(mesa_historico):
    chave_mesa = str(mesa_historico.get('id_mesa', ''))
    chave_aberto = str(mesa_historico.get('aberto_em', ''))

    historico = ler_tabela("historico_mesas")

    if not historico.empty:
        mask = (
            (historico['id_mesa'].astype(str) == chave_mesa) &
            (historico['aberto_em'].astype(str) == chave_aberto)
        )
        if mask.any():
            executar(
                'DELETE FROM "historico_mesas" WHERE "id_mesa" = :m AND "aberto_em" = :a',
                {"m": chave_mesa, "a": chave_aberto}
            )

    limpo = {k: _limpar_valor(v) for k, v in mesa_historico.items()}

    try:
        inserir_linha("historico_mesas", limpo)
    except Exception as e:
        st.error(f"⚠️ Erro ao salvar histórico de mesa: {str(e)}")


def obter_id_venda_mesa(mesa_id, aberto_em):
    mesas_df = carregar_mesas()

    if mesas_df.empty:
        return ''

    filtro = (
        (mesas_df['id_mesa'].astype(str) == str(mesa_id)) &
        (mesas_df['aberto_em'].astype(str) == str(aberto_em))
    )

    if not filtro.any():
        return ''

    id_v = mesas_df.loc[filtro, 'id_venda_caixa'].iloc[0]

    if pd.isna(id_v):
        return ''

    return str(id_v)


def reabrir_mesa(mesas_df, mesa_id):
    idx = mesas_df[mesas_df['id_mesa'] == mesa_id].index

    if idx.empty:
        return mesas_df, False

    idx = idx[0]

    if mesas_df.loc[idx, 'status'] != 'fechada':
        return mesas_df, False

    mesas_df.loc[idx, 'status'] = 'aberta'
    mesas_df.loc[idx, 'fechado_em'] = ''

    return mesas_df, True


def obter_itens_mesa(mesa_id, pedidos_df):
    return pedidos_df[
        pedidos_df['id_mesa'].astype(str).str.strip() ==
        str(mesa_id).strip()
    ].copy()


def localizar_item_pedido(pedidos_df, id_pedido, cod_item):
    mask = (
        pedidos_df['id_pedido'].astype(str) == str(id_pedido)
    ) & (
        pedidos_df['cod_item'].astype(str) == str(cod_item)
    )

    return pedidos_df.index[mask]


def _valor_original_item(row):
    preco = pd.to_numeric(row.get('preco_unitario', 0), errors='coerce')
    quantidade = pd.to_numeric(row.get('quantidade', 1), errors='coerce')

    preco = 0.0 if pd.isna(preco) else float(preco)
    quantidade = 1.0 if pd.isna(quantidade) else float(quantidade)

    return preco * quantidade


def _normalizar_valores_item(pedidos_df, idx):
    valor_original = _valor_original_item(pedidos_df.loc[idx])

    subtotal = pd.to_numeric(
        pedidos_df.loc[idx].get('subtotal', valor_original),
        errors='coerce'
    )

    valor_com_desconto = pd.to_numeric(
        pedidos_df.loc[idx].get('valor_com_desconto', valor_original),
        errors='coerce'
    )

    if pd.isna(subtotal):
        pedidos_df.loc[idx, 'subtotal'] = valor_original

    if pd.isna(valor_com_desconto):
        pedidos_df.loc[idx, 'valor_com_desconto'] = valor_original

    return valor_original


def aplicar_cortesia_item(pedidos_df, id_pedido, cod_item):
    indices = localizar_item_pedido(pedidos_df, id_pedido, cod_item)

    if indices.empty:
        return pedidos_df

    idx = indices[0]

    valor_original = _valor_original_item(pedidos_df.loc[idx])

    pedidos_df.loc[idx, 'subtotal'] = valor_original
    pedidos_df.loc[idx, 'valor_com_desconto'] = 0.0
    pedidos_df.loc[idx, 'desconto_valor'] = valor_original
    pedidos_df.loc[idx, 'desconto_percentual'] = 100.0
    pedidos_df.loc[idx, 'desconto_item'] = valor_original
    pedidos_df.loc[idx, 'desconto_tipo'] = 'cortesia'
    pedidos_df.loc[idx, 'cortesia'] = True

    return pedidos_df


def remover_cortesia_item(pedidos_df, id_pedido, cod_item):
    indices = localizar_item_pedido(pedidos_df, id_pedido, cod_item)

    if indices.empty:
        return pedidos_df

    idx = indices[0]

    valor_original = _valor_original_item(pedidos_df.loc[idx])

    pedidos_df.loc[idx, 'subtotal'] = valor_original
    pedidos_df.loc[idx, 'valor_com_desconto'] = valor_original
    pedidos_df.loc[idx, 'desconto_valor'] = 0.0
    pedidos_df.loc[idx, 'desconto_percentual'] = 0.0
    pedidos_df.loc[idx, 'desconto_item'] = 0.0
    pedidos_df.loc[idx, 'desconto_tipo'] = 'nenhum'
    pedidos_df.loc[idx, 'cortesia'] = False

    return pedidos_df


def aplicar_devolucao_item(pedidos_df, id_pedido, cod_item):
    indices = localizar_item_pedido(pedidos_df, id_pedido, cod_item)

    if indices.empty:
        return pedidos_df

    idx = indices[0]

    valor_original = _valor_original_item(pedidos_df.loc[idx])

    pedidos_df.loc[idx, 'subtotal'] = valor_original
    pedidos_df.loc[idx, 'valor_com_desconto'] = 0.0
    pedidos_df.loc[idx, 'desconto_valor'] = valor_original
    pedidos_df.loc[idx, 'desconto_percentual'] = 100.0
    pedidos_df.loc[idx, 'desconto_item'] = valor_original
    pedidos_df.loc[idx, 'desconto_tipo'] = 'devolucao'
    pedidos_df.loc[idx, 'cortesia'] = False

    return pedidos_df


def remover_devolucao_item(pedidos_df, id_pedido, cod_item):
    indices = localizar_item_pedido(pedidos_df, id_pedido, cod_item)

    if indices.empty:
        return pedidos_df

    idx = indices[0]

    valor_original = _valor_original_item(pedidos_df.loc[idx])

    pedidos_df.loc[idx, 'subtotal'] = valor_original
    pedidos_df.loc[idx, 'valor_com_desconto'] = valor_original
    pedidos_df.loc[idx, 'desconto_valor'] = 0.0
    pedidos_df.loc[idx, 'desconto_percentual'] = 0.0
    pedidos_df.loc[idx, 'desconto_item'] = 0.0
    pedidos_df.loc[idx, 'desconto_tipo'] = 'nenhum'
    pedidos_df.loc[idx, 'cortesia'] = False

    return pedidos_df


def aplicar_desconto_item(pedidos_df, id_pedido, cod_item, valor_desconto, tipo='percentual'):
    indices = localizar_item_pedido(pedidos_df, id_pedido, cod_item)

    if indices.empty:
        return pedidos_df

    idx = indices[0]

    valor_original = _valor_original_item(pedidos_df.loc[idx])

    valor_desconto = pd.to_numeric(valor_desconto, errors='coerce')

    if pd.isna(valor_desconto):
        valor_desconto = 0.0

    valor_desconto = max(float(valor_desconto), 0.0)

    if tipo == 'percentual':
        valor_desconto = min(valor_desconto, 100.0)
        desconto = valor_original * (valor_desconto / 100)
        desconto_percentual = valor_desconto
    else:
        desconto = min(valor_desconto, valor_original)
        desconto_percentual = 0.0

    novo_valor = max(valor_original - desconto, 0.0)

    pedidos_df.loc[idx, 'subtotal'] = valor_original
    pedidos_df.loc[idx, 'valor_com_desconto'] = novo_valor
    pedidos_df.loc[idx, 'desconto_item'] = desconto
    pedidos_df.loc[idx, 'desconto_valor'] = desconto
    pedidos_df.loc[idx, 'desconto_percentual'] = desconto_percentual
    pedidos_df.loc[idx, 'desconto_tipo'] = 'desconto'
    pedidos_df.loc[idx, 'cortesia'] = False

    return pedidos_df


def remover_desconto_item(pedidos_df, id_pedido, cod_item):
    indices = localizar_item_pedido(pedidos_df, id_pedido, cod_item)

    if indices.empty:
        return pedidos_df

    idx = indices[0]

    valor_original = _valor_original_item(pedidos_df.loc[idx])

    pedidos_df.loc[idx, 'subtotal'] = valor_original
    pedidos_df.loc[idx, 'valor_com_desconto'] = valor_original
    pedidos_df.loc[idx, 'desconto_item'] = 0.0
    pedidos_df.loc[idx, 'desconto_tipo'] = 'nenhum'
    pedidos_df.loc[idx, 'desconto_percentual'] = 0.0
    pedidos_df.loc[idx, 'desconto_valor'] = 0.0
    pedidos_df.loc[idx, 'cortesia'] = False

    return pedidos_df