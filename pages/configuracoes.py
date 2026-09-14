import streamlit as st
import os
import json
import time
import requests
from datetime import datetime
from utils.print import listar_impressoras, imprimir_ticket

from components.auth import exigir_permissao
exigir_permissao("configuracoes")


ARQUIVO_CONFIG = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "config.json")


def carregar_config():
    if os.path.exists(ARQUIVO_CONFIG):
        with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "impressora_cozinha": "",
        "impressora_salao": "",
        "impressora_comanda": "",
        "max_mesas": 50,
        "empresa": {
            "nome": "",
            "email_contato": "",
            "telefone": "",
            "cnpj": ""
        }
    }


def salvar_config(config):
    os.makedirs(os.path.dirname(ARQUIVO_CONFIG), exist_ok=True)
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


if 'config' not in st.session_state:
    st.session_state.config = carregar_config()

if 'empresa' not in st.session_state.config:
    st.session_state.config['empresa'] = {
        "nome": "",
        "email_contato": "",
        "telefone": "",
        "cnpj": ""
    }

if 'max_mesas' not in st.session_state.config:
    st.session_state.config['max_mesas'] = 50


st.header("Configurações")

aba_impressoras, aba_empresa, aba_integracoes = st.tabs([
    "Impressoras",
    "Empresa",
    "Integrações"
])


# ============================================================
# ABA IMPRESSORAS
# ============================================================
with aba_impressoras:
    st.subheader("🖨️ Impressoras")

    impressoras_disponiveis = listar_impressoras()

    if not impressoras_disponiveis:
        st.warning("⚠️ Nenhuma impressora encontrada no sistema. Verifique se as impressoras estão conectadas.")
    else:
        st.success(f"✅ {len(impressoras_disponiveis)} impressora(s) encontrada(s) no sistema.")

    st.divider()

    st.subheader("🍳 Impressora da Cozinha")
    if impressoras_disponiveis:
        impressora_cozinha = st.selectbox(
            "Selecione a impressora para os pedidos da cozinha:",
            impressoras_disponiveis,
            index=impressoras_disponiveis.index(st.session_state.config.get("impressora_cozinha", ""))
            if st.session_state.config.get("impressora_cozinha", "") in impressoras_disponiveis else 0,
            key="config_impressora_cozinha"
        )
    else:
        impressora_cozinha = st.text_input(
            "Nome da impressora da cozinha (digite manualmente):",
            value=st.session_state.config.get("impressora_cozinha", ""),
            key="config_impressora_cozinha_manual"
        )

    st.subheader("Impressora do Salão")
    if impressoras_disponiveis:
        impressora_salao = st.selectbox(
            "Selecione a impressora para o salão (comandas):",
            impressoras_disponiveis,
            index=impressoras_disponiveis.index(st.session_state.config.get("impressora_salao", ""))
            if st.session_state.config.get("impressora_salao", "") in impressoras_disponiveis else 0,
            key="config_impressora_salao"
        )
    else:
        impressora_salao = st.text_input(
            "Nome da impressora do salão (digite manualmente):",
            value=st.session_state.config.get("impressora_salao", ""),
            key="config_impressora_salao_manual"
        )

    st.subheader("Impressora de Comandas")
    if impressoras_disponiveis:
        impressora_comanda = st.selectbox(
            "Selecione a impressora para comandas (opcional):",
            [""] + impressoras_disponiveis,
            index=([""] + impressoras_disponiveis).index(st.session_state.config.get("impressora_comanda", ""))
            if st.session_state.config.get("impressora_comanda", "") in [""] + impressoras_disponiveis else 0,
            key="config_impressora_comanda"
        )
    else:
        impressora_comanda = st.text_input(
            "Nome da impressora de comandas (opcional, deixe vazio para não usar):",
            value=st.session_state.config.get("impressora_comanda", ""),
            key="config_impressora_comanda_manual"
        )

    st.caption("💡 Deixe vazio para não usar impressora de comandas.")

    st.divider()

    col_salvar1, col_salvar2, col_salvar3 = st.columns([1, 2, 1])
    with col_salvar2:
        if st.button("💾 Salvar Impressoras", use_container_width=True, type="primary", key="salvar_impressoras"):
            st.session_state.config["impressora_cozinha"] = impressora_cozinha if impressora_cozinha else ""
            st.session_state.config["impressora_salao"] = impressora_salao if impressora_salao else ""
            st.session_state.config["impressora_comanda"] = impressora_comanda if impressora_comanda else ""

            salvar_config(st.session_state.config)

            st.session_state.impressora_cozinha = st.session_state.config["impressora_cozinha"]
            st.session_state.impressora_salao = st.session_state.config["impressora_salao"]
            st.session_state.impressora_comanda = st.session_state.config["impressora_comanda"]

            st.success("✅ Configurações salvas com sucesso!")
            time.sleep(0.5)
            st.rerun()

    st.divider()
    st.subheader("Configurações Atuais")

    config_atual = carregar_config()

    col_atual1, col_atual2, col_atual3 = st.columns(3)
    with col_atual1:
        st.info(f"**Cozinha:** {config_atual.get('impressora_cozinha', 'Nenhuma') or 'Nenhuma'}")
    with col_atual2:
        st.info(f"**Salão:** {config_atual.get('impressora_salao', 'Nenhuma') or 'Nenhuma'}")
    with col_atual3:
        st.info(f"**Comandas:** {config_atual.get('impressora_comanda', 'Nenhuma') or 'Nenhuma'}")

    st.divider()
    st.subheader("Testar Impressora")

    col_testar1, col_testar2, col_testar3 = st.columns([1, 2, 1])
    with col_testar2:
        impressora_teste = st.selectbox(
            "Selecione a impressora para testar:",
            impressoras_disponiveis if impressoras_disponiveis else ["Nenhuma impressora disponível"],
            key="testar_impressora"
        )

        if st.button("Testar Impressora", use_container_width=True):
            if impressora_teste and impressora_teste != "Nenhuma impressora disponível":
                teste = f"""
                    {"="*40}
                    TESTE DE IMPRESSÃO
                    {"="*40}
                    Data: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
                    Impressora: {impressora_teste}
                    {"-"*40}
                    Este é um teste de impressão.

                    Se você está vendo esta mensagem,
                    a impressora está funcionando corretamente!
                    {"="*40}
                    """
                sucesso = imprimir_ticket(teste, impressora_teste)
                if sucesso:
                    st.success(f"✅ Teste enviado para a impressora **{impressora_teste}**!")
                else:
                    st.error(f"❌ Falha ao testar a impressora **{impressora_teste}**. Verifique a conexão.")
            else:
                st.warning("⚠️ Selecione uma impressora válida para testar.")


# ============================================================
# ABA EMPRESA
# ============================================================
with aba_empresa:
    st.subheader("🏢 Dados da Empresa")

    empresa_atual = st.session_state.config.get('empresa', {})

    nome_empresa = st.text_input(
        "Nome da empresa",
        value=empresa_atual.get('nome', ''),
        key="config_empresa_nome"
    )

    col1, col2 = st.columns(2)
    with col1:
        email_contato = st.text_input(
            "E-mail de contato",
            value=empresa_atual.get('email_contato', ''),
            placeholder="contato@suaempresa.com",
            key="config_empresa_email"
        )
        st.caption("💡 Usado em integrações externas (Nominatim, ViaCEP).")
    with col2:
        telefone_empresa = st.text_input(
            "Telefone",
            value=empresa_atual.get('telefone', ''),
            key="config_empresa_telefone"
        )
        cnpj_empresa = st.text_input(
            "CNPJ",
            value=empresa_atual.get('cnpj', ''),
            key="config_empresa_cnpj"
        )

    st.divider()

    st.subheader("🍽️ Salão")

    max_mesas = st.number_input(
        "Máximo de mesas:",
        min_value=1,
        max_value=200,
        step=1,
        value=int(st.session_state.config.get('max_mesas', 50)),
        key="config_max_mesas"
    )
    st.caption("💡 Define o limite de mesas no salão.")

    st.divider()

    col_salvar1, col_salvar2, col_salvar3 = st.columns([1, 2, 1])
    with col_salvar2:
        if st.button("💾 Salvar Empresa", use_container_width=True, type="primary", key="salvar_empresa"):
            st.session_state.config['empresa'] = {
                'nome': nome_empresa.strip(),
                'email_contato': email_contato.strip(),
                'telefone': telefone_empresa.strip(),
                'cnpj': cnpj_empresa.strip()
            }
            st.session_state.config['max_mesas'] = int(max_mesas)
            salvar_config(st.session_state.config)
            st.success("✅ Dados da empresa salvos!")
            time.sleep(0.5)
            st.rerun()


# ============================================================
# ABA INTEGRAÇÕES
# ============================================================
with aba_integracoes:
    st.subheader("🔌 Integrações")

    email_contato = st.session_state.config.get('empresa', {}).get('email_contato', '').strip()

    # ---------- ViaCEP ----------
    with st.container(border=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("**📮 ViaCEP**")
            st.caption("Consulta de endereços por CEP (gratuito, sem autenticação).")
        with col2:
            if st.button("Testar", key="teste_viacep", use_container_width=True):
                try:
                    r = requests.get("https://viacep.com.br/ws/11680001/json/", timeout=5)
                    if r.status_code == 200 and not r.json().get('erro'):
                        d = r.json()
                        st.success(f"✅ Online — {d.get('logradouro')}, {d.get('bairro')}")
                    else:
                        st.error("❌ Resposta inválida")
                except Exception as e:
                    st.error(f"❌ Falha: {e}")

    # ---------- Nominatim ----------
    with st.container(border=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("**🗺️ Nominatim (OpenStreetMap)**")
            st.caption("Geocodificação de endereços para o mapa de clientes. Exige e-mail de contato.")
            if email_contato:
                st.caption(f"User-Agent: `consumer/1.0 ({email_contato})`")
            else:
                st.warning("⚠️ Preencha o e-mail de contato em **Empresa** para ativar.")
        with col2:
            if st.button("Testar", key="teste_nominatim", use_container_width=True, disabled=not email_contato):
                try:
                    r = requests.get(
                        "https://nominatim.openstreetmap.org/search",
                        params={"q": "Ubatuba, SP", "format": "json", "limit": 1},
                        headers={"User-Agent": f"consumer/1.0 ({email_contato})"},
                        timeout=10
                    )
                    if r.status_code == 200 and r.json():
                        d = r.json()[0]
                        st.success(f"✅ Online — lat {d.get('lat')}, lon {d.get('lon')}")
                    else:
                        st.error("❌ Sem resposta válida")
                except Exception as e:
                    st.error(f"❌ Falha: {e}")