import psycopg2
from psycopg2.extras import RealDictCursor
import os

def connect_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "YOUR DATA BASE"),
        user=os.getenv("DB_USER", "******"),
        password=os.getenv("DB_PASS", "******"),
        port=os.getenv("DB_PORT", 5432)
    )

db = connect_db()
cursor = db.cursor(cursor_factory=RealDictCursor)
