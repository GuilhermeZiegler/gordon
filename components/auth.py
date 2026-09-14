import streamlit as st
import hashlib
import os
import pickle
import time
from pathlib import Path


_CAMINHO_FUNCIONARIOS = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
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

PERMISSOES = {
    'admin': [
        'caixa', 'mesas', 'pedidos', 'produtos', 'estoque',
        'indicadores', 'clientes', 'delivery', 'configuracoes', 'staff'
    ],
    'operador': ['pedidos']
}


def _hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def _garantir_admin_fixo(funcionarios):
    for i, f in enumerate(funcionarios):
        if f.get('login', '').strip().lower() == 'admin':
            funcionarios[i] = ADMIN_FIXO.copy()
            return funcionarios
    funcionarios.insert(0, ADMIN_FIXO.copy())
    return funcionarios


def _salvar_funcionarios(funcionarios):
    os.makedirs(os.path.dirname(_CAMINHO_FUNCIONARIOS), exist_ok=True)
    with open(_CAMINHO_FUNCIONARIOS, "wb") as f:
        pickle.dump(funcionarios, f)


def _carregar_funcionarios():
    if os.path.exists(_CAMINHO_FUNCIONARIOS):
        with open(_CAMINHO_FUNCIONARIOS, "rb") as f:
            funcionarios = pickle.load(f)
        funcionarios = _garantir_admin_fixo(funcionarios)
        _salvar_funcionarios(funcionarios)
        return funcionarios

    funcionarios = [ADMIN_FIXO.copy()]
    _salvar_funcionarios(funcionarios)
    return funcionarios


def autenticar(login, senha):
    login = str(login or '').strip().lower()
    senha_hash = _hash_senha(str(senha or '').strip())

    for func in _carregar_funcionarios():
        if not func.get('ativo', True):
            continue
        if str(func.get('login', '')).strip().lower() == login and func.get('senha_hash', '') == senha_hash:
            return func
    return None


def usuario_logado():
    return st.session_state.get('usuario_logado')


def fazer_logout():
    st.session_state.pop('usuario_logado', None)
    st.rerun()


def tem_permissao(pagina):
    user = usuario_logado()
    if not user:
        return False
    return pagina in PERMISSOES.get(user.get('nivel_acesso', ''), [])


def exigir_permissao(pagina):
    user = usuario_logado()
    if not user:
        st.error("❌ Faça login para continuar.")
        st.stop()
    if not tem_permissao(pagina):
        st.error(f"❌ Seu nível de acesso ({user.get('nivel_acesso')}) não permite acessar esta página.")
        st.stop()


def render_login():
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] { display: none; }
        div[data-testid="appViewContainer"] > section { padding-top: 4rem; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        LOGO = Path(__file__).resolve().parent.parent / "images" / "logo.png"
        if LOGO.exists():
            col_a, col_b, col_c = st.columns([1, 1, 1])
            with col_b:
                st.image(str(LOGO), use_container_width=True)

        st.divider()

        with st.form("form_login"):
            login = st.text_input("Login", key="login_input")
            senha = st.text_input("Senha", type="password", key="senha_input")

            if st.form_submit_button("Entrar", use_container_width=True, type="primary"):
                user = autenticar(login, senha)
                if user:
                    st.session_state.usuario_logado = user
                    st.success(f"Bem-vindo, {user['nome']}!")
                    time.sleep(0.3)
                    st.rerun()
                else:
                    st.error("❌ Login ou senha inválidos.")