from datetime import datetime
import pandas as pd
from utils.db import ler_tabela


HOJE = datetime.now().strftime("%d/%m/%Y")


def separador(titulo):
    print()
    print("=" * 70)
    print(titulo)
    print("=" * 70)


def _filtrar_por_data(df, coluna):
    if df.empty or coluna not in df.columns:
        return df

    datas = pd.to_datetime(df[coluna], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    hoje = datetime.now().date()

    filtrado = df[datas.dt.date == hoje].copy()

    if filtrado.empty:
        filtrado = df.tail(20).copy()
        print(f"(sem registros de hoje — mostrando últimos 20)")
    else:
        print(f"({len(filtrado)} registro(s) de hoje)")

    return filtrado


def mostrar_tabela(df, colunas=None):
    if df.empty:
        print("  (vazio)")
        return

    if colunas:
        colunas = [c for c in colunas if c in df.columns]
        df = df[colunas]

    print(df.to_string(index=False))


def carregar_jsonb(nome_tabela):
    import json
    df = ler_tabela(nome_tabela)

    if df.empty or "dados" not in df.columns:
        return None

    valor = df["dados"].iloc[0]

    if valor is None:
        return None

    if isinstance(valor, (dict, list)):
        return valor

    if isinstance(valor, str):
        try:
            return json.loads(valor)
        except Exception:
            return None

    return None