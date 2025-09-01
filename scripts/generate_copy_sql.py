#!/usr/bin/env python
import sys
from pathlib import Path

TEMPLATE = """-- Generated COPY script
-- Edit the CSV paths if needed. Requires headers in CSV files.
\timing on

COPY tenant (id, name, email, client_id, created_at)
FROM '%(TENANTS)s' WITH (FORMAT csv, HEADER true);

COPY lease (id, tenant_id, contract_rent, start_date, end_date, created_at)
FROM '%(LEASES)s' WITH (FORMAT csv, HEADER true);

COPY payment (id, tenant_id, month, amount_due, amount_paid, days_late, paid, created_at)
FROM '%(PAYMENTS)s' WITH (FORMAT csv, HEADER true);

COPY expense (id, client_id, category, amount, date, created_at)
FROM '%(EXPENSES)s' WITH (FORMAT csv, HEADER true);

COPY utility_bill (id, client_id, month, amount, heating_type, created_at)
FROM '%(UTILITY)s' WITH (FORMAT csv, HEADER true);

COPY message (id, client_id, tenant_id, text, created_at)
FROM '%(MESSAGES)s' WITH (FORMAT csv, HEADER true);

COPY application (id, tenant_name, income, proposed_rent, credit_score, late_payments, client_id, created_at)
FROM '%(APPLICATIONS)s' WITH (FORMAT csv, HEADER true);
"""

def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/generate_copy_sql.py <csv_folder> <output_sql_path>")
        sys.exit(1)
    folder = Path(sys.argv[1]).resolve()
    out_sql = Path(sys.argv[2]).resolve()
    if not folder.exists():
        print(f"CSV folder not found: {folder}")
        sys.exit(2)

    mapping = {
        "TENANTS": (folder / "tenants_psql.csv"),
        "LEASES": (folder / "leases_psql.csv"),
        "PAYMENTS": (folder / "payments_psql.csv"),
        "EXPENSES": (folder / "expenses_psql.csv"),
        "UTILITY": (folder / "utility_bills_psql.csv"),
        "MESSAGES": (folder / "messages_psql.csv"),
        "APPLICATIONS": (folder / "applications_psql.csv"),
    }

    values = {k: str(v).replace("\\", "/") for k, v in mapping.items()}
    sql = TEMPLATE % values
    out_sql.write_text(sql, encoding="utf-8")
    print(f"Wrote {out_sql}")

if __name__ == "__main__":
    main()
