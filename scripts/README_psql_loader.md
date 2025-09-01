# Postgres Bulk Loader (psql COPY)

This method is **fast** for large datasets. It bypasses the Flask app and uses `psql COPY`.

## 0) Prepare Postgres env (Windows)
1) Duplicate `scripts\set_pg_env_example.bat` to `scripts\set_pg_env.bat`
2) Edit values (user/password/db), then run it in your PowerShell/CMD session:
```
scripts\set_pg_env.bat
```
This sets `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` for `psql`.

## 1) CSVs for COPY
Use the `*_psql.csv` templates (they include `id` and `created_at` columns that COPY expects).
Templates are in: `csv_templates_psql\`

Columns must match exactly:

- `tenants_psql.csv`: id,name,email,client_id,created_at
- `leases_psql.csv`: id,tenant_id,contract_rent,start_date,end_date,created_at
- `payments_psql.csv`: id,tenant_id,month,amount_due,amount_paid,days_late,paid,created_at
- `expenses_psql.csv`: id,client_id,category,amount,date,created_at
- `utility_bills_psql.csv`: id,client_id,month,amount,heating_type,created_at
- `messages_psql.csv`: id,client_id,tenant_id,text,created_at
- `applications_psql.csv`: id,tenant_name,income,proposed_rent,credit_score,late_payments,client_id,created_at

> If you don't have ids/created_at, you can leave them empty in CSV; Postgres will fill defaults when possible.

## 2) Generate the COPY SQL
```
python scripts\generate_copy_sql.py csv_templates_psql scripts\copy_import.sql
```

## 3) Run it with psql
```
psql -v ON_ERROR_STOP=1 -f scripts\copy_import.sql
```
If you see permission issues, make sure the file paths in the SQL exist and Postgres can read them. On Windows, using the psql client locally with absolute paths works reliably.

## 4) Optional: create schema via SQL
If you haven't run the Flask app yet, you can create tables directly with:
```
psql -v ON_ERROR_STOP=1 -f scripts\schema_ddl.sql
```
But normally, just run the Flask app once (`setup.bat`) and tables are created.
