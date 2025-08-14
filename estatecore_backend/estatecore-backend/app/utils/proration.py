from datetime import date
def prorate_monthly(amount_cents: int, start: date, end: date):
    days = (end - start).days + 1
    per_day = amount_cents / 30.0  # simple 30-day month
    return int(round(per_day * days))
