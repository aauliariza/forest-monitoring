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

## 🔍 Monitoring & Debugging

### Melihat Container yang Berjalan

```bash
# Lihat semua container yang berjalan
docker ps

# Lihat semua container termasuk yang stopped
docker ps -a
```

### Masuk ke Container Untuk Debug

```bash
# Masuk ke sensor temperature
docker exec -it sensor-temperature bash

# Masuk ke dashboard service
docker exec -it dashboard-service bash

# Masuk ke database
docker exec -it postgres-db bash
```

### Cek Network Connectivity

```bash
# Masuk ke sensor container
docker exec -it sensor-temperature bash

# Cek bisa connect ke broker
nc -zv broker 1883

# Cek bisa connect ke database
nc -zv db 5432
```

### Lihat Docker Network

```bash
# List semua network
docker network ls

# Inspect forest-network
docker network inspect sister_forest_forest-network
```

## ⚠️ Troubleshooting

### ❌ Error: "Cannot connect to broker"

**Solusi:**
```bash
# Pastikan broker container running
docker-compose ps | grep mqtt

# Check broker logs
docker-compose logs mqtt-broker

# Restart broker
docker-compose restart broker
```

### ❌ Error: "Database connection failed"

**Solusi:**
```bash
# Tunggu beberapa detik, database butuh waktu untuk start
docker-compose logs postgres-db

# Pastikan database healthcheck passed
docker ps | grep postgres-db  # STATUS harus 'Up'

# Restart dashboard service
docker-compose restart dashboard-service
```

### ❌ Dashboard tidak menampilkan data

**Solusi:**
```bash
# Cek API endpoint
curl http://localhost:8000/api/readings/latest

# Buka browser console (F12) untuk melihat error JavaScript
# Check CORS: API harus allow origin dari dashboard

# Cek WebSocket connection di console browser
# Jika WebSocket fail, dashboard fallback ke polling
```

### ❌ Sensor tidak mengirim data

**Solusi:**
```bash
# Cek logs sensor
docker-compose logs sensor-temperature

# Pastikan sensor dapat connect ke broker
docker exec -it sensor-temperature ping broker

# Restart sensor
docker-compose restart sensor-temperature
```

### ❌ Port 3000 atau 8000 sudah terpakai

**Solusi:**
Ubah port di `docker-compose.yml`:

```yaml
web_dashboard:
  ports:
    - "3001:80"  # Ubah 3000 ke 3001

dashboard_service:
  ports:
    - "8001:80"  # Ubah 8000 ke 8001
```

Kemudian akses ke http://localhost:3001 dan http://localhost:8001

## 📈 Performance Tips

### Reduce Database Load

Kurangi frekuensi penyimpanan data dengan mengubah interval:
```bash
# Ubah di docker-compose.yml
SAMPLE_INTERVAL: "10"  # 10 detik sekali mengirim
```

### Limit Historical Data

Query dengan limit untuk performa lebih baik:
```bash
# Ambil hanya 50 data terakhir
curl http://localhost:8000/api/readings/history?limit=50
```

### Monitor Resource Usage

```bash
# Lihat CPU dan memory usage
docker stats

# Lihat detail container
docker inspect sensor-temperature
```

## 📝 Cleanup dan Reset

### Remove Semua Container dan Images

```bash
# Stop dan remove semua
docker-compose down --remove-orphans

# Remove images
docker-compose down --rmi all

# Clean up unused resources
docker system prune -a --volumes
```

### Reset Database Saja

```bash
# Remove volume database
docker volume rm sister_forest_postgres_data

# Restart services (database akan di-create ulang)
docker-compose up -d
```

## 🎯 Skenario Demonstrasi

### Demo 1: Monitoring Real-time

1. Buka 2 terminal
2. Terminal 1: `docker-compose logs -f`
3. Terminal 2: Buka http://localhost:3000
4. Lihat data sensor update setiap 3 detik di dashboard dan logs

### Demo 2: Fault Tolerance

1. Buka http://localhost:3000
2. Stop sensor temperature: `docker-compose stop sensor-temperature`
3. Lihat di dashboard: hanya 2 sensor yang update
4. Restart sensor: `docker-compose start sensor-temperature`
5. Sensor kembali mengirim data

### Demo 3: Data Persistence

1. Jalankan sistem 2-3 menit
2. Stop semua: `docker-compose down`
3. Start kembali: `docker-compose up -d`
4. Buka dashboard: data historis masih ada!

### Demo 4: API Testing

```bash
# Terminal 1
docker-compose up -d

# Terminal 2
# Query API setiap 5 detik
watch -n 5 'curl -s http://localhost:8000/api/readings/latest | jq'
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

## 📞 Support & Questions

Jika ada pertanyaan atau issue:
1. Cek troubleshooting section di atas
2. Lihat Docker logs untuk error messages
3. Baca dokumentasi di Laporan_Proyek.md

## 📄 Lisensi

Proyek edukasi untuk mata kuliah Sistem Terdistribusi.

---

**🚀 Happy Monitoring! Sistem Anda sudah siap dijalankan.**