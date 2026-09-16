import os
import json
import pickle
import pandas as pd

from utils.paths import get_caminhos
from utils.db import escrever_tabela, executar


_c = get_caminhos()
DATA_DIR = os.path.dirname(_c["produtos"])


def _carregar_pkl(nome):
    caminho = os.path.join(DATA_DIR, f"{nome}.pkl")
    if not os.path.exists(caminho):
        return None
    with open(caminho, "rb") as f:
        return pickle.load(f)


def _para_df(dados):
    if dados is None:
        return pd.DataFrame()
    if isinstance(dados, pd.DataFrame):
        return dados
    if isinstance(dados, list):
        return pd.DataFrame(dados) if dados else pd.DataFrame()
    return pd.DataFrame()


def migrar_dataframes():
    arquivos = [
        "produtos", "insumos", "ficha_tecnica", "mesas", "pedidos",
        "movimentacoes", "compras", "estoque", "estoque_baixas",
        "estoque_inventario",
    ]

    for nome in arquivos:
        dados = _carregar_pkl(nome)

        if dados is None:
            print(f"[skip] {nome}.pkl não encontrado")
            continue

        df = _para_df(dados)

        if nome == "produtos" and "desc" in df.columns:
            df = df.rename(columns={"desc": "descricao"})

        if df.empty:
            print(f"[vazio] {nome}")
            continue

        df = df.where(pd.notna(df), None)

        if "cod_prod" in df.columns:
            df["cod_prod"] = df["cod_prod"].astype(str)
        if "cod_item" in df.columns:
            df["cod_item"] = df["cod_item"].astype(str)

        escrever_tabela(nome, df)
        print(f"[ok] {nome}: {len(df)} linhas")


def migrar_listas():
    arquivos = [
        "clientes",
        "funcionarios",
        "delivery",
        "agendamentos",
        "historico_pedidos",
        "historico_mesas",
    ]

    for nome in arquivos:
        dados = _carregar_pkl(nome)

        if dados is None:
            print(f"[skip] {nome}.pkl não encontrado")
            continue

        df = _para_df(dados)

        if df.empty:
            print(f"[vazio] {nome}")
            continue

        df = df.where(pd.notna(df), None)

        if "cod_prod" in df.columns:
            df["cod_prod"] = df["cod_prod"].astype(str)
        if "cod_item" in df.columns:
            df["cod_item"] = df["cod_item"].astype(str)
        if "id_mesa" in df.columns:
            df["id_mesa"] = df["id_mesa"].astype(str)

        escrever_tabela(nome, df)
        print(f"[ok] {nome}: {len(df)} linhas")


def migrar_jsonb():
    arquivos = [
        "historico_caixa",
        "historico_estoque",
        "historico_baixas",
        "historico_inventario",
        "historico_nao_baixados",
        "historico_compras",
    ]

    for nome in arquivos:
        dados = _carregar_pkl(nome)

        if dados is None:
            print(f"[skip] {nome}.pkl não encontrado")
            continue

        if isinstance(dados, pd.DataFrame):
            dados = dados.to_dict(orient="records")

        payload = json.dumps(dados, ensure_ascii=False, default=str)

        executar(f'TRUNCATE TABLE "{nome}"')
        executar(
            f'INSERT INTO "{nome}" (dados) VALUES (:d)',
            {"d": payload}
        )
        print(f"[ok] {nome}: JSONB gravado ({len(dados) if isinstance(dados, list) else 1} itens)")


def migrar_caixa():
    dados = _carregar_pkl("caixa")
    if dados is None:
        print("[skip] caixa.pkl não encontrado")
        return

    payload = json.dumps(dados, ensure_ascii=False, default=str)
    executar('TRUNCATE TABLE "caixa"')
    executar('INSERT INTO "caixa" (dados) VALUES (:d)', {"d": payload})
    print("[ok] caixa: JSONB gravado")


def migrar_config():
    caminho = os.path.join(DATA_DIR, "config.json")
    if not os.path.exists(caminho):
        print("[skip] config.json não encontrado")
        return

    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)

    payload = json.dumps(dados, ensure_ascii=False)
    executar('TRUNCATE TABLE "config"')
    executar('INSERT INTO "config" (dados) VALUES (:d)', {"d": payload})
    print("[ok] config: JSONB gravado")


def migrar_tudo():
    print("=== DataFrames ===")
    migrar_dataframes()
    print("=== Listas ===")
    migrar_listas()
    print("=== JSONB ===")
    migrar_jsonb()
    print("=== Caixa ===")
    migrar_caixa()
    print("=== Config ===")
    migrar_config()
    print("Migração concluída.")


if __name__ == "__main__":
    migrar_tudo()