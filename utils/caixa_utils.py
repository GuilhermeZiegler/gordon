import json
import pandas as pd
import streamlit as st

from datetime import datetime
from utils.db import ler_tabela, escrever_tabela, executar
from utils.pedidos_utils import gerar_id_pedido, gerar_cod_item, sincronizar_historico_pedido
from utils.movimentacoes_utils import baixar_por_produto


_cache_venda = {}
_cache_estorno = {}


def _carregar_jsonb(nome_tabela):
    df = ler_tabela(nome_tabela)

    if df.empty or "dados" not in df.columns:
        return None

    valor = df["dados"].iloc[0]

    if valor is None:
        return None

    if isinstance(valor, dict):
        return valor

    if isinstance(valor, str):
        try:
            return json.loads(valor)
        except Exception:
            return None

    return valor


def _salvar_jsonb(nome_tabela, dados):
    payload = json.dumps(dados, ensure_ascii=False, default=str)

    executar(f'TRUNCATE TABLE "{nome_tabela}"')
    executar(
        f'INSERT INTO "{nome_tabela}" (dados) VALUES (:d)',
        {"d": payload}
    )


def carregar_caixa():
    caixa = _carregar_jsonb("caixa")

    if caixa is None:
        caixa = {}

    caixa.setdefault("saldo_inicial", 0.0)
    caixa.setdefault("data_abertura", "")
    caixa.setdefault("data_fechamento", "")
    caixa.setdefault("status", "fechado")
    caixa.setdefault("vendas_mesa", 0.0)
    caixa.setdefault("vendas_balcao", 0.0)
    caixa.setdefault("vendas_takeaway", 0.0)
    caixa.setdefault("vendas_delivery", 0.0)
    caixa.setdefault("reembolso", 0.0)
    caixa.setdefault("pagamentos", [])
    caixa.setdefault("entradas", [])
    caixa.setdefault("saidas", [])
    caixa.setdefault("vendas_metodo", {})
    caixa.setdefault("fiados", [])
    caixa.setdefault("estornos", [])

    return caixa


def salvar_caixa(caixa):
    caixa.setdefault("fiados", [])
    caixa.setdefault("vendas_takeaway", 0.0)
    caixa.setdefault("estornos", [])

    _salvar_jsonb("caixa", caixa)


def carregar_produtos():
    return ler_tabela("produtos")


def carregar_historico_caixa():
    historico = _carregar_jsonb("historico_caixa")

    if not isinstance(historico, list):
        return []

    return historico


def salvar_historico_caixa(caixa):
    historico = carregar_historico_caixa()
    data_abertura = caixa.get("data_abertura", "")

    if data_abertura:
        historico = [
            h for h in historico
            if h.get("data_abertura", "") != data_abertura
        ]

    historico.append(caixa.copy())

    _salvar_jsonb("historico_caixa", historico)

    return True


def atualizar_historico_caixa(caixa):
    historico = carregar_historico_caixa()

    if not isinstance(historico, list):
        historico = []

    data_abertura = caixa.get("data_abertura", "")

    historico = [
        h for h in historico
        if h.get("data_abertura") != data_abertura
    ]

    historico.append(caixa.copy())

    _salvar_jsonb("historico_caixa", historico)


def calcular_saldo_caixa(caixa):
    total_entradas = sum(
        float(e.get("valor", 0)) for e in caixa.get("entradas", [])
    )

    total_estornos = sum(
        float(e.get("valor_estornado", 0)) for e in caixa.get("estornos", [])
    )

    total_saidas = (
        total_estornos
        + float(caixa.get("reembolso", 0) or 0)
        + sum(float(p.get("valor", 0)) for p in caixa.get("pagamentos", []))
        + sum(float(s.get("valor", 0)) for s in caixa.get("saidas", []))
    )

    saldo_final = (
        float(caixa.get("saldo_inicial", 0) or 0)
        + total_entradas
        - total_saidas
    )

    return saldo_final, total_entradas, total_saidas


def gerar_id_venda():
    from datetime import datetime as _dt

    ano_mes = _dt.now().strftime("%y%m")
    prefixo = f"VD{ano_mes}"

    if prefixo in _cache_venda:
        numero = _cache_venda[prefixo]
    else:
        maior = 0

        for cx in carregar_historico_caixa():
            for entrada in cx.get("entradas", []):
                id_v = str(entrada.get("id_venda", "") or "")
                if id_v.startswith(prefixo):
                    try:
                        n = int(id_v[len(prefixo):])
                        if n > maior:
                            maior = n
                    except ValueError:
                        pass

        caixa = carregar_caixa()
        for entrada in caixa.get("entradas", []):
            id_v = str(entrada.get("id_venda", "") or "")
            if id_v.startswith(prefixo):
                try:
                    n = int(id_v[len(prefixo):])
                    if n > maior:
                        maior = n
                except ValueError:
                    pass

        numero = maior + 1

    _cache_venda[prefixo] = numero + 1

    return f"{prefixo}{numero:04d}"


