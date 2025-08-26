@echo off
SETLOCAL
cd /d %~dp0
set DATABASE_URL=postgresql+psycopg2://postgres:YOURPASSWORD@localhost:5432/estatecore
echo DATABASE_URL set for this session.
