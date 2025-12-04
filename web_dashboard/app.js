// Konfigurasi API
const API_BASE_URL = 'http://localhost:8000';

// Data storage untuk grafik
const chartData = {
    labels: [],
    datasets: {}
};

const MAX_DATA_POINTS = 20;

// Charts
let temperatureChart, humidityChart, smokeChart;

// Sensor data
let sensorsData = {};

// Initialize charts
function initCharts() {
    const chartConfig = (label, color) => ({
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 750
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            }
        }
    });

    const tempCtx = document.getElementById('temperatureChart').getContext('2d');
    temperatureChart = new Chart(tempCtx, chartConfig('Temperature', 'red'));

    const humCtx = document.getElementById('humidityChart').getContext('2d');
    humidityChart = new Chart(humCtx, chartConfig('Humidity', 'blue'));

    const smokeCtx = document.getElementById('smokeChart').getContext('2d');
    smokeChart = new Chart(smokeCtx, chartConfig('Smoke', 'gray'));
}

// Fetch initial data from API
async function fetchInitialData() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/readings/latest`);
        const data = await response.json();
        
        // Make sure we have all 3 sensors in order
        const sensorOrder = ['temp-01', 'hum-01', 'smoke-01'];
        sensorOrder.forEach(sensorId => {
            const sensorData = data.find(d => d.sensor_id === sensorId);
            if (sensorData) {
                updateSensorCard(sensorData);
            }
        });

        // Fetch combined area status
        try {
            const stResp = await fetch(`${API_BASE_URL}/api/status`);
            const stData = await stResp.json();
            if (stData && stData.area_status) {
                updateAreaStatus(stData.area_status, stData.area_values || {});
            }
        } catch (e) {
            console.warn('Could not fetch area status', e);
        }

        document.getElementById('loading').style.display = 'none';
        document.getElementById('sensors-container').style.display = 'grid';
        document.getElementById('charts-section').style.display = 'block';
        
    } catch (error) {
        console.error('Error fetching initial data:', error);
        document.getElementById('loading').textContent = 'Gagal memuat data. Mencoba lagi...';
        setTimeout(fetchInitialData, 3000);
    }
}

// Fetch data historis untuk chart
async function fetchHistoricalData() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/readings/history?limit=20`);
        const data = await response.json();
        
        // Group by sensor
        const groupedData = {};
        data.reverse().forEach(reading => {
            if (!groupedData[reading.sensor_id]) {
                groupedData[reading.sensor_id] = {
                    labels: [],
                    temperature: [],
                    humidity: [],
                    smoke: []
                };
            }
            
            const time = new Date(reading.timestamp).toLocaleTimeString('id-ID');
            groupedData[reading.sensor_id].labels.push(time);
            groupedData[reading.sensor_id].temperature.push(reading.data?.temperature || null);
            groupedData[reading.sensor_id].humidity.push(reading.data?.humidity || null);
            groupedData[reading.sensor_id].smoke.push(reading.data?.smoke || null);
        });

        // Update charts
        updateChartsWithHistoricalData(groupedData);
        
    } catch (error) {
        console.error('Error fetching historical data:', error);
    }
}

// Update charts dengan data historis
function updateChartsWithHistoricalData(groupedData) {
    const sensorColorMap = {
        'temp-01': '#ef4444',      // Red for Temperature
        'hum-01': '#3b82f6',       // Blue for Humidity
        'smoke-01': '#8b7355'      // Brown for Smoke
    };

    // Clear existing datasets
    temperatureChart.data.datasets = [];
    humidityChart.data.datasets = [];
    smokeChart.data.datasets = [];

    // Use labels from first sensor
    const firstSensor = Object.keys(groupedData)[0];
    if (firstSensor) {
        chartData.labels = groupedData[firstSensor].labels;
        temperatureChart.data.labels = chartData.labels;
        humidityChart.data.labels = chartData.labels;
        smokeChart.data.labels = chartData.labels;
    }

    // Add datasets for each sensor (only show relevant data)
    Object.keys(groupedData).forEach(sensorId => {
        const color = sensorColorMap[sensorId] || '#666666';

        // Only add temperature data from temp sensor
        if (sensorId === 'temp-01' && groupedData[sensorId].temperature.some(v => v !== null)) {
            temperatureChart.data.datasets.push({
                label: sensorId,
                data: groupedData[sensorId].temperature,
                borderColor: color,
                backgroundColor: color + '20',
                tension: 0.4
            });
        }

        // Only add humidity data from humidity sensor
        if (sensorId === 'hum-01' && groupedData[sensorId].humidity.some(v => v !== null)) {
            humidityChart.data.datasets.push({
                label: sensorId,
                data: groupedData[sensorId].humidity,
                borderColor: color,
                backgroundColor: color + '20',
                tension: 0.4
            });
        }

        // Only add smoke data from smoke sensor
        if (sensorId === 'smoke-01' && groupedData[sensorId].smoke.some(v => v !== null)) {
            smokeChart.data.datasets.push({
                label: sensorId,
                data: groupedData[sensorId].smoke,
                borderColor: color,
                backgroundColor: color + '20',
                tension: 0.4
            });
        }
    });

    temperatureChart.update();
    humidityChart.update();
    smokeChart.update();
}

