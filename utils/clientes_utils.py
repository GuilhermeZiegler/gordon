import os
import pickle
import time
import requests
from datetime import datetime

from utils.paths import get_caminhos

_c = get_caminhos()
CAMINHO_CLIENTES = os.path.join(os.path.dirname(_c["caixa"]), "clientes.pkl")


def carregar_clientes():
    if os.path.exists(CAMINHO_CLIENTES):
        with open(CAMINHO_CLIENTES, 'rb') as f:
            return pickle.load(f)
    return []


def salvar_clientes(clientes):
    os.makedirs(os.path.dirname(CAMINHO_CLIENTES), exist_ok=True)
    with open(CAMINHO_CLIENTES, 'wb') as f:
        pickle.dump(clientes, f)


def gerar_id_cliente(clientes):
    numeros = []
    for c in clientes:
        id_c = str(c.get('id_cliente', ''))
        if id_c.startswith('CLI-'):
            try:
                numeros.append(int(id_c.replace('CLI-', '')))
            except ValueError:
                pass
    proximo = max(numeros) + 1 if numeros else 1
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


def geocodificar_pendentes(email_contato, progresso_callback=None):
    clientes = carregar_clientes()
    total = len(clientes)
    pendentes = [
        i for i, c in enumerate(clientes)
        if not str(c.get('latitude', '')).strip() and _montar_endereco(c).strip()
    ]

    if not pendentes:
        return 0

    processados = 0

    for idx, i in enumerate(pendentes):
        c = _garantir_campos(clientes[i])
        coord = geocodificar_endereco(c, email_contato)
        if coord:
            clientes[i]['latitude'] = coord[0]
            clientes[i]['longitude'] = coord[1]
            processados += 1

        if progresso_callback:
            progresso_callback(idx + 1, len(pendentes), c.get('nome_cliente', ''))

        time.sleep(1.1)

    salvar_clientes(clientes)
    return processados