# 🔥 Sistem Pemantauan Kebakaran Hutan Real-time

Sistem terdistribusi untuk pemantauan kebakaran hutan menggunakan arsitektur **Publish-Subscribe** dengan protokol **MQTT**, diimplementasikan sebagai microservices berbasis Docker.

## 📋 Deskripsi Proyek

Proyek ini merupakan simulasi sistem monitoring kebakaran hutan yang menggunakan:
- **3 Sensor Node** (Publisher) yang mensimulasikan data suhu, kelembaban, dan asap
- **MQTT Broker** (Mosquitto) sebagai middleware komunikasi
- **Dashboard Service** (Backend API + Subscriber) untuk menerima dan menyimpan data
- **PostgreSQL Database** untuk penyimpanan data historis
- **Web Dashboard** (Frontend) untuk visualisasi real-time

## 🏗️ Arsitektur Sistem

```
┌─────────────────┐
│  Sensor Node 1  │─┐
└─────────────────┘ │
                    │
┌─────────────────┐ │    ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│  Sensor Node 2  │─┼───▶│ MQTT Broker  │───▶│ Dashboard Service│───▶│  PostgreSQL  │
└─────────────────┘ │    └──────────────┘    └──────────────────┘    └──────────────┘
                    │              │                    │
┌─────────────────┐ │              │                    │
│  Sensor Node 3  │─┘              └────────────────────┼─────────────────────┐
└─────────────────┘                                     │                     │
    (Publisher)                                         │                     ▼
                                                        │           ┌──────────────────┐
                                                        └──────────▶│  Web Dashboard   │
                                                                    └──────────────────┘
                                                                      (User Interface)
```

## 📁 Struktur Direktori

```
proyek-sistem-terdistribusi/
├── sensor_node/
│   ├── Dockerfile
│   └── sensor.py
├── dashboard_service/
│   ├── Dockerfile
│   └── main.py
├── web_dashboard/
│   ├── Dockerfile
│   ├── index.html
│   └── app.js
├── broker_config/
│   └── mosquitto.conf
├── docker-compose.yml
└── README.md
```

## 🚀 Cara Menjalankan

### Prasyarat
- Docker (versi 20.10+)
- Docker Compose (versi 1.29+)

### Langkah-langkah

1. **Clone atau buat struktur direktori sesuai blueprint**

2. **Jalankan semua services dengan Docker Compose:**
```bash
docker-compose up --build
```

3. **Akses aplikasi:**
   - **Web Dashboard**: http://localhost:3000
   - **API Backend**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **Database**: localhost:5432 (user: admin, password: password123)

4. **Untuk menghentikan:**
```bash
docker-compose down
```

5. **Untuk menghapus data (termasuk database):**
```bash
docker-compose down -v
```

## 📊 Fitur Utama

### 1. Sensor Simulation (Publisher)
- Mensimulasikan 3 sensor independen
- Data yang dihasilkan: suhu, kelembaban, asap
- Status otomatis: normal, warning, danger
- Interval pengiriman: 3 detik (dapat dikonfigurasi)

### 2. MQTT Broker (Mosquitto)
- Port 1883: MQTT standar
- Port 9001: MQTT via WebSocket
- Allow anonymous connection
- Tanpa persistence untuk demo

### 3. Dashboard Service (Backend)
- **REST API Endpoints:**
  - `GET /api/sensors` - Daftar semua sensor
  - `GET /api/sensors/{sensor_id}/latest` - Data terbaru per sensor
  - `GET /api/readings/latest` - Data terbaru semua sensor
  - `GET /api/readings/history?limit=100` - Data historis
- **WebSocket**: `/ws` untuk real-time updates
- **Database ORM**: SQLAlchemy dengan PostgreSQL

### 4. Web Dashboard (Frontend)
- Tampilan real-time untuk setiap sensor
- Grafik line chart untuk suhu, kelembaban, asap
- Status indicator (normal/warning/danger)
- Auto-refresh via WebSocket
- Responsive design

### 5. Database (PostgreSQL)
- Tabel `sensor_nodes`: Informasi sensor
- Tabel `telemetry_readings`: Data historis
- Persistent storage via Docker volume

## 🧪 Skenario Pengujian

### 1. Test Alur Data (Publish-Subscribe)
```bash
# Cek logs dari sensor
docker logs sensor-area-01 -f

# Cek logs dari dashboard service
docker logs dashboard-service -f

# Buka dashboard di browser
# http://localhost:3000
```

### 2. Test Independensi Sensor
```bash
# Stop salah satu sensor
docker-compose stop sensor_node_1

# Sensor lain tetap berjalan
# Cek dashboard - data dari sensor_node_1 berhenti
```

### 3. Test Toleransi Kegagalan Broker
```bash
# Stop broker
docker-compose stop broker

# Cek logs - akan muncul pesan reconnecting
docker logs sensor-area-01
docker logs dashboard-service

# Start broker kembali
docker-compose start broker

# Sistem akan otomatis reconnect
```

