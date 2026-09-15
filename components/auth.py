import streamlit as st
import time
from pathlib import Path

from utils.staff_utils import (
    carregar_funcionarios_com_admin as _carregar_funcionarios,
    hash_senha as _hash_senha,
)


PERMISSOES = {
    'admin': [
        'caixa', 'mesas', 'pedidos', 'produtos', 'estoque',
        'indicadores', 'clientes', 'delivery', 'configuracoes', 'staff'
    ],
    'operador': ['pedidos']
}


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