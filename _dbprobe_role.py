from app import create_app, db
from sqlalchemy import text
a = create_app()
with a.app_context():
    print("DB URI:", a.config["SQLALCHEMY_DATABASE_URI"])
    cols = db.session.execute(text("""
        select column_name
        from information_schema.columns
        where table_schema='public' and table_name='user'
        order by ordinal_position
    """)).scalars().all()
    print("user columns:", cols)