// Create sensor card
function createSensorCard(sensorId) {
    // Determine sensor name and icon based on sensor_id
    let sensorDisplay = sensorId;
    let metricLabel = '';
    let metricUnit = '';
    let cardClass = '';
    let icon = '';
    let metricClass = '';
    
    if (sensorId === 'temp-01') {
        sensorDisplay = 'Sensor Suhu';
        metricLabel = 'Suhu Udara';
        metricUnit = '°C';
        cardClass = 'temp';
        icon = '🌡️';
        metricClass = 'temp';
    } else if (sensorId === 'hum-01') {
        sensorDisplay = 'Sensor Kelembaban';
        metricLabel = 'Kelembaban Udara';
        metricUnit = '%';
        cardClass = 'hum';
        icon = '💧';
        metricClass = 'hum';
    } else if (sensorId === 'smoke-01') {
        sensorDisplay = 'Sensor Asap';
        metricLabel = 'Konsentrasi Asap';
        metricUnit = 'ppm';
        cardClass = 'smoke';
        icon = '💨';
        metricClass = 'smoke';
    }
    
    const card = document.createElement('div');
    card.className = `sensor-card ${cardClass}`;
    card.id = `sensor-${sensorId}`;
    
    card.innerHTML = `
        <div class="sensor-icon">${icon}</div>
        <div class="sensor-header">
            <div class="sensor-info">
                <div class="sensor-title">${sensorDisplay}</div>
                <div class="sensor-location"></div>
                <div class="sensor-status status-normal">Normal</div>
            </div>
        </div>
        <div class="sensor-metrics">
            <div class="metric ${metricClass}">
                <div class="metric-label">${metricLabel}</div>
                <div class="metric-value">--<span class="metric-unit">${metricUnit}</span></div>
                <div class="metric-range"></div>
            </div>
        </div>
        <div class="last-update">Memuat data...</div>
    `;
    
    document.getElementById('sensors-container').appendChild(card);
}

// Update sensor card
function updateSensorCard(data) {
    const sensorId = data.sensor_id;
    let card = document.getElementById(`sensor-${sensorId}`);
    
    if (!card) {
        createSensorCard(sensorId);
        card = document.getElementById(`sensor-${sensorId}`);
    }
    
    // Update status
    const statusElement = card.querySelector('.sensor-status');
    statusElement.className = `sensor-status status-${data.status}`;
    statusElement.textContent = data.status.toUpperCase();
    
    // Update location
    card.querySelector('.sensor-location').textContent = data.location;
    
    // Update metrics based on sensor type
    const metricValue = card.querySelector('.metric-value');
    const metricRange = card.querySelector('.metric-range');
    
    if (data.data.temperature !== undefined) {
        metricValue.innerHTML = `${data.data.temperature.toFixed(1)}<span class="metric-unit">°C</span>`;
        // Show range info
        if (data.status === 'normal') {
            metricRange.textContent = 'Range: 20-35°C (Normal)';
        } else if (data.status === 'warning') {
            metricRange.textContent = 'Range: 35-45°C (Peringatan)';
        } else {
            metricRange.textContent = 'Range: >45°C (Bahaya)';
        }
    } else if (data.data.humidity !== undefined) {
        metricValue.innerHTML = `${data.data.humidity.toFixed(1)}<span class="metric-unit">%</span>`;
        // Show range info
        if (data.status === 'normal') {
            metricRange.textContent = 'Range: 40-70% (Normal)';
        } else if (data.status === 'warning') {
            metricRange.textContent = 'Range: 30-40% (Peringatan)';
        } else {
            metricRange.textContent = 'Range: <30% (Bahaya)';
        }
    } else if (data.data.smoke !== undefined) {
        metricValue.innerHTML = `${data.data.smoke}<span class="metric-unit">ppm</span>`;
        // Show range info
        if (data.status === 'normal') {
            metricRange.textContent = 'Range: 0-300 ppm (Normal)';
        } else if (data.status === 'warning') {
            metricRange.textContent = 'Range: 300-600 ppm (Peringatan)';
        } else {
            metricRange.textContent = 'Range: >600 ppm (Bahaya)';
        }
    }
    
    // Update timestamp
    const timestamp = new Date(data.timestamp).toLocaleString('id-ID');
    card.querySelector('.last-update').textContent = `Update: ${timestamp}`;
    
    // Update chart
    updateChartData(data);
}

