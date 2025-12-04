# 🔥 Sister Forest - Sistem Pemantauan Kebakaran Hutan Real-time

Sistem monitoring kebakaran hutan terdistribusi dengan arsitektur **Publish-Subscribe** menggunakan **MQTT** dan **Docker Compose** untuk implementasi microservices.

## 📋 Deskripsi Proyek

Sister Forest adalah simulasi sistem monitoring kebakaran hutan dengan komponen:
- **3 Sensor Nodes** (Container terpisah): Temperature, Humidity, dan Smoke sensor
- **MQTT Broker** (Mosquitto): Middleware komunikasi antar komponen
- **Dashboard Service**: Backend API + MQTT Subscriber + Database
- **PostgreSQL Database**: Penyimpanan data historis sensor
- **Web Dashboard**: Frontend interaktif untuk visualisasi real-time

**Monitoring dilakukan pada: 1 lokasi (Hutan Lindung Area 1) dengan 3 tipe sensor berbeda**

## 🏗️ Arsitektur Sistem

```
SENSOR NODES (Publishers)          MQTT Broker          SERVICES (Subscribers)
═══════════════════════════════════════════════════════════════════════════════

┌──────────────────┐
│ Sensor Suhu      │─┐
│ (temp-01)        │ │
└──────────────────┘ │              ┌──────────────┐     ┌──────────────────┐
                     │              │              │     │                  │
┌──────────────────┐ │   Topics:    │  MQTT Broker │────▶│ Dashboard Service│
│ Sensor Kelembaban│─┼────────────▶ │ (Mosquitto)  │     │  (FastAPI)       │
│ (hum-01)         │ │              │              │     │                  │
└──────────────────┘ │              └──────────────┘     └────────┬─────────┘
                     │                     ▲                      │
┌──────────────────┐ │            - telemetry                     ▼
│ Sensor Asap      │─┘            - command                ┌──────────────┐
│ (smoke-01)       │                                       │  PostgreSQL  │
└──────────────────┘                                       │  Database    │
                                                           └──────────────┘
                                                                  ▲
                                                                  │
                                                           ┌──────────────┐
                                                           │ Web Dashboard│
                                                           │ (JavaScript) │
                                                           └──────────────┘
                                                           http://localhost:3000
```

## 📁 Struktur Direktori

```
sister_forest/
├── sensor_node/
│   ├── Dockerfile           # Container untuk sensor node
│   └── sensor.py            # Script simulasi sensor
├── dashboard_service/
│   ├── Dockerfile           # Container untuk backend
│   └── main.py              # FastAPI backend + MQTT subscriber
├── web_dashboard/
│   ├── Dockerfile           # Container untuk frontend
│   ├── index.html           # UI Dashboard
│   └── app.js               # JavaScript logic
├── broker_config/
│   └── mosquitto.conf       # Konfigurasi MQTT Broker
├── docker-compose.yml       # Orchestration semua service
├── README.md                # File ini
└── Laporan_Proyek.md        # Dokumentasi lengkap proyek
```

## 🚀 Cara Menjalankan

