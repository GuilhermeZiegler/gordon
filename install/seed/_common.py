import os
import sys

raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if raiz not in sys.path:
    sys.path.insert(0, raiz)

from utils.paths import get_caminhos

_c = get_caminhos()
DATA_DIR = os.path.dirname(_c["produtos"])