def gerar_id_estorno():
    from datetime import datetime as _dt

    ano_mes = _dt.now().strftime("%y%m")
    prefixo = f"EST{ano_mes}"

    if prefixo in _cache_estorno:
        numero = _cache_estorno[prefixo]
    else:
        maior = 0

        for cx in carregar_historico_caixa():
            for estorno in cx.get("estornos", []):
                id_e = str(estorno.get("id_estorno", "") or "")
                if id_e.startswith(prefixo):
                    try:
                        n = int(id_e[len(prefixo):])
                        if n > maior:
                            maior = n
                    except ValueError:
                        pass

        caixa = carregar_caixa()
        for estorno in caixa.get("estornos", []):
            id_e = str(estorno.get("id_estorno", "") or "")
            if id_e.startswith(prefixo):
                try:
                    n = int(id_e[len(prefixo):])
                    if n > maior:
                        maior = n
                except ValueError:
                    pass

        numero = maior + 1

    _cache_estorno[prefixo] = numero + 1

    return f"{prefixo}{numero:04d}"


def listar_vendas_estornaveis(periodo="Hoje"):
    from datetime import datetime, timedelta

    agora = datetime.now()

    if periodo == "Hoje":
        corte = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periodo == "Últimos 7 dias":
        corte = agora - timedelta(days=7)
    elif periodo == "Últimos 30 dias":
        corte = agora - timedelta(days=30)
    elif periodo == "Últimos 90 dias":
        corte = agora - timedelta(days=90)
    else:
        corte = None

    resultado = []
    vistos = set()

    def _adicionar(id_v, entrada, data_caixa):
        if not id_v or id_v in vistos:
            return
        data_str = entrada.get("data", "")
        if corte is not None:
            try:
                dt = datetime.strptime(data_str, "%d/%m/%Y %H:%M:%S")
            except Exception:
                try:
                    dt = datetime.strptime(data_str, "%d/%m/%Y")
                except Exception:
                    return
            if dt < corte:
                return
        vistos.add(id_v)
        resultado.append({
            "id_venda": id_v,
            "categoria": entrada.get("categoria", ""),
            "valor": float(entrada.get("valor", 0)),
            "metodo": entrada.get("metodo", ""),
            "descricao": entrada.get("descricao", ""),
            "data": data_str,
            "data_caixa": data_caixa,
        })

    for cx in carregar_historico_caixa():
        data_caixa = cx.get("data_abertura", "")
        for entrada in cx.get("entradas", []):
            id_v = str(entrada.get("id_venda", "") or "")
            _adicionar(id_v, entrada, data_caixa)

    caixa_atual = carregar_caixa()
    data_caixa = caixa_atual.get("data_abertura", "")
    for entrada in caixa_atual.get("entradas", []):
        id_v = str(entrada.get("id_venda", "") or "")
        _adicionar(id_v, entrada, data_caixa)

    resultado.sort(key=lambda x: x.get("data", ""), reverse=True)
    return resultado


def calcular_estornado_venda(id_venda):
    total = 0.0

    for cx in carregar_historico_caixa():
        for estorno in cx.get("estornos", []):
            if str(estorno.get("id_venda_original", "")) == str(id_venda):
                total += float(estorno.get("valor_estornado", 0))

    caixa = carregar_caixa()
    for estorno in caixa.get("estornos", []):
        if str(estorno.get("id_venda_original", "")) == str(id_venda):
            total += float(estorno.get("valor_estornado", 0))

    return round(total, 2)


def _aplicar_venda_nos_totais(caixa, entrada):
    categoria = entrada.get("categoria", "")
    metodo = entrada.get("metodo", "")
    valor = float(entrada.get("valor", 0.0))

    if categoria == "Mesa":
        caixa["vendas_mesa"] = caixa.get("vendas_mesa", 0.0) + valor
    elif categoria == "Takeaway":
        caixa["vendas_takeaway"] = caixa.get("vendas_takeaway", 0.0) + valor
    elif categoria in ["Balcão", "Bar", "Avulso"]:
        caixa["vendas_balcao"] = caixa.get("vendas_balcao", 0.0) + valor
    elif categoria == "Delivery":
        caixa["vendas_delivery"] = caixa.get("vendas_delivery", 0.0) + valor

    if metodo:
        caixa.setdefault("vendas_metodo", {})
        caixa["vendas_metodo"][metodo] = (
            caixa["vendas_metodo"].get(metodo, 0.0) + valor
        )