### ✅ Prasyarat
Pastikan Anda sudah menginstall:
- **Docker** (versi 20.10+) - [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** (versi 1.29+) - Biasanya sudah bundled dengan Docker Desktop

**Cek versi:**
```bash
docker --version      # Harus v20.10+
docker-compose --version  # Harus v1.29+
```

### 📦 Step 1: Clone atau Setup Proyek

```bash
# Jika menggunakan Git
git clone https://github.com/luthfizahrane/sister_forest.git
cd sister_forest

# Atau jika sudah di folder proyek
cd /path/to/sister_forest
```

### 🔧 Step 2: Build dan Jalankan Services

Untuk menjalankan semua services sekaligus:

```bash
# Build images dan start semua container
docker-compose up --build

# Atau untuk background mode
docker-compose up -d --build
```

**Output yang diharapkan:**
```
Creating postgres-db ... done
Creating mqtt-broker ... done
Creating dashboard-service ... done
Creating sensor-temperature ... done
Creating sensor-humidity ... done
Creating sensor-smoke ... done
Creating web-dashboard ... done
```

### 🌐 Step 3: Akses Aplikasi

Setelah semua service berjalan, akses melalui:

| Service | URL | Keterangan |
|---------|-----|-----------|
| **Web Dashboard** | http://localhost:3000 | Visualisasi real-time sensor |
| **API Backend** | http://localhost:8000 | REST API endpoints |
| **API Docs** | http://localhost:8000/docs | Swagger documentation |
| **Database** | localhost:5432 | PostgreSQL (user: admin, password: password123) |
| **MQTT Broker** | localhost:1883 | MQTT protocol |

### 🛑 Step 4: Menghentikan Services

```bash
# Stop semua container (data tetap tersimpan)
docker-compose stop

# Atau stop dan remove container
docker-compose down

# Stop dan hapus semua (termasuk data database)
docker-compose down -v
```

## 📊 Struktur Data dan Sensor

### Daftar Sensor
Ketiga sensor berjalan di lokasi yang sama: **Hutan Lindung Area 1**

| Sensor ID | Container Name | Tipe | Unit | Normal | Warning | Danger |
|-----------|----------------|------|------|--------|---------|--------|
| `temp-01` | sensor-temperature | Temperature | °C | 20-35 | 35-45 | >45 |
| `hum-01` | sensor-humidity | Humidity | % | 40-70 | 30-40 | <30 |
| `smoke-01` | sensor-smoke | Smoke | ppm | 0-300 | 300-600 | >600 |

### Format Pesan MQTT

**Topic**: `sensors/telemetry`

**Payload dari Sensor:**
```json
{
  "sensor_id": "temp-01",
  "sensor_type": "temperature",
  "location": "Hutan Lindung Area 1",
  "timestamp": "2025-12-04T10:30:01Z",
  "data": {
    "temperature": 32.5
  },
  "status": "normal"
}
```

## 🧪 Testing dan Verifikasi

### 1️⃣ Verifikasi Services Running

```bash
# Lihat status semua container
docker-compose ps

# Output:
# NAME               STATUS
# mqtt-broker        Up X minutes
# postgres-db        Up X minutes
# dashboard-service  Up X minutes
# sensor-temperature Up X minutes
# sensor-humidity    Up X minutes
# sensor-smoke       Up X minutes
# web-dashboard      Up X minutes
```

### 2️⃣ Lihat Logs Real-time

```bash
# Logs semua service
docker-compose logs -f

# Logs spesifik sensor
docker-compose logs -f sensor_temperature
docker-compose logs -f sensor_humidity
docker-compose logs -f sensor_smoke

# Logs dashboard service
docker-compose logs -f dashboard_service
```

**Output yang diharapkan dari sensor:**
```
[temp-01] Berhasil terhubung ke broker MQTT di broker
[temp-01] Subscribe ke topic: sensors/command/temp-01
[temp-01] Mulai mengirim data sensor temperature setiap 3 detik...
[temp-01] Published: Temp=28.3°C - Status: normal
[temp-01] Published: Temp=29.1°C - Status: normal
...
```

### 3️⃣ Test API Endpoints

```bash
# Get daftar semua sensor
curl http://localhost:8000/api/sensors

# Get data terbaru semua sensor
curl http://localhost:8000/api/readings/latest

# Get data terbaru sensor tertentu
curl http://localhost:8000/api/sensors/temp-01/latest

# Get data historis (limit 20 data terakhir)
curl http://localhost:8000/api/readings/history?limit=20
```

### 4️⃣ Akses Web Dashboard

Buka browser ke: **http://localhost:3000**

Anda akan melihat:
- ✅ 3 sensor cards dengan data real-time
- ✅ Status indicator (Normal/Warning/Danger)
- ✅ Nilai sensor dengan range info
- ✅ 3 grafik line chart (Suhu, Kelembaban, Asap)
- ✅ Auto-update setiap 3 detik

### 5️⃣ Test Database

```bash
# Masuk ke PostgreSQL container
docker exec -it postgres-db psql -U admin -d forest_db

# Query untuk melihat sensor nodes
SELECT * FROM sensor_nodes;

# Query untuk melihat 10 reading terbaru
SELECT sr.*, sn.sensor_id_string 
FROM telemetry_readings sr
JOIN sensor_nodes sn ON sr.node_id = sn.id
ORDER BY sr.timestamp DESC
LIMIT 10;

# Query statistik per sensor
SELECT 
    sn.sensor_id_string,
    COUNT(*) as total_readings,
    AVG(COALESCE(sr.temperature, 0)) as avg_temp,
    AVG(COALESCE(sr.humidity, 0)) as avg_humidity,
    AVG(COALESCE(sr.smoke, 0)) as avg_smoke
FROM sensor_nodes sn
JOIN telemetry_readings sr ON sn.id = sr.node_id
GROUP BY sn.sensor_id_string;

# Exit database
\q
```

## 🎛️ Konfigurasi & Customization

### Mengubah Interval Pengiriman Sensor

Edit `docker-compose.yml`:

```yaml
environment:
  SAMPLE_INTERVAL: "5"  # Ubah dari 3 ke 5 detik
```

Kemudian restart services:
```bash
docker-compose up -d --build
```

### Mengubah Credentials Database

Edit di `docker-compose.yml`:

```yaml
environment:
  POSTGRES_USER: admin          # Ubah username
  POSTGRES_PASSWORD: password123  # Ubah password
  POSTGRES_DB: forest_db        # Ubah nama database
```

### Mengubah Nama Lokasi

Edit `docker-compose.yml` pada setiap sensor:

```yaml
environment:
  LOCATION: "Hutan Lindung Area 1"  # Ubah lokasi
```

## 📚 Teknologi Stack

| Komponen | Teknologi | Versi |
|----------|-----------|-------|
| **Backend** | Python, FastAPI | 3.10, 0.95+ |
| **Frontend** | HTML5, JavaScript, Chart.js | ES6, 4.4+ |
| **Broker** | Eclipse Mosquitto | 2.0+ |
| **Database** | PostgreSQL | 14+ |
| **Container** | Docker | 20.10+ |
| **Orchestration** | Docker Compose | 1.29+ |

## 🎓 Konsep yang Dipelajari

✅ **Event-Driven Architecture** - Publish-Subscribe pattern dengan MQTT

✅ **Microservices** - Setiap komponen independent dan scalable

✅ **Real-time Communication** - MQTT dan WebSocket

✅ **Data Persistence** - PostgreSQL dengan Docker volumes

✅ **API Design** - REST API dengan FastAPI

✅ **Frontend** - Vanilla JavaScript dengan Chart.js

✅ **Containerization** - Docker untuk reproducibility

✅ **System Reliability** - Auto-reconnect dan error handling
