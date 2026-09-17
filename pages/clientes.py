import streamlit as st
import pandas as pd
import time
from datetime import datetime

from components.auth import exigir_permissao
exigir_permissao("clientes")

from utils.cep_utils import buscar_cep, buscar_cep_edit, buscar_cep_novo
from utils.clientes_utils import (
    carregar_clientes,
    salvar_clientes,
    gerar_id_cliente,
    geocodificar_pendentes,
    _tem_coord_valida,
    _garantir_campos,
    _montar_endereco
)

if "clientes" not in st.session_state:
    st.session_state.clientes = [_garantir_campos(c) for c in carregar_clientes()]

if "cliente_selecionado" not in st.session_state:
    st.session_state.cliente_selecionado = None

if "editando_cliente" not in st.session_state:
    st.session_state.editando_cliente = None

if "novo_logradouro" not in st.session_state:
    st.session_state.novo_logradouro = ""

if "novo_bairro" not in st.session_state:
    st.session_state.novo_bairro = ""

if "novo_cidade" not in st.session_state:
    st.session_state.novo_cidade = ""

if "novo_estado" not in st.session_state:
    st.session_state.novo_estado = ""

if "novo_numero" not in st.session_state:
    st.session_state.novo_numero = ""

if "novo_complemento" not in st.session_state:
    st.session_state.novo_complemento = ""

if "cep_novo_erro" not in st.session_state:
    st.session_state.cep_novo_erro = ""

if "cep_edit_erro" not in st.session_state:
    st.session_state.cep_edit_erro = ""


st.title("Clientes")
st.caption("Cadastro e gerenciamento de clientes")

aba_buscar, aba_cadastro, aba_mapa = st.tabs(["🔎 Buscar / Editar", "➕ Novo Cliente", "🗺️ Mapa"])


