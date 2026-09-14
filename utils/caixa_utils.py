import os
import pickle
import pandas as pd
import streamlit as st

from datetime import datetime
from utils.paths import get_caminhos
from utils.pedidos_utils import gerar_id_pedido, gerar_cod_item, sincronizar_historico_pedido
from utils.movimentacoes_utils import baixar_por_produto

_c = get_caminhos()

CAMINHO_CAIXA = _c["caixa"]
CAMINHO_PRODUTOS = _c["produtos"]
CAMINHO_HISTORICO = os.path.join(
    os.path.dirname(CAMINHO_CAIXA),
    "historico_caixa.pkl"
)


def carregar_caixa():
    if os.path.exists(CAMINHO_CAIXA):
        with open(CAMINHO_CAIXA, "rb") as f:
            caixa = pickle.load(f)

        caixa.setdefault("saldo_inicial", 0.0)
        caixa.setdefault("data_abertura", "")
        caixa.setdefault("data_fechamento", "")
        caixa.setdefault("status", "fechado")
        caixa.setdefault("vendas_mesa", 0.0)
        caixa.setdefault("vendas_balcao", 0.0)
        caixa.setdefault("vendas_takeaway", 0.0)
        caixa.setdefault("vendas_delivery", 0.0)
        caixa.setdefault("reembolso", 0.0)
        caixa.setdefault("estorno", 0.0)
        caixa.setdefault("pagamentos", [])
        caixa.setdefault("entradas", [])
        caixa.setdefault("saidas", [])
        caixa.setdefault("vendas_metodo", {})
        caixa.setdefault("fiados", [])

        return caixa

    return {
        "saldo_inicial": 0.0,
        "data_abertura": "",
        "data_fechamento": "",
        "status": "fechado",
        "vendas_mesa": 0.0,
        "vendas_balcao": 0.0,
        "vendas_takeaway": 0.0,
        "vendas_delivery": 0.0,
        "reembolso": 0.0,
        "estorno": 0.0,
        "pagamentos": [],
        "entradas": [],
        "saidas": [],
        "vendas_metodo": {},
        "fiados": []
    }


def salvar_caixa(caixa):
    os.makedirs(os.path.dirname(CAMINHO_CAIXA), exist_ok=True)

    caixa.setdefault("fiados", [])
    caixa.setdefault("vendas_takeaway", 0.0)

    with open(CAMINHO_CAIXA, "wb") as f:
        pickle.dump(caixa, f)


def carregar_produtos():
    if os.path.exists(CAMINHO_PRODUTOS):
        with open(CAMINHO_PRODUTOS, "rb") as f:
            return pickle.load(f)

    return pd.DataFrame()


def carregar_historico_caixa():
    historico_path = os.path.join(
        os.path.dirname(CAMINHO_CAIXA),
        "historico_caixa.pkl"
    )

    if not os.path.exists(historico_path):
        return []

    with open(historico_path, "rb") as f:
        historico = pickle.load(f)

    if not isinstance(historico, list):
        return []

    return historico


def salvar_historico_caixa(caixa):
    historico_path = os.path.join(
        os.path.dirname(CAMINHO_CAIXA),
        "historico_caixa.pkl"
    )

    historico = carregar_historico_caixa()
    data_abertura = caixa.get("data_abertura", "")

    if data_abertura:
        historico = [
            h for h in historico
            if h.get("data_abertura", "") != data_abertura
        ]

    historico.append(caixa.copy())

    os.makedirs(os.path.dirname(historico_path), exist_ok=True)

    with open(historico_path, "wb") as f:
        pickle.dump(historico, f)

    return True


def registrar_venda_no_caixa(categoria, valor, metodo, descricao, itens=None):
    if itens:
        id_pedido = gerar_id_pedido()
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        for numero_item, item in enumerate(itens, start=1):
            cod_item = gerar_cod_item()
            cod_prod = str(item['cod_prod'])
            nome_prod = item['nome']
            quantidade = item['quantidade']
            preco_unitario = item['preco_unitario']
            subtotal = item['subtotal']

            pedido_historico = {
                'id_pedido': id_pedido,
                'id_item': numero_item,
                'cod_item': cod_item,
                'id_mesa': '',
                'cod_prod': cod_prod,
                'nome_prod': nome_prod,
                'quantidade': quantidade,
                'preco_unitario': preco_unitario,
                'preco_final': preco_unitario,
                'desconto_tipo': 'Nenhum',
                'desconto_valor': 0.0,
                'subtotal': subtotal,
                'valor_com_desconto': subtotal,
                'observacao': '',
                'criado_em': agora,
                'data_fechamento': agora,
                'fechado_em': agora,
                'status': 'fechado',
                'categoria': '',
                'tipo_venda': 'caixa',
                'item_individual': f"{cod_prod}_{numero_item}_{agora}",
                'origem_venda': 'caixa',
                'taxa_entrega': 0.0,
                'taxa_embalagem': 0.0,
                'id_cliente': descricao if metodo == 'Fiado' else '',
                'metodo_pagamento': metodo
            }

            sincronizar_historico_pedido(pedido_historico)
            baixar_por_produto(id_pedido, cod_item, cod_prod, quantidade, nome_prod)

    caixa = carregar_caixa()

    if metodo == "Fiado":
        caixa.setdefault("fiados", [])

        id_fiado = len(caixa["fiados"]) + 1

        caixa["fiados"].append({
            "id": id_fiado,
            "cliente": descricao if descricao else f"Venda {categoria}",
            "valor": valor,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "status": "pendente",
            "itens": descricao,
            "tipo": categoria,
            "metodo": "Fiado"
        })

        salvar_caixa(caixa)
        salvar_historico_caixa(caixa)

        if "caixa" in st.session_state:
            st.session_state.caixa = caixa

        return caixa

    caixa.setdefault("entradas", [])
    caixa.setdefault("vendas_metodo", {})

    caixa["entradas"].append({
        "categoria": categoria,
        "valor": valor,
        "metodo": metodo,
        "descricao": descricao,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    })

    if categoria == "Mesa":
        caixa["vendas_mesa"] += valor
    elif categoria == "Takeaway":
        caixa["vendas_takeaway"] += valor
    elif categoria in ["Balcão", "Bar", "Avulso"]:
        caixa["vendas_balcao"] += valor
    elif categoria == "Delivery":
        caixa["vendas_delivery"] += valor

    caixa["vendas_metodo"][metodo] = (
        caixa["vendas_metodo"].get(metodo, 0.0) + valor
    )

    salvar_caixa(caixa)
    salvar_historico_caixa(caixa)

    if "caixa" in st.session_state:
        st.session_state.caixa = caixa

    return caixa


def resetar_caixa():
    caixa = {
        "saldo_inicial": 0.0,
        "data_abertura": "",
        "data_fechamento": "",
        "status": "fechado",
        "vendas_mesa": 0.0,
        "vendas_balcao": 0.0,
        "vendas_takeaway": 0.0,
        "vendas_delivery": 0.0,
        "reembolso": 0.0,
        "estorno": 0.0,
        "pagamentos": [],
        "entradas": [],
        "saidas": [],
        "vendas_metodo": {},
        "fiados": []
    }

    salvar_caixa(caixa)

    return caixa


def atualizar_historico_caixa(caixa):
    historico = carregar_historico_caixa()

    if not isinstance(historico, list):
        historico = []

    data_abertura = caixa.get("data_abertura", "")

    historico = [
        h
        for h in historico
        if h.get("data_abertura") != data_abertura
    ]

    historico.append(caixa.copy())

    with open(CAMINHO_HISTORICO, "wb") as f:
        pickle.dump(historico, f)


def obter_caixa_aberto():
    caixa = carregar_caixa()

    if (
        caixa.get("status") == "aberto"
        and not caixa.get("data_fechamento")
    ):
        return caixa

    return None


def garantir_estrutura_caixa(caixa):
    if "fiados" not in caixa:
        caixa["fiados"] = []

    if "entradas" not in caixa:
        caixa["entradas"] = []

    if "saidas" not in caixa:
        caixa["saidas"] = []

    if "pagamentos" not in caixa:
        caixa["pagamentos"] = []

    if "vendas_metodo" not in caixa:
        caixa["vendas_metodo"] = {}

    if "vendas_mesa" not in caixa:
        caixa["vendas_mesa"] = 0.0

    if "vendas_balcao" not in caixa:
        caixa["vendas_balcao"] = 0.0

    if "vendas_delivery" not in caixa:
        caixa["vendas_delivery"] = 0.0

    if "reembolso" not in caixa:
        caixa["reembolso"] = 0.0

    if "estorno" not in caixa:
        caixa["estorno"] = 0.0

    if "saldo_inicial" not in caixa:
        caixa["saldo_inicial"] = 0.0

    return caixa