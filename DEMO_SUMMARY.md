# Forest Fire Monitoring System - End-to-End Demo

## Overview
A complete Docker-based forest fire monitoring system with:
- **3 isolated sensors** (temperature, humidity, smoke) in separate containers
- **MQTT broker** for pub/sub messaging
- **Backend API** (FastAPI) for computing aggregated status based on sensor values
- **PostgreSQL database** for persisting telemetry readings
- **Web dashboard** (nginx + vanilla JS) with real-time updates, charts, and alerts

## Architecture & Features

### Backend Status Computation Logic
The system combines sensor readings using the following rules (implemented in `compute_combined_status()`):

```
if (smoke >= SMOKE_DANG)  → DANGER
else if (temperature >= 35 AND humidity < 40)  → DANGER
else if (smoke >= SMOKE_WARNING AND smoke < SMOKE_DANG)  → WARNING
else if (temperature >= 30 AND temperature < 35 AND humidity >= 40 AND humidity < 70)  → WARNING
else  → NORMAL
```

### Configuration
Thresholds are configurable via `.env` file:
```
SMOKE_WARNING=300
SMOKE_DANG=600
```

### Frontend Alerts
Two types of notifications when status changes to WARNING or DANGER:
1. **Floating banner** (in-page UI)
   - DANGER: persistent red banner with auto-sound
   - WARNING: orange banner auto-dismisses after 8 seconds
   
2. **Browser Notifications** (desktop)
   - Click opens/focuses the dashboard
   - Requires permission grant on first visit

## Quick Start

### Start the Full Stack
```bash
cd /home/auliariza/sister_forest
docker-compose up -d
```

### Access the Dashboard
```
http://localhost:3000
```

### Check API Status
```bash
curl -sS http://localhost:8000/api/status | jq '.'
curl -sS http://localhost:8000/api/readings/latest | jq '.'
```

## Test Scenarios

### Scenario 1: Smoke WARNING Trigger
Publish a message with smoke value between SMOKE_WARNING and SMOKE_DANG (300-600):

```bash
docker exec -i dashboard-service python - << 'PYTHON'
import paho.mqtt.client as mqtt, json, time
from datetime import datetime

client = mqtt.Client()
client.connect('broker', 1883)
client.loop_start()

payload = {
    'sensor_id': 'smoke-01',
    'sensor_type': 'smoke',
    'location': 'Hutan Lindung Area 1',
    'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    'data': {'smoke': 450},
    'status': 'warning'
}
client.publish('sensors/telemetry', json.dumps(payload), qos=1)
print('Published: WARNING (smoke=450)')
time.sleep(1)
client.loop_stop()
PYTHON
```

Expected:
- `GET /api/status` returns `"area_status": "WARNING"`
- Dashboard shows orange alert banner
- Browser notification appears (if permission granted)

### Scenario 2: Smoke DANGER Trigger
```bash
# Publish smoke value >= SMOKE_DANG (600+)
payload = {'smoke': 750}
```

Expected:
- `GET /api/status` returns `"area_status": "DANGER"`
- Dashboard shows persistent red alert banner + sound alert
- Browser notification appears with "DANGER" title

### Scenario 3: Temp/Humidity DANGER Trigger
```bash
# Publish T=36, H=35 (triggers T>=35 AND H<40)
payload_temp = {'temperature': 36.0}
payload_hum = {'humidity': 35.0}
```

Expected:
- `GET /api/status` returns `"area_status": "DANGER"`

## Test Sequence Output Example

When you run the deterministic test (paused sensors + scripted MQTT publishes):

### Phase 1: NORMAL
```json
{
  "area_status": "NORMAL",
  "area_values": {
    "temperature": 25.0,
    "humidity": 60.0,
    "smoke": 100,
    "timestamp": "2025-12-04T03:41:25Z"
  }
}
```

### Phase 2: WARNING (smoke=400)
```json
{
  "area_status": "WARNING",
  "area_values": {
    "temperature": 25.0,
    "humidity": 60.0,
    "smoke": 400,
    "timestamp": "2025-12-04T03:41:27Z"
  }
}
```

### Phase 3: DANGER (smoke=700)
```json
{
  "area_status": "DANGER",
  "area_values": {
    "temperature": 25.0,
    "humidity": 60.0,
    "smoke": 700,
    "timestamp": "2025-12-04T03:41:29Z"
  }
}
```

### Phase 4: Back to NORMAL
```json
{
  "area_status": "NORMAL",
  "area_values": {
    "temperature": 25.0,
    "humidity": 60.0,
    "smoke": 100,
    "timestamp": "2025-12-04T03:41:31Z"
  }
}
```

### Phase 5: DANGER (temp/humidity)
```json
{
  "area_status": "DANGER",
  "area_values": {
    "temperature": 36.0,
    "humidity": 35.0,
    "smoke": 100,
    "timestamp": "2025-12-04T03:41:33Z"
  }
}
```

## API Endpoints

### Get Current Area Status
```
GET /api/status
```
Returns: `{ "area_status": "NORMAL|WARNING|DANGER", "area_values": {...} }`

### Get Latest Readings (All Sensors)
```
GET /api/readings/latest
```
Returns: Array of latest readings for each sensor

### Get Historical Readings
```
GET /api/readings/history?limit=20
```
Returns: Last N readings (default 20)

### WebSocket Real-time Updates
```
ws://localhost:8000/ws
```
Receives: `{ "type": "telemetry", "payload": {...}, "area_status": "...", "area_values": {...} }`

## Dashboard UI Elements

- **Header Status Badge**: Shows current area status (NORMAL/WARNING/DANGER) with color-coded dot
- **3 Sensor Cards**: Display latest temperature, humidity, and smoke readings
- **Real-time Charts**: Line graphs for each metric
- **Alert Banner**: Floating notification in top-right corner
- **Connection Status**: Shows WebSocket connection state

## Files Modified/Created

- `.env` - Environment variables for thresholds
- `docker-compose.yml` - Added `env_file` directive
- `dashboard_service/main.py` - Added `compute_combined_status()` logic
- `web_dashboard/index.html` - Added alert UI and status badge
- `web_dashboard/app.js` - Added alert handling and browser notifications
- `README.md` - Updated run instructions

## Troubleshooting

### Notifications not appearing?
- Check browser console (F12) for permission errors
- Ensure notifications permission is granted for localhost:3000
- Verify backend is broadcasting area_status via WebSocket

### Status not updating?
- Check dashboard logs: `docker-compose logs dashboard_service`
- Verify sensors are running: `docker-compose ps`
- Check WebSocket connection in browser DevTools

### Reset Everything
```bash
docker-compose down -v
docker volume rm sister_forest_postgres_data
docker-compose up -d
```

---

**Last Updated**: December 4, 2025  
**System Status**: ✓ Fully functional with deterministic test results captured
