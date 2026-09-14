import pandas as pd
import os
import pickle

def carregar_pkl(caminho):
    if os.path.exists(caminho):
        with open(caminho, 'rb') as f:
            return pickle.load(f)
    return pd.DataFrame()

def salvar_pkl(df, caminho):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, 'wb') as f:
        pickle.dump(df, f)