// Update chart data
function updateChartData(data) {
    const timestamp = new Date(data.timestamp).toLocaleTimeString('id-ID');
    const sensorId = data.sensor_id;
    
    // Initialize dataset for sensor if not exists
    if (!chartData.datasets[sensorId]) {
        const sensorColorMap = {
            'temp-01': '#ef4444',      // Red for Temperature
            'hum-01': '#3b82f6',       // Blue for Humidity
            'smoke-01': '#8b7355'      // Brown for Smoke
        };
        const color = sensorColorMap[sensorId] || '#666666';
        
        chartData.datasets[sensorId] = {
            temperature: [],
            humidity: [],
            smoke: []
        };
        
        // Add dataset to charts (specific to sensor type)
        if (sensorId === 'temp-01') {
            temperatureChart.data.datasets.push({
                label: sensorId,
                data: [],
                borderColor: color,
                backgroundColor: color + '20',
                tension: 0.4
            });
        } else if (sensorId === 'hum-01') {
            humidityChart.data.datasets.push({
                label: sensorId,
                data: [],
                borderColor: color,
                backgroundColor: color + '20',
                tension: 0.4
            });
        } else if (sensorId === 'smoke-01') {
            smokeChart.data.datasets.push({
                label: sensorId,
                data: [],
                borderColor: color,
                backgroundColor: color + '20',
                tension: 0.4
            });
        }
    }
    
    // Update labels (use common timeline)
    if (!chartData.labels.includes(timestamp)) {
        chartData.labels.push(timestamp);
        if (chartData.labels.length > MAX_DATA_POINTS) {
            chartData.labels.shift();
        }
    }
    
    // Update data based on sensor type
    if (data.data.temperature !== undefined) {
        chartData.datasets[sensorId].temperature.push(data.data.temperature);
        if (chartData.datasets[sensorId].temperature.length > MAX_DATA_POINTS) {
            chartData.datasets[sensorId].temperature.shift();
        }
    }
    
    if (data.data.humidity !== undefined) {
        chartData.datasets[sensorId].humidity.push(data.data.humidity);
        if (chartData.datasets[sensorId].humidity.length > MAX_DATA_POINTS) {
            chartData.datasets[sensorId].humidity.shift();
        }
    }
    
    if (data.data.smoke !== undefined) {
        chartData.datasets[sensorId].smoke.push(data.data.smoke);
        if (chartData.datasets[sensorId].smoke.length > MAX_DATA_POINTS) {
            chartData.datasets[sensorId].smoke.shift();
        }
    }
    
    // Update charts
    temperatureChart.data.labels = chartData.labels;
    humidityChart.data.labels = chartData.labels;
    smokeChart.data.labels = chartData.labels;
    
    // Update temperature chart (only from temp-01)
    if (sensorId === 'temp-01' && temperatureChart.data.datasets.length > 0) {
        temperatureChart.data.datasets[0].data = chartData.datasets[sensorId].temperature;
    }
    
    // Update humidity chart (only from hum-01)
    if (sensorId === 'hum-01' && humidityChart.data.datasets.length > 0) {
        humidityChart.data.datasets[0].data = chartData.datasets[sensorId].humidity;
    }
    
    // Update smoke chart (only from smoke-01)
    if (sensorId === 'smoke-01' && smokeChart.data.datasets.length > 0) {
        smokeChart.data.datasets[0].data = chartData.datasets[sensorId].smoke;
    }
    
    temperatureChart.update('none');
    humidityChart.update('none');
    smokeChart.update('none');
    
    // Update last update time
    document.getElementById('last-update').textContent = 
        `Terakhir diperbarui: ${new Date().toLocaleString('id-ID')}`;
}

    // Update area status in header
    function updateAreaStatus(areaStatus, areaValues) {
        const el = document.getElementById('area-status');
        if (!el) return;
        // Update label and dot inside area-status
        const dot = el.querySelector('.status-dot');
        const text = el.querySelector('span');
        if (text) text.textContent = `Area Status: ${areaStatus}`;

        if (dot) {
            dot.className = 'status-dot';
            if (areaStatus === 'DANGER') dot.classList.add('status-danger');
            else if (areaStatus === 'WARNING') dot.classList.add('status-warning');
            else dot.classList.add('status-online');
        }

        // Log values
        console.log('Area values:', areaValues);

        // Show notification/banner for WARNING and DANGER
        if (areaStatus === 'DANGER') {
            showAlert('DANGER: Risiko kebakaran tinggi! Ambil tindakan segera.', 'danger', true);
        } else if (areaStatus === 'WARNING') {
            // show a less intrusive alert that auto-dismisses after 8s
            showAlert('WARNING: Kondisi memperingatkan — monitor area lebih sering.', 'warning', false, 8000);
        } else {
            // Clear any existing alerts when back to normal
            clearAlert();
        }
    }

    // Alert utility
    function showAlert(message, level = 'warning', persistent = false, timeout = 0) {
        const alertEl = document.getElementById('area-alert');
        if (!alertEl) return;
        alertEl.className = '';
        if (level === 'danger') alertEl.classList.add('alert-danger');
        else if (level === 'warning') alertEl.classList.add('alert-warning');
        else alertEl.classList.add('alert-normal');

        alertEl.innerHTML = `<div class=\"alert-message\">${message}</div>` +
            `<div class=\"alert-close\">✕</div>`;
        alertEl.style.display = 'block';

        // close handler
        const closeBtn = alertEl.querySelector('.alert-close');
        if (closeBtn) {
            closeBtn.onclick = () => { alertEl.style.display = 'none'; };
        }

        // play a brief attention sound for danger (optional)
        if (level === 'danger') {
            try {
                const audio = new Audio();
                // small beep encoded as data URI (short tone)
                audio.src = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAIlYAAESsAAACABAAZGF0YQAAAAA=';
                audio.play().catch(()=>{});
            } catch (e) {}
        }

        if (!persistent && timeout > 0) {
            setTimeout(() => { alertEl.style.display = 'none'; }, timeout);
        }
        // Also show browser notification when possible for warning/danger
        if (level === 'danger' || level === 'warning') {
            showNotification(message, level);
        }
    }

    function clearAlert() {
        const alertEl = document.getElementById('area-alert');
        if (!alertEl) return;
        alertEl.style.display = 'none';
        alertEl.className = '';
        alertEl.innerHTML = '';
    }

