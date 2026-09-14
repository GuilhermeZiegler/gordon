import os
import pandas as pd
import pickle
import random
from datetime import datetime, timedelta
from collections import defaultdict

from install.seed._common import DATA_DIR, _c
from install.seed.insumos import INSUMOS
from install.seed.produtos import PRODUTOS
from install.seed.fichas import FICHAS
from utils.movimentacoes_utils import COLUNAS_MOVIMENTACOES

FORNECEDORES = ['Fornecedor A', 'Fornecedor B', 'Fornecedor C', 'Fornecedor D', 'Fornecedor E']

ESTOQUE_MINIMO = 5
FOLGA_SEMANAL = 1.20

USUARIO_SEED = 'seed'


def _parse_dt(s):
    return datetime.strptime(s, "%d/%m/%Y %H:%M:%S")


def _format_dt(dt, com_hora=True):
    if com_hora:
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    return dt.strftime("%d/%m/%Y")


def _converter_unidade(quantidade, origem, destino):
    if origem == destino:
        return quantidade
    if origem == 'g' and destino == 'kg':
        return quantidade / 1000
    if origem == 'kg' and destino == 'g':
        return quantidade * 1000
    if origem == 'ml' and destino == 'L':
        return quantidade / 1000
    if origem == 'L' and destino == 'ml':
        return quantidade * 1000
    if origem == 'un' and destino == 'un':
        return quantidade
    return None


def _calcular_consumo_item(cod_prod, quantidade):
    produto = next((p for p in PRODUTOS if str(p['cod_prod']) == str(cod_prod)), None)
    if not produto:
        return None, f"Produto {cod_prod} não encontrado"

    insumo_direto = produto.get('insumo_direto', '')

    ficha = FICHAS.get(str(cod_prod))

    if ficha:
        consumo = defaultdict(float)
        for id_insumo, qtd_ficha, unidade_ficha in ficha:
            insumo = next((i for i in INSUMOS if i['id_insumo'] == id_insumo), None)
            if not insumo:
                continue
            unidade_compra = insumo['unidade_compra']
            qtd_total = qtd_ficha * quantidade
            qtd_convertida = _converter_unidade(qtd_total, unidade_ficha, unidade_compra)
            if qtd_convertida is None:
                continue
            consumo[id_insumo] += qtd_convertida
        return dict(consumo), None

    if insumo_direto:
        insumo = next((i for i in INSUMOS if i['id_insumo'] == insumo_direto), None)
        if not insumo:
            return None, f"Insumo {insumo_direto} não encontrado"
        return {insumo_direto: quantidade}, None

    return None, f"Produto {cod_prod} sem ficha nem insumo direto"


def _novo_id_movimentacao(seq):
    return f"MOV-{seq:05d}"


