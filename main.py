from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, SensorReading
from schemas import SensorData, Pzem004tData, Dht11Data
import random

# Create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sensor Monitor API")

# Allow any app (Flutter, web, Pi, etc.) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

# Database connection per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Fake Data for Now ---
latest_data = SensorData(
    deviceName="AirCon Monitor 1",
    pzem004t=Pzem004tData(
        voltage=220.0,
        current=1.2,
        power=264.6,
        energy=0.25,
        frequency=60.0,
        powerFactor=0.98,
        alarm=False
    ),
    dht11=Dht11Data(
        temperature=27.3,
        humidity=65.2
    )
)

# --- 1️⃣ Simulated Data (GET) ---
@app.get("/api/sensor")
def get_sensor_data():
    """
    Simulates real-time sensor data changes.
    Later, when the Raspberry Pi sends data,
    this endpoint can just return the most recent reading from PostgreSQL.
    """
    # Only simulate if Pi is not yet sending data
    latest_data.pzem004t.voltage += random.uniform(-0.5, 0.5)
    latest_data.pzem004t.current += random.uniform(-0.05, 0.05)
    latest_data.dht11.temperature += random.uniform(-0.3, 0.3)
    latest_data.dht11.humidity += random.uniform(-1, 1)
    return latest_data


# --- 2️⃣ Real Sensor Data from Raspberry Pi (POST) ---
@app.post("/api/sensor")
def update_sensor_data(data: SensorData, db: Session = Depends(get_db)):
    """
    This is what your Raspberry Pi will use later:
    It sends real sensor readings in JSON format.
    """
    global latest_data
    latest_data = data  # refresh current dashboard view

    # Store to PostgreSQL
    reading = SensorReading(
        device_name=data.deviceName,
        voltage=data.pzem004t.voltage,
        current=data.pzem004t.current,
        power=data.pzem004t.power,
        energy=data.pzem004t.energy,
        frequency=data.pzem004t.frequency,
        power_factor=data.pzem004t.powerFactor,
        temperature=data.dht11.temperature,
        humidity=data.dht11.humidity
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    return {"message": "✅ Sensor data saved!", "id": reading.id}


# --- Dashboard UI ---
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
