import streamlit as st
from pathlib import Path
from components.clock import clock
from components.auth import render_login, usuario_logado, fazer_logout, tem_permissao
from install.bootstrap import bootstrap

bootstrap()

st.set_page_config(page_title="Velho Gordon", layout="wide")

if not usuario_logado():
    render_login()
    st.stop()

LOGO = Path(__file__).parent / "images" / "logo.png"

with st.sidebar:
    col1, col2 = st.columns(2)
    with col1:
        st.image(str(LOGO), width=100)
    with col2:
        st.components.v1.html(clock, height=120)

    st.divider()

    user = usuario_logado()
    st.markdown(f"👤 **{user['nome']}**")
    st.caption(f"Nível: {user['nivel_acesso']}")

    if st.button("🚪 Sair", use_container_width=True):
        fazer_logout()

TODAS_PAGES = [
    ("caixa", "pages/caixa.py", "Caixa"),
    ("mesas", "pages/mesas.py", "Mesas"),
    ("pedidos", "pages/pedidos.py", "Pedidos"),
    ("delivery", "pages/delivery.py", "Delivery"),
    ("produtos", "pages/produtos.py", "Produtos"),
    ("estoque", "pages/estoque.py", "Estoque"),
    ("clientes", "pages/clientes.py", "Clientes"),
    ("staff", "pages/staff.py", "Staff"),
    ("indicadores", "pages/indicadores.py", "Indicadores"),
    ("configuracoes", "pages/configuracoes.py", "Configurações"),
]

pages = [
    st.Page(caminho, title=titulo)
    for chave, caminho, titulo in TODAS_PAGES
    if tem_permissao(chave)
]

pg = st.navigation(pages)
pg.run()