# ============================================================
# ABA BUSCAR / EDITAR
# ============================================================
with aba_buscar:
    st.subheader("🔎 Buscar Cliente")

    busca = st.text_input(
        "Nome ou ID do cliente",
        placeholder="Digite o nome ou ID_cliente...",
        key="busca_cliente"
    )

    termo = busca.strip().lower()

    if not termo:
        st.caption(f"📊 {len(st.session_state.clientes)} clientes cadastrados")
        df_clientes = st.session_state.clientes
        tabela = [
            {
                'ID': c.get('id_cliente', ''),
                'Nome': c.get('nome_cliente', ''),
                'Telefone': c.get('telefone_principal', ''),
                'Cidade': c.get('cidade', ''),
                'Bairro': c.get('bairro', ''),
                'Lat/Lon': '✓' if str(c.get('latitude', '')).strip() else '—'
            }
            for c in df_clientes
        ]
        # st.dataframe(tabela, use_container_width=True, hide_index=True)
    else:
        resultados = [
            cliente
            for cliente in st.session_state.clientes
            if termo in str(cliente.get("nome_cliente", "")).lower()
            or termo in str(cliente.get("id_cliente", "")).lower()
        ]

        if resultados:
            st.caption(f"{len(resultados)} cliente(s) encontrado(s)")

            opcoes = {
                f"{cliente.get('nome_cliente', '')} — {cliente.get('id_cliente', '')}": cliente
                for cliente in resultados
            }

            selecionado = st.selectbox(
                "Selecione o cliente",
                list(opcoes.keys()),
                key="selecao_cliente"
            )

            cliente = opcoes[selecionado]

            with st.container(border=True):
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(f"### 👤 {cliente.get('nome_cliente', '')}")
                    st.caption(f"ID: {cliente.get('id_cliente', '')}")

                with col2:
                    if st.button(
                        "✏️ Editar",
                        key=f"editar_{cliente.get('id_cliente')}",
                        use_container_width=True
                    ):
                        st.session_state.editando_cliente = cliente.copy()

                        st.session_state.edit_nome_cliente = cliente.get("nome_cliente", "")
                        st.session_state.edit_telefone_principal = cliente.get("telefone_principal", "")
                        st.session_state.edit_telefone_secundario = cliente.get("telefone_secundario", "")
                        st.session_state.edit_email = cliente.get("email", "")
                        st.session_state.edit_cep = cliente.get("cep", "")
                        st.session_state.edit_logradouro = cliente.get("logradouro", "")
                        st.session_state.edit_numero = cliente.get("numero", "")
                        st.session_state.edit_complemento = cliente.get("complemento", "")
                        st.session_state.edit_bairro = cliente.get("bairro", "")
                        st.session_state.edit_cidade = cliente.get("cidade", "")
                        st.session_state.edit_estado = cliente.get("estado", "")
                        st.session_state.edit_referencia = cliente.get("referencia", "")
                        st.session_state.edit_observacao = cliente.get("observacao", "")
                        st.session_state.cep_edit_erro = ""

                        st.rerun()

                col1, col2, col3 = st.columns(3)

                with col1:
                    if cliente.get("telefone_principal"):
                        st.write(f"📞 {cliente.get('telefone_principal')}")

                    if cliente.get("telefone_secundario"):
                        st.write(f"📱 {cliente.get('telefone_secundario')}")

                with col2:
                    if cliente.get("email"):
                        st.write(f"📧 {cliente.get('email')}")

                with col3:
                    cidade = cliente.get("cidade", "")
                    estado = cliente.get("estado", "")

                    if cidade or estado:
                        st.write(f"🏙️ {cidade} - {estado}")

                endereco = " ".join(
                    str(valor).strip()
                    for valor in [
                        cliente.get("logradouro", ""),
                        cliente.get("numero", ""),
                        cliente.get("complemento", "")
                    ]
                    if str(valor).strip()
                )

                if endereco:
                    st.write(f"📍 {endereco}")

                localidade = " - ".join(
                    str(valor).strip()
                    for valor in [
                        cliente.get("bairro", ""),
                        cliente.get("cidade", ""),
                        cliente.get("estado", "")
                    ]
                    if str(valor).strip()
                )

                if localidade:
                    st.caption(
                        f"{localidade} | CEP: {cliente.get('cep', '')}"
                    )

                if cliente.get("referencia"):
                    st.caption(f"📌 {cliente.get('referencia')}")

                if cliente.get("observacao"):
                    st.caption(f"📝 {cliente.get('observacao')}")

                if str(cliente.get('latitude', '')).strip():
                    st.caption(f"🌍 Coord: {cliente.get('latitude')}, {cliente.get('longitude')}")
        else:
            st.info("Nenhum cliente encontrado.")


