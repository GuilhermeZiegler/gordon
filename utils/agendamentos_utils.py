import os
import pickle
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from utils.paths import get_caminhos

_c = get_caminhos()
CAMINHO_AGENDAMENTOS = os.path.join(os.path.dirname(_c["caixa"]), "agendamentos.pkl")

COLUNAS_AGENDAMENTOS = [
    'id_agendamento',
    'descricao',
    'valor',
    'data_vencimento',
    'categoria',
    'fornecedor',
    'metodo_pagamento',
    'recorrente',
    'periodicidade',
    'status',
    'data_pagamento',
    'observacao'
]

CATEGORIAS_AGENDAMENTO = [
    'Aluguel', 'Energia', 'Água', 'Internet', 'Telefone',
    'Folha de Pagamento', 'Fornecedor', 'Impostos', 'Manutenção',
    'Marketing', 'Software', 'Outros'
]

PERIODICIDADES = ['mensal', 'semanal', 'quinzenal', 'anual']


def carregar_agendamentos():
    if os.path.exists(CAMINHO_AGENDAMENTOS):
        with open(CAMINHO_AGENDAMENTOS, 'rb') as f:
            dados = pickle.load(f)
        if isinstance(dados, list):
            return pd.DataFrame(dados) if dados else pd.DataFrame(columns=COLUNAS_AGENDAMENTOS)
        return dados
    return pd.DataFrame(columns=COLUNAS_AGENDAMENTOS)


def salvar_agendamentos(df):
    os.makedirs(os.path.dirname(CAMINHO_AGENDAMENTOS), exist_ok=True)
    with open(CAMINHO_AGENDAMENTOS, 'wb') as f:
        pickle.dump(df, f)


def gerar_id_agendamento():
    df = carregar_agendamentos()
    if df.empty:
        return "AGD-00001"

    numeros = []
    for id_a in df['id_agendamento'].astype(str):
        if id_a.startswith('AGD-'):
            try:
                numeros.append(int(id_a.replace('AGD-', '')))
            except ValueError:
                pass

    proximo = max(numeros) + 1 if numeros else 1
    return f"AGD-{proximo:05d}"


def _proxima_data(data_str, periodicidade):
    dt = datetime.strptime(data_str, "%d/%m/%Y")
    if periodicidade == 'mensal':
        return (dt + relativedelta(months=1)).strftime("%d/%m/%Y")
    if periodicidade == 'semanal':
        return (dt + timedelta(days=7)).strftime("%d/%m/%Y")
    if periodicidade == 'quinzenal':
        return (dt + timedelta(days=15)).strftime("%d/%m/%Y")
    if periodicidade == 'anual':
        return (dt + relativedelta(years=1)).strftime("%d/%m/%Y")
    return None


def criar_agendamento(descricao, valor, data_vencimento, categoria, fornecedor='', metodo_pagamento='Pix', recorrente=False, periodicidade='mensal', observacao=''):
    novo = {
        'id_agendamento': gerar_id_agendamento(),
        'descricao': descricao,
        'valor': float(valor),
        'data_vencimento': data_vencimento,
        'categoria': categoria,
        'fornecedor': fornecedor,
        'metodo_pagamento': metodo_pagamento,
        'recorrente': bool(recorrente),
        'periodicidade': periodicidade if recorrente else '',
        'status': 'pendente',
        'data_pagamento': '',
        'observacao': observacao
    }

    df = carregar_agendamentos()
    df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
    salvar_agendamentos(df)
    return novo


def pagar_agendamento(id_agendamento):
    df = carregar_agendamentos()

    idx = df[df['id_agendamento'] == id_agendamento].index
    if idx.empty:
        return False, "Agendamento não encontrado"

    idx = idx[0]
    registro = df.loc[idx].to_dict()

    if registro['status'] != 'pendente':
        return False, f"Agendamento {id_agendamento} não está pendente"

    hoje = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    df.loc[idx, 'status'] = 'pago'
    df.loc[idx, 'data_pagamento'] = hoje

    if registro['recorrente'] and registro['periodicidade']:
        proxima = _proxima_data(registro['data_vencimento'], registro['periodicidade'])
        if proxima:
            novo_registro = registro.copy()
            novo_registro['id_agendamento'] = gerar_id_agendamento()
            novo_registro['data_vencimento'] = proxima
            novo_registro['status'] = 'pendente'
            novo_registro['data_pagamento'] = ''

            df = pd.concat([df, pd.DataFrame([novo_registro])], ignore_index=True)

    salvar_agendamentos(df)
    return True, f"Agendamento {id_agendamento} pago"


def cancelar_agendamento(id_agendamento):
    df = carregar_agendamentos()

    idx = df[df['id_agendamento'] == id_agendamento].index
    if idx.empty:
        return False, "Agendamento não encontrado"

    idx = idx[0]

    if df.loc[idx, 'status'] != 'pendente':
        return False, f"Agendamento {id_agendamento} não está pendente"

    df.loc[idx, 'status'] = 'cancelado'
    salvar_agendamentos(df)
    return True, f"Agendamento {id_agendamento} cancelado"


def importar_agendamentos_excel(df_upload):
    importados = 0
    erros = []

    obrigatorias = ['descricao', 'valor', 'data_vencimento', 'categoria']
    ausentes = [c for c in obrigatorias if c not in df_upload.columns]

    if ausentes:
        return 0, [f"Colunas obrigatórias faltando: {', '.join(ausentes)}"]

    for idx, row in df_upload.iterrows():
        try:
            descricao = str(row['descricao']).strip()
            valor = float(row['valor'])
            data_vencimento = str(row['data_vencimento']).strip()
            categoria = str(row['categoria']).strip()
            fornecedor = str(row.get('fornecedor', '')).strip() if pd.notna(row.get('fornecedor', '')) else ''
            metodo_pagamento = str(row.get('metodo_pagamento', 'Pix')).strip() if pd.notna(row.get('metodo_pagamento', 'Pix')) else 'Pix'
            recorrente_raw = str(row.get('recorrente', '')).strip().lower()
            recorrente = recorrente_raw in ['sim', 'true', '1', 'yes', 's']
            periodicidade = str(row.get('periodicidade', 'mensal')).strip().lower() if pd.notna(row.get('periodicidade', 'mensal')) else 'mensal'
            observacao = str(row.get('observacao', '')).strip() if pd.notna(row.get('observacao', '')) else ''

            criar_agendamento(
                descricao=descricao,
                valor=valor,
                data_vencimento=data_vencimento,
                categoria=categoria,
                fornecedor=fornecedor,
                metodo_pagamento=metodo_pagamento,
                recorrente=recorrente,
                periodicidade=periodicidade,
                observacao=observacao
            )
            importados += 1
        except Exception as e:
            erros.append(f"Linha {idx+2}: {str(e)}")

    return importados, erros


def listar_pendentes():
    df = carregar_agendamentos()
    if df.empty:
        return df
    return df[df['status'] == 'pendente'].copy()


def listar_vencidos():
    df = listar_pendentes()
    if df.empty:
        return df

    hoje = datetime.now().date()
    df['data_venc_dt'] = pd.to_datetime(df['data_vencimento'], format="%d/%m/%Y", errors='coerce').dt.date
    vencidos = df[df['data_venc_dt'] <= hoje].copy()
    return vencidos.drop(columns=['data_venc_dt'])


def listar_pagos():
    df = carregar_agendamentos()
    if df.empty:
        return df
    return df[df['status'] == 'pago'].copy()