### 4. Test Persistensi Database
```bash
# Stop semua container
docker-compose down

# Start kembali
docker-compose up

# Data historis masih ada karena menggunakan volume
```

### 5. Test API
```bash
# Get all sensors
curl http://localhost:8000/api/sensors

# Get latest readings
curl http://localhost:8000/api/readings/latest

# Get historical data
curl http://localhost:8000/api/readings/history?limit=50
```

## 📡 Format Pesan MQTT

### Telemetry Message (Sensor → Broker → Dashboard)
**Topic**: `sensors/telemetry`

**Payload**:
```json
{
  "sensor_id": "sensor-area-01",
  "location": "Sektor 1A",
  "timestamp": "2025-11-13T10:30:01Z",
  "data": {
    "temperature": 45.2,
    "humidity": 30.5,
    "smoke": 850
  },
  "status": "warning"
}
```

### Command Message (Dashboard → Broker → Sensor) - Opsional
**Topic**: `sensors/command/{sensor_id}`

**Payload**:
```json
{
  "command_id": "cmd-123",
  "command": "SET_SAMPLE_INTERVAL",
  "payload": 5
}
```

## 🛠️ Konfigurasi

### Environment Variables (Sensor Node)
- `MQTT_BROKER_HOST`: Host broker MQTT (default: broker)
- `SENSOR_ID`: ID unik sensor (default: sensor-area-01)
- `LOCATION`: Lokasi sensor (default: Sektor 1A)
- `SAMPLE_INTERVAL`: Interval pengiriman data dalam detik (default: 3)

### Environment Variables (Dashboard Service)
- `DATABASE_URL`: Connection string PostgreSQL
- `MQTT_BROKER_HOST`: Host broker MQTT
- `MQTT_BROKER_PORT`: Port broker MQTT (default: 1883)

## 📈 Monitoring & Debugging

### Melihat Logs Container
```bash
# Semua logs
docker-compose logs -f

# Specific service
docker-compose logs -f sensor_node_1
docker-compose logs -f dashboard_service
docker-compose logs -f broker
```

### Masuk ke Container
```bash
# Masuk ke dashboard service
docker exec -it dashboard-service bash

# Masuk ke database
docker exec -it postgres-db psql -U admin -d forest_db
```

### Query Database
```sql
-- Cek semua sensor
SELECT * FROM sensor_nodes;

-- Cek data terbaru
SELECT * FROM telemetry_readings ORDER BY timestamp DESC LIMIT 10;

-- Statistik per sensor
SELECT 
    sn.sensor_id_string,
    COUNT(*) as total_readings,
    AVG(tr.temperature) as avg_temp,
    AVG(tr.humidity) as avg_humidity,
    AVG(tr.smoke) as avg_smoke
FROM sensor_nodes sn
JOIN telemetry_readings tr ON sn.id = tr.node_id
GROUP BY sn.sensor_id_string;
```

## 🔧 Troubleshooting

### Problem: Container tidak bisa connect ke broker
**Solution**: 
- Pastikan broker sudah running: `docker ps | grep mqtt-broker`
- Cek network: `docker network inspect proyek-sistem-terdistribusi_forest-network`

### Problem: Dashboard tidak menampilkan data
**Solution**:
- Cek API endpoint: `curl http://localhost:8000/api/readings/latest`
- Buka browser console untuk melihat error
- Cek CORS settings di dashboard_service/main.py

### Problem: Database connection error
**Solution**:
- Tunggu database ready (healthcheck)
- Cek DATABASE_URL di environment variables
- Restart dashboard_service: `docker-compose restart dashboard_service`

## 📚 Teknologi yang Digunakan

- **Backend**: Python 3.10, FastAPI, SQLAlchemy
- **Frontend**: HTML5, JavaScript, Chart.js
- **Broker**: Eclipse Mosquitto 2.0
- **Database**: PostgreSQL 14
- **Containerization**: Docker, Docker Compose
- **MQTT Library**: paho-mqtt

## 🎯 Tujuan Pembelajaran

Proyek ini mendemonstrasikan:
1. ✅ Arsitektur event-driven dengan publish-subscribe
2. ✅ Komunikasi real-time menggunakan MQTT
3. ✅ Microservices architecture dengan Docker
4. ✅ Database integration untuk data persistence
5. ✅ REST API dan WebSocket untuk frontend
6. ✅ Multi-threading simulation pada sensor nodes
7. ✅ Fault tolerance dan auto-reconnection

## 📝 Lisensi

Proyek ini dibuat untuk keperluan edukasi Sistem Terdistribusi.

## 👥 Kontributor

Dikembangkan berdasarkan studi kasus: "Agri-tech innovations for sustainability: A fire detection system based on MQTT broker and IoT"

---

**Happy Coding! 🚀**