# 🚀 Instalação e Uso do Gordon

## Pré-requisitos
- Ter o **Git** instalado na máquina.
- Ter acesso ao repositório no GitHub.
- Não é necessário instalar Python ou VS Code — o script cuida disso.

---

## 🔧 Instalação com Debug (criação de dados)

```powershell
# 1. Clonar o repositório
git clone https://github.com/seu-usuario/seu-repo.git
cd seu-repo

# 2. Rodar o instalador em modo debug (acompanhar passo a passo)
.\install\install.bat

# 3. Abrir o Gordon
.\launcher.bat

# 4.  Apagar tudo e recriar vazio
.venv\Scripts\python.exe install\install.py --force

# .venv\Scripts\python.exe install\install.py --force --seed