def _remover_venda_dos_totais(caixa, entrada):
    categoria = entrada.get("categoria", "")
    metodo = entrada.get("metodo", "")
    valor = float(entrada.get("valor", 0.0))

    if categoria == "Mesa":
        caixa["vendas_mesa"] = caixa.get("vendas_mesa", 0.0) - valor
    elif categoria == "Takeaway":
        caixa["vendas_takeaway"] = caixa.get("vendas_takeaway", 0.0) - valor
    elif categoria in ["Balcão", "Bar", "Avulso"]:
        caixa["vendas_balcao"] = caixa.get("vendas_balcao", 0.0) - valor
    elif categoria == "Delivery":
        caixa["vendas_delivery"] = caixa.get("vendas_delivery", 0.0) - valor

    if metodo and metodo in caixa.get("vendas_metodo", {}):
        caixa["vendas_metodo"][metodo] = (
            caixa["vendas_metodo"].get(metodo, 0.0) - valor
        )
        if abs(caixa["vendas_metodo"][metodo]) < 1e-9:
            caixa["vendas_metodo"][metodo] = 0.0


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
        id_venda = gerar_id_venda()

        caixa["fiados"].append({
            "id": id_fiado,
            "cliente": descricao if descricao else f"Venda {categoria}",
            "valor": valor,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "status": "pendente",
            "itens": descricao,
            "tipo": categoria,
            "metodo": "Fiado",
            "id_venda": id_venda
        })

        salvar_caixa(caixa)
        salvar_historico_caixa(caixa)

        if "caixa" in st.session_state:
            st.session_state.caixa = caixa

        return caixa, id_venda

    caixa.setdefault("entradas", [])
    caixa.setdefault("vendas_metodo", {})

    id_venda = gerar_id_venda()

    entrada = {
        "id_venda": id_venda,
        "categoria": categoria,
        "valor": valor,
        "metodo": metodo,
        "descricao": descricao,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }

    caixa["entradas"].append(entrada)
    _aplicar_venda_nos_totais(caixa, entrada)

    salvar_caixa(caixa)
    salvar_historico_caixa(caixa)

    if "caixa" in st.session_state:
        st.session_state.caixa = caixa

    return caixa, id_venda


def substituir_venda_no_caixa(id_venda, categoria, valor, metodo, descricao):
    caixa = carregar_caixa()
    caixa.setdefault("entradas", [])
    caixa.setdefault("vendas_metodo", {})

    idx = None
    for i, entrada in enumerate(caixa["entradas"]):
        if str(entrada.get("id_venda", "")) == str(id_venda):
            idx = i
            break

    if idx is None:
        entrada_nova = {
            "id_venda": id_venda,
            "categoria": categoria,
            "valor": valor,
            "metodo": metodo,
            "descricao": descricao,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        caixa["entradas"].append(entrada_nova)
        _aplicar_venda_nos_totais(caixa, entrada_nova)
    else:
        antiga = caixa["entradas"][idx]
        _remover_venda_dos_totais(caixa, antiga)

        nova = {
            "id_venda": id_venda,
            "categoria": categoria,
            "valor": valor,
            "metodo": metodo,
            "descricao": descricao,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        caixa["entradas"][idx] = nova
        _aplicar_venda_nos_totais(caixa, nova)

    salvar_caixa(caixa)
    salvar_historico_caixa(caixa)

    if "caixa" in st.session_state:
        st.session_state.caixa = caixa

    return caixa


def registrar_estorno(id_venda_original, valor_estornado, metodo, motivo, classificacao='outros'):
    venda = None

    for cx in carregar_historico_caixa():
        for entrada in cx.get("entradas", []):
            if str(entrada.get("id_venda", "")) == str(id_venda_original):
                venda = entrada
                break
        if venda:
            break

    if venda is None:
        caixa_atual = carregar_caixa()
        for entrada in caixa_atual.get("entradas", []):
            if str(entrada.get("id_venda", "")) == str(id_venda_original):
                venda = entrada
                break

    if venda is None:
        return False, "Venda original não encontrada"

    valor_venda = float(venda.get("valor", 0))
    ja_estornado = calcular_estornado_venda(id_venda_original)
    disponivel = round(valor_venda - ja_estornado, 2)

    valor_estornado = float(valor_estornado)

    if valor_estornado <= 0:
        return False, "Valor do estorno deve ser maior que zero"

    if valor_estornado > disponivel:
        return False, f"Valor excede o disponível para estorno (R$ {disponivel:.2f})"

    caixa = carregar_caixa()
    caixa.setdefault("estornos", [])

    id_estorno = gerar_id_estorno()

    tipo = "total" if abs(valor_estornado - disponivel) < 1e-9 else "parcial"

    caixa["estornos"].append({
        "id_estorno": id_estorno,
        "id_venda_original": id_venda_original,
        "valor_estornado": round(valor_estornado, 2),
        "valor_venda_original": round(valor_venda, 2),
        "tipo": tipo,
        "metodo": metodo,
        "motivo": motivo,
        "classificacao": classificacao,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    })

    salvar_caixa(caixa)
    salvar_historico_caixa(caixa)

    if "caixa" in st.session_state:
        st.session_state.caixa = caixa

    return True, id_estorno


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
        "pagamentos": [],
        "entradas": [],
        "saidas": [],
        "vendas_metodo": {},
        "fiados": [],
        "estornos": []
    }

    salvar_caixa(caixa)

    return caixa


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

    if "saldo_inicial" not in caixa:
        caixa["saldo_inicial"] = 0.0

    if "estornos" not in caixa:
        caixa["estornos"] = []

    return caixa