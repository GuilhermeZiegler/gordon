import os
import pickle
import random
from datetime import datetime, timedelta
from collections import defaultdict

from install.seed._common import DATA_DIR
from install.seed.funcionarios import FUNCIONARIOS

FORNECEDORES_PAGAMENTO = [f['nome'] for f in FUNCIONARIOS]

DIAS_SEMANA_PAGAMENTO = 0  # segunda


def _parse_dt(s):
    return datetime.strptime(s, "%d/%m/%Y %H:%M:%S")


def _gerar_id_venda(ano_mes, seq):
    return f"VD{ano_mes}{seq:04d}"


def popular_historico_caixa():
    random.seed(42)

    with open(os.path.join(DATA_DIR, "historico_pedidos.pkl"), 'rb') as f:
        pedidos = pickle.load(f)

    pedidos_por_dia = defaultdict(list)
    for item in pedidos:
        dt = _parse_dt(item['criado_em'])
        dia = dt.date()
        pedidos_por_dia[dia].append(item)

    dias_ordenados = sorted(pedidos_por_dia.keys())

    if not dias_ordenados:
        print("Nenhum pedido encontrado")
        return

    historico_caixa = []
    fiados_rolados = []
    seq_fiado = 1

    seq_venda_por_mes = defaultdict(int)

    for dia in dias_ordenados:
        itens_dia = pedidos_por_dia[dia]
        data_str = dia.strftime("%d/%m/%Y")
        ano_mes = dia.strftime("%y%m")

        vendas_mesa = 0.0
        vendas_takeaway = 0.0
        vendas_delivery = 0.0
        vendas_balcao = 0.0

        vendas_metodo = defaultdict(float)
        entradas = []
        pedidos_agrupados = defaultdict(list)

        for item in itens_dia:
            if item.get('status') == 'cancelado':
                continue
            pedidos_agrupados[item['id_pedido']].append(item)

        novos_fiados = []

        for id_pedido, itens in pedidos_agrupados.items():
            valor_itens = round(sum(float(i.get('valor_com_desconto', 0)) for i in itens), 2)
            taxa_emb = float(itens[0].get('taxa_embalagem', 0))
            taxa_ent = float(itens[0].get('taxa_entrega', 0))
            origem = itens[0].get('origem_venda', '')
            metodo = itens[0].get('metodo_pagamento', '')

            if origem == 'mesa':
                valor_total = valor_itens
            elif origem == 'takeaway':
                valor_total = valor_itens + taxa_emb
            elif origem == 'delivery':
                valor_total = valor_itens + taxa_emb + taxa_ent
            elif origem == 'caixa':
                valor_total = valor_itens
            else:
                continue

            if valor_total <= 0:
                continue

            if metodo == 'Fiado':
                seq_venda_por_mes[ano_mes] += 1
                id_venda = _gerar_id_venda(ano_mes, seq_venda_por_mes[ano_mes])

                novos_fiados.append({
                    'id': seq_fiado,
                    'cliente': f"Fiado {id_pedido}",
                    'valor': valor_total,
                    'data': itens[0]['criado_em'],
                    'status': 'pendente',
                    'itens': ', '.join([f"{i['quantidade']}x {i['nome_prod']}" for i in itens]),
                    'tipo': origem.capitalize(),
                    'metodo': 'Fiado',
                    'id_venda': id_venda
                })
                seq_fiado += 1
                continue

            categoria_entrada = ''
            if origem == 'mesa':
                vendas_mesa += valor_total
                categoria_entrada = 'Mesa'
            elif origem == 'takeaway':
                vendas_takeaway += valor_total
                categoria_entrada = 'Takeaway'
            elif origem == 'delivery':
                vendas_delivery += valor_total
                categoria_entrada = 'Delivery'
            elif origem == 'caixa':
                vendas_balcao += valor_total
                categoria_entrada = 'Balcão'

            if metodo:
                vendas_metodo[metodo] += valor_total

            seq_venda_por_mes[ano_mes] += 1
            id_venda = _gerar_id_venda(ano_mes, seq_venda_por_mes[ano_mes])

            entrada_dt = _parse_dt(itens[0]['criado_em']) + timedelta(minutes=random.randint(30, 90))
            entrada_data = entrada_dt.strftime("%d/%m/%Y %H:%M:%S")

            entradas.append({
                'id_venda': id_venda,
                'categoria': categoria_entrada,
                'valor': round(valor_total, 2),
                'metodo': metodo,
                'descricao': f"{categoria_entrada} - Pedido {id_pedido}",
                'data': entrada_data
            })

        fiados_pendentes_agora = []
        for fiado in fiados_rolados:
            if fiado.get('status') != 'pendente':
                continue
            if random.random() < 0.60:
                data_pag = (datetime.combine(dia, datetime.min.time()) + timedelta(hours=random.randint(10, 20))).strftime("%d/%m/%Y %H:%M:%S")
                fiado['status'] = 'pago'
                fiado['data_pagamento'] = data_pag

                vendas_balcao += fiado['valor']
                vendas_metodo['Fiado'] += fiado['valor']

                seq_venda_por_mes[ano_mes] += 1
                id_venda = _gerar_id_venda(ano_mes, seq_venda_por_mes[ano_mes])

                entradas.append({
                    'id_venda': id_venda,
                    'categoria': 'Quitação Fiado',
                    'valor': round(fiado['valor'], 2),
                    'metodo': 'Fiado',
                    'descricao': f"Quitação - {fiado['cliente']}",
                    'data': data_pag
                })
            else:
                fiados_pendentes_agora.append(fiado)

        fiados_dia = fiados_pendentes_agora + novos_fiados

        saldo_inicial = random.randint(100, 500)

        saidas = []
        if random.random() < 0.20:
            saidas.append({
                'descricao': 'Troco',
                'valor': round(random.uniform(10, 50), 2),
                'data': f"{data_str} {random.randint(8, 22):02d}:{random.randint(0, 59):02d}",
                'metodo': 'Dinheiro'
            })

        pagamentos = []
        if dia.weekday() == DIAS_SEMANA_PAGAMENTO:
            for func in random.sample(FORNECEDORES_PAGAMENTO, random.randint(2, 4)):
                pagamentos.append({
                    'funcionario': func,
                    'valor': round(random.uniform(50, 200), 2),
                    'descricao': f'Pagamento semanal - {func}',
                    'data': f"{data_str} 20:00:00",
                    'metodo': 'Dinheiro'
                })

        reembolso = round(random.uniform(0, 30), 2) if random.random() < 0.10 else 0.0

        historico_caixa.append({
            'saldo_inicial': saldo_inicial,
            'data_abertura': f"{data_str} 08:00:00",
            'data_fechamento': f"{data_str} 22:00:00",
            'status': 'fechado',
            'vendas_mesa': round(vendas_mesa, 2),
            'vendas_balcao': round(vendas_balcao, 2),
            'vendas_delivery': round(vendas_delivery, 2),
            'vendas_takeaway': round(vendas_takeaway, 2),
            'reembolso': reembolso,
            'pagamentos': pagamentos,
            'entradas': entradas,
            'saidas': saidas,
            'vendas_metodo': {k: round(v, 2) for k, v in vendas_metodo.items()},
            'fiados': fiados_dia,
            'estornos': []
        })

        fiados_rolados = [f for f in fiados_dia if f.get('status') == 'pendente']

    with open(os.path.join(DATA_DIR, "historico_caixa.pkl"), 'wb') as f:
        pickle.dump(historico_caixa, f)

    print(f"historico_caixa.pkl: {len(historico_caixa)} dias")


if __name__ == "__main__":
    popular_historico_caixa()