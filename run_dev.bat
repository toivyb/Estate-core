@echo off
SETLOCAL
cd /d %~dp0
call .venv\Scripts\activate
set FLASK_APP=estatecore_backend.app
set FLASK_ENV=production
python -m flask run --port=5000
