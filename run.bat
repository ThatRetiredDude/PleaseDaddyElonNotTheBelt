@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo No .venv in this directory. Create it and install dependencies, for example:
  echo   py -3 -m venv .venv
  echo   .venv\Scripts\pip install -r requirements.txt
  exit /b 1
)
.venv\Scripts\pip show tweepy >nul 2>&1
if errorlevel 1 (
  echo Installing requirements into .venv …
  .venv\Scripts\pip install -r requirements.txt
)
.venv\Scripts\python.exe PleaseDaddyElonNotTheBelt.py
endlocal
