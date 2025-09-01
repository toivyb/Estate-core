@echo off
REM Copy this to set_pg_env.bat and edit values, then run it in the same shell before running psql loader.
SETLOCAL
set PGHOST=localhost
set PGPORT=5432
set PGUSER=postgres
set PGPASSWORD=YOURPASSWORD
set PGDATABASE=estatecore
echo Postgres env set for this session.
