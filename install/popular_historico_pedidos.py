import os
import pickle
import random
from datetime import datetime, timedelta

from install.seed._common import DATA_DIR
from install.seed.clientes import CLIENTES
from install.seed.produtos import PRODUTOS

OBSERVACOES = [
    'sem cebola', 'bem passado', 'sem tomate', 'pouco sal', 'sem gelo',
    'ao ponto', 'sem maionese', 'extra bacon', 'sem alface', 'bem frito'
]

METODOS_MESA = ['Pix', 'Débito', 'Crédito', 'Dinheiro', 'Voucher', 'Fiado']
METODOS_TAKEAWAY = ['Dinheiro', 'Pix', 'Débito', 'Crédito', 'Voucher']
METODOS_CAIXA = ['Pix', 'Débito', 'Crédito', 'Dinheiro', 'Voucher', 'Fiado']


def gerar_horario_aleatorio():
    return f"{random.randint(10, 21):02d}:{random.randint(0, 59):02d}"


def _sortear_metodo(origem):
    if origem == 'delivery':
        return 'iFood'
    if origem == 'takeaway':
        return random.choice(METODOS_TAKEAWAY)
    if origem == 'mesa':
        if random.random() < 0.05:
            return 'Fiado'
        return random.choice([m for m in METODOS_MESA if m != 'Fiado'])
    if origem == 'caixa':
        if random.random() < 0.05:
            return 'Fiado'
        return random.choice([m for m in METODOS_CAIXA if m != 'Fiado'])
    return ''


def _sortear_origem():
    r = random.random()
    if r < 0.45:
        return 'mesa'
    if r < 0.70:
        return 'takeaway'
    if r < 0.90:
        return 'delivery'
    return 'caixa'


def _sortear_desconto(subtotal, origem):
    r = random.random()

    if origem == 'mesa':
        if r < 0.86:
            return 'Nenhum', 0.0, subtotal
        if r < 0.96:
            if random.random() < 0.5:
                pct = random.uniform(5, 30)
                return 'promo', round(pct, 2), round(subtotal * (1 - pct / 100), 2)
            vlr = random.uniform(2, 10)
            return 'promo', round(vlr, 2), round(max(0.0, subtotal - vlr), 2)
        if r < 0.97:
            return 'cortesia', round(subtotal, 2), 0.0
        if r < 0.972:
            return 'devolucao', round(subtotal, 2), 0.0
        return 'cancelado', 0.0, 0.0
    else:
        if r < 0.87:
            return 'Nenhum', 0.0, subtotal
        if r < 0.97:
            if random.random() < 0.5:
                pct = random.uniform(5, 30)
                return 'promo', round(pct, 2), round(subtotal * (1 - pct / 100), 2)
            vlr = random.uniform(2, 10)
            return 'promo', round(vlr, 2), round(max(0.0, subtotal - vlr), 2)
        if r < 0.972:
            return 'devolucao', round(subtotal, 2), 0.0
        return 'cancelado', 0.0, 0.0


def _sortear_status(desconto_tipo):
    if desconto_tipo == 'cancelado':
        return 'cancelado'
    return 'fechado'


def popular_historico_pedidos(dias=180):
    random.seed(42)

    produtos_menu = [p for p in PRODUTOS if p.get('tipo_venda') in ('menu', 'bar')]
    produtos_caixa = [p for p in PRODUTOS if p.get('tipo_venda') == 'caixa']

    historico = []
    seq_pedido = 1
    seq_cod_item = 1

    hoje = datetime.now()

    for cliente in CLIENTES:
        num_pedidos = random.randint(1, 10)

        for _ in range(num_pedidos):
            origem = _sortear_origem()

            if origem == 'caixa':
                produtos_disponiveis = produtos_caixa
            else:
                produtos_disponiveis = produtos_menu

            if not produtos_disponiveis:
                continue

            dias_atras = random.randint(0, dias - 1)
            data_pedido = hoje - timedelta(days=dias_atras)
            data_str = data_pedido.strftime("%d/%m/%Y")

            hora = gerar_horario_aleatorio()
            dt_criado = datetime.strptime(f"{data_str} {hora}", "%d/%m/%Y %H:%M")
            dt_fechado = dt_criado + timedelta(minutes=random.randint(20, 90))

            criado_em = dt_criado.strftime("%d/%m/%Y %H:%M:%S")
            fechado_em = dt_fechado.strftime("%d/%m/%Y %H:%M:%S")

            id_pedido = f"PED-{seq_pedido:05d}"

            if origem == 'mesa':
                id_mesa = f"MESA-{random.randint(1, 40)}"
                id_cliente = ''
                taxa_entrega = 0.0
                taxa_embalagem = 0.0
            elif origem == 'takeaway':
                id_mesa = ''
                id_cliente = cliente['id_cliente']
                taxa_entrega = 0.0
                taxa_embalagem = 2.00
            elif origem == 'delivery':
                id_mesa = ''
                id_cliente = cliente['id_cliente']
                taxa_entrega = 10.00
                taxa_embalagem = 2.00
            else:
                id_mesa = ''
                id_cliente = ''
                taxa_entrega = 0.0
                taxa_embalagem = 0.0

            metodo_pagamento = _sortear_metodo(origem)

            num_itens = random.randint(1, 4)

            for id_item in range(1, num_itens + 1):
                produto = random.choice(produtos_disponiveis)
                qtd = random.randint(1, 3)
                preco_unitario = float(produto['p_venda'])
                subtotal = round(preco_unitario * qtd, 2)

                desconto_tipo, desconto_valor, valor_com_desconto = _sortear_desconto(subtotal, origem)
                status = _sortear_status(desconto_tipo)

                if status == 'cancelado':
                    valor_com_desconto = 0.0

                if produto.get('tipo_venda') == 'menu' and random.random() < 0.10:
                    observacao = random.choice(OBSERVACOES)
                else:
                    observacao = ''

                cod_item = f"ID_{seq_cod_item:05d}"
                item_individual = f"{produto['cod_prod']}_{id_item}_{random.randint(100000, 999999)}"

                historico.append({
                    'id_pedido': id_pedido,
                    'id_item': id_item,
                    'cod_item': cod_item,
                    'id_mesa': id_mesa,
                    'cod_prod': produto['cod_prod'],
                    'nome_prod': produto['nome'],
                    'quantidade': qtd,
                    'preco_unitario': preco_unitario,
                    'preco_final': preco_unitario,
                    'desconto_tipo': desconto_tipo,
                    'desconto_valor': desconto_valor,
                    'subtotal': subtotal,
                    'valor_com_desconto': valor_com_desconto,
                    'observacao': observacao,
                    'criado_em': criado_em,
                    'data_fechamento': fechado_em,
                    'fechado_em': fechado_em,
                    'status': status,
                    'categoria': produto.get('categoria', ''),
                    'tipo_venda': produto.get('tipo_venda', 'menu'),
                    'item_individual': item_individual,
                    'origem_venda': origem,
                    'taxa_entrega': taxa_entrega,
                    'taxa_embalagem': taxa_embalagem,
                    'id_cliente': id_cliente,
                    'metodo_pagamento': metodo_pagamento
                })

                seq_cod_item += 1

            seq_pedido += 1

    with open(os.path.join(DATA_DIR, "historico_pedidos.pkl"), 'wb') as f:
        pickle.dump(historico, f)

    print(f"historico_pedidos.pkl: {len(historico)} itens | {seq_pedido - 1} pedidos")


if __name__ == "__main__":
    popular_historico_pedidos(dias=180)