@echo off
SETLOCAL
cd /d %~dp0

if not exist .venv (
  echo Creating venv...
  py -3 -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
set FLASK_APP=estatecore_backend.app
set FLASK_ENV=production
python -m flask run --port=5000