# ============================================================
# ABA CADASTRO / EDIÇÃO
# ============================================================
with aba_cadastro:

    if st.session_state.editando_cliente is None:

        st.subheader("➕ Novo Cliente")

        with st.container(border=True):
            st.markdown("**👤 Dados do Cliente**")

            nome_cliente = st.text_input(
                "Nome completo *",
                key="novo_nome_cliente"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                telefone_principal = st.text_input(
                    "Telefone principal *",
                    placeholder="(00) 00000-0000",
                    key="novo_telefone_principal"
                )

            with col2:
                telefone_secundario = st.text_input(
                    "Telefone secundário",
                    placeholder="(00) 00000-0000",
                    key="novo_telefone_secundario"
                )

            with col3:
                email = st.text_input(
                    "E-mail",
                    placeholder="cliente@email.com",
                    key="novo_email"
                )

        with st.container(border=True):
            st.markdown("**📍 Endereço**")

            col1, col2, col3 = st.columns(3)

            with col1:
                cep = st.text_input(
                    "CEP",
                    placeholder="00000-000",
                    key="novo_cep"
                )

            with col2:
                st.write("")
                st.button(
                    "🔎 Buscar CEP",
                    key="buscar_cep_novo",
                    use_container_width=True,
                    on_click=buscar_cep_novo
                )

            with col3:
                logradouro = st.text_input(
                    "Logradouro",
                    placeholder="Rua, Avenida...",
                    key="novo_logradouro"
                )

            col1, col2, col3 = st.columns(3)

            with col1:
                numero = st.text_input(
                    "Número *",
                    key="novo_numero"
                )

            with col2:
                complemento = st.text_input(
                    "Complemento",
                    key="novo_complemento"
                )

            with col3:
                referencia = st.text_input(
                    "Referência",
                    placeholder="Próximo a...",
                    key="novo_referencia"
                )

            col1, col2, col3 = st.columns(3)

            with col1:
                bairro = st.text_input(
                    "Bairro",
                    key="novo_bairro"
                )

            with col2:
                cidade = st.text_input(
                    "Cidade",
                    key="novo_cidade"
                )

            with col3:
                estado = st.text_input(
                    "Estado",
                    key="novo_estado"
                )

            if st.session_state.cep_novo_erro:
                st.error(st.session_state.cep_novo_erro)

        if st.button(
            "➕ Cadastrar Cliente",
            type="primary",
            use_container_width=True
        ):
            if not nome_cliente.strip():
                st.warning("O nome é obrigatório.")
            elif not telefone_principal.strip():
                st.warning("O telefone principal é obrigatório.")
            elif not numero.strip():
                st.warning("O número é obrigatório.")
            else:
                novo_cliente = {
                    "id_cliente": gerar_id_cliente(st.session_state.clientes),
                    "nome_cliente": nome_cliente.strip(),
                    "telefone_principal": telefone_principal.strip(),
                    "telefone_secundario": telefone_secundario.strip(),
                    "email": email.strip(),
                    "cep": cep.strip(),
                    "logradouro": logradouro.strip(),
                    "numero": numero.strip(),
                    "complemento": complemento.strip(),
                    "bairro": bairro.strip(),
                    "cidade": cidade.strip(),
                    "estado": estado.strip(),
                    "referencia": referencia.strip(),
                    "data_cadastro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "ativo": True,
                    "latitude": "",
                    "longitude": ""
                }

                st.session_state.clientes.append(novo_cliente)
                salvar_clientes(st.session_state.clientes)

                st.success(
                    f"Cliente {novo_cliente['nome_cliente']} cadastrado com ID "
                    f"{novo_cliente['id_cliente']}."
                )

                st.rerun()

    else:

        data = st.session_state.editando_cliente
        id_cliente = data.get("id_cliente")

        st.subheader(f"✏️ Editar Cliente — {id_cliente}")

        with st.container(border=True):
            st.markdown("**👤 Dados do Cliente**")

            edit_nome = st.text_input(
                "Nome completo *",
                key="edit_nome_cliente"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                edit_telefone_principal = st.text_input(
                    "Telefone principal *",
                    key="edit_telefone_principal"
                )

            with col2:
                edit_telefone_secundario = st.text_input(
                    "Telefone secundário",
                    key="edit_telefone_secundario"
                )

            with col3:
                edit_email = st.text_input(
                    "E-mail",
                    key="edit_email"
                )

        with st.container(border=True):
            st.markdown("**📍 Endereço**")

            col1, col2, col3 = st.columns(3)

            with col1:
                edit_cep = st.text_input(
                    "CEP",
                    placeholder="00000-000",
                    key="edit_cep"
                )

            with col2:
                st.write("")
                st.button(
                    "🔎 Buscar CEP",
                    key="buscar_cep_edit",
                    use_container_width=True,
                    on_click=buscar_cep_edit
                )

            with col3:
                edit_logradouro = st.text_input(
                    "Logradouro",
                    key="edit_logradouro"
                )

            col1, col2, col3 = st.columns(3)

            with col1:
                edit_numero = st.text_input(
                    "Número *",
                    key="edit_numero"
                )

            with col2:
                edit_complemento = st.text_input(
                    "Complemento",
                    key="edit_complemento"
                )

            with col3:
                edit_referencia = st.text_input(
                    "Referência",
                    key="edit_referencia"
                )

            col1, col2, col3 = st.columns(3)

            with col1:
                edit_bairro = st.text_input(
                    "Bairro",
                    key="edit_bairro"
                )

            with col2:
                edit_cidade = st.text_input(
                    "Cidade",
                    key="edit_cidade"
                )

            with col3:
                edit_estado = st.text_input(
                    "Estado",
                    key="edit_estado"
                )

            if st.session_state.cep_edit_erro:
                st.error(st.session_state.cep_edit_erro)

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "💾 Salvar Alterações",
                type="primary",
                use_container_width=True
            ):
                if not edit_nome.strip():
                    st.warning("O nome é obrigatório.")
                elif not edit_telefone_principal.strip():
                    st.warning("O telefone principal é obrigatório.")
                elif not edit_numero.strip():
                    st.warning("O número é obrigatório.")
                else:
                    endereco_mudou = (
                        data.get('cep', '') != edit_cep.strip()
                        or data.get('logradouro', '') != edit_logradouro.strip()
                        or data.get('numero', '') != edit_numero.strip()
                        or data.get('bairro', '') != edit_bairro.strip()
                        or data.get('cidade', '') != edit_cidade.strip()
                        or data.get('estado', '') != edit_estado.strip()
                    )

                    for i, cliente in enumerate(st.session_state.clientes):
                        if cliente.get("id_cliente") == id_cliente:
                            lat = "" if endereco_mudou else cliente.get("latitude", "")
                            lon = "" if endereco_mudou else cliente.get("longitude", "")

                            st.session_state.clientes[i] = {
                                "id_cliente": id_cliente,
                                "nome_cliente": edit_nome.strip(),
                                "telefone_principal": edit_telefone_principal.strip(),
                                "telefone_secundario": edit_telefone_secundario.strip(),
                                "email": edit_email.strip(),
                                "cep": edit_cep.strip(),
                                "logradouro": edit_logradouro.strip(),
                                "numero": edit_numero.strip(),
                                "complemento": edit_complemento.strip(),
                                "bairro": edit_bairro.strip(),
                                "cidade": edit_cidade.strip(),
                                "estado": edit_estado.strip(),
                                "referencia": edit_referencia.strip(),
                                "data_cadastro": cliente.get("data_cadastro"),
                                "ativo": cliente.get("ativo", True),
                                "latitude": lat,
                                "longitude": lon
                            }
                            break

                    salvar_clientes(st.session_state.clientes)
                    st.session_state.editando_cliente = None
                    st.rerun()

        with col2:
            if st.button(
                "❌ Cancelar",
                use_container_width=True
            ):
                st.session_state.editando_cliente = None
                st.rerun()


# ============================================================
# ABA MAPA
# ============================================================
with aba_mapa:
    st.subheader("🗺️ Mapa de Clientes")

    clientes_com_coord = [c for c in st.session_state.clientes if _tem_coord_valida(c)]

    pendentes = [
        c for c in st.session_state.clientes
        if not _tem_coord_valida(c) and _montar_endereco(c).strip()
    ]

    col_info1, col_info2, col_info3 = st.columns(3)
    col_info1.metric("Total", len(st.session_state.clientes))
    col_info2.metric("Com coordenadas", len(clientes_com_coord))
    col_info3.metric("Sem coordenadas", len(pendentes))

    st.divider()

    from pages.configuracoes import carregar_config
    _config = carregar_config()
    email_contato = _config.get('empresa', {}).get('email_contato', '').strip()

    col_btn1, col_btn2 = st.columns([3, 1])

    with col_btn1:
        if pendentes:
            if not email_contato:
                st.warning("⚠️ Preencha o e-mail de contato em Configurações → Empresa para ativar a geocodificação.")
            else:
                st.caption(f"{len(pendentes)} cliente(s) sem coordenadas. Geocodificação leva ~{len(pendentes)}s (1 req/s).")

    with col_btn2:
        if pendentes and email_contato:
            if st.button(f"🌍 Geocodificar {len(pendentes)}", use_container_width=True, type="primary"):
                progresso = st.progress(0.0)
                status = st.empty()

                def _cb(atual, total, nome):
                    progresso.progress(atual / total)
                    status.caption(f"({atual}/{total}) {nome}")

                qtd = geocodificar_pendentes(email_contato, _cb)
                st.session_state.clientes = [_garantir_campos(c) for c in carregar_clientes()]
                st.success(f"✅ {qtd} cliente(s) geocodificado(s)!")
                time.sleep(0.8)
                st.rerun()

    st.divider()

    with st.expander("🐛 Debug — Testar 1 cliente"):
        debug_email = st.text_input(
            "Email de contato",
            value=email_contato if email_contato else "",
            key="debug_email"
        )

        if st.button("Testar 1 cliente", key="debug_geo_1"):
            if not debug_email.strip():
                st.error("Preencha o email")
            elif not pendentes:
                st.warning("Nenhum pendente")
            else:
                exemplo = pendentes[0]
                endereco = _montar_endereco(exemplo)

                st.write("**Cliente:**", exemplo.get('nome_cliente'))
                st.write("**Endereço montado:**", endereco)

                import requests
                try:
                    r = requests.get(
                        "https://nominatim.openstreetmap.org/search",
                        params={"q": endereco, "format": "json", "limit": 1},
                        headers={"User-Agent": f"consumer/1.0 ({debug_email})"},
                        timeout=10,
                        verify=False
                    )
                    st.write("**Status:**", r.status_code)
                    st.json(r.json())
                except Exception as e:
                    st.error(f"Erro: {e}")

                from utils.clientes_utils import geocodificar_endereco
                st.write("**Retorno do geocodificar_endereco:**", geocodificar_endereco(exemplo, debug_email))

    st.divider()

    if not clientes_com_coord:
        st.info("📭 Nenhum cliente com coordenadas ainda. Geocodifique acima.")
    else:
        modo = st.radio(
            "Visualização:",
            ["Por Cliente", "Por Bairro"],
            horizontal=True,
            key="mapa_modo"
        )

        try:
            import folium
            from streamlit_folium import st_folium

            centro_lat = sum(float(c['latitude']) for c in clientes_com_coord) / len(clientes_com_coord)
            centro_lon = sum(float(c['longitude']) for c in clientes_com_coord) / len(clientes_com_coord)
            mapa = folium.Map(
                location=[-23.43, -45.08],
                zoom_start=12,
                min_zoom=11,
                max_zoom=18,
                max_bounds=True,
                tiles="OpenStreetMap"
            )
            mapa.fit_bounds([[-23.65, -45.35], [-23.30, -44.85]])

            if modo == "Por Cliente":
                for c in clientes_com_coord:
                    popup = f"""
                    <b>{c.get('nome_cliente', '')}</b><br>
                    {c.get('id_cliente', '')}<br>
                    {c.get('telefone_principal', '')}<br>
                    {_montar_endereco(c)}
                    """
                    folium.Marker(
                        location=[float(c['latitude']), float(c['longitude'])],
                        popup=folium.Popup(popup, max_width=250),
                        tooltip=c.get('nome_cliente', '')
                    ).add_to(mapa)
            else:
                bairros = {}
                for c in clientes_com_coord:
                    b = c.get('bairro', 'Sem bairro')
                    bairros.setdefault(b, []).append(c)

                for bairro, lista in bairros.items():
                    lat = sum(float(c['latitude']) for c in lista) / len(lista)
                    lon = sum(float(c['longitude']) for c in lista) / len(lista)

                    nomes = '<br>'.join([c.get('nome_cliente', '') for c in lista[:15]])
                    if len(lista) > 15:
                        nomes += f'<br>... (+{len(lista)-15})'

                    popup = f"<b>{bairro}</b><br>{len(lista)} cliente(s)<hr>{nomes}"

                    folium.CircleMarker(
                        location=[lat, lon],
                        radius=min(30, 8 + len(lista) * 1.2),
                        popup=folium.Popup(popup, max_width=300),
                        tooltip=f"{bairro} ({len(lista)})",
                        color="#3498db",
                        fill=True,
                        fillColor="#3498db",
                        fillOpacity=0.6
                    ).add_to(mapa)

            st_folium(mapa, use_container_width=True, height=600, returned_objects=[])

        except ImportError:
            st.error("❌ `folium` e `streamlit-folium` não instalados. Rode: `uv add folium streamlit-folium`")