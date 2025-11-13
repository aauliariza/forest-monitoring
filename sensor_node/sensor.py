#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sensor Node Publisher - Simulasi Sensor Kebakaran Hutan
Mengirimkan data suhu, kelembaban, dan asap ke MQTT Broker
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
SENSOR_ID = os.getenv('SENSOR_ID', 'sensor-area-01')
LOCATION = os.getenv('LOCATION', 'Sektor 1A')
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

# Fungsi untuk mensimulasikan pembacaan sensor
def generate_sensor_data():
    """
    Mensimulasikan data sensor dengan nilai yang realistis
    - Normal: suhu 20-35°C, kelembaban 40-70%, asap 0-300
    - Warning: suhu 35-45°C, kelembaban 30-40%, asap 300-600
    - Danger: suhu >45°C, kelembaban <30%, asap >600
    """
    # Randomize kondisi (80% normal, 15% warning, 5% danger)
    rand = random.random()
    
    if rand < 0.80:  # Normal
        temperature = round(random.uniform(20, 35), 1)
        humidity = round(random.uniform(40, 70), 1)
        smoke = random.randint(0, 300)
        status = "normal"
    elif rand < 0.95:  # Warning
        temperature = round(random.uniform(35, 45), 1)
        humidity = round(random.uniform(30, 40), 1)
        smoke = random.randint(300, 600)
        status = "warning"
    else:  # Danger
        temperature = round(random.uniform(45, 60), 1)
        humidity = round(random.uniform(10, 30), 1)
        smoke = random.randint(600, 1000)
        status = "danger"
    
    return {
        "sensor_id": SENSOR_ID,
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
    print(f"[{SENSOR_ID}] Mulai mengirim data sensor setiap {INTERVAL} detik...")
    while True:
        # Generate dan kirim data sensor
        sensor_data = generate_sensor_data()
        message = json.dumps(sensor_data)
        
        result = client.publish(TOPIC, message, qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"[{SENSOR_ID}] Published: Temp={sensor_data['data']['temperature']}°C, "
                  f"Hum={sensor_data['data']['humidity']}%, "
                  f"Smoke={sensor_data['data']['smoke']} - Status: {sensor_data['status']}")
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
    print("Dashboard Service is running.")
    