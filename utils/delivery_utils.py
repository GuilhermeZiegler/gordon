import os
import pickle
import pandas as pd
from datetime import datetime

from utils.paths import get_caminhos
from utils.clientes_utils import carregar_clientes

_c = get_caminhos()
CAMINHO_DELIVERY = os.path.join(os.path.dirname(_c["caixa"]), "delivery.pkl")

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
    if os.path.exists(CAMINHO_DELIVERY):
        with open(CAMINHO_DELIVERY, 'rb') as f:
            dados = pickle.load(f)
        if isinstance(dados, list):
            return pd.DataFrame(dados) if dados else pd.DataFrame(columns=COLUNAS_DELIVERY)
        return dados
    return pd.DataFrame(columns=COLUNAS_DELIVERY)


def salvar_delivery(df):
    os.makedirs(os.path.dirname(CAMINHO_DELIVERY), exist_ok=True)
    with open(CAMINHO_DELIVERY, 'wb') as f:
        pickle.dump(df, f)


def criar_registro_delivery(id_pedido, id_cliente, nome_cliente, telefone, endereco, referencia, itens_resumo, valor_total, taxa_entrega, latitude='', longitude=''):
    df = carregar_delivery()
    if id_pedido in df['id_pedido'].astype(str).values:
        return
    novo = pd.DataFrame([{
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
    }])
    df = pd.concat([df, novo], ignore_index=True)
    salvar_delivery(df)


def atualizar_status(id_pedido, novo_status, motoboy=''):
    df = carregar_delivery()
    idx = df[df['id_pedido'].astype(str) == str(id_pedido)].index
    if idx.empty:
        return False
    idx = idx[0]
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    if novo_status == 'pronto':
        df.loc[idx, 'pronto_em'] = agora
    elif novo_status == 'em_rota':
        df.loc[idx, 'saiu_entrega_em'] = agora
        if motoboy:
            df.loc[idx, 'motoboy'] = motoboy
    elif novo_status == 'chegou':
        df.loc[idx, 'chegou_cliente_em'] = agora
    elif novo_status == 'entregue':
        df.loc[idx, 'entregue_em'] = agora

    df.loc[idx, 'status_entrega'] = novo_status
    salvar_delivery(df)
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