def popular_historicos_estoque():
    random.seed(42)

    with open(os.path.join(DATA_DIR, "historico_pedidos.pkl"), 'rb') as f:
        pedidos = pickle.load(f)

    itens_validos = [
        p for p in pedidos
        if p.get('status') != 'cancelado'
    ]

    itens_por_dia = defaultdict(list)
    for item in itens_validos:
        dt = _parse_dt(item['criado_em'])
        dia = dt.date()
        itens_por_dia[dia].append(item)

    dias_ordenados = sorted(itens_por_dia.keys())

    if not dias_ordenados:
        print("Nenhum item válido para processar")
        return

    primeira_semana = dias_ordenados[:7]
    consumo_primeira_semana = defaultdict(float)

    for dia in primeira_semana:
        for item in itens_por_dia[dia]:
            consumo, _ = _calcular_consumo_item(item['cod_prod'], item['quantidade'])
            if consumo:
                for id_insumo, qtd in consumo.items():
                    consumo_primeira_semana[id_insumo] += qtd

    estoque_atual = {}
    for insumo in INSUMOS:
        id_insumo = insumo['id_insumo']
        consumo_semana = consumo_primeira_semana.get(id_insumo, 0)
        estoque_inicial = max(ESTOQUE_MINIMO + 1, round(consumo_semana * FOLGA_SEMANAL, 1))
        estoque_atual[id_insumo] = {
            'id_insumo': id_insumo,
            'nome_insumo': insumo['nome'],
            'unidade': insumo['unidade_compra'],
            'estoque': estoque_inicial
        }

    estoque_inicio_semana = {k: v['estoque'] for k, v in estoque_atual.items()}

    movimentacoes = []
    seq_mov = 1

    dia_anterior = None

    for dia in dias_ordenados:
        if dia.weekday() == 0 or dia_anterior is None:
            estoque_inicio_semana = {k: v['estoque'] for k, v in estoque_atual.items()}

        insumos_baixos = [
            id_insumo for id_insumo, info in estoque_atual.items()
            if info['estoque'] < ESTOQUE_MINIMO
        ]

        if insumos_baixos:
            fornecedor = random.choice(FORNECEDORES)
            nota_fiscal = f"NF-{random.randint(1000, 9999)}"
            data_compra_dt = datetime.combine(dia, datetime.min.time()).replace(hour=8)

            for id_insumo in insumos_baixos:
                info = estoque_atual[id_insumo]
                alvo = estoque_inicio_semana.get(id_insumo, info['estoque'])
                qtd_repor = round(max(0.0, alvo - info['estoque']), 1)

                if qtd_repor <= 0:
                    continue

                insumo = next((i for i in INSUMOS if i['id_insumo'] == id_insumo), None)
                if not insumo:
                    continue

                preco_unitario = float(insumo['preco_unitario'])

                movimentacoes.append({
                    'id_movimentacao': _novo_id_movimentacao(seq_mov),
                    'tipo': 'compra',
                    'id_insumo': id_insumo,
                    'quantidade': qtd_repor,
                    'unidade': insumo['unidade_compra'],
                    'data_movimentacao': _format_dt(data_compra_dt),
                    'preco_unitario': preco_unitario,
                    'fornecedor': fornecedor,
                    'nota_fiscal': nota_fiscal,
                    'data_validade': _format_dt(
                        datetime.combine(dia, datetime.min.time()) + timedelta(days=random.randint(15, 60)),
                        com_hora=False
                    ),
                    'id_pedido': None,
                    'cod_item': None,
                    'cod_prod': None,
                    'motivo': None,
                    'usuario': USUARIO_SEED,
                    'observacao': None
                })
                seq_mov += 1

                info['estoque'] += qtd_repor

        for item in itens_por_dia[dia]:
            consumo, erro = _calcular_consumo_item(item['cod_prod'], item['quantidade'])

            if erro:
                continue

            for id_insumo, qtd in consumo.items():
                if id_insumo not in estoque_atual:
                    continue

                insumo = next((i for i in INSUMOS if i['id_insumo'] == id_insumo), None)
                if not insumo:
                    continue

                estoque_atual[id_insumo]['estoque'] -= qtd

                movimentacoes.append({
                    'id_movimentacao': _novo_id_movimentacao(seq_mov),
                    'tipo': 'venda',
                    'id_insumo': id_insumo,
                    'quantidade': round(qtd, 3),
                    'unidade': insumo['unidade_compra'],
                    'data_movimentacao': item['criado_em'],
                    'preco_unitario': None,
                    'fornecedor': None,
                    'nota_fiscal': None,
                    'data_validade': None,
                    'id_pedido': item['id_pedido'],
                    'cod_item': item['cod_item'],
                    'cod_prod': item['cod_prod'],
                    'motivo': None,
                    'usuario': USUARIO_SEED,
                    'observacao': None
                })
                seq_mov += 1

        dia_anterior = dia

    df_movimentacoes = pd.DataFrame(movimentacoes, columns=COLUNAS_MOVIMENTACOES)

    os.makedirs(os.path.dirname(_c["movimentacoes"]), exist_ok=True)

    with open(_c["movimentacoes"], 'wb') as f:
        pickle.dump(df_movimentacoes, f)

    compras = df_movimentacoes[df_movimentacoes['tipo'] == 'compra']
    vendas = df_movimentacoes[df_movimentacoes['tipo'] == 'venda']

    print(f"movimentacoes.pkl: {len(df_movimentacoes)} registros")
    print(f"  compras: {len(compras)}")
    print(f"  vendas: {len(vendas)}")


if __name__ == "__main__":
    popular_historicos_estoque()