// Solar Sync - Main JavaScript

// Global variables
let powerChart = null;
let chartData = {
    labels: [],
    solar: [],
    battery: [],
    load: [],
    grid: []
};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Solar Sync - Initializing...');
    
    // Initialize navigation
    initNavigation();
    
    // Initialize dashboard if on dashboard page
    if (document.querySelector('.dashboard')) {
        initDashboard();
    }
    
    // Initialize charts if on charts page
    if (document.querySelector('.charts-page')) {
        initCharts();
    }
    
    // Initialize control if on control page
    if (document.querySelector('.control-page')) {
        initControl();
    }
    
    // Initialize settings if on settings page
    if (document.querySelector('.settings-page')) {
        initSettings();
    }
});

// Navigation functionality
function initNavigation() {
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!navToggle.contains(event.target) && !navMenu.contains(event.target)) {
                navMenu.classList.remove('active');
            }
        });
    }
}

// Dashboard initialization
function initDashboard() {
    console.log('Initializing dashboard...');
    
    // Initialize real-time chart
    initPowerChart();
    
    // Load initial data
    loadDashboardData();
    
    // Set up periodic data refresh
    setInterval(loadDashboardData, 10000); // Refresh every 10 seconds
    
    // Set up chart controls
    setupChartControls();
}

// Initialize power chart
function initPowerChart() {
    const ctx = document.getElementById('power-chart');
    if (!ctx) return;
    
    const chartConfig = {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Solar Power',
                    data: [],
                    borderColor: '#FFD700',
                    backgroundColor: 'rgba(255, 215, 0, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Battery Power',
                    data: [],
                    borderColor: '#28A745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4
                },
                {
                    label: 'Load Power',
                    data: [],
                    borderColor: '#17A2B8',
                    backgroundColor: 'rgba(23, 162, 184, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4
                },
                {
                    label: 'Grid Power',
                    data: [],
                    borderColor: '#FF8C00',
                    backgroundColor: 'rgba(255, 140, 0, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#FFD700',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Power (Watts)'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                }
            }
        }
    };
    
    powerChart = new Chart(ctx, chartConfig);
}

// Load dashboard data
async function loadDashboardData() {
    try {
        // Load current data
        const response = await fetch('/dashboard/current');
        const data = await response.json();
        
        // Update metrics
        updateMetrics(data);
        
        // Update chart
        updateChart(data);
        
        // Update last update time
        updateLastUpdate();
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showError('Failed to load dashboard data');
    }
}

// Update metrics display
function updateMetrics(data) {
    // Solar power
    const solarElement = document.getElementById('solar-power');
    if (solarElement) {
        solarElement.textContent = formatPower(data.solar_power_w);
    }
    
    // Battery
    const batterySocElement = document.getElementById('battery-soc');
    const batteryPowerElement = document.getElementById('battery-power');
    if (batterySocElement) {
        batterySocElement.textContent = data.battery_soc_percent.toFixed(1);
    }
    if (batteryPowerElement) {
        const power = data.battery_power_w;
        const sign = power >= 0 ? '+' : '';
        batteryPowerElement.textContent = `${sign}${formatPower(power)}`;
    }
    
    // Load power
    const loadElement = document.getElementById('load-power');
    if (loadElement) {
        loadElement.textContent = formatPower(data.load_power_w);
    }
    
    // Grid power
    const gridElement = document.getElementById('grid-power');
    const gridDirectionElement = document.getElementById('grid-direction');
    if (gridElement) {
        gridElement.textContent = formatPower(Math.abs(data.grid_power_w));
    }
    if (gridDirectionElement) {
        const direction = data.grid_power_w >= 0 ? 'Import' : 'Export';
        gridDirectionElement.textContent = direction;
    }
    
    // System temperature
    const tempElement = document.getElementById('system-temp');
    if (tempElement) {
        tempElement.textContent = `${data.inverter_temp_c.toFixed(1)}°C`;
    }
    
    // System efficiency
    const efficiencyElement = document.getElementById('system-efficiency');
    if (efficiencyElement) {
        efficiencyElement.textContent = `${data.system_efficiency_percent.toFixed(1)}%`;
    }
}

// Update chart with new data
function updateChart(data) {
    if (!powerChart) return;
    
    const now = new Date();
    const timeLabel = now.toLocaleTimeString();
    
    // Add new data point
    chartData.labels.push(timeLabel);
    chartData.solar.push(data.solar_power_w);
    chartData.battery.push(data.battery_power_w);
    chartData.load.push(data.load_power_w);
    chartData.grid.push(data.grid_power_w);
    
    // Keep only last 20 data points
    const maxPoints = 20;
    if (chartData.labels.length > maxPoints) {
        chartData.labels.shift();
        chartData.solar.shift();
        chartData.battery.shift();
        chartData.load.shift();
        chartData.grid.shift();
    }
    
    // Update chart
    powerChart.data.labels = chartData.labels;
    powerChart.data.datasets[0].data = chartData.solar;
    powerChart.data.datasets[1].data = chartData.battery;
    powerChart.data.datasets[2].data = chartData.load;
    powerChart.data.datasets[3].data = chartData.grid;
    
    powerChart.update('none');
}

// Setup chart controls
function setupChartControls() {
    const chartToggle = document.getElementById('chart-toggle');
    if (chartToggle) {
        chartToggle.addEventListener('click', function() {
            if (powerChart.options.plugins.legend.display) {
                powerChart.options.plugins.legend.display = false;
                chartToggle.textContent = 'Show Legend';
            } else {
                powerChart.options.plugins.legend.display = true;
                chartToggle.textContent = 'Hide Legend';
            }
            powerChart.update();
        });
    }
}

// Update last update time
function updateLastUpdate() {
    const lastUpdateElement = document.getElementById('last-update');
    if (lastUpdateElement) {
        const now = new Date();
        lastUpdateElement.textContent = now.toLocaleTimeString();
    }
}

// Utility functions
function formatPower(watts) {
    if (watts >= 1000) {
        return (watts / 1000).toFixed(1) + 'k';
    }
    return watts.toString();
}

function formatEnergy(wattHours) {
    if (wattHours >= 1000) {
        return (wattHours / 1000).toFixed(2) + ' kWh';
    }
    return wattHours.toFixed(0) + ' Wh';
}

function showError(message) {
    console.error(message);
    // You can implement a toast notification system here
}

function showSuccess(message) {
    console.log(message);
    // You can implement a toast notification system here
}

// Charts page initialization
function initCharts() {
    console.log('Initializing charts page...');
    // Charts page specific functionality
}

// Control page initialization
function initControl() {
    console.log('Initializing control page...');
    // Control page specific functionality
}

// Settings page initialization
function initSettings() {
    console.log('Initializing settings page...');
    // Settings page specific functionality
}

// Export functions for use in other modules
window.SolarSync = {
    formatPower,
    formatEnergy,
    showError,
    showSuccess
};
