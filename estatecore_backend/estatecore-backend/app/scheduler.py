
from apscheduler.schedulers.background import BackgroundScheduler
from estatecore_backend.models.training_log import TrainingLog
from estatecore_backend import db
from datetime import datetime

from estatecore_backend.ai_models.training.train_lease_model import train_lease_model
from estatecore_backend.ai_models.training.train_rent_delay import train_rent_delay_model
from estatecore_backend.ai_models.training.train_maintenance_forecast import train_maintenance_model
from estatecore_backend.ai_models.training.train_utility_forecast import train_utility_model
from estatecore_backend.ai_models.training.train_revenue_leakage import train_revenue_model
from estatecore_backend.ai_models.training.train_asset_health_score import train_asset_health_model

def safe_train(model_name, fn):
    log = TrainingLog.query.filter_by(model_name=model_name).first()
    if not log or log.is_enabled:
        fn()
        if not log:
            log = TrainingLog(model_name=model_name)
        log.last_trained = datetime.utcnow()
        db.session.add(log)
        db.session.commit()

def schedule_jobs():
    scheduler = BackgroundScheduler()

    scheduler.add_job(lambda: safe_train("Lease Model", train_lease_model), 'interval', days=30)
    scheduler.add_job(lambda: safe_train("Rent Delay Model", train_rent_delay_model), 'interval', days=30)
    scheduler.add_job(lambda: safe_train("Maintenance Model", train_maintenance_model), 'interval', days=30)
    scheduler.add_job(lambda: safe_train("Utility Model", train_utility_model), 'interval', days=30)
    scheduler.add_job(lambda: safe_train("Revenue Model", train_revenue_model), 'interval', days=30)
    scheduler.add_job(lambda: safe_train("Asset Health Model", train_asset_health_model), 'interval', days=30)

    scheduler.start()
    print("🧠 Smart AI scheduler with toggle control loaded.")
