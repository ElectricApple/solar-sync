class SolarSyncChartManager {
    constructor() {
        this.charts = {};
        this.websocket = null;
        this.updateInterval = null;
        this.theme = this.getTheme();
        
        // Initialize Chart.js defaults
        this.initChartDefaults();
    }
    
    initChartDefaults() {
        // Solar Sync yellow theme
        Chart.defaults.color = '#E5E7EB';
        Chart.defaults.borderColor = '#374151';
        Chart.defaults.backgroundColor = 'rgba(255, 215, 0, 0.1)';
        
        // Font settings
        Chart.defaults.font = {
            family: "'Inter', system-ui, sans-serif",
            size: 12
        };
        
        // Animation settings (optimized for Pi)
        Chart.defaults.animation = {
            duration: window.location.hostname === 'localhost' ? 750 : 300,
            easing: 'easeInOutQuart'
        };
    }
    
    getTheme() {
        return {
            colors: {
                solar: '#FFD700',      // Bright yellow
                battery: '#10B981',    // Green (charging)
                batteryDrain: '#EF4444', // Red (discharging)
                load: '#3B82F6',       // Blue
                grid: '#6B7280',       // Gray
                background: '#1F2937', // Dark gray
                text: '#F9FAFB',       // Light gray
                border: '#374151'      // Medium gray
            },
            gradients: {
                solar: 'linear-gradient(180deg, rgba(255,215,0,0.4) 0%, rgba(255,215,0,0.1) 100%)',
                battery: 'linear-gradient(180deg, rgba(16,185,129,0.4) 0%, rgba(16,185,129,0.1) 100%)'
            }
        };
    }
    
    createPowerFlowChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        
        // Destroy existing chart if it exists
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        // Ensure data exists and has the expected structure
        if (!data || !data.datasets || !data.datasets.timestamps) {
            console.error('Invalid data structure for power flow chart:', data);
            return null;
        }
        
        // Format timestamps for display
        const labels = data.datasets.timestamps.map(ts => {
            try {
                return new Date(ts).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            } catch (e) {
                return ts; // Fallback to original timestamp
            }
        });
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Solar Power',
                        data: data.datasets.solar_power || [],
                        borderColor: this.theme.colors.solar,
                        backgroundColor: this.theme.colors.solar + '20',
                        fill: true,
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 6
                    },
                    {
                        label: 'Battery Power',
                        data: data.datasets.battery_power || [],
                        borderColor: this.theme.colors.battery,
                        backgroundColor: this.theme.colors.battery + '20',
                        fill: false,
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 6
                    },
                    {
                        label: 'Load Power',
                        data: data.datasets.load_power || [],
                        borderColor: this.theme.colors.load,
                        backgroundColor: this.theme.colors.load + '20',
                        fill: false,
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 6
                    },
                    {
                        label: 'Grid Power',
                        data: data.datasets.grid_power || [],
                        borderColor: this.theme.colors.grid,
                        backgroundColor: this.theme.colors.grid + '10',
                        fill: false,
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 3,
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
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Time',
                            color: this.theme.colors.text,
                            font: {
                                size: 14,
                                weight: '600'
                            }
                        },
                        grid: {
                            color: this.theme.colors.border
                        },
                        ticks: {
                            color: this.theme.colors.text
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Power (W)',
                            color: this.theme.colors.text,
                            font: {
                                size: 14,
                                weight: '600'
                            }
                        },
                        grid: {
                            color: this.theme.colors.border
                        },
                        ticks: {
                            color: this.theme.colors.text
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            color: this.theme.colors.text,
                            font: {
                                size: 12,
                                weight: '500'
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: this.theme.colors.background,
                        titleColor: this.theme.colors.text,
                        bodyColor: this.theme.colors.text,
                        borderColor: this.theme.colors.border,
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: true,
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.parsed.y + 'W';
                            }
                        }
                    }
                }
            }
        });
        
        return this.charts[canvasId];
    }
    
    createBatteryPerformanceChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        
        // Destroy existing chart if it exists
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        // Ensure data exists and has the expected structure
        if (!data || !data.timestamps) {
            console.error('Invalid data structure for battery performance chart:', data);
            return null;
        }
        
        // Format timestamps for display
        const labels = data.timestamps.map(ts => {
            try {
                return new Date(ts).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            } catch (e) {
                return ts; // Fallback to original timestamp
            }
        });
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Battery SOC (%)',
                        data: data.soc_data || [],
                        borderColor: this.theme.colors.battery,
                        backgroundColor: this.theme.colors.battery + '20',
                        fill: true,
                        yAxisID: 'y',
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 6
                    },
                    {
                        label: 'Battery Voltage (V)',
                        data: data.voltage_data || [],
                        borderColor: this.theme.colors.solar,
                        backgroundColor: this.theme.colors.solar + '10',
                        fill: false,
                        yAxisID: 'y1',
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 3,
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
                scales: {
                    x: {
                        title: { 
                            display: true, 
                            text: 'Time',
                            color: this.theme.colors.text,
                            font: {
                                size: 14,
                                weight: '600'
                            }
                        },
                        grid: { color: this.theme.colors.border },
                        ticks: {
                            color: this.theme.colors.text
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: { 
                            display: true, 
                            text: 'SOC (%)',
                            color: this.theme.colors.text,
                            font: {
                                size: 14,
                                weight: '600'
                            }
                        },
                        min: 0,
                        max: 100,
                        grid: { color: this.theme.colors.border },
                        ticks: {
                            color: this.theme.colors.text
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: { 
                            display: true, 
                            text: 'Voltage (V)',
                            color: this.theme.colors.text,
                            font: {
                                size: 14,
                                weight: '600'
                            }
                        },
                        grid: { drawOnChartArea: false },
                        ticks: {
                            color: this.theme.colors.text
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            color: this.theme.colors.text,
                            font: {
                                size: 12,
                                weight: '500'
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: this.theme.colors.background,
                        titleColor: this.theme.colors.text,
                        bodyColor: this.theme.colors.text,
                        borderColor: this.theme.colors.border,
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                }
            }
        });
        
        return this.charts[canvasId];
    }
    
    createEnergySummaryChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        
        // Destroy existing chart if it exists
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        // Ensure data exists and has the expected structure
        if (!data || !data.labels) {
            console.error('Invalid data structure for energy summary chart:', data);
            return null;
        }
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: 'Solar Generated (kWh)',
                        data: data.solar_energy || [],
                        backgroundColor: this.theme.colors.solar + '80',
                        borderColor: this.theme.colors.solar,
                        borderWidth: 1,
                        borderRadius: 4
                    },
                    {
                        label: 'Energy Consumed (kWh)', 
                        data: data.load_energy || [],
                        backgroundColor: this.theme.colors.load + '80',
                        borderColor: this.theme.colors.load,
                        borderWidth: 1,
                        borderRadius: 4
                    },
                    {
                        label: 'Net Energy (kWh)',
                        data: data.net_energy || [],
                        type: 'line',
                        borderColor: this.theme.colors.battery,
                        backgroundColor: 'transparent',
                        borderWidth: 3,
                        fill: false,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 8
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
                scales: {
                    x: {
                        title: { 
                            display: true, 
                            text: 'Time Period',
                            color: this.theme.colors.text,
                            font: {
                                size: 14,
                                weight: '600'
                            }
                        },
                        grid: { color: this.theme.colors.border },
                        ticks: {
                            color: this.theme.colors.text
                        }
                    },
                    y: {
                        title: { 
                            display: true, 
                            text: 'Energy (kWh)',
                            color: this.theme.colors.text,
                            font: {
                                size: 14,
                                weight: '600'
                            }
                        },
                        grid: { color: this.theme.colors.border },
                        ticks: {
                            color: this.theme.colors.text
                        }
                    }
                },
                plugins: {
                    legend: { 
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            color: this.theme.colors.text,
                            font: {
                                size: 12,
                                weight: '500'
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: this.theme.colors.background,
                        titleColor: this.theme.colors.text,
                        bodyColor: this.theme.colors.text,
                        borderColor: this.theme.colors.border,
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                }
            }
        });
        
        return this.charts[canvasId];
    }
    
    createEfficiencyChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        
        // Destroy existing chart if it exists
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        // Ensure data exists and has the expected structure
        if (!data || !data.timestamps) {
            console.error('Invalid data structure for efficiency chart:', data);
            return null;
        }
        
        // Format timestamps for display
        const labels = data.timestamps.map(ts => {
            try {
                return new Date(ts).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            } catch (e) {
                return ts; // Fallback to original timestamp
            }
        });
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'System Efficiency (%)',
                    data: data.efficiency_data || [],
                    borderColor: this.theme.colors.solar,
                    backgroundColor: this.theme.colors.solar + '20',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                scales: {
                    x: {
                        title: { 
                            display: true, 
                            text: 'Time',
                            color: this.theme.colors.text,
                            font: {
                                size: 14,
                                weight: '600'
                            }
                        },
                        grid: { color: this.theme.colors.border },
                        ticks: {
                            color: this.theme.colors.text
                        }
                    },
                    y: {
                        title: { 
                            display: true, 
                            text: 'Efficiency (%)',
                            color: this.theme.colors.text,
                            font: {
                                size: 14,
                                weight: '600'
                            }
                        },
                        min: 0,
                        max: 100,
                        grid: { color: this.theme.colors.border },
                        ticks: {
                            color: this.theme.colors.text
                        }
                    }
                },
                plugins: {
                    legend: { 
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            color: this.theme.colors.text,
                            font: {
                                size: 12,
                                weight: '500'
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: this.theme.colors.background,
                        titleColor: this.theme.colors.text,
                        bodyColor: this.theme.colors.text,
                        borderColor: this.theme.colors.border,
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                }
            }
        });
        
        return this.charts[canvasId];
    }
    
    updateChartData(chartId, newData) {
        const chart = this.charts[chartId];
        if (chart && newData) {
            chart.data = newData;
            chart.update('none'); // Skip animation for real-time updates
        }
    }
    
    startRealTimeUpdates() {
        if (this.websocket) return;
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/dashboard/ws`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleRealTimeData(data);
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.websocket.onclose = () => {
            setTimeout(() => this.startRealTimeUpdates(), 5000);
        };
    }
    
    handleRealTimeData(data) {
        Object.keys(this.charts).forEach(chartId => {
            const chart = this.charts[chartId];
            if (chart && chartId.includes('live')) {
                this.addDataPoint(chart, data);
            }
        });
    }
    
    addDataPoint(chart, data) {
        const timestamp = new Date(data.timestamp).toLocaleTimeString([], {
            hour: '2-digit', 
            minute: '2-digit'
        });
        
        chart.data.labels.push(timestamp);
        chart.data.datasets[0].data.push(data.solar_power_w);
        chart.data.datasets[1].data.push(data.battery_power_w);
        chart.data.datasets[2].data.push(data.load_power_w);
        chart.data.datasets[3].data.push(data.grid_power_w);
        
        if (chart.data.labels.length > 20) {
            chart.data.labels.shift();
            chart.data.datasets.forEach(dataset => dataset.data.shift());
        }
        
        chart.update('none');
    }
    
    exportChartAsImage(chartId, filename) {
        const chart = this.charts[chartId];
        if (chart) {
            const link = document.createElement('a');
            link.download = filename || `solar-sync-chart-${Date.now()}.png`;
            link.href = chart.toBase64Image('image/png', 1.0);
            link.click();
        }
    }
    
    destroyChart(chartId) {
        if (this.charts[chartId]) {
            this.charts[chartId].destroy();
            delete this.charts[chartId];
        }
    }
    
    destroyAllCharts() {
        Object.keys(this.charts).forEach(chartId => {
            this.destroyChart(chartId);
        });
    }
}

// Global chart manager instance
window.solarChartManager = new SolarSyncChartManager();
