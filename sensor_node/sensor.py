#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sensor Node Publisher - Simulasi Sensor Kebakaran Hutan
Mengirimkan data suhu, kelembaban, dan asap ke MQTT Broker
Setiap sensor mengirim tipe data spesifik sesuai jenisnya
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import os
import sys
from datetime import datetime

# Konfigurasi dari environment variables
BROKER_HOST = os.getenv('MQTT_BROKER_HOST', 'broker')
BROKER_PORT = 1883
SENSOR_ID = os.getenv('SENSOR_ID', 'temp-01')
SENSOR_TYPE = os.getenv('SENSOR_TYPE', 'temperature')  # temperature, humidity, smoke
LOCATION = os.getenv('LOCATION', 'Hutan Lindung Area 1')
TOPIC = "sensors/telemetry"
INTERVAL = int(os.getenv('SAMPLE_INTERVAL', '3'))  # Interval pengiriman dalam detik

# Callback saat koneksi berhasil
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"[{SENSOR_ID}] Berhasil terhubung ke broker MQTT di {BROKER_HOST}")
        # Subscribe ke topic command untuk sensor ini
        command_topic = f"sensors/command/{SENSOR_ID}"
        client.subscribe(command_topic)
        print(f"[{SENSOR_ID}] Subscribe ke topic: {command_topic}")
    else:
        print(f"[{SENSOR_ID}] Gagal terhubung ke broker, kode error: {rc}")
        sys.exit(1)

# Callback untuk menerima perintah dari server
def on_message(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode())
        command = payload.get('command')
        
        if command == 'SET_SAMPLE_INTERVAL':
            global INTERVAL
            INTERVAL = payload.get('payload', INTERVAL)
            print(f"[{SENSOR_ID}] Interval sampling diubah menjadi {INTERVAL} detik")
    except Exception as e:
        print(f"[{SENSOR_ID}] Error memproses command: {e}")

# Fungsi untuk generate data sensor Temperature
def generate_temperature_data():
    """Mensimulasikan pembacaan sensor suhu"""
    # Randomize kondisi (80% normal, 15% warning, 5% danger)
    rand = random.random()
    
    if rand < 0.80:  # Normal
        temperature = round(random.uniform(20, 35), 1)
        status = "normal"
    elif rand < 0.95:  # Warning
        temperature = round(random.uniform(35, 45), 1)
        status = "warning"
    else:  # Danger
        temperature = round(random.uniform(45, 60), 1)
        status = "danger"
    
    return {
        "sensor_id": SENSOR_ID,
        "sensor_type": SENSOR_TYPE,
        "location": LOCATION,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data": {
            "temperature": temperature
        },
        "status": status
    }

# Fungsi untuk generate data sensor Humidity
def generate_humidity_data():
    """Mensimulasikan pembacaan sensor kelembaban"""
    # Randomize kondisi (80% normal, 15% warning, 5% danger)
    rand = random.random()
    
    if rand < 0.80:  # Normal (kelembaban tinggi = baik)
        humidity = round(random.uniform(40, 70), 1)
        status = "normal"
    elif rand < 0.95:  # Warning
        humidity = round(random.uniform(30, 40), 1)
        status = "warning"
    else:  # Danger (kelembaban rendah = bahaya)
        humidity = round(random.uniform(10, 30), 1)
        status = "danger"
    
    return {
        "sensor_id": SENSOR_ID,
        "sensor_type": SENSOR_TYPE,
        "location": LOCATION,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data": {
            "humidity": humidity
        },
        "status": status
    }

# Fungsi untuk generate data sensor Smoke
def generate_smoke_data():
    """Mensimulasikan pembacaan sensor asap"""
    # Randomize kondisi (80% normal, 15% warning, 5% danger)
    rand = random.random()
    
    if rand < 0.80:  # Normal
        smoke = random.randint(0, 300)
        status = "normal"
    elif rand < 0.95:  # Warning
        smoke = random.randint(300, 600)
        status = "warning"
    else:  # Danger
        smoke = random.randint(600, 1000)
        status = "danger"
    
    return {
        "sensor_id": SENSOR_ID,
        "sensor_type": SENSOR_TYPE,
        "location": LOCATION,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data": {
            "smoke": smoke
        },
        "status": status
    }

# Fungsi untuk generate data sensor sesuai tipenya
def generate_sensor_data():
    """
    Mensimulasikan data sensor berdasarkan tipe sensor
    """
    if SENSOR_TYPE == "temperature":
        return generate_temperature_data()
    elif SENSOR_TYPE == "humidity":
        return generate_humidity_data()
    elif SENSOR_TYPE == "smoke":
        return generate_smoke_data()
    else:
        # Default: return all data
        rand = random.random()
        if rand < 0.80:
            temperature = round(random.uniform(20, 35), 1)
            humidity = round(random.uniform(40, 70), 1)
            smoke = random.randint(0, 300)
            status = "normal"
        elif rand < 0.95:
            temperature = round(random.uniform(35, 45), 1)
            humidity = round(random.uniform(30, 40), 1)
            smoke = random.randint(300, 600)
            status = "warning"
        else:
            temperature = round(random.uniform(45, 60), 1)
            humidity = round(random.uniform(10, 30), 1)
            smoke = random.randint(600, 1000)
            status = "danger"
        
        return {
            "sensor_id": SENSOR_ID,
            "sensor_type": SENSOR_TYPE,
            "location": LOCATION,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "data": {
                "temperature": temperature,
                "humidity": humidity,
                "smoke": smoke
            },
            "status": status
        }

# Callback saat koneksi terputus
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"[{SENSOR_ID}] Koneksi terputus. Mencoba reconnect...")

# Inisialisasi klien MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=SENSOR_ID)
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# Menghubungkan ke broker
try:
    print(f"[{SENSOR_ID}] Menghubungkan ke broker {BROKER_HOST}:{BROKER_PORT}...")
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()  # Start loop in background thread
except Exception as e:
    print(f"[{SENSOR_ID}] Gagal menghubungkan ke broker: {e}")
    sys.exit(1)

# Loop utama untuk mengirim data
try:
    print(f"[{SENSOR_ID}] Mulai mengirim data sensor {SENSOR_TYPE} setiap {INTERVAL} detik...")
    while True:
        # Generate dan kirim data sensor
        sensor_data = generate_sensor_data()
        message = json.dumps(sensor_data)
        
        result = client.publish(TOPIC, message, qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            if SENSOR_TYPE == "temperature":
                print(f"[{SENSOR_ID}] Published: Temp={sensor_data['data']['temperature']}°C - Status: {sensor_data['status']}")
            elif SENSOR_TYPE == "humidity":
                print(f"[{SENSOR_ID}] Published: Hum={sensor_data['data']['humidity']}% - Status: {sensor_data['status']}")
            elif SENSOR_TYPE == "smoke":
                print(f"[{SENSOR_ID}] Published: Smoke={sensor_data['data']['smoke']} - Status: {sensor_data['status']}")
        else:
            print(f"[{SENSOR_ID}] Gagal publish data, error code: {result.rc}")
        
        time.sleep(INTERVAL)

except KeyboardInterrupt:
    print(f"\n[{SENSOR_ID}] Publisher dihentikan.")
    client.loop_stop()
    client.disconnect()
except Exception as e:
    print(f"[{SENSOR_ID}] Error: {e}")
    client.loop_stop()
    client.disconnect()
    sys.exit(1)
    