from apscheduler.schedulers.background import BackgroundScheduler
from estatecore_backend.models.rent import Rent
from estatecore_backend.models import db
from utils.email import send_rent_reminder
from utils.sms import send_rent_reminder_sms
from datetime import datetime, timedelta

def apply_late_fees():
    today = datetime.utcnow().date()
    rents = Rent.query.filter_by(status='unpaid').all()
    for rent in rents:
        grace = 5  # Default grace days
        fee_per_day = 50  # Default fee
        if today > rent.due_date + timedelta(days=grace):
            days_late = (today - rent.due_date - timedelta(days=grace)).days
            rent.late_fee = days_late * fee_per_day
            db.session.commit()

def send_reminders():
    rents = Rent.query.filter_by(status='unpaid').all()
    for rent in rents:
        send_rent_reminder(rent)
        send_rent_reminder_sms(rent)
        rent.reminders_sent += 1
        db.session.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(apply_late_fees, 'interval', hours=24)
scheduler.add_job(send_reminders, 'interval', hours=24)
scheduler.start()
