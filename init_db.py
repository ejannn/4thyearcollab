# init_db.py
import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine
from models import Base

DB_USER = "postgres"
DB_PASSWORD = "nieljhon1"
DB_HOST = "localhost"
DB_NAME = "sensor_db"

# Step 1: Connect to the default database first
conn = psycopg2.connect(
    dbname="postgres", user=DB_USER, password=DB_PASSWORD, host=DB_HOST
)
conn.autocommit = True

# Step 2: Create the database if it doesn't exist
cursor = conn.cursor()
cursor.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), [DB_NAME])
exists = cursor.fetchone()
if not exists:
    cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
    print(f"✅ Database '{DB_NAME}' created!")
else:
    print(f"ℹ️ Database '{DB_NAME}' already exists.")

cursor.close()
conn.close()

# Step 3: Create tables using SQLAlchemy
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully!")
