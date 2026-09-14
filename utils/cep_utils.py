import requests
import re
import streamlit as st

def buscar_cep(cep):
    cep = re.sub(r"\D", "", cep)
    try:
        resposta = requests.get(
            f"https://viacep.com.br/ws/{cep}/json/",
            timeout=10
        )

        dados = resposta.json()
        st.write("Dados:", dados)
        
        if dados.get("erro"):
            st.write("CEP não encontrado")
            return None

        return dados

    except Exception as e:
        st.write("ERRO:", str(e))
        return None

def buscar_cep_novo():
    dados_cep = buscar_cep(st.session_state.novo_cep)

    st.session_state.novo_numero = ""
    st.session_state.novo_complemento = ""

    if dados_cep:
        st.session_state.novo_logradouro = dados_cep.get("logradouro", "")
        st.session_state.novo_bairro = dados_cep.get("bairro", "")
        st.session_state.novo_cidade = dados_cep.get("localidade", "")
        st.session_state.novo_estado = dados_cep.get("uf", "")
        st.session_state.cep_novo_erro = ""
    else:
        st.session_state.novo_logradouro = ""
        st.session_state.novo_bairro = ""
        st.session_state.novo_cidade = ""
        st.session_state.novo_estado = ""
        st.session_state.cep_novo_erro = "CEP inválido ou não encontrado."


def buscar_cep_edit():
    dados_cep = buscar_cep(st.session_state.edit_cep)

    st.session_state.edit_numero = ""
    st.session_state.edit_complemento = ""

    if dados_cep:
        st.session_state.edit_logradouro = dados_cep.get("logradouro", "")
        st.session_state.edit_bairro = dados_cep.get("bairro", "")
        st.session_state.edit_cidade = dados_cep.get("localidade", "")
        st.session_state.edit_estado = dados_cep.get("uf", "")
        st.session_state.cep_edit_erro = ""
    else:
        st.session_state.edit_logradouro = ""
        st.session_state.edit_bairro = ""
        st.session_state.edit_cidade = ""
        st.session_state.edit_estado = ""
        st.session_state.cep_edit_erro = "CEP inválido ou não encontrado."