import streamlit as st
import time
from utils.staff_utils import carregar_funcionarios as _carregar, salvar_funcionarios as _salvar

from components.auth import exigir_permissao
exigir_permissao("staff")

from utils.staff_utils import (
    carregar_funcionarios as _carregar,
    salvar_funcionarios as _salvar,
    hash_senha as _hash_senha,
    gerar_id_funcionario as _gerar_id,
    garantir_campos_funcionario as _garantir_campos,
)

if 'funcionarios' not in st.session_state:
    st.session_state.funcionarios = [_garantir_campos(f) for f in _carregar()]

if 'editando_funcionario' not in st.session_state:
    st.session_state.editando_funcionario = None

if 'staff_aba' not in st.session_state:
    st.session_state.staff_aba = "Equipe"

if 'staff_aba_radio' in st.session_state:
    del st.session_state['staff_aba_radio']

st.header("Staff")
st.caption("Cadastro e gerenciamento de funcionários")

funcionarios = st.session_state.funcionarios

opcoes_abas = ["📋 Equipe", "➕ Cadastrar / Editar"]

if st.session_state.get('editando_funcionario') is not None:
    st.session_state.staff_aba = "➕ Cadastrar / Editar"

if st.session_state.staff_aba not in opcoes_abas:
    st.session_state.staff_aba = "📋 Equipe"

aba_selecionada = st.radio(
    "Navegação",
    opcoes_abas,
    index=opcoes_abas.index(st.session_state.staff_aba),
    horizontal=True,
    label_visibility="collapsed"
)

st.session_state.staff_aba = aba_selecionada

# ============================================================
# ABA CADASTRAR / EDITAR
# ============================================================
if st.session_state.staff_aba == "➕ Cadastrar / Editar":

    editando = st.session_state.editando_funcionario

    if editando is not None:
        dados = funcionarios[editando]
        st.subheader(f"✏️ Editando — {dados.get('nome', '')}")
    else:
        dados = {
            'id_funcionario': '',
            'nome': '',
            'cargo': '',
            'telefone': '',
            'email': '',
            'endereco': '',
            'valor_dia': 0.0,
            'ativo': True,
            'login': '',
            'senha_hash': '',
            'nivel_acesso': 'operador'
        }
        st.subheader("➕ Novo Funcionário")

    with st.container(border=True):
        st.markdown("**👤 Dados Pessoais**")

        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome completo *", value=dados.get('nome', ''), key="staff_nome")
            telefone = st.text_input("Telefone", value=dados.get('telefone', ''), key="staff_telefone")
            email = st.text_input("E-mail", value=dados.get('email', ''), key="staff_email")
        with col2:
            cargo = st.selectbox(
                "Cargo *",
                ["Garçom", "Cozinheiro", "Barman", "Gerente", "Atendente", "Auxiliar", "Outro"],
                index=(["Garçom", "Cozinheiro", "Barman", "Gerente", "Atendente", "Auxiliar", "Outro"].index(dados.get('cargo')) if dados.get('cargo') in ["Garçom", "Cozinheiro", "Barman", "Gerente", "Atendente", "Auxiliar", "Outro"] else 0),
                key="staff_cargo"
            )
            valor_dia = st.number_input("Valor / dia (R$)", min_value=0.0, step=1.0, value=float(dados.get('valor_dia', 0.0)), key="staff_valor_dia")
            endereco = st.text_area("Endereço", value=dados.get('endereco', ''), key="staff_endereco", height=68)

    with st.container(border=True):
        st.markdown("**🔐 Acesso ao Sistema**")

        col1, col2 = st.columns(2)
        with col1:
            login = st.text_input("Login *", value=dados.get('login', ''), key="staff_login")
        with col2:
            senha = st.text_input("Senha (deixe vazio para manter)", type="password", key="staff_senha")

        col1, col2, col3 = st.columns(3)
        with col1:
            nivel = st.selectbox(
                "Nível de Acesso",
                ["admin", "operador"],
                index=(["admin", "operador"].index(dados.get('nivel_acesso')) if dados.get('nivel_acesso') in ["admin", "operador"] else 1),
                key="staff_nivel"
            )
        with col2:
            ativo = st.checkbox("Ativo", value=bool(dados.get('ativo', True)), key="staff_ativo")
        with col3:
            st.caption("**Admin:** todas as páginas")
            st.caption("**Operador:** mesas e pedidos")

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("💾 Salvar", use_container_width=True, type="primary", key="staff_salvar"):
            erros = []
            if not nome.strip():
                erros.append("Nome")
            if not login.strip():
                erros.append("Login")
            if not email.strip():
                erros.append("E-mail")

            if editando is None and not senha.strip():
                erros.append("Senha")

            login_em_uso = any(
                f.get('login', '').strip().lower() == login.strip().lower() and i != editando
                for i, f in enumerate(funcionarios)
            )
            if login_em_uso:
                erros.append("Login já em uso")

            if erros:
                st.error(f"⚠️ Verifique: {', '.join(erros)}")
            else:
                senha_hash = dados.get('senha_hash', '')
                if senha.strip():
                    senha_hash = _hash_senha(senha.strip())

                novo = {
                    'id_funcionario': dados.get('id_funcionario') or _gerar_id(funcionarios),
                    'nome': nome.strip(),
                    'cargo': cargo,
                    'telefone': telefone.strip(),
                    'email': email.strip(),
                    'endereco': endereco.strip(),
                    'valor_dia': float(valor_dia),
                    'ativo': bool(ativo),
                    'login': login.strip(),
                    'senha_hash': senha_hash,
                    'nivel_acesso': nivel
                }

                if editando is None:
                    funcionarios.append(novo)
                else:
                    funcionarios[editando] = novo

                _salvar(funcionarios)
                st.session_state.funcionarios = funcionarios
                st.session_state.editando_funcionario = None
                st.session_state.staff_aba = "📋 Equipe"
                st.success("✅ Funcionário salvo!")
                time.sleep(0.5)
                st.rerun()

    with col_b2:
        if editando is not None:
            if st.button("❌ Cancelar Edição", use_container_width=True, key="staff_cancelar"):
                st.session_state.editando_funcionario = None
                st.session_state.staff_aba = "Equipe"
                st.rerun()

