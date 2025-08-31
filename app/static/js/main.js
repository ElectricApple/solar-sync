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
let isChartPaused = false;

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
    const navLinks = document.querySelectorAll('.nav-link');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            navMenu.classList.toggle('active');
            
            // Update toggle icon
            const icon = navToggle.querySelector('i');
            if (navMenu.classList.contains('active')) {
                icon.className = 'fas fa-times';
            } else {
                icon.className = 'fas fa-bars';
            }
        });
        
        // Close mobile menu when clicking on a link
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                navMenu.classList.remove('active');
                const icon = navToggle.querySelector('i');
                icon.className = 'fas fa-bars';
            });
        });
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!navToggle.contains(event.target) && !navMenu.contains(event.target)) {
                navMenu.classList.remove('active');
                const icon = navToggle.querySelector('i');
                icon.className = 'fas fa-bars';
            }
        });
        
        // Close mobile menu on window resize
        window.addEventListener('resize', function() {
            if (window.innerWidth > 575) {
                navMenu.classList.remove('active');
                const icon = navToggle.querySelector('i');
                icon.className = 'fas fa-bars';
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
    setInterval(() => {
        if (!isChartPaused) {
            loadDashboardData();
        }
    }, 5000); // Refresh every 5 seconds
    
    // Set up chart controls
    setupChartControls();
    
    // Add fade-in animation to dashboard elements
    addDashboardAnimations();
}

// Add animations to dashboard elements
function addDashboardAnimations() {
    const elements = document.querySelectorAll('.metric-card, .status-card, .chart-container, .events-container');
    elements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            element.style.transition = 'all 0.6s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 100);
    });
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
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'Battery Power',
                    data: [],
                    borderColor: '#28A745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'Load Power',
                    data: [],
                    borderColor: '#17A2B8',
                    backgroundColor: 'rgba(23, 162, 184, 0.1)',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'Grid Power',
                    data: [],
                    borderColor: '#FF8C00',
                    backgroundColor: 'rgba(255, 140, 0, 0.1)',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
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
                        padding: 20,
                        font: {
                            size: 12,
                            weight: '500'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.9)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#FFD700',
                    borderWidth: 1,
                    cornerRadius: 8,
                    displayColors: true,
                    titleFont: {
                        size: 14,
                        weight: '600'
                    },
                    bodyFont: {
                        size: 13
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time',
                        font: {
                            size: 12,
                            weight: '500'
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)',
                        drawBorder: false
                    },
                    ticks: {
                        font: {
                            size: 11
                        }
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Power (Watts)',
                        font: {
                            size: 12,
                            weight: '500'
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)',
                        drawBorder: false
                    },
                    ticks: {
                        font: {
                            size: 11
                        }
                    }
                }
            },
            animation: {
                duration: 750,
                easing: 'easeInOutQuart'
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
        
        // Update metrics with animation
        updateMetrics(data);
        
        // Update chart
        if (!isChartPaused) {
            updateChart(data);
        }
        
        // Update last update time
        updateLastUpdate();
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showError('Failed to load dashboard data');
    }
}

// Update metrics display with animations
function updateMetrics(data) {
    // Solar power
    updateMetricWithAnimation('solar-power', formatPower(data.solar_power_w));
    
    // Battery
    updateMetricWithAnimation('battery-soc', data.battery_soc_percent.toFixed(1));
    const batteryPower = data.battery_power_w;
    const sign = batteryPower >= 0 ? '+' : '';
    updateMetricWithAnimation('battery-power', `${sign}${formatPower(batteryPower)}`);
    
    // Load power
    updateMetricWithAnimation('load-power', formatPower(data.load_power_w));
    
    // Grid power
    updateMetricWithAnimation('grid-power', formatPower(Math.abs(data.grid_power_w)));
    const direction = data.grid_power_w >= 0 ? 'Import' : 'Export';
    updateMetricWithAnimation('grid-direction', direction);
    
    // System temperature
    updateMetricWithAnimation('system-temp', `${data.inverter_temp_c.toFixed(1)}°C`);
    
    // System efficiency
    updateMetricWithAnimation('system-efficiency', `${data.system_efficiency_percent.toFixed(1)}%`);
    
    // Daily production
    updateMetricWithAnimation('daily-production', `${data.daily_energy_kwh.toFixed(2)} kWh`);
}

// Update metric with subtle animation
function updateMetricWithAnimation(elementId, newValue) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    if (element.textContent !== newValue) {
        element.style.transform = 'scale(1.05)';
        element.style.transition = 'transform 0.2s ease';
        element.textContent = newValue;
        
        setTimeout(() => {
            element.style.transform = 'scale(1)';
        }, 200);
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
    
    // Keep only last 30 data points
    const maxPoints = 30;
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
            isChartPaused = !isChartPaused;
            
            const icon = chartToggle.querySelector('i');
            const text = chartToggle.querySelector('span') || chartToggle;
            
            if (isChartPaused) {
                icon.className = 'fas fa-play';
                text.textContent = 'Resume';
                chartToggle.classList.remove('btn-secondary');
                chartToggle.classList.add('btn-warning');
            } else {
                icon.className = 'fas fa-pause';
                text.textContent = 'Pause';
                chartToggle.classList.remove('btn-warning');
                chartToggle.classList.add('btn-secondary');
            }
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
    return Math.round(watts).toString();
}

function formatEnergy(wattHours) {
    if (wattHours >= 1000) {
        return (wattHours / 1000).toFixed(2) + ' kWh';
    }
    return wattHours.toFixed(0) + ' Wh';
}

function showError(message) {
    console.error(message);
    // Create a toast notification
    createToast(message, 'error');
}

function showSuccess(message) {
    console.log(message);
    // Create a toast notification
    createToast(message, 'success');
}

// Create toast notification
function createToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
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
    showSuccess,
    createToast
};
