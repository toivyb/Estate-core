
#!/usr/bin/env python
import sys
import csv
from pathlib import Path
from datetime import date
from estatecore_backend.app import app as flask_app
from estatecore_backend.extensions import db
from estatecore_backend.models.tenant import Tenant
from estatecore_backend.models.lease import Lease
from estatecore_backend.models.payment import Payment
from estatecore_backend.models.expense import Expense
from estatecore_backend.models.utilitybill import UtilityBill
from estatecore_backend.models.message import Message
from estatecore_backend.models.application import Application

def parse_bool(v):
    if isinstance(v, bool):
        return v
    s = str(v or '').strip().lower()
    return s in ('1','true','yes','y')

def parse_int(v, default=0):
    try:
        return int(float(v))
    except Exception:
        return default

def parse_float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default

def parse_date(v, default=date(2025,1,1)):
    try:
        y,m,d = map(int, str(v).split('-'))
        return date(y,m,d)
    except Exception:
        return default

def load_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows

def ensure_dirs():
    Path('uploads').mkdir(exist_ok=True)

def import_tenants(rows, dry):
    created=0
    for r in rows:
        name = r.get('name')
        if not name:
            continue
        email = r.get('email')
        client_id = parse_int(r.get('client_id',1),1)
        # de-dup by email+client
        q = Tenant.query.filter_by(email=email, client_id=client_id) if email else None
        if q and q.first():
            continue
        t = Tenant(name=name, email=email, client_id=client_id)
        if not dry:
            db.session.add(t)
        created+=1
    if not dry:
        db.session.commit()
    return created

def import_leases(rows, dry):
    created=0
    for r in rows:
        tenant_id = parse_int(r.get('tenant_id'))
        if not tenant_id:
            continue
        contract_rent = parse_float(r.get('contract_rent'))
        start_date = parse_date(r.get('start_date','2025-01-01'))
        end_date = parse_date(r.get('end_date','2025-12-31'))
        l = Lease(tenant_id=tenant_id, contract_rent=contract_rent, start_date=start_date, end_date=end_date)
        if not dry:
            db.session.add(l)
        created+=1
    if not dry:
        db.session.commit()
    return created

def import_payments(rows, dry):
    created=0
    for r in rows:
        tenant_id = parse_int(r.get('tenant_id'))
        month = r.get('month')
        if not (tenant_id and month):
            continue
        p = Payment(
            tenant_id=tenant_id,
            month=month,
            amount_due=parse_float(r.get('amount_due',0)),
            amount_paid=parse_float(r.get('amount_paid',0)),
            days_late=parse_int(r.get('days_late',0)),
            paid=parse_bool(r.get('paid', False))
        )
        if not dry:
            db.session.add(p)
        created+=1
    if not dry:
        db.session.commit()
    return created

def import_expenses(rows, dry):
    created=0
    for r in rows:
        e = Expense(
            client_id=parse_int(r.get('client_id',1)),
            category=r.get('category') or 'Other',
            amount=parse_float(r.get('amount',0)),
            date=parse_date(r.get('date','2025-08-01'))
        )
        if not dry:
            db.session.add(e)
        created+=1
    if not dry:
        db.session.commit()
    return created

def import_utility(rows, dry):
    created=0
    for r in rows:
        u = UtilityBill(
            client_id=parse_int(r.get('client_id',1)),
            month=r.get('month'),
            amount=parse_float(r.get('amount',0)),
            heating_type=(r.get('heating_type') or 'gas')
        )
        if not dry:
            db.session.add(u)
        created+=1
    if not dry:
        db.session.commit()
    return created

def import_messages(rows, dry):
    created=0
    for r in rows:
        m = Message(
            client_id=parse_int(r.get('client_id',1)),
            tenant_id=parse_int(r.get('tenant_id',0)) or None,
            text=r.get('text') or ''
        )
        if not dry:
            db.session.add(m)
        created+=1
    if not dry:
        db.session.commit()
    return created

def import_applications(rows, dry):
    created=0
    for r in rows:
        a = Application(
            tenant_name=r.get('tenant_name') or 'Unknown',
            income=parse_float(r.get('income',0)),
            proposed_rent=parse_float(r.get('proposed_rent',0)),
            credit_score=parse_int(r.get('credit_score',0)),
            late_payments=parse_int(r.get('late_payments',0)),
            client_id=parse_int(r.get('client_id',1))
        )
        if not dry:
            db.session.add(a)
        created+=1
    if not dry:
        db.session.commit()
    return created

def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/import_csv.py <folder> [--dry-run]')
        sys.exit(1)
    folder = Path(sys.argv[1])
    dry = ('--dry-run' in sys.argv)
    if not folder.exists():
        print(f'Folder not found: {folder}')
        sys.exit(2)
    files = {
        'tenants.csv': import_tenants,
        'leases.csv': import_leases,
        'payments.csv': import_payments,
        'expenses.csv': import_expenses,
        'utility_bills.csv': import_utility,
        'messages.csv': import_messages,
        'applications.csv': import_applications,
    }
    with flask_app.app_context():
        total=0
        for name, fn in files.items():
            p = folder / name
            if p.exists():
                rows = load_csv(p)
                count = fn(rows, dry)
                print(f'[{name}] {count} rows processed' + (' (dry-run)' if dry else ''))
                total += count
            else:
                print(f'[{name}] skipped (missing)')
        print(f'Done. {total} total rows.')

if __name__ == '__main__':
    main()
