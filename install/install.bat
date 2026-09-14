@echo off

cd /d "%~dp0.."

set "PROJECT_DIR=%cd%"
set "UV_DIR=%LOCALAPPDATA%\Gordon\uv"
set "UV_EXE=%UV_DIR%\uv.exe"
set "UV_ZIP=%UV_DIR%\uv.zip"

if not exist "%UV_EXE%" (
    echo Baixando uv...
    mkdir "%UV_DIR%" 2>nul

    powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip' -OutFile '%UV_ZIP%'"

    if errorlevel 1 (
        echo Erro ao baixar uv.
        pause
        exit /b 1
    )

    powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%UV_ZIP%' -DestinationPath '%UV_DIR%' -Force"

    if exist "%UV_DIR%\uv-x86_64-pc-windows-msvc\uv.exe" (
        move /Y "%UV_DIR%\uv-x86_64-pc-windows-msvc\uv.exe" "%UV_EXE%" >nul
        rmdir /s /q "%UV_DIR%\uv-x86_64-pc-windows-msvc"
    )

    del /q "%UV_ZIP%" 2>nul
)

if not exist "%UV_EXE%" (
    echo Erro: uv nao foi instalado.
    pause
    exit /b 1
)

echo Instalando Python...
"%UV_EXE%" python install

if errorlevel 1 (
    echo Erro ao instalar Python.
    pause
    exit /b 1
)

echo Instalando dependencias...
"%UV_EXE%" sync --frozen

if errorlevel 1 (
    echo Erro ao instalar dependencias.
    pause
    exit /b 1
)

echo Inicializando dados...
"%UV_EXE%" run python install\install.py --seed

if errorlevel 1 (
    echo Erro ao inicializar dados.
    pause
    exit /b 1
)

set "VENV_DIR=%PROJECT_DIR%\.venv"
set "LAUNCHER=%PROJECT_DIR%\launcher.bat"

(
echo @echo off
echo cd /d "%PROJECT_DIR%"
echo "%VENV_DIR%\Scripts\streamlit.exe" run Gordon.py --server.headless false --browser.gatherUsageStats false
) > "%LAUNCHER%"

echo Criando atalho...

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Gordon.lnk'); $s.TargetPath = '%LAUNCHER%'; $s.WorkingDirectory = '%PROJECT_DIR%'; $s.Save()"

echo.
echo ========================================
echo INSTALACAO CONCLUIDA
echo ========================================
echo.
echo Gordon instalado em:
echo %PROJECT_DIR%
echo.
echo Atalho criado na area de trabalho.
echo.

pause