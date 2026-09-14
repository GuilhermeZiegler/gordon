import os
import pickle
import random

from install.seed._common import DATA_DIR
from install.seed.funcionarios import FUNCIONARIOS

GARCOMS = [f['nome'] for f in FUNCIONARIOS if f.get('cargo') == 'Garçom']


def _parse_dt(s):
    from datetime import datetime
    return datetime.strptime(s, "%d/%m/%Y %H:%M:%S")


def popular_historico_mesas():
    random.seed(42)

    historico_pedidos_path = os.path.join(DATA_DIR, "historico_pedidos.pkl")

    with open(historico_pedidos_path, 'rb') as f:
        pedidos = pickle.load(f)

    pedidos_mesa = [p for p in pedidos if p.get('origem_venda') == 'mesa']

    agrupados = {}
    for item in pedidos_mesa:
        chave = (item['id_mesa'], item['criado_em'])
        agrupados.setdefault(chave, []).append(item)

    historico_mesas = []

    for (id_mesa, aberto_em), itens in agrupados.items():
        itens_validos = [i for i in itens if i.get('status') != 'cancelado']

        valor_pedidos = round(sum(float(i.get('subtotal', 0)) for i in itens_validos), 2)
        valor_com_desconto = round(sum(float(i.get('valor_com_desconto', 0)) for i in itens_validos), 2)
        desconto_valor = round(valor_pedidos - valor_com_desconto, 2)

        fechado_em = itens[0]['fechado_em']

        qtd_clientes = random.randint(1, 6)

        incluir_10 = random.random() < 0.90

        valor_10 = round(valor_com_desconto * 0.10, 2) if incluir_10 and valor_com_desconto > 0 else 0.0

        if random.random() < 0.60:
            cover_unitario = round(random.uniform(5, 15), 2)
        else:
            cover_unitario = 0.0

        cover_total = round(cover_unitario * qtd_clientes, 2)

        valor_total = round(valor_com_desconto + cover_total + valor_10, 2)

        ticket_medio = round(valor_total / qtd_clientes, 2) if qtd_clientes > 0 else 0.0

        garcom = random.choice(GARCOMS)

        historico_mesas.append({
            'id_mesa': id_mesa,
            'garcom': garcom,
            'qtd_clientes': qtd_clientes,
            'aberto_em': aberto_em,
            'fechado_em': fechado_em,
            'valor_pedidos': valor_pedidos,
            'valor_total': valor_total,
            'valor_com_desconto': valor_com_desconto,
            'desconto_valor': desconto_valor,
            'valor_10': valor_10,
            'ticket_medio': ticket_medio,
            'cover': cover_unitario,
            'incluir_10': incluir_10
        })

    with open(os.path.join(DATA_DIR, "historico_mesas.pkl"), 'wb') as f:
        pickle.dump(historico_mesas, f)

    print(f"historico_mesas.pkl: {len(historico_mesas)} registros")


if __name__ == "__main__":
    popular_historico_mesas()