// Setup WebSocket connection
function setupWebSocket() {
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onopen = () => {
        console.log('WebSocket connected');
        document.getElementById('connection-status').textContent = 'Terhubung';
    };
    
    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        console.log('Received data via WebSocket:', msg);

        // Support new broadcast format { type: 'telemetry', payload, area_status, area_values }
        if (msg.type && msg.type === 'telemetry') {
            const payload = msg.payload;
            const area_status = msg.area_status;
            const area_values = msg.area_values;
            if (payload) updateSensorCard(payload);
            if (area_status) updateAreaStatus(area_status, area_values || {});
        } else {
            // Backwards compat: single payload
            updateSensorCard(msg);
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        document.getElementById('connection-status').textContent = 'Error Koneksi';
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected. Reconnecting...');
        document.getElementById('connection-status').textContent = 'Reconnecting...';
        setTimeout(setupWebSocket, 3000);
    };
}

// Browser Notifications
function requestNotificationPermission() {
    if (!('Notification' in window)) return;
    if (Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            console.log('Notification permission:', permission);
        }).catch(() => {});
    }
}

function showNotification(message, level = 'warning') {
    if (!('Notification' in window)) return;
    if (Notification.permission !== 'granted') return;

    const title = level === 'danger' ? 'DANGER - Forest Alert' : 'WARNING - Forest Alert';
    const options = {
        body: message,
        icon: '',
        silent: level !== 'danger'
    };

    try {
        const n = new Notification(title, options);
        // close automatically after 8s for warnings, keep for danger until clicked
        if (level === 'warning') setTimeout(() => n.close(), 8000);
        n.onclick = () => { try { window.open('http://localhost:3000', '_blank'); } catch(e) { window.focus(); } finally { n.close(); } };
    } catch (e) {
        console.warn('Notification error', e);
    }
}

// Polling sebagai fallback jika WebSocket gagal
function startPolling() {
    setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/readings/latest`);
            const data = await response.json();
            
            data.forEach(reading => {
                updateSensorCard(reading);
            });
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 5000); // Poll setiap 5 detik
}

// Initialize application
async function init() {
    initCharts();
    await fetchInitialData();
    await fetchHistoricalData();
    
    // Try WebSocket first
    try {
        setupWebSocket();
    } catch (error) {
        console.log('WebSocket not available, using polling');
        startPolling();
    }
}

// Start application
document.addEventListener('DOMContentLoaded', init);