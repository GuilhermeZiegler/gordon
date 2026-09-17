import os
import pandas as pd
from sqlalchemy import create_engine, text
import streamlit as st


def _get_url():
    try:
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass

    from dotenv import load_dotenv
    load_dotenv()
    return os.getenv("DATABASE_URL")


_url = _get_url()

if not _url:
    raise RuntimeError("DATABASE_URL não configurada (.env ou st.secrets).")

_engine = create_engine(
    _url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=300,
)

_colunas_cache = {}
_cache_prox_id = {}


def _limpar_valor(v):
    if v is None:
        return None

    try:
        import numpy as np
        if isinstance(v, np.generic):
            return v.item()
    except ImportError:
        pass

    try:
        if pd.isna(v):
            return None
    except Exception:
        pass

    return v


def _limpar_dict(dados):
    return {k: _limpar_valor(v) for k, v in dados.items()}


def _get_colunas(nome):
    if nome not in _colunas_cache:
        with _engine.connect() as conn:
            _colunas_cache[nome] = pd.read_sql(
                f'SELECT * FROM "{nome}" LIMIT 0',
                conn
            ).columns.tolist()

    return _colunas_cache[nome]


def ler_tabela(nome):
    return pd.read_sql(f'SELECT * FROM "{nome}"', _engine)


def escrever_tabela(nome, df):
    colunas = _get_colunas(nome)

    df = df[[c for c in df.columns if c in colunas]].copy()

    with _engine.begin() as conn:
        conn.execute(text(f'TRUNCATE TABLE "{nome}"'))

    if not df.empty:
        df.to_sql(nome, _engine, if_exists="append", index=False)


def inserir_linha(nome, dados):
    colunas = _get_colunas(nome)

    filtrado = {k: v for k, v in dados.items() if k in colunas}

    if not filtrado:
        return

    filtrado = _limpar_dict(filtrado)

    cols = ", ".join(f'"{c}"' for c in filtrado.keys())
    vals = ", ".join(f":{c}" for c in filtrado.keys())

    with _engine.begin() as conn:
        conn.execute(
            text(f'INSERT INTO "{nome}" ({cols}) VALUES ({vals})'),
            filtrado
        )


def inserir_varias_linhas(nome, lista_dicts):
    if not lista_dicts:
        return

    colunas = _get_colunas(nome)

    filtrados = [
        _limpar_dict({k: v for k, v in d.items() if k in colunas})
        for d in lista_dicts
    ]

    filtrados = [f for f in filtrados if f]

    if not filtrados:
        return

    cols = ", ".join(f'"{c}"' for c in filtrados[0].keys())
    vals = ", ".join(f":{c}" for c in filtrados[0].keys())

    with _engine.begin() as conn:
        conn.execute(
            text(f'INSERT INTO "{nome}" ({cols}) VALUES ({vals})'),
            filtrados
        )


def atualizar_linhas(nome, filtro_col, filtro_val, novos_valores):
    colunas = _get_colunas(nome)

    filtrado = {k: v for k, v in novos_valores.items() if k in colunas}

    if not filtrado:
        return

    filtrado = _limpar_dict(filtrado)

    sets = ", ".join(f'"{c}" = :{c}' for c in filtrado.keys())
    params = dict(filtrado)
    params["_filtro"] = _limpar_valor(filtro_val)

    with _engine.begin() as conn:
        conn.execute(
            text(
                f'UPDATE "{nome}" SET {sets} '
                f'WHERE "{filtro_col}" = :_filtro'
            ),
            params
        )


def deletar_linhas(nome, filtro_col, filtro_val):
    with _engine.begin() as conn:
        conn.execute(
            text(f'DELETE FROM "{nome}" WHERE "{filtro_col}" = :_v'),
            {"_v": filtro_val}
        )


def executar(sql, params=None):
    with _engine.begin() as conn:
        conn.execute(text(sql), params or {})


def proximo_id_numerico(nome_tabela, coluna_id, prefixo):
    with _engine.connect() as conn:
        resultado = conn.execute(
            text(
                f'SELECT "{coluna_id}" FROM "{nome_tabela}" '
                f'WHERE "{coluna_id}" LIKE :p '
                f'ORDER BY "{coluna_id}" DESC LIMIT 1'
            ),
            {"p": f"{prefixo}%"}
        ).scalar()

    if not resultado:
        return 1

    try:
        return int(str(resultado).replace(prefixo, "")) + 1
    except ValueError:
        return 1


def obter_proximo_id(nome_tabela, coluna_id, prefixo, reiniciar=False):
    chave = f"{nome_tabela}:{coluna_id}:{prefixo}"

    if reiniciar or chave not in _cache_prox_id:
        _cache_prox_id[chave] = proximo_id_numerico(nome_tabela, coluna_id, prefixo)

    valor = _cache_prox_id[chave]
    _cache_prox_id[chave] = valor + 1

    return valor


def ler_tabela_df(nome, colunas=None, renomear=None):
    df = ler_tabela(nome)

    if df.empty:
        return pd.DataFrame(columns=colunas or [])

    if renomear:
        df = df.rename(columns=renomear)

    if colunas:
        for col in colunas:
            if col not in df.columns:
                df[col] = ''

    return df


def escrever_tabela_df(df, nome, renomear=None):
    df_save = df.copy()

    if renomear:
        df_save = df_save.rename(columns=renomear)

    escrever_tabela(nome, df_save)


def testar_conexao():
    with _engine.connect() as conn:
        return conn.execute(text("SELECT 1")).scalar() == 1