@echo off
title 🚀 Instalação e Uso do Gordon
echo ============================================
echo   🚀 Instalador do Gordon
echo ============================================

REM 1. Clonar o repositório
git clone https://github.com/GuilhermeZiegler/gordon.git
cd gordon

REM 2. Rodar o instalador em modo debug
call install\install.bat

REM 3. Abrir o Gordon
call launcher.bat

REM 4. Apagar tudo e recriar vazio
.venv\Scripts\python.exe install\install.py --force

REM Para recriar com seed:
REM .venv\Scripts\python.exe install\install.py --force --seed

pause
