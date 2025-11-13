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
        
        data.forEach(reading => {
            updateSensorCard(reading);
        });

        document.getElementById('loading').style.display = 'none';
        document.getElementById('sensors-container').style.display = 'grid';
        document.getElementById('charts-section').style.display = 'block';
        document.getElementById('sensor-count').textContent = `Sensor: ${data.length}`;
        
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
            groupedData[reading.sensor_id].temperature.push(reading.temperature);
            groupedData[reading.sensor_id].humidity.push(reading.humidity);
            groupedData[reading.sensor_id].smoke.push(reading.smoke);
        });

        // Update charts
        updateChartsWithHistoricalData(groupedData);
        
    } catch (error) {
        console.error('Error fetching historical data:', error);
    }
}

// Update charts dengan data historis
function updateChartsWithHistoricalData(groupedData) {
    const colors = ['#ef4444', '#3b82f6', '#10b981'];
    let colorIndex = 0;

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

    // Add datasets for each sensor
    Object.keys(groupedData).forEach(sensorId => {
        const color = colors[colorIndex % colors.length];
        colorIndex++;

        temperatureChart.data.datasets.push({
            label: sensorId,
            data: groupedData[sensorId].temperature,
            borderColor: color,
            backgroundColor: color + '20',
            tension: 0.4
        });

        humidityChart.data.datasets.push({
            label: sensorId,
            data: groupedData[sensorId].humidity,
            borderColor: color,
            backgroundColor: color + '20',
            tension: 0.4
        });

        smokeChart.data.datasets.push({
            label: sensorId,
            data: groupedData[sensorId].smoke,
            borderColor: color,
            backgroundColor: color + '20',
            tension: 0.4
        });
    });

    temperatureChart.update();
    humidityChart.update();
    smokeChart.update();
}

// Create sensor card
function createSensorCard(sensorId) {
    const card = document.createElement('div');
    card.className = 'sensor-card';
    card.id = `sensor-${sensorId}`;
    
    card.innerHTML = `
        <div class="sensor-header">
            <div class="sensor-title">${sensorId}</div>
            <div class="sensor-status status-normal">Normal</div>
        </div>
        <div class="sensor-location"></div>
        <div class="sensor-metrics">
            <div class="metric">
                <div class="metric-label">Suhu</div>
                <div class="metric-value">--<span class="metric-unit">°C</span></div>
            </div>
            <div class="metric">
                <div class="metric-label">Kelembaban</div>
                <div class="metric-value">--<span class="metric-unit">%</span></div>
            </div>
            <div class="metric">
                <div class="metric-label">Asap</div>
                <div class="metric-value">--<span class="metric-unit">ppm</span></div>
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
    
    // Update metrics
    const metrics = card.querySelectorAll('.metric-value');
    metrics[0].innerHTML = `${data.temperature.toFixed(1)}<span class="metric-unit">°C</span>`;
    metrics[1].innerHTML = `${data.humidity.toFixed(1)}<span class="metric-unit">%</span>`;
    metrics[2].innerHTML = `${data.smoke}<span class="metric-unit">ppm</span>`;
    
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
        const colors = ['#ef4444', '#3b82f6', '#10b981'];
        const colorIndex = Object.keys(chartData.datasets).length % colors.length;
        const color = colors[colorIndex];
        
        chartData.datasets[sensorId] = {
            temperature: [],
            humidity: [],
            smoke: []
        };
        
        // Add dataset to charts
        [temperatureChart, humidityChart, smokeChart].forEach((chart, index) => {
            chart.data.datasets.push({
                label: sensorId,
                data: [],
                borderColor: color,
                backgroundColor: color + '20',
                tension: 0.4
            });
        });
    }
    
    // Update labels (use common timeline)
    if (!chartData.labels.includes(timestamp)) {
        chartData.labels.push(timestamp);
        if (chartData.labels.length > MAX_DATA_POINTS) {
            chartData.labels.shift();
        }
    }
    
    // Update data
    chartData.datasets[sensorId].temperature.push(data.temperature);
    chartData.datasets[sensorId].humidity.push(data.humidity);
    chartData.datasets[sensorId].smoke.push(data.smoke);
    
    // Trim old data
    if (chartData.datasets[sensorId].temperature.length > MAX_DATA_POINTS) {
        chartData.datasets[sensorId].temperature.shift();
        chartData.datasets[sensorId].humidity.shift();
        chartData.datasets[sensorId].smoke.shift();
    }
    
    // Update charts
    temperatureChart.data.labels = chartData.labels;
    humidityChart.data.labels = chartData.labels;
    smokeChart.data.labels = chartData.labels;
    
    Object.keys(chartData.datasets).forEach((sid, idx) => {
        if (temperatureChart.data.datasets[idx]) {
            temperatureChart.data.datasets[idx].data = chartData.datasets[sid].temperature;
            humidityChart.data.datasets[idx].data = chartData.datasets[sid].humidity;
            smokeChart.data.datasets[idx].data = chartData.datasets[sid].smoke;
        }
    });
    
    temperatureChart.update('none');
    humidityChart.update('none');
    smokeChart.update('none');
    
    // Update last update time
    document.getElementById('last-update').textContent = 
        `Terakhir diperbarui: ${new Date().toLocaleString('id-ID')}`;
}

// Setup WebSocket connection
function setupWebSocket() {
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onopen = () => {
        console.log('WebSocket connected');
        document.getElementById('connection-status').textContent = 'Terhubung';
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received data via WebSocket:', data);
        updateSensorCard(data);
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