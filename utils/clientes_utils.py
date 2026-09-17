import time
import requests
import pandas as pd

from datetime import datetime

from utils.db import ler_tabela, escrever_tabela


def carregar_clientes():
    df = ler_tabela("clientes")

    if df.empty:
        return []

    registros = df.to_dict(orient="records")

    for c in registros:
        c['ativo'] = bool(c.get('ativo', True))

    return registros


def salvar_clientes(clientes):
    df = pd.DataFrame(clientes)

    for col in ['latitude', 'longitude']:
        if col in df.columns:
            df[col] = df[col].replace('', None)

    escrever_tabela("clientes", df)


def gerar_id_cliente(clientes=None):
    from utils.db import obter_proximo_id

    proximo = obter_proximo_id("clientes", "id_cliente", "CLI-")
    return f"CLI-{proximo:03d}"


def buscar_clientes_por_nome(termo):
    clientes = carregar_clientes()
    termo = termo.strip().lower()
    if not termo:
        return []
    return [
        c for c in clientes
        if termo in str(c.get('nome_cliente', '')).lower()
    ]


def _cliente_base(nome):
    return {
        'id_cliente': '',
        'nome_cliente': nome.strip(),
        'telefone_principal': '',
        'telefone_secundario': '',
        'email': '',
        'cep': '',
        'logradouro': '',
        'numero': '',
        'complemento': '',
        'bairro': '',
        'cidade': '',
        'estado': '',
        'referencia': '',
        'data_cadastro': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'ativo': True,
        'latitude': '',
        'longitude': ''
    }


def criar_cliente_minimo(nome):
    clientes = carregar_clientes()
    novo = _cliente_base(nome)
    novo['id_cliente'] = gerar_id_cliente(clientes)
    clientes.append(novo)
    salvar_clientes(clientes)
    return novo


def _garantir_campos(cliente):
    cliente.setdefault('latitude', '')
    cliente.setdefault('longitude', '')
    return cliente


def _montar_endereco(cliente):
    partes = [
        cliente.get('logradouro', ''),
        cliente.get('numero', ''),
        cliente.get('bairro', ''),
        cliente.get('cidade', ''),
        cliente.get('estado', ''),
        cliente.get('cep', '')
    ]
    return ', '.join([p for p in partes if str(p).strip()])


def geocodificar_endereco(cliente, email_contato):
    if not email_contato:
        return None

    logradouro = str(cliente.get('logradouro', '')).strip()
    numero = str(cliente.get('numero', '')).strip()
    bairro = str(cliente.get('bairro', '')).strip()
    cidade = str(cliente.get('cidade', '')).strip()
    estado = str(cliente.get('estado', '')).strip()
    cep = str(cliente.get('cep', '')).strip()

    tentativas = [
        ', '.join([p for p in [cep, cidade, estado] if p]),
        ', '.join([p for p in [logradouro, bairro, cidade, estado] if p]),
        ', '.join([p for p in [logradouro, cidade, estado] if p]),
        ', '.join([p for p in [bairro, cidade, estado] if p]),
        ', '.join([p for p in [cidade, estado] if p]),
    ]

    tentativas = [t for t in tentativas if t.strip()]

    for endereco in tentativas:
        try:
            r = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": endereco, "format": "json", "limit": 1},
                headers={"User-Agent": f"consumer/1.0 ({email_contato})"},
                timeout=10,
                verify=False
            )
            if r.status_code != 200:
                continue
            dados = r.json()
            if dados:
                return float(dados[0]['lat']), float(dados[0]['lon'])
        except Exception:
            continue
        time.sleep(1.1)

    return None


def geocodificar_cliente(id_cliente, email_contato):
    clientes = carregar_clientes()
    for i, c in enumerate(clientes):
        if c.get('id_cliente') == id_cliente:
            coord = geocodificar_endereco(c, email_contato)
            if coord:
                clientes[i]['latitude'] = coord[0]
                clientes[i]['longitude'] = coord[1]
                salvar_clientes(clientes)
                return True
            return False
    return False


def geocodificar_pendentes(email_contato, progresso_callback=None, salvar_cada=5):
    clientes = carregar_clientes()

    pendentes = [
        i for i, c in enumerate(clientes)
        if not str(c.get('latitude', '')).strip() and _montar_endereco(c).strip()
    ]

    if not pendentes:
        return 0

    processados = 0
    nao_salvos = 0

    for idx, i in enumerate(pendentes):
        c = _garantir_campos(clientes[i])
        coord = geocodificar_endereco(c, email_contato)

        if coord:
            clientes[i]['latitude'] = coord[0]
            clientes[i]['longitude'] = coord[1]
            processados += 1
            nao_salvos += 1

        if progresso_callback:
            progresso_callback(idx + 1, len(pendentes), c.get('nome_cliente', ''))

        if nao_salvos >= salvar_cada:
            try:
                salvar_clientes(clientes)
                nao_salvos = 0
            except Exception:
                pass

        time.sleep(1.1)

    if nao_salvos > 0:
        try:
            salvar_clientes(clientes)
        except Exception:
            pass

    return processados