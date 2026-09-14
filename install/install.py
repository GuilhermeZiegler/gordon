import os
import sys
import shutil
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from install.bootstrap import bootstrap
from install.popular_dados import popular_dados
from install.seed_all import seed_all
from install.seed._common import DATA_DIR


def limpar():
    if not os.path.exists(DATA_DIR):
        return
    for arquivo in os.listdir(DATA_DIR):
        caminho = os.path.join(DATA_DIR, arquivo)
        if os.path.isfile(caminho) and (arquivo.endswith('.pkl') or arquivo == 'config.json'):
            os.remove(caminho)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', action='store_true')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()

    if args.force:
        limpar()

    bootstrap()

    if args.seed:
        popular_dados()
        seed_all()

    print("Instalacao concluida.")


if __name__ == "__main__":
    main()