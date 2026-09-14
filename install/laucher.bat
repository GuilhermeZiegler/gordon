@echo off
cd /d "%LOCALAPPDATA%\Gordon\app"
"%LOCALAPPDATA%\Gordon\app\.venv\Scripts\streamlit.exe" run Gordon.py --server.headless true --browser.gatherUsageStats false