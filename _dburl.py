from app import create_app
a = create_app()
print("SQLALCHEMY_DATABASE_URI =", a.config["SQLALCHEMY_DATABASE_URI"])
