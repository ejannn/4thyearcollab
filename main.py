from fastapi import FastAPI, Depends, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, SensorReading
from schemas import SensorData, Pzem004tData, Dht11Data
import csv
from io import StringIO

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


# --- 1️⃣ Get Latest Data from Database (GET) ---
@app.get("/api/sensor")
def get_sensor_data(db: Session = Depends(get_db)):
    """
    Returns the latest sensor data from PostgreSQL.
    Dashboard polls this every 2 seconds to display real data from Raspberry Pi.
    """
    # Get the most recent reading from the database
    latest_reading = db.query(SensorReading).order_by(
        SensorReading.timestamp.desc()
    ).first()
    
    if latest_reading:
        # Convert database record to Pydantic schema for response
        return SensorData(
            deviceName=latest_reading.device_name,
            pzem004t=Pzem004tData(
                voltage=latest_reading.voltage,
                current=latest_reading.current,
                power=latest_reading.power,
                energy=latest_reading.energy,
                frequency=latest_reading.frequency,
                powerFactor=latest_reading.power_factor,
                alarm=latest_reading.alarm
            ),
            dht11=Dht11Data(
                temperature=latest_reading.temperature,
                humidity=latest_reading.humidity
            )
        )
    else:
        # Return default data if no readings exist yet
        return SensorData(
            deviceName="No data yet",
            pzem004t=Pzem004tData(
                voltage=0.0,
                current=0.0,
                power=0.0,
                energy=0.0,
                frequency=0.0,
                powerFactor=0.0,
                alarm=False
            ),
            dht11=Dht11Data(
                temperature=0.0,
                humidity=0.0
            )
        )



# --- 2️⃣ Real Sensor Data from Raspberry Pi (POST) ---
@app.post("/api/sensor")
def update_sensor_data(data: SensorData, db: Session = Depends(get_db)):
    """
    Receives sensor data from Raspberry Pi and stores it in PostgreSQL.
    The dashboard's GET /api/sensor will return this latest data.
    """
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


# --- 3️⃣ Get Sensor Data History (GET) ---
@app.get("/api/sensor/history")
def get_sensor_history(limit: int = Query(100, ge=1, le=10000), db: Session = Depends(get_db)):
    """
    Returns the last N sensor readings from PostgreSQL.
    Query parameter 'limit': number of records to return (default 100, max 10000).
    
    Example: GET /api/sensor/history?limit=50
    """
    readings = db.query(SensorReading).order_by(
        SensorReading.timestamp.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat(),
            "device_name": r.device_name,
            "voltage": round(r.voltage, 2),
            "current": round(r.current, 2),
            "power": round(r.power, 2),
            "energy": round(r.energy, 2),
            "frequency": round(r.frequency, 2),
            "power_factor": round(r.power_factor, 2),
            "alarm": r.alarm,
            "temperature": round(r.temperature, 2),
            "humidity": round(r.humidity, 2)
        }
        for r in reversed(readings)  # Return oldest first for chronological order
    ]


# --- 4️⃣ Export Sensor Data as CSV (GET) ---
@app.get("/api/sensor/export")
def export_sensor_data(db: Session = Depends(get_db)):
    """
    Exports all sensor readings as a CSV file.
    Download: GET /api/sensor/export
    """
    readings = db.query(SensorReading).order_by(SensorReading.timestamp.asc()).all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'ID', 'Device', 'Voltage(V)', 'Current(A)', 'Power(W)', 'Energy(kWh)',
        'Frequency(Hz)', 'Power Factor', 'Alarm', 'Temperature(°C)', 'Humidity(%)', 'Timestamp'
    ])
    
    for r in readings:
        writer.writerow([
            r.id,
            r.device_name,
            round(r.voltage, 2),
            round(r.current, 2),
            round(r.power, 2),
            round(r.energy, 2),
            round(r.frequency, 2),
            round(r.power_factor, 2),
            r.alarm,
            round(r.temperature, 2),
            round(r.humidity, 2),
            r.timestamp.isoformat()
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment;filename=sensor_data.csv"}
    )


# --- Dashboard UI ---
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
