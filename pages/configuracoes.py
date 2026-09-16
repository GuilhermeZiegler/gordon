import streamlit as st
import json
import time
import requests
from datetime import datetime

from utils.print import imprimir_rede
from utils.db import ler_tabela, executar

from components.auth import exigir_permissao
exigir_permissao("configuracoes")


CONFIG_PADRAO = {
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


def carregar_config():
    try:
        df = ler_tabela("config")

        if df.empty or "dados" not in df.columns:
            return CONFIG_PADRAO.copy()

        valor = df["dados"].iloc[0]

        if valor is None:
            return CONFIG_PADRAO.copy()

        if isinstance(valor, dict):
            dados = valor
        elif isinstance(valor, str):
            dados = json.loads(valor)
        else:
            return CONFIG_PADRAO.copy()

        for k, v in CONFIG_PADRAO.items():
            if k not in dados:
                dados[k] = v

        return dados
    except Exception:
        return CONFIG_PADRAO.copy()


def salvar_config(config):
    payload = json.dumps(config, ensure_ascii=False)

    executar('TRUNCATE TABLE "config"')
    executar('INSERT INTO "config" (dados) VALUES (:d)', {"d": payload})


if 'config' not in st.session_state:
    st.session_state.config = carregar_config()

if 'empresa' not in st.session_state.config:
    st.session_state.config['empresa'] = CONFIG_PADRAO['empresa'].copy()

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
    st.subheader("🖨️ Impressoras de Rede")

    st.caption(
        "Endereço no formato `host:porta`. "
        "Ex: `100.64.0.5:9100` (Tailscale) ou `192.168.1.50:9100` (rede local). "
        "Se omitir a porta, assume `9100`. "
        "Deixe vazio para gerar PDF."
    )

    st.divider()

    # ---------------- COZINHA ----------------
    st.markdown("**🍳 Impressora da Cozinha**")
    col_c1, col_c2 = st.columns([5, 1])
    with col_c1:
        imp_cozinha = st.text_input(
            "Cozinha",
            value=st.session_state.config.get("impressora_cozinha", ""),
            placeholder="100.64.0.5:9100",
            key="config_imp_cozinha",
            label_visibility="collapsed"
        )
    with col_c2:
        if st.button("Testar", key="testar_cozinha", use_container_width=True):
            if not imp_cozinha.strip():
                st.warning("Informe o endereço.")
            else:
                ok = imprimir_rede(
                    "\n========================================\n"
                    "           TESTE COZINHA\n"
                    "========================================\n"
                    f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                    f"Destino: {imp_cozinha}\n"
                    "----------------------------------------\n"
                    "Impressora OK.\n"
                    "========================================\n\n",
                    imp_cozinha
                )
                if ok:
                    st.success("✅ Impressora respondeu.")
                else:
                    st.error("❌ Falha ao conectar.")

    # ---------------- SALÃO ----------------
    st.markdown("**🍽️ Impressora do Salão**")
    col_s1, col_s2 = st.columns([5, 1])
    with col_s1:
        imp_salao = st.text_input(
            "Salão",
            value=st.session_state.config.get("impressora_salao", ""),
            placeholder="100.64.0.6:9100",
            key="config_imp_salao",
            label_visibility="collapsed"
        )
    with col_s2:
        if st.button("Testar", key="testar_salao", use_container_width=True):
            if not imp_salao.strip():
                st.warning("Informe o endereço.")
            else:
                ok = imprimir_rede(
                    "\n========================================\n"
                    "            TESTE SALÃO\n"
                    "========================================\n"
                    f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                    f"Destino: {imp_salao}\n"
                    "----------------------------------------\n"
                    "Impressora OK.\n"
                    "========================================\n\n",
                    imp_salao
                )
                if ok:
                    st.success("✅ Impressora respondeu.")
                else:
                    st.error("❌ Falha ao conectar.")

    # ---------------- COMANDAS ----------------
    st.markdown("**🧾 Impressora de Comandas**")
    col_cm1, col_cm2 = st.columns([5, 1])
    with col_cm1:
        imp_comanda = st.text_input(
            "Comandas",
            value=st.session_state.config.get("impressora_comanda", ""),
            placeholder="100.64.0.7:9100",
            key="config_imp_comanda",
            label_visibility="collapsed"
        )
    with col_cm2:
        if st.button("Testar", key="testar_comanda", use_container_width=True):
            if not imp_comanda.strip():
                st.warning("Informe o endereço.")
            else:
                ok = imprimir_rede(
                    "\n========================================\n"
                    "          TESTE COMANDAS\n"
                    "========================================\n"
                    f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                    f"Destino: {imp_comanda}\n"
                    "----------------------------------------\n"
                    "Impressora OK.\n"
                    "========================================\n\n",
                    imp_comanda
                )
                if ok:
                    st.success("✅ Impressora respondeu.")
                else:
                    st.error("❌ Falha ao conectar.")

    st.caption("💡 Deixe a impressora de comandas vazio para não usar.")

    st.divider()

    col_sv1, col_sv2, col_sv3 = st.columns([1, 2, 1])
    with col_sv2:
        if st.button("💾 Salvar Impressoras", use_container_width=True, type="primary", key="salvar_impressoras"):
            st.session_state.config["impressora_cozinha"] = imp_cozinha.strip()
            st.session_state.config["impressora_salao"] = imp_salao.strip()
            st.session_state.config["impressora_comanda"] = imp_comanda.strip()

            salvar_config(st.session_state.config)

            st.session_state.impressora_cozinha = imp_cozinha.strip()
            st.session_state.impressora_salao = imp_salao.strip()
            st.session_state.impressora_comanda = imp_comanda.strip()

            st.success("✅ Configurações salvas!")
            time.sleep(0.5)
            st.rerun()

    st.divider()
    st.subheader("Configurações Atuais")

    config_atual = carregar_config()

    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        st.info(f"**Cozinha:** {config_atual.get('impressora_cozinha') or 'Nenhuma'}")
    with col_a2:
        st.info(f"**Salão:** {config_atual.get('impressora_salao') or 'Nenhuma'}")
    with col_a3:
        st.info(f"**Comandas:** {config_atual.get('impressora_comanda') or 'Nenhuma'}")


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

    col_sv1, col_sv2, col_sv3 = st.columns([1, 2, 1])
    with col_sv2:
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