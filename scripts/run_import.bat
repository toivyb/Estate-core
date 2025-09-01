@echo off
SETLOCAL
cd /d %~dp0\..

if not exist .venv (
  echo Virtualenv not found. Run setup.bat once first.
  exit /b 1
)

call .venv\Scripts\activate
set FLASK_APP=estatecore_backend.app
set FLASK_ENV=production

REM Change 'csv_templates' to your folder with real CSVs
python scripts\import_csv.py csv_templates
