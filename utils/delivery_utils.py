import pandas as pd

from datetime import datetime

from utils.db import ler_tabela, inserir_linha, atualizar_linhas
from utils.clientes_utils import carregar_clientes


COLUNAS_DELIVERY = [
    'id_pedido',
    'id_cliente',
    'nome_cliente',
    'telefone',
    'endereco',
    'referencia',
    'itens_resumo',
    'valor_total',
    'taxa_entrega',
    'criado_em',
    'pronto_em',
    'saiu_entrega_em',
    'chegou_cliente_em',
    'entregue_em',
    'motoboy',
    'status_entrega',
    'latitude',
    'longitude'
]


def carregar_delivery():
    df = ler_tabela("delivery")

    if df.empty:
        return pd.DataFrame(columns=COLUNAS_DELIVERY)

    for coluna in COLUNAS_DELIVERY:
        if coluna not in df.columns:
            df[coluna] = ''

    return df


def salvar_delivery(df):
    from utils.db import escrever_tabela
    escrever_tabela("delivery", df)


def criar_registro_delivery(id_pedido, id_cliente, nome_cliente, telefone, endereco, referencia, itens_resumo, valor_total, taxa_entrega, latitude='', longitude=''):
    df = carregar_delivery()

    if not df.empty and id_pedido in df['id_pedido'].astype(str).values:
        return

    novo = {
        'id_pedido': id_pedido,
        'id_cliente': id_cliente,
        'nome_cliente': nome_cliente,
        'telefone': telefone,
        'endereco': endereco,
        'referencia': referencia,
        'itens_resumo': itens_resumo,
        'valor_total': valor_total,
        'taxa_entrega': taxa_entrega,
        'criado_em': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        'pronto_em': '',
        'saiu_entrega_em': '',
        'chegou_cliente_em': '',
        'entregue_em': '',
        'motoboy': '',
        'status_entrega': 'preparando',
        'latitude': latitude,
        'longitude': longitude
    }

    inserir_linha("delivery", novo)


def atualizar_status(id_pedido, novo_status, motoboy=''):
    df = carregar_delivery()

    if df.empty:
        return False

    idx = df[df['id_pedido'].astype(str) == str(id_pedido)].index

    if idx.empty:
        return False

    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    valores = {'status_entrega': novo_status}

    if novo_status == 'pronto':
        valores['pronto_em'] = agora
    elif novo_status == 'em_rota':
        valores['saiu_entrega_em'] = agora
        if motoboy:
            valores['motoboy'] = motoboy
    elif novo_status == 'chegou':
        valores['chegou_cliente_em'] = agora
    elif novo_status == 'entregue':
        valores['entregue_em'] = agora

    atualizar_linhas("delivery", "id_pedido", id_pedido, valores)
    return True


def calcular_tempo(criado, alvo):
    if not criado or not alvo:
        return None
    try:
        d1 = datetime.strptime(criado, "%d/%m/%Y %H:%M:%S")
        d2 = datetime.strptime(alvo, "%d/%m/%Y %H:%M:%S")
        return int((d2 - d1).total_seconds() / 60)
    except Exception:
        return None


def obter_dados_cliente(id_cliente):
    if not id_cliente:
        return None
    for c in carregar_clientes():
        if str(c.get('id_cliente')) == str(id_cliente):
            return c
    return None


def metricas_delivery(df):
    ativos = df[df['status_entrega'].isin(['preparando', 'pronto', 'em_rota', 'chegou'])]
    entregues_hoje = df[
        (df['status_entrega'] == 'entregue') &
        (df['entregue_em'].astype(str).str.startswith(datetime.now().strftime("%d/%m/%Y")))
    ]

    tempos_producao = []
    tempos_entrega = []
    atrasados = 0

    for _, row in df.iterrows():
        t_prod = calcular_tempo(row['criado_em'], row['pronto_em'])
        if t_prod is not None:
            tempos_producao.append(t_prod)
        t_ent = calcular_tempo(row['saiu_entrega_em'], row['entregue_em'])
        if t_ent is not None:
            tempos_entrega.append(t_ent)

        if row['status_entrega'] in ['preparando', 'pronto', 'em_rota', 'chegou']:
            t_total = calcular_tempo(row['criado_em'], datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            if t_total is not None and t_total > 45:
                atrasados += 1

    return {
        'ativos': len(ativos),
        'entregues_hoje': len(entregues_hoje),
        'tempo_medio_producao': round(sum(tempos_producao) / len(tempos_producao), 1) if tempos_producao else 0,
        'tempo_medio_entrega': round(sum(tempos_entrega) / len(tempos_entrega), 1) if tempos_entrega else 0,
        'atrasados': atrasados
    }