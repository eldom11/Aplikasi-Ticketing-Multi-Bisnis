from sqlalchemy import text

from app.db.session import engine

with engine.connect() as conn:
    result = conn.execute(text("SELECT version()"))
    print("Terhubung!")
    print(result.scalar())