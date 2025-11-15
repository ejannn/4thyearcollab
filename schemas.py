from pydantic import BaseModel

class Pzem004tData(BaseModel):
    voltage: float
    current: float
    power: float
    energy: float
    frequency: float
    powerFactor: float
    alarm: bool

class Dht11Data(BaseModel):
    temperature: float
    humidity: float

class SensorData(BaseModel):
    deviceName: str
    pzem004t: Pzem004tData
    dht11: Dht11Data
    
