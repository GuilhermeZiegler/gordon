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

    for dia in dias_ordenados:
        itens_dia = pedidos_por_dia[dia]
        data_str = dia.strftime("%d/%m/%Y")

        # ================== VENDAS DO DIA ==================
        vendas_mesa = 0.0
        vendas_takeaway = 0.0
        vendas_delivery = 0.0
        vendas_balcao = 0.0

        vendas_metodo = defaultdict(float)
        entradas_por_origem = defaultdict(float)
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

            if metodo == 'Fiado':
                novos_fiados.append({
                    'id': seq_fiado,
                    'cliente': f"Fiado {id_pedido}",
                    'valor': valor_total,
                    'data': itens[0]['criado_em'],
                    'status': 'pendente',
                    'itens': ', '.join([f"{i['quantidade']}x {i['nome_prod']}" for i in itens]),
                    'tipo': origem.capitalize(),
                    'metodo': 'Fiado'
                })
                seq_fiado += 1
                continue

            if origem == 'mesa':
                vendas_mesa += valor_total
                entradas_por_origem['Mesa'] += valor_total
            elif origem == 'takeaway':
                vendas_takeaway += valor_total
                entradas_por_origem['Takeaway'] += valor_total
            elif origem == 'delivery':
                vendas_delivery += valor_total
                entradas_por_origem['Delivery'] += valor_total
            elif origem == 'caixa':
                vendas_balcao += valor_total
                entradas_por_origem['Balcão'] += valor_total

            if metodo:
                vendas_metodo[metodo] += valor_total

        # ================== QUITAÇÃO DE FIADOS ==================
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
                entradas_por_origem['Quitação Fiado'] += fiado['valor']
            else:
                fiados_pendentes_agora.append(fiado)

        fiados_dia = fiados_pendentes_agora + novos_fiados

        # ================== SALDO INICIAL ==================
        saldo_inicial = random.randint(100, 500)

        # ================== ENTRADAS ==================
        entradas = []
        for categoria, valor in entradas_por_origem.items():
            if valor <= 0:
                continue
            entradas.append({
                'categoria': categoria,
                'valor': round(valor, 2),
                'metodo': 'Diversos',
                'descricao': f"Vendas {categoria.lower()} - {data_str}",
                'data': f"{data_str} 22:00:00"
            })

        # ================== SAÍDAS ==================
        saidas = []
        if random.random() < 0.20:
            saidas.append({
                'descricao': 'Troco',
                'valor': round(random.uniform(10, 50), 2),
                'data': f"{data_str} {random.randint(8, 22):02d}:{random.randint(0, 59):02d}",
                'metodo': 'Dinheiro'
            })

        # ================== PAGAMENTOS ==================
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

        # ================== REEMBOLSO / ESTORNO ==================
        reembolso = round(random.uniform(0, 30), 2) if random.random() < 0.10 else 0.0
        estorno = round(random.uniform(0, 20), 2) if random.random() < 0.05 else 0.0

        # ================== SNAPSHOT ==================
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
            'estorno': estorno,
            'pagamentos': pagamentos,
            'entradas': entradas,
            'saidas': saidas,
            'vendas_metodo': {k: round(v, 2) for k, v in vendas_metodo.items()},
            'fiados': fiados_dia
        })

        fiados_rolados = [f for f in fiados_dia if f.get('status') == 'pendente']

    with open(os.path.join(DATA_DIR, "historico_caixa.pkl"), 'wb') as f:
        pickle.dump(historico_caixa, f)

    print(f"historico_caixa.pkl: {len(historico_caixa)} dias")


if __name__ == "__main__":
    popular_historico_caixa()