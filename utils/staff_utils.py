import os
import pickle
import hashlib

from utils.paths import get_caminhos

_c = get_caminhos()
CAMINHO_FUNCIONARIOS = os.path.join(
    os.path.dirname(_c["caixa"]),
    "funcionarios.pkl"
)

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
    if os.path.exists(CAMINHO_FUNCIONARIOS):
        with open(CAMINHO_FUNCIONARIOS, "rb") as f:
            return pickle.load(f)
    return []


def salvar_funcionarios(lista):
    os.makedirs(os.path.dirname(CAMINHO_FUNCIONARIOS), exist_ok=True)
    with open(CAMINHO_FUNCIONARIOS, "wb") as f:
        pickle.dump(lista, f)


def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def gerar_id_funcionario(lista):
    numeros = []
    for f in lista:
        id_f = str(f.get('id_funcionario', ''))
        if id_f.startswith('FUN-'):
            try:
                numeros.append(int(id_f.replace('FUN-', '')))
            except ValueError:
                pass
    proximo = max(numeros) + 1 if numeros else 1
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