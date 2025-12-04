# Quick Reference: Monitoring MQTT Communication

## 🚀 Instant Monitoring Commands

### Option 1: Python Script (Recommended - dengan Colors & Stats)
```bash
cd /home/auliariza/sister_forest
pip install paho-mqtt colorama  # (if not installed)
python3 mqtt_monitor.py
```

**Output: Real-time display dengan statistics**

---

### Option 2: Command Line (mosquitto_sub)
```bash
# Install jika belum ada
sudo apt-get install mosquitto-clients

# Subscribe ke sensor telemetry
mosquitto_sub -h localhost -p 1883 -t "sensors/telemetry" -v

# Atau lihat ALL topics
mosquitto_sub -h localhost -p 1883 -t "#" -v
```

**Output:**
```
sensors/telemetry {"sensor_id":"temp-01","sensor_type":"temperature",...}
sensors/telemetry {"sensor_id":"hum-01","sensor_type":"humidity",...}
sensors/telemetry {"sensor_id":"smoke-01","sensor_type":"smoke",...}
```

---

### Option 3: Docker Logs (Monitor Backend)
```bash
cd /home/auliariza/sister_forest

# Real-time logs dashboard
docker-compose logs -f dashboard-service

# MQTT Broker logs
docker-compose logs -f mqtt-broker

# Semua services
docker-compose logs -f
```

**Output:**
```
mqtt-broker | 1764822683: Received PUBLISH from temp-01 (d0, q1, r0, m10, 'sensors/telemetry', ... (178 bytes))
mqtt-broker | 1764822683: Sending PUBLISH to dashboard_service (d0, q0, r0, m0, 'sensors/telemetry', ... (178 bytes))
dashboard-service | [Dashboard Service] Menerima data dari temp-01
```

---

### Option 4: API Health Check (Every 2 Seconds)
```bash
# Monitor status
while true; do 
  clear
  echo "=== FOREST MONITORING STATUS ==="
  echo "Time: $(date)"
  echo
  curl -s http://localhost:8000/api/status | python3 -m json.tool
  sleep 2
done
```

**Output:**
```json
{
    "area_status": "NORMAL",
    "area_values": {
        "temperature": 25.4,
        "humidity": 65.3,
        "smoke": 150.2,
        "timestamp": "2025-12-04T10:30:45Z"
    }
}
```

---

### Option 5: Database Query (Check Persistence)
```bash
docker exec -it postgres-db psql -U forest_user -d forest_db

# Inside psql:
SELECT sensor_id, sensor_type, data, status, timestamp 
FROM telemetry_readings 
ORDER BY timestamp DESC 
LIMIT 20;

# Exit with: \q
```

---

## 🔍 What You Should See

### ✅ Protocol Communication Flow:

```
1. SENSOR PUBLISHES (every 10 sec)
   └─ temp-01, hum-01, smoke-01
      └─ Topic: sensors/telemetry
         └─ QoS: 1 (At least once delivery)
         └─ Payload: JSON with temperature/humidity/smoke value

2. MQTT BROKER RECEIVES & RELAYS
   └─ PUBACK sent to sensor (acknowledgment)
   └─ PUBLISH forwarded to all subscribers
      └─ dashboard-service (subscribed)
         └─ other monitoring clients (if any)

3. DASHBOARD SERVICE PROCESSES
   └─ Parses JSON
   └─ Validates data against rules
   └─ Saves to PostgreSQL
   └─ Computes area_status
   └─ Broadcasts via WebSocket

4. WEB DASHBOARD RECEIVES
   └─ Updates charts
   └─ Shows alerts/notifications
   └─ Displays in real-time
```

---

## 📊 Expected Data Examples

### Temperature Sensor Message:
```json
{
  "sensor_id": "temp-01",
  "sensor_type": "temperature",
  "location": "Hutan Lindung Area 1",
  "timestamp": "2025-12-04T04:31:45.123456Z",
  "data": {
    "temperature": 25.4
  },
  "status": "normal"
}
```

### Humidity Sensor Message:
```json
{
  "sensor_id": "hum-01",
  "sensor_type": "humidity",
  "location": "Hutan Lindung Area 1",
  "timestamp": "2025-12-04T04:31:45.123456Z",
  "data": {
    "humidity": 65.3
  },
  "status": "normal"
}
```

### Smoke Sensor Message:
```json
{
  "sensor_id": "smoke-01",
  "sensor_type": "smoke",
  "location": "Hutan Lindung Area 1",
  "timestamp": "2025-12-04T04:31:45.123456Z",
  "data": {
    "smoke": 150.2
  },
  "status": "normal"
}
```

---

## 🔧 Troubleshooting

| Symptom | Check | Fix |
|---------|-------|-----|
| No messages | `docker-compose ps` | Start services: `docker-compose up -d` |
| Connection refused | `lsof -i :1883` | Kill other process or use different port |
| Command not found | `which mosquitto_sub` | `sudo apt-get install mosquitto-clients` |
| Broker not responding | `docker logs mqtt-broker` | Restart: `docker-compose restart mqtt-broker` |
| Dashboard not updating | Check websocket | Check browser console (F12) for errors |

---

## 📈 Performance Metrics

**Current Configuration:**
- Sample Interval: **10 seconds** (per sensor)
- Topics: **1** (sensors/telemetry)
- Subscribers: Dashboard Service + Monitoring clients
- QoS Level: **1** (At least once)
- Payload Size: ~180-200 bytes per message
- Messages per Minute: **18** (3 sensors × 1 msg every 10sec)

**Total Data per Hour:**
- 3 sensors × 6 messages/min × 60 min = **1,080 messages/hour**
- ~200 KB/hour of MQTT traffic

---

## ✅ Verification Checklist

Use ini untuk memverifikasi sistem:

- [ ] Semua container berjalan: `docker-compose ps`
- [ ] MQTT Broker listening: `netstat -tlnp | grep 1883`
- [ ] Messages masuk broker: `mosquitto_sub -h localhost -p 1883 -t "sensors/telemetry"` (harus ada output)
- [ ] Dashboard service menerima: `docker-compose logs dashboard-service | grep "Menerima"`
- [ ] Data ada di database: `docker exec postgres-db psql -U forest_user -d forest_db -c "SELECT COUNT(*) FROM telemetry_readings;"`
- [ ] API endpoint working: `curl http://localhost:8000/api/status`
- [ ] WebSocket connection: Buka http://localhost:3000, buka F12, tab Network → WS filter
- [ ] Dashboard showing alerts: Check untuk alert notifications

Semua ✅ = **Protokol MQTT bekerja sempurna!**

