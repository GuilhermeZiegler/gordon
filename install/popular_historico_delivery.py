import os
import pickle
import random
from datetime import datetime, timedelta

from install.seed._common import DATA_DIR

MOTOBOYS = [
    'Anderson Silva', 'Bruno Costa', 'Cesar Santos', 'Diego Lima',
    'Eduardo Alves', 'Felipe Rocha', 'Gustavo Prado', 'Henrique Souza',
    'Igor Martins', 'Jonas Pereira', 'Kleber Ramos', 'Leandro Dias',
    'Marcos Vinicius', 'Nelson Barbosa', 'Otávio Freitas', 'Paulo Mendes'
]


def _parse_dt(s):
    return datetime.strptime(s, "%d/%m/%Y %H:%M:%S")


def _format_dt(dt):
    return dt.strftime("%d/%m/%Y %H:%M:%S")


def popular_historico_delivery():
    random.seed(42)

    historico_pedidos_path = os.path.join(DATA_DIR, "historico_pedidos.pkl")
    clientes_path = os.path.join(DATA_DIR, "clientes.pkl")

    with open(historico_pedidos_path, 'rb') as f:
        pedidos = pickle.load(f)

    with open(clientes_path, 'rb') as f:
        clientes = pickle.load(f)

    clientes_map = {c['id_cliente']: c for c in clientes}

    pedidos_delivery = [p for p in pedidos if p.get('origem_venda') == 'delivery']

    agrupados = {}
    for item in pedidos_delivery:
        id_pedido = item['id_pedido']
        agrupados.setdefault(id_pedido, []).append(item)

    ids_ordenados = sorted(agrupados.keys(), key=lambda x: agrupados[x][0]['criado_em'])

    total = len(ids_ordenados)

    if total == 0:
        with open(os.path.join(DATA_DIR, "delivery.pkl"), 'wb') as f:
            pickle.dump([], f)
        print("delivery.pkl: 0 registros (nenhum pedido de delivery)")
        return

    qtd_cancelados = max(1, int(total * 0.02))
    qtd_ativos = min(8, total)

    indices_cancelados = set(ids_ordenados[-qtd_cancelados:])
    indices_ativos = set(ids_ordenados[-(qtd_cancelados + qtd_ativos):-qtd_cancelados]) if qtd_cancelados + qtd_ativos <= total else set()

    status_ativos = ['preparando', 'pronto', 'em_rota', 'chegou']

    historico_delivery = []

    for id_pedido in ids_ordenados:
        itens = agrupados[id_pedido]
        primeiro = itens[0]

        id_cliente = primeiro.get('id_cliente', '')
        cliente = clientes_map.get(id_cliente)

        if cliente:
            telefone = cliente.get('telefone_principal', '')
            partes_end = [
                cliente.get('logradouro', ''),
                cliente.get('numero', ''),
                cliente.get('complemento', '')
            ]
            endereco_base = ' '.join([p for p in partes_end if p])
            bairro_cidade = ' - '.join([
                p for p in [
                    cliente.get('bairro', ''),
                    cliente.get('cidade', ''),
                    cliente.get('estado', '')
                ] if p
            ])
            if bairro_cidade:
                endereco = f"{endereco_base} ({bairro_cidade})"
            else:
                endereco = endereco_base
            referencia = cliente.get('referencia', '')
        else:
            telefone = ''
            endereco = ''
            referencia = ''

        itens_nao_cancelados = [i for i in itens if i.get('status') != 'cancelado']
        itens_resumo = ', '.join([
            f"{i['quantidade']}x {i['nome_prod']}"
            for i in itens_nao_cancelados
        ])

        valor_total = round(sum(float(i.get('valor_com_desconto', 0)) for i in itens_nao_cancelados), 2)
        taxa_entrega = float(primeiro.get('taxa_entrega', 0))

        criado_em_str = primeiro['criado_em']
        criado_dt = _parse_dt(criado_em_str)

        pronto_dt = criado_dt + timedelta(minutes=random.randint(20, 40))
        saiu_dt = pronto_dt + timedelta(minutes=random.randint(5, 15))
        chegou_dt = saiu_dt + timedelta(minutes=random.randint(10, 25))
        entregue_dt = chegou_dt + timedelta(minutes=random.randint(3, 10))

        pronto_em = _format_dt(pronto_dt)
        saiu_em = _format_dt(saiu_dt)
        chegou_em = _format_dt(chegou_dt)
        entregue_em = _format_dt(entregue_dt)

        if id_pedido in indices_cancelados:
            status_entrega = 'cancelado'
            motoboy = ''
            pronto_em = _format_dt(pronto_dt) if random.random() < 0.5 else ''
            saiu_em = ''
            chegou_em = ''
            entregue_em = ''
        elif id_pedido in indices_ativos:
            status_entrega = random.choice(status_ativos)
            motoboy = random.choice(MOTOBOYS) if status_entrega in ['em_rota', 'chegou'] else ''

            if status_entrega == 'preparando':
                pronto_em = ''
                saiu_em = ''
                chegou_em = ''
                entregue_em = ''
            elif status_entrega == 'pronto':
                saiu_em = ''
                chegou_em = ''
                entregue_em = ''
            elif status_entrega == 'em_rota':
                chegou_em = ''
                entregue_em = ''
            else:
                entregue_em = ''
        else:
            status_entrega = 'entregue'
            motoboy = random.choice(MOTOBOYS)

        historico_delivery.append({
            'id_pedido': id_pedido,
            'id_cliente': id_cliente,
            'telefone': telefone,
            'endereco': endereco,
            'referencia': referencia,
            'itens_resumo': itens_resumo,
            'valor_total': valor_total,
            'taxa_entrega': taxa_entrega,
            'criado_em': criado_em_str,
            'pronto_em': pronto_em,
            'saiu_entrega_em': saiu_em,
            'chegou_cliente_em': chegou_em,
            'entregue_em': entregue_em,
            'motoboy': motoboy,
            'status_entrega': status_entrega
        })

    with open(os.path.join(DATA_DIR, "delivery.pkl"), 'wb') as f:
        pickle.dump(historico_delivery, f)

    print(f"delivery.pkl: {len(historico_delivery)} registros")


if __name__ == "__main__":
    popular_historico_delivery()