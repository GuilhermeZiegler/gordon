@echo off

cd /d "%~dp0"

where uv >nul 2>nul

if errorlevel 1 (
    echo uv nao encontrado. Instale uv primeiro.
    exit /b 1
)

set "ROOT=%~dp0.."
set "PAYLOAD=%~dp0_payload"
set "OUTPUT=%USERPROFILE%\Desktop\Gordon-Installers"

if exist "%PAYLOAD%" (
    rmdir /s /q "%PAYLOAD%"
)

if exist "%OUTPUT%" (
    del /q "%OUTPUT%\Gordon-Setup.exe" >nul 2>nul
    del /q "%OUTPUT%\Gordon-Setup-Debug.exe" >nul 2>nul
) else (
    mkdir "%OUTPUT%"
)

echo Preparando projeto para empacotamento...

mkdir "%PAYLOAD%"

robocopy "%ROOT%" "%PAYLOAD%" /E ^
  /XD ".venv" ^
      "build" ^
      "dist" ^
      ".git" ^
      "_payload" ^
  /XF "*.pyc" ^
      "*.spec" ^
      "Gordon-Setup*.exe"

if errorlevel 8 (
    echo Erro ao preparar o projeto.
    rmdir /s /q "%PAYLOAD%"
    exit /b 1
)

uv pip install pyinstaller

"..\.venv\Scripts\pyinstaller.exe" ^
  --onefile ^
  --noconsole ^
  --name Gordon-Setup ^
  --distpath "%OUTPUT%" ^
  --workpath "build" ^
  --specpath "build" ^
  --add-data "%PAYLOAD%;payload" ^
  launcher.py

if errorlevel 1 (
    echo Erro ao gerar Gordon-Setup.exe.
    rmdir /s /q "%PAYLOAD%"
    exit /b 1
)

"..\.venv\Scripts\pyinstaller.exe" ^
  --onefile ^
  --name Gordon-Setup-Debug ^
  --distpath "%OUTPUT%" ^
  --workpath "build" ^
  --specpath "build" ^
  --add-data "%PAYLOAD%;payload" ^
  launcher.py

if errorlevel 1 (
    echo Erro ao gerar Gordon-Setup-Debug.exe.
    rmdir /s /q "%PAYLOAD%"
    exit /b 1
)

rmdir /s /q "%PAYLOAD%"

echo.
echo Build concluido.
echo Instaladores gerados em:
echo %OUTPUT%
echo.

pause