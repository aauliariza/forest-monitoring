# Panduan Memantau Sistem MQTT (Forest Monitoring)

Dokumen ini menjelaskan berbagai cara untuk memantau komunikasi MQTT dan memverifikasi bahwa sistem bekerja sesuai protokol MQTT. Ya, **semuanya bisa terlihat!**

---

## 1. Memahami Alur MQTT dalam Sistem Kami

```
┌──────────────────────────────────────┐
│  Sensor Container                    │
│  - sensor_temperature                │
│  - sensor_humidity                   │
│  - sensor_smoke                      │
│  (Publish data setiap 10 detik)      │
└────────────┬─────────────────────────┘
             │ MQTT Publish (Port 1883)
             │ Topic: "sensors/telemetry"
             ↓
┌──────────────────────────────────────┐
│  MQTT Broker (Mosquitto)             │
│  - Eclipse Mosquitto                 │
│  - Port: 1883 (MQTT), 9001 (WebSocket)
└────────────┬─────────────────────────┘
             │
             ├─→ Dashboard Service (Subscribe)
             │   - Simpan ke DB
             │   - Hitung status
             │   - Broadcast ke WebSocket
             │
             └─→ Clients bisa Subscribe
                 untuk monitoring
```

---

## 2. Metode Monitoring MQTT

### **Metode A: Menggunakan `mosquitto_sub` (Paling Mudah)**

#### Cara 1: Dari Host Machine
Jika `mosquitto-clients` sudah terinstall di host:
```bash
# Subscribe ke semua pesan MQTT
mosquitto_sub -h localhost -p 1883 -t "sensors/telemetry" -v

# Output akan terlihat seperti:
# sensors/telemetry {"sensor_id": "temp-01", "sensor_type": "temperature", ...}
# sensors/telemetry {"sensor_id": "hum-01", "sensor_type": "humidity", ...}
# sensors/telemetry {"sensor_id": "smoke-01", "sensor_type": "smoke", ...}
```

#### Cara 2: Dari Container MQTT Broker
```bash
docker exec -it mqtt-broker mosquitto_sub -t "sensors/telemetry" -v
```

#### Cara 3: Subscribe ke Semua Topic (Wildcard)
```bash
mosquitto_sub -h localhost -p 1883 -t "#" -v
```

---

### **Metode B: Menggunakan Python dengan paho-mqtt**

Buat file `mqtt_monitor.py` dan jalankan di host atau dalam container:

```python
import paho.mqtt.client as mqtt
import json
from datetime import datetime

# Callback ketika subscribe berhasil
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Terhubung ke MQTT Broker")
        # Subscribe ke topic sensor
        client.subscribe("sensors/telemetry")
    else:
        print(f"Koneksi gagal, kode: {rc}")

# Callback ketika menerima pesan
def on_message(client, userdata, msg):
    timestamp = datetime.now().strftime('%H:%M:%S')
    try:
        payload = json.loads(msg.payload.decode())
        sensor_id = payload.get('sensor_id', 'unknown')
        sensor_type = payload.get('sensor_type', 'unknown')
        data = payload.get('data', {})
        status = payload.get('status', 'unknown')
        
        print(f"[{timestamp}] 📡 MQTT Pesan Diterima")
        print(f"  Topic: {msg.topic}")
        print(f"  Sensor ID: {sensor_id}")
        print(f"  Tipe Sensor: {sensor_type}")
        print(f"  Data: {data}")
        print(f"  Status: {status}")
        print("-" * 50)
    except json.JSONDecodeError:
        print(f"[{timestamp}] ⚠ Pesan tidak valid JSON: {msg.payload}")

# Setup client
client = mqtt.Client("monitor_client")
client.on_connect = on_connect
client.on_message = on_message

# Koneksi ke broker
print("🔌 Menghubungkan ke MQTT Broker di localhost:1883...")
client.connect("localhost", 1883, keepalive=60)

# Loop untuk listening
print("Menunggu pesan... (Tekan Ctrl+C untuk berhenti)\n")
client.loop_forever()
```

Jalankan dengan:
```bash
python3 mqtt_monitor.py
```

---

### **Metode C: Dashboard Service Logs**

Monitor logs dari dashboard-service untuk melihat apa yang diterima:

```bash
# Real-time logs
docker-compose logs -f dashboard-service

# Lihat hanya 50 baris terakhir
docker-compose logs --tail=50 dashboard-service

# Filter pesan tertentu
docker-compose logs dashboard-service | grep "telemetry"
```

Contoh output:
```
[Dashboard Service] Menerima data dari sensor: temp-01
[Dashboard Service] Data: {'temperature': 25.4, 'timestamp': '2025-12-04T...'}
[Dashboard Service] Menerima data dari sensor: hum-01
[Dashboard Service] Data: {'humidity': 65.3, 'timestamp': '2025-12-04T...'}
[Dashboard Service] Menerima data dari sensor: smoke-01
[Dashboard Service] Data: {'smoke': 150.2, 'timestamp': '2025-12-04T...'}
```

---

### **Metode D: Check API Endpoint**

Lihat data terbaru yang diterima sistem:

```bash
# Baca pembacaan sensor terbaru
curl -s http://localhost:8000/api/readings/latest | python3 -m json.tool

# Output:
# {
#   "temp-01": {
#     "sensor_id": "temp-01",
#     "sensor_type": "temperature",
#     "data": {"temperature": 25.4},
#     "status": "normal",
#     "timestamp": "2025-12-04T10:30:45.123456Z"
#   },
#   ...
# }

# Lihat status area gabungan
curl -s http://localhost:8000/api/status | python3 -m json.tool

# Output:
# {
#   "area_status": "NORMAL",
#   "area_values": {
#     "temperature": 25.4,
#     "humidity": 65.3,
#     "smoke": 150.2,
#     "timestamp": "2025-12-04T10:30:45.123456Z"
#   }
# }
```

---

### **Metode E: Database Query**

Lihat data yang disimpan di PostgreSQL:

```bash
# Masuk ke container database
docker exec -it postgres-db psql -U forest_user -d forest_db

# Query untuk melihat telemetry terbaru
SELECT 
  sensor_id, 
  sensor_type, 
  temperature, 
  humidity, 
  smoke,
  status,
  timestamp 
FROM telemetry_readings 
ORDER BY timestamp DESC 
LIMIT 20;

# Query berdasar sensor tertentu
SELECT * FROM telemetry_readings 
WHERE sensor_id = 'temp-01' 
ORDER BY timestamp DESC 
LIMIT 10;
```

---

### **Metode F: Browser WebSocket Monitor**

Buka browser developer tools dan monitor WebSocket messages:

```javascript
// Copy-paste ke console browser saat di dashboard (http://localhost:3000)

const ws = new WebSocket("ws://localhost:8000/ws");

ws.onopen = () => {
  console.log("✓ WebSocket terbuka");
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("📡 WebSocket Message:", data);
  
  if (data.type === "telemetry") {
    console.log("Sensor ID:", data.payload.sensor_id);
    console.log("Area Status:", data.area_status);
    console.log("Area Values:", data.area_values);
  }
};

ws.onerror = (error) => {
  console.error("❌ WebSocket Error:", error);
};

ws.onclose = () => {
  console.log("❌ WebSocket ditutup");
};
```

---

## 3. Verifikasi Protokol MQTT

### **Protocol Compliance Check**

✅ **QoS Level**
```bash
# Lihat QoS dari subscriber (default: 0)
mosquitto_sub -h localhost -p 1883 -t "sensors/telemetry" --verbose
```

✅ **Publish Flow**
```bash
# Test publish manual ke broker
mosquitto_pub -h localhost -p 1883 -t "test/topic" -m "Hello MQTT"

# Subscribe di terminal lain untuk melihat message
mosquitto_sub -h localhost -p 1883 -t "test/topic" -v
```

✅ **Broker Information**
```bash
# Lihat info mosquitto
docker exec mqtt-broker mosquitto -v
```

---

## 4. Monitoring Tools Eksternal (Opsional)

### **MQTT Explorer** (GUI Tool)
Unduh dari: https://mqtt-explorer.com/

Konfigurasi:
- Host: `localhost`
- Port: `1883`
- Username/Password: kosongkan (broker kami tidak perlu auth)

Keuntungan:
- UI visual
- Browse semua topic
- Publish/Subscribe manual
- Real-time message rate

---

## 5. Troubleshooting & Common Issues

| Masalah | Solusi |
|---------|--------|
| `Connection refused` | Pastikan `mqtt-broker` container running: `docker-compose ps` |
| `Topic tidak ada pesan` | Cek apakah sensor container running: `docker-compose logs sensor-temperature` |
| `Pesan tidak masuk DB` | Cek dashboard-service logs: `docker-compose logs dashboard-service` |
| `Port 1883 sudah dipakai` | `lsof -i :1883` kemudian stop container yang pakai port itu |
| `mosquitto_sub: command not found` | Install: `sudo apt-get install mosquitto-clients` |

---

## 6. Quick Start Commands

Copy-paste untuk monitoring cepat:

```bash
# Terminal 1: Monitor MQTT messages
mosquitto_sub -h localhost -p 1883 -t "sensors/telemetry" -v

# Terminal 2: Check API endpoint real-time (setiap 2 detik)
while true; do clear; echo "=== API Status ==="; curl -s http://localhost:8000/api/status | python3 -m json.tool; sleep 2; done

# Terminal 3: Monitor dashboard logs
docker-compose logs -f dashboard-service

# Terminal 4: Monitor database
docker exec -it postgres-db psql -U forest_user -d forest_db -c "SELECT sensor_id, sensor_type, status, timestamp FROM telemetry_readings ORDER BY timestamp DESC LIMIT 5;"
```

---

## 7. Expected Message Format

Pesan yang dipublish sensor ke `sensors/telemetry`:

```json
{
  "sensor_id": "temp-01",
  "sensor_type": "temperature",
  "location": "hutan_area_1",
  "timestamp": "2025-12-04T10:30:45.123456Z",
  "data": {
    "temperature": 25.4
  },
  "status": "normal"
}
```

Setiap sensor mempublish setiap 10 detik (bisa diubah via `SAMPLE_INTERVAL`).

---

## Kesimpulan

**Ya, semuanya bisa terlihat!** Gunakan salah satu dari 6 metode di atas sesuai preferensi Anda. Metode paling mudah adalah:

1. **Metode A (mosquitto_sub)** - Untuk quick check
2. **Metode C (Docker logs)** - Untuk debug backend
3. **Metode D (API)** - Untuk verify data di sistem
4. **Metode E (Database)** - Untuk long-term data persistence check

Semua metode menunjukkan **protokol MQTT bekerja dengan sempurna** jika Anda bisa melihat pesan mengalir dari sensor → broker → backend → database.

