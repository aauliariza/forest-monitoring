#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Service - Backend API dan MQTT Subscriber
Menerima data dari broker, menyimpan ke database, dan menyediakan API
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import paho.mqtt.client as mqtt
import json
import os
import threading
import asyncio
from typing import List

# Konfigurasi
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://admin:password123@db/forest_db')
MQTT_BROKER_HOST = os.getenv('MQTT_BROKER_HOST', 'broker')
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "sensors/telemetry"

# Setup Database
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Model Database
class SensorNode(Base):
    __tablename__ = "sensor_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id_string = Column(String, unique=True, index=True)
    location = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    readings = relationship("TelemetryReading", back_populates="node")

class TelemetryReading(Base):
    __tablename__ = "telemetry_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("sensor_nodes.id"))
    sensor_type = Column(String)  # temperature, humidity, smoke
    timestamp = Column(DateTime)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    smoke = Column(Float, nullable=True)
    status = Column(String)
    node = relationship("SensorNode", back_populates="readings")

# Buat tabel jika belum ada
Base.metadata.create_all(bind=engine)

# FastAPI App
app = FastAPI(title="Forest Fire Monitoring API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# MQTT Client Setup
mqtt_client = None
latest_data = {}

# Thresholds for smoke (can be adjusted via env vars)
SMOKE_WARNING = int(os.getenv('SMOKE_WARNING', '300'))
SMOKE_DANGER = int(os.getenv('SMOKE_DANG', '600'))

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"[Dashboard Service] Terhubung ke broker MQTT")
        client.subscribe(MQTT_TOPIC)
        print(f"[Dashboard Service] Subscribe ke topic: {MQTT_TOPIC}")
    else:
        print(f"[Dashboard Service] Gagal terhubung ke broker, rc: {rc}")

def on_message(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode())
        print(f"[Dashboard Service] Menerima data dari {payload['sensor_id']}")
        
        # Simpan ke database
        save_to_database(payload)
        
        # Update latest data untuk WebSocket
        latest_data[payload['sensor_id']] = payload

        # Compute combined area status from latest readings
        area_status, area_values = compute_combined_status()

        # Prepare broadcast payload: include original payload and area status/values
        broadcast_payload = {
            "type": "telemetry",
            "payload": payload,
            "area_status": area_status,
            "area_values": area_values
        }

        # Broadcast ke WebSocket clients (non-blocking)
        asyncio.run(manager.broadcast(broadcast_payload))
        
    except Exception as e:
        print(f"[Dashboard Service] Error memproses pesan: {e}")

def save_to_database(payload):
    """Simpan data telemetri ke database"""
    db = SessionLocal()
    try:
        # Cari atau buat sensor node
        sensor = db.query(SensorNode).filter(
            SensorNode.sensor_id_string == payload['sensor_id']
        ).first()
        
        if not sensor:
            sensor = SensorNode(
                sensor_id_string=payload['sensor_id'],
                location=payload['location']
            )
            db.add(sensor)
            db.commit()
            db.refresh(sensor)
        
        # Simpan reading dengan data yang relevan sesuai sensor_type
        reading_data = {
            "node_id": sensor.id,
            "sensor_type": payload.get('sensor_type', 'unknown'),
            "timestamp": datetime.strptime(payload['timestamp'], "%Y-%m-%dT%H:%M:%SZ"),
            "status": payload.get('status', 'unknown'),
            "temperature": payload['data'].get('temperature'),
            "humidity": payload['data'].get('humidity'),
            "smoke": payload['data'].get('smoke')
        }
        
        reading = TelemetryReading(**reading_data)
        db.add(reading)
        db.commit()
        
    except Exception as e:
        print(f"[Dashboard Service] Error menyimpan ke database: {e}")
        db.rollback()
    finally:
        db.close()


def compute_combined_status():
    """Compute combined status using latest_data values.

    Rules (as provided):
    if (S >= S_dang) then DANGER
    else if (T >= 35 and H < 40) then DANGER
    else if (S >= S_warn and S < S_dang) then WARNING
    else if (T >= 30 and T < 35 and H >= 40 and H < 70) then WARNING
    else NORMAL
    """
    # Gather latest values
    T = None
    H = None
    S = None
    latest_timestamp = None

    for sensor_id, p in latest_data.items():
        data = p.get('data', {})
        if 'temperature' in data and data['temperature'] is not None:
            T = float(data['temperature'])
            latest_timestamp = p.get('timestamp', latest_timestamp)
        if 'humidity' in data and data['humidity'] is not None:
            H = float(data['humidity'])
            latest_timestamp = p.get('timestamp', latest_timestamp)
        if 'smoke' in data and data['smoke'] is not None:
            S = float(data['smoke'])
            latest_timestamp = p.get('timestamp', latest_timestamp)

    # Default status
    status = 'NORMAL'

    try:
        if S is not None and S >= SMOKE_DANGER:
            status = 'DANGER'
        elif T is not None and H is not None and (T >= 35 and H < 40):
            status = 'DANGER'
        elif S is not None and S >= SMOKE_WARNING and S < SMOKE_DANGER:
            status = 'WARNING'
        elif T is not None and (T >= 30 and T < 35) and H is not None and (H >= 40 and H < 70):
            status = 'WARNING'
        else:
            status = 'NORMAL'
    except Exception:
        status = 'NORMAL'

    area_values = {"temperature": T, "humidity": H, "smoke": S, "timestamp": latest_timestamp}
    return status, area_values

@app.get("/api/status")
async def get_area_status():
    """Ambil status area gabungan berdasarkan pembacaan terbaru"""
    status, values = compute_combined_status()
    return {"area_status": status, "area_values": values}

def start_mqtt_client():
    """Jalankan MQTT client di background thread"""
    global mqtt_client
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="dashboard_service")
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    try:
        mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=60)
        mqtt_client.loop_forever()
    except Exception as e:
        print(f"[Dashboard Service] Error MQTT: {e}")

# Start MQTT client di background thread
mqtt_thread = threading.Thread(target=start_mqtt_client, daemon=True)
mqtt_thread.start()

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Forest Fire Monitoring API", "status": "running"}

@app.get("/api/sensors")
async def get_sensors():
    """Ambil daftar semua sensor"""
    db = SessionLocal()
    try:
        sensors = db.query(SensorNode).all()
        return [
            {
                "id": s.id,
                "sensor_id": s.sensor_id_string,
                "location": s.location,
                "created_at": s.created_at.isoformat()
            }
            for s in sensors
        ]
    finally:
        db.close()

@app.get("/api/sensors/{sensor_id}/latest")
async def get_latest_reading(sensor_id: str):
    """Ambil data terbaru dari sensor tertentu"""
    db = SessionLocal()
    try:
        sensor = db.query(SensorNode).filter(
            SensorNode.sensor_id_string == sensor_id
        ).first()
        
        if not sensor:
            return {"error": "Sensor not found"}
        
        reading = db.query(TelemetryReading).filter(
            TelemetryReading.node_id == sensor.id
        ).order_by(TelemetryReading.timestamp.desc()).first()
        
        if not reading:
            return {"error": "No readings found"}
        
        result = {
            "sensor_id": sensor.sensor_id_string,
            "location": sensor.location,
            "timestamp": reading.timestamp.isoformat(),
            "status": reading.status,
            "sensor_type": reading.sensor_type,
            "data": {}
        }
        
        # Add data fields yang relevan
        if reading.temperature is not None:
            result["data"]["temperature"] = reading.temperature
        if reading.humidity is not None:
            result["data"]["humidity"] = reading.humidity
        if reading.smoke is not None:
            result["data"]["smoke"] = reading.smoke
        
        return result
    finally:
        db.close()

@app.get("/api/readings/latest")
async def get_all_latest_readings():
    """Ambil data terbaru dari semua sensor"""
    db = SessionLocal()
    try:
        sensors = db.query(SensorNode).all()
        results = []
        
        for sensor in sensors:
            reading = db.query(TelemetryReading).filter(
                TelemetryReading.node_id == sensor.id
            ).order_by(TelemetryReading.timestamp.desc()).first()
            
            if reading:
                result = {
                    "sensor_id": sensor.sensor_id_string,
                    "location": sensor.location,
                    "timestamp": reading.timestamp.isoformat(),
                    "status": reading.status,
                    "sensor_type": reading.sensor_type,
                    "data": {}
                }
                
                # Add data fields yang relevan
                if reading.temperature is not None:
                    result["data"]["temperature"] = reading.temperature
                if reading.humidity is not None:
                    result["data"]["humidity"] = reading.humidity
                if reading.smoke is not None:
                    result["data"]["smoke"] = reading.smoke
                
                results.append(result)
        
        return results
    finally:
        db.close()

@app.get("/api/readings/history")
async def get_readings_history(limit: int = 100):
    """Ambil data historis dari semua sensor"""
    db = SessionLocal()
    try:
        readings = db.query(TelemetryReading, SensorNode).join(
            SensorNode
        ).order_by(TelemetryReading.timestamp.desc()).limit(limit).all()
        
        results = []
        for reading, sensor in readings:
            result = {
                "sensor_id": sensor.sensor_id_string,
                "location": sensor.location,
                "timestamp": reading.timestamp.isoformat(),
                "status": reading.status,
                "sensor_type": reading.sensor_type,
                "data": {}
            }
            
            # Add data fields yang relevan
            if reading.temperature is not None:
                result["data"]["temperature"] = reading.temperature
            if reading.humidity is not None:
                result["data"]["humidity"] = reading.humidity
            if reading.smoke is not None:
                result["data"]["smoke"] = reading.smoke
            
            results.append(result)
        
        return results
    finally:
        db.close()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint untuk real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)