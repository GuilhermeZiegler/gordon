import os
import sys
import shutil
import subprocess
from pathlib import Path

APP_NAME = "Gordon"
UV_URL = "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip"

LOCAL = Path(os.environ["LOCALAPPDATA"])
INSTALL_DIR = LOCAL / APP_NAME
UV_DIR = INSTALL_DIR / "uv"
UV_EXE = UV_DIR / "uv.exe"
PROJECT_DIR = INSTALL_DIR / "app"
VENV_DIR = PROJECT_DIR / ".venv"
LAUNCHER_BAT = INSTALL_DIR / "launcher.bat"
DESKTOP = Path(os.environ["USERPROFILE"]) / "Desktop"
START_MENU = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs"

if getattr(sys, "frozen", False):
    SRC_DIR = Path(sys._MEIPASS) / "payload"
else:
    SRC_DIR = Path(__file__).resolve().parent.parent


def log(msg):
    print(f"[{APP_NAME}] {msg}", flush=True)


def download_uv():
    if UV_EXE.exists():
        return

    UV_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = UV_DIR / "uv.zip"

    log("Baixando uv...")

    subprocess.run([
        "powershell",
        "-NoProfile",
        "-Command",
        f"Invoke-WebRequest -Uri '{UV_URL}' -OutFile '{zip_path}'"
    ], check=True)

    import zipfile

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(UV_DIR)

    zip_path.unlink()

    for sub in UV_DIR.iterdir():
        if sub.is_dir() and (sub / "uv.exe").exists():
            for f in sub.iterdir():
                shutil.move(str(f), str(UV_DIR / f.name))
            shutil.rmtree(sub)
            break


def copy_project():
    if PROJECT_DIR.exists():
        log("Removendo instalação anterior...")
        shutil.rmtree(PROJECT_DIR)

    log("Copiando projeto...")

    shutil.copytree(
        SRC_DIR,
        PROJECT_DIR,
        ignore=shutil.ignore_patterns(
            ".venv",
            "__pycache__",
            "*.pyc",
            ".git",
            "dist",
            "build",
            "*.spec",
            "Gordon-Setup*.exe"
        )
    )


def run_uv(*args):
    return subprocess.run(
        [str(UV_EXE), *args],
        cwd=PROJECT_DIR,
        check=True
    )


def install_deps():
    log("Instalando Python via uv...")
    run_uv("python", "install")

    log("Sincronizando dependências...")
    run_uv("sync", "--frozen", "--native-tls")


def run_seed():
    log("Populando dados de exemplo...")

    subprocess.run(
        [
            str(VENV_DIR / "Scripts" / "python.exe"),
            "install/install.py",
            "--seed"
        ],
        cwd=PROJECT_DIR,
        check=True
    )


def write_launcher_bat():
    content = f"""@echo off
cd /d "{PROJECT_DIR}"
"{VENV_DIR}\\Scripts\\streamlit.exe" run Gordon.py --server.headless false --browser.gatherUsageStats false
"""

    LAUNCHER_BAT.write_text(content, encoding="utf-8")


def create_shortcut(target_dir):
    target_dir.mkdir(parents=True, exist_ok=True)

    lnk_path = target_dir / f"{APP_NAME}.lnk"

    ps = f"""
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut("{lnk_path}")
$s.TargetPath = "{LAUNCHER_BAT}"
$s.WorkingDirectory = "{INSTALL_DIR}"
$s.IconLocation = "{LAUNCHER_BAT}"
$s.Save()
"""

    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        check=True
    )


def main():
    log(f"Instalando em {INSTALL_DIR}")

    INSTALL_DIR.mkdir(parents=True, exist_ok=True)

    download_uv()
    copy_project()
    install_deps()
    run_seed()
    write_launcher_bat()
    create_shortcut(DESKTOP)
    create_shortcut(START_MENU)

    log("Concluído. Use o atalho 'Gordon' na área de trabalho.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"ERRO: {e}")
        sys.exit(1)
