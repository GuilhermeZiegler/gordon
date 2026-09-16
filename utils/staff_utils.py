import hashlib
import pandas as pd
from utils.db import ler_tabela, escrever_tabela

ADMIN_FIXO = {
    'id_funcionario': 'FUN-000',
    'nome': 'Admin Master',
    'cargo': 'Gerente',
    'telefone': '',
    'email': '',
    'endereco': '',
    'valor_dia': 0.0,
    'ativo': True,
    'login': 'admin',
    'senha_hash': hashlib.sha256('GordonAdmin$'.encode('utf-8')).hexdigest(),
    'nivel_acesso': 'admin',
    'fixo': True
}


def carregar_funcionarios():
    df = ler_tabela("funcionarios")

    if df.empty:
        return []

    registros = df.to_dict(orient="records")

    for f in registros:
        f['ativo'] = bool(f.get('ativo', True))
        f['fixo'] = bool(f.get('fixo', False))
        f['valor_dia'] = float(f.get('valor_dia', 0.0) or 0.0)

    return registros


def salvar_funcionarios(lista):
    df = pd.DataFrame(lista)

    escrever_tabela("funcionarios", df)


def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def gerar_id_funcionario(lista=None):
    from utils.db import proximo_id_numerico

    proximo = proximo_id_numerico("funcionarios", "id_funcionario", "FUN-")
    return f"FUN-{proximo:03d}"


def garantir_campos_funcionario(func):
    func.setdefault('id_funcionario', '')
    func.setdefault('nome', '')
    func.setdefault('cargo', '')
    func.setdefault('telefone', '')
    func.setdefault('email', '')
    func.setdefault('endereco', '')
    func.setdefault('valor_dia', 0.0)
    func.setdefault('ativo', True)
    func.setdefault('login', '')
    func.setdefault('senha_hash', '')
    func.setdefault('nivel_acesso', 'operador')
    return func


def garantir_admin_fixo(funcionarios):
    for i, f in enumerate(funcionarios):
        if f.get('login', '').strip().lower() == 'admin':
            funcionarios[i] = ADMIN_FIXO.copy()
            return funcionarios
    funcionarios.insert(0, ADMIN_FIXO.copy())
    return funcionarios


def carregar_funcionarios_com_admin():
    funcionarios = carregar_funcionarios()

    if funcionarios:
        funcionarios = garantir_admin_fixo(funcionarios)
        salvar_funcionarios(funcionarios)
        return funcionarios

    funcionarios = [ADMIN_FIXO.copy()]
    salvar_funcionarios(funcionarios)
    return funcionarios