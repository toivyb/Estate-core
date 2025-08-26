# EstateCore Backend — Real Endpoints Edition

This build removes synthetic ML pickles. All AI endpoints compute from **real DB data** using clear rules
and trend calculations. If there is no historical data yet, they degrade gracefully.

## Windows Quick Start
1) Unzip to:
   `C:\Users\toivybraun\estatecore_project\estatecore_backend`
2) PowerShell:
```
cd C:\Users\toivybraun\estatecore_project\estatecore_backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
$env:FLASK_APP="estatecore_backend.app"
$env:FLASK_ENV="production"
# Recommended for production:
# $env:DATABASE_URL="postgresql+psycopg2://postgres:YOURPASSWORD@localhost:5432/estatecore"
python -m flask run --port=5000
```

## Core Tables Added
- Tenant, Lease, Payment, Expense, UtilityBill, Message, Application
- FeatureToggle (for per-client enable/disable)

## Key Endpoints (new)
- POST `/api/seed/demo` — optional seed data for quick realism.
- CRUD for tenants, leases, payments, expenses, messages.
- "AI" endpoints now read live data:
  - `/api/ai/lease-score` — computes from **Application** payload or latest application row.
  - `/api/ai/rent-delay` — uses **Payment** history stats for a tenant.
  - `/api/ai/expense-anomaly` — compares against **Expense** rolling average by category (90 days).
  - `/api/ai/cashflow` — sums **Payment (paid)** minus **Expense** by month and projects via linear trend.
  - `/api/ai/asset-health` — from last 30 days collection %, open maintenance backlog, last 90 days expense ratio.
  - `/api/ai/revenue-leakage` — compares **Lease.contract_rent** vs **Payment.charge_applied**.
  - `/api/ai/sentiment` — lexicon-based on **Message** text or provided input.
  - `/api/ai/maintenance-risk` — keyword-based severity.

You can swap these rule engines for ML later without changing the API.