# ============================================================
# ABA EQUIPE
# ============================================================
else:
    if not funcionarios:
        st.info("Nenhum funcionário cadastrado.")
    else:
        ativos = [f for f in funcionarios if f.get('ativo')]
        admins = [f for f in funcionarios if f.get('nivel_acesso') == 'admin']

        col1, col2, col3 = st.columns(3)
        col1.metric("Total", len(funcionarios))
        col2.metric("Ativos", len(ativos))
        col3.metric("Admins", len(admins))

        st.divider()

        for i, func in enumerate(funcionarios):
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                with col1:
                    status_icon = "🟢" if func.get('ativo') else "🔴"
                    nivel_icon = "👑" if func.get('nivel_acesso') == 'admin' else "👤"
                    st.markdown(f"{status_icon} {nivel_icon} **{func.get('nome', '')}**")
                    st.caption(f"{func.get('id_funcionario', '')} · {func.get('cargo', '')}")

                with col2:
                    st.write(f"🔑 `{func.get('login', '')}`")
                    st.caption(f"Nível: {func.get('nivel_acesso', '')}")

                with col3:
                    st.write(f"💰 R$ {float(func.get('valor_dia', 0)):.2f} / dia")
                    st.caption(func.get('email', '') or '—')

                with col4:
                    if st.button("✏️", key=f"staff_edit_{i}", use_container_width=True):
                        st.session_state.editando_funcionario = i
                        st.session_state.staff_aba = "➕ Cadastrar / Editar"
                        st.rerun()
                    if st.button("🗑️", key=f"staff_del_{i}", use_container_width=True):
                        if func.get('nivel_acesso') == 'admin' and len(admins) == 1:
                            st.error("⚠️ Não é possível excluir o único admin.")
                        else:
                            del funcionarios[i]
                            _salvar(funcionarios)
                            st.session_state.funcionarios = funcionarios
                            st.rerun()