import os
import json
import pickle
import pandas as pd
from utils.paths import get_caminhos

_c = get_caminhos()
DATA_DIR = os.path.dirname(_c["produtos"])

COLUNAS = {
    "produtos": ['cod_prod', 'nome', 'desc', 'tipo', 'categoria', 'p_venda', 'p_custo', 'margem', 'tipo_venda', 'insumo_direto'],
    "insumos": ['id_insumo', 'nome', 'categoria_insumo', 'unidade_compra', 'preco_unitario'],
    "ficha_tecnica": ['cod_prod', 'id_insumo', 'quantidade', 'unidade_ficha'],
    "mesas": ['id_mesa', 'status', 'garcom', 'qtd_clientes', 'aberto_em', 'fechado_em', 'valor_pedidos', 'valor_total', 'valor_com_desconto', 'desconto_valor', 'valor_10', 'ticket_medio', 'cover', 'incluir_10'],
    "pedidos": ['id_pedido', 'id_item', 'cod_item', 'id_mesa', 'cod_prod', 'nome_prod', 'quantidade', 'preco_unitario', 'preco_final', 'desconto_tipo', 'desconto_valor', 'subtotal', 'valor_com_desconto', 'observacao', 'criado_em', 'status', 'categoria', 'tipo_venda', 'item_individual', 'origem_venda', 'taxa_entrega', 'taxa_embalagem', 'id_cliente', 'metodo_pagamento'],
    "delivery": ['id_pedido', 'id_cliente', 'nome_cliente', 'telefone', 'endereco', 'referencia', 'itens_resumo', 'valor_total', 'taxa_entrega', 'criado_em', 'pronto_em', 'saiu_entrega_em', 'chegou_cliente_em', 'entregue_em', 'motoboy', 'status_entrega', 'latitude', 'longitude'],
    "movimentacoes": ['id_movimentacao', 'tipo', 'id_insumo', 'quantidade', 'unidade', 'data_movimentacao', 'preco_unitario', 'fornecedor', 'nota_fiscal', 'data_validade', 'id_pedido', 'cod_item', 'cod_prod', 'motivo', 'usuario', 'observacao'],
}

LISTAS = ["historico_mesas", "historico_pedidos", "historico_caixa", "historico_compras", "historico_estoque", "historico_baixas", "historico_inventario", "historico_nao_baixados", "funcionarios", "clientes"]

CAIXA_INICIAL = {
    'saldo_inicial': 0.0,
    'data_abertura': '',
    'data_fechamento': '',
    'status': 'fechado',
    'vendas_mesa': 0.0,
    'vendas_balcao': 0.0,
    'vendas_delivery': 0.0,
    'vendas_takeaway': 0.0,
    'reembolso': 0.0,
    'estorno': 0.0,
    'pagamentos': [],
    'entradas': [],
    'saidas': [],
    'vendas_metodo': {},
    'fiados': []
}

CONFIG_INICIAL = {
    "impressora_cozinha": "",
    "impressora_salao": "",
    "impressora_comanda": "",
    "empresa": {
        "nome": "",
        "email_contato": "",
        "telefone": "",
        "cnpj": ""
    }
}


def bootstrap():
    os.makedirs(DATA_DIR, exist_ok=True)
    for pasta in ["backups_produtos", "backups_estoque", "backups_compras", "backups_mesas", "tickets", "tickets/cozinha", "tickets/bar"]:
        os.makedirs(os.path.join(DATA_DIR, pasta), exist_ok=True)

    for nome, colunas in COLUNAS.items():
        path = os.path.join(DATA_DIR, f"{nome}.pkl")
        if not os.path.exists(path):
            with open(path, "wb") as f:
                pickle.dump(pd.DataFrame(columns=colunas), f)
            print(f"Criado: {path}")

    for nome in LISTAS:
        path = os.path.join(DATA_DIR, f"{nome}.pkl")
        if not os.path.exists(path):
            with open(path, "wb") as f:
                pickle.dump([], f)
            print(f"Criado: {path}")

    path = os.path.join(DATA_DIR, "caixa.pkl")
    if not os.path.exists(path):
        with open(path, "wb") as f:
            pickle.dump(CAIXA_INICIAL, f)
        print(f"Criado: {path}")

    path = os.path.join(DATA_DIR, "config.json")
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(CONFIG_INICIAL, f, indent=4, ensure_ascii=False)
        print(f"Criado: {path}")

    print("Bootstrap concluído.")


if __name__ == "__main__":
    bootstrap()