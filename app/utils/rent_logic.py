from datetime import date, timedelta
from estatecore_backend import db
from estatecore_backend.models import RentRecord, User
from estatecore_backend.utils.email_sms import send_email

LATE_FEE_AMOUNT = 50.0
REMINDER_DAY_OFFSETS = (-3, +2)  # 3 days before due, 2 days after missed

def apply_late_fees_today():
    today = date.today()
    q = RentRecord.query.filter(
        RentRecord.due_date != None,
        RentRecord.due_date < today,
        RentRecord.is_paid == False,
        RentRecord.late_fee_applied == False
    ).all()
    for r in q:
        r.amount += LATE_FEE_AMOUNT
        r.late_fee_applied = True
    if q:
        db.session.commit()
    return len(q)

def send_rent_reminders_today():
    today = date.today()
    sent = 0
    for offset in REMINDER_DAY_OFFSETS:
        target = today + timedelta(days=offset)
        matches = RentRecord.query.filter(RentRecord.due_date == target).all()
        for r in matches:
            # In a real system map to tenant email via user relation.
            send_email("tenant@example.com", "Rent Reminder",
                       f"Your rent of ${r.amount:.2f} is due on {r.due_date}.")
            sent += 1
    return sent
