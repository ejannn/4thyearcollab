# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Example: change credentials to match your setup
DATABASE_URL = "postgresql+psycopg2://postgres:nieljhon1@localhost/sensor_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()
