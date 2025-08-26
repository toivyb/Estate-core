@echo off
SETLOCAL
cd /d %~dp0\..
if not exist scripts\set_pg_env.bat (
  echo Please copy scripts\set_pg_env_example.bat to scripts\set_pg_env.bat and edit credentials.
  exit /b 1
)
call scripts\set_pg_env.bat
echo Running COPY import...
psql -v ON_ERROR_STOP=1 -f scripts\copy_import.sql
