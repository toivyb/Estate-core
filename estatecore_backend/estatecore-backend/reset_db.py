from estatecore_backend import db, create_app

app = create_app()

with app.app_context():
    db.drop_all()
    print("Database reset successful.")
