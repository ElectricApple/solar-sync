// Solar Sync - Utility Functions

// Date and time utilities
const Utils = {
    // Format date for display
    formatDate(date, format = 'short') {
        const d = new Date(date);
        
        switch (format) {
            case 'short':
                return d.toLocaleDateString();
            case 'long':
                return d.toLocaleDateString('en-US', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });
            case 'time':
                return d.toLocaleTimeString();
            case 'datetime':
                return d.toLocaleString();
            case 'iso':
                return d.toISOString();
            default:
                return d.toString();
        }
    },
    
    // Format relative time
    formatRelativeTime(date) {
        const now = new Date();
        const diff = now - new Date(date);
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (days > 0) {
            return `${days} day${days > 1 ? 's' : ''} ago`;
        } else if (hours > 0) {
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else if (minutes > 0) {
            return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else {
            return 'Just now';
        }
    },
    
    // Format power values
    formatPower(watts, decimals = 1) {
        if (watts === null || watts === undefined) return '--';
        
        if (watts >= 1000000) {
            return (watts / 1000000).toFixed(decimals) + ' MW';
        } else if (watts >= 1000) {
            return (watts / 1000).toFixed(decimals) + ' kW';
        } else {
            return watts.toFixed(0) + ' W';
        }
    },
    
    // Format energy values
    formatEnergy(wattHours, decimals = 2) {
        if (wattHours === null || wattHours === undefined) return '--';
        
        if (wattHours >= 1000000) {
            return (wattHours / 1000000).toFixed(decimals) + ' MWh';
        } else if (wattHours >= 1000) {
            return (wattHours / 1000).toFixed(decimals) + ' kWh';
        } else {
            return wattHours.toFixed(0) + ' Wh';
        }
    },
    
    // Format percentage
    formatPercentage(value, decimals = 1) {
        if (value === null || value === undefined) return '--';
        return value.toFixed(decimals) + '%';
    },
    
    // Format temperature
    formatTemperature(celsius, unit = 'C') {
        if (celsius === null || celsius === undefined) return '--';
        
        switch (unit.toUpperCase()) {
            case 'F':
                const fahrenheit = (celsius * 9/5) + 32;
                return fahrenheit.toFixed(1) + '°F';
            case 'K':
                const kelvin = celsius + 273.15;
                return kelvin.toFixed(1) + 'K';
            default:
                return celsius.toFixed(1) + '°C';
        }
    },
    
    // Format voltage
    formatVoltage(volts, decimals = 1) {
        if (volts === null || volts === undefined) return '--';
        return volts.toFixed(decimals) + ' V';
    },
    
    // Format current
    formatCurrent(amps, decimals = 2) {
        if (amps === null || amps === undefined) return '--';
        return amps.toFixed(decimals) + ' A';
    },
    
    // Color utilities
    colors: {
        // Get color based on battery SOC
        getBatteryColor(soc) {
            if (soc >= 80) return '#28A745'; // Green
            if (soc >= 50) return '#FFC107'; // Yellow
            if (soc >= 20) return '#FD7E14'; // Orange
            return '#DC3545'; // Red
        },
        
        // Get color based on power flow
        getPowerColor(power) {
            if (power > 0) return '#28A745'; // Green (generating/charging)
            if (power < 0) return '#DC3545'; // Red (consuming/discharging)
            return '#6C757D'; // Gray (neutral)
        },
        
        // Get color based on temperature
        getTemperatureColor(temp) {
            if (temp < 30) return '#28A745'; // Green (cool)
            if (temp < 50) return '#FFC107'; // Yellow (warm)
            if (temp < 70) return '#FD7E14'; // Orange (hot)
            return '#DC3545'; // Red (very hot)
        },
        
        // Get color based on efficiency
        getEfficiencyColor(efficiency) {
            if (efficiency >= 90) return '#28A745'; // Green
            if (efficiency >= 80) return '#FFC107'; // Yellow
            if (efficiency >= 70) return '#FD7E14'; // Orange
            return '#DC3545'; // Red
        }
    },
    
    // Validation utilities
    validation: {
        // Check if value is numeric
        isNumeric(value) {
            return !isNaN(parseFloat(value)) && isFinite(value);
        },
        
        // Check if value is in range
        isInRange(value, min, max) {
            return this.isNumeric(value) && value >= min && value <= max;
        },
        
        // Validate email
        isValidEmail(email) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        },
        
        // Validate URL
        isValidUrl(url) {
            try {
                new URL(url);
                return true;
            } catch {
                return false;
            }
        }
    },
    
    // Storage utilities
    storage: {
        // Set item in localStorage
        set(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (error) {
                console.error('Failed to save to localStorage:', error);
                return false;
            }
        },
        
        // Get item from localStorage
        get(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (error) {
                console.error('Failed to read from localStorage:', error);
                return defaultValue;
            }
        },
        
        // Remove item from localStorage
        remove(key) {
            try {
                localStorage.removeItem(key);
                return true;
            } catch (error) {
                console.error('Failed to remove from localStorage:', error);
                return false;
            }
        },
        
        // Clear all localStorage
        clear() {
            try {
                localStorage.clear();
                return true;
            } catch (error) {
                console.error('Failed to clear localStorage:', error);
                return false;
            }
        }
    },
    
    // DOM utilities
    dom: {
        // Create element with attributes
        createElement(tag, attributes = {}, children = []) {
            const element = document.createElement(tag);
            
            // Set attributes
            Object.entries(attributes).forEach(([key, value]) => {
                if (key === 'className') {
                    element.className = value;
                } else if (key === 'textContent') {
                    element.textContent = value;
                } else if (key === 'innerHTML') {
                    element.innerHTML = value;
                } else {
                    element.setAttribute(key, value);
                }
            });
            
            // Add children
            children.forEach(child => {
                if (typeof child === 'string') {
                    element.appendChild(document.createTextNode(child));
                } else {
                    element.appendChild(child);
                }
            });
            
            return element;
        },
        
        // Add event listener with error handling
        addEventListener(element, event, handler, options = {}) {
            if (element && typeof handler === 'function') {
                element.addEventListener(event, handler, options);
                return true;
            }
            return false;
        },
        
        // Remove event listener
        removeEventListener(element, event, handler, options = {}) {
            if (element && typeof handler === 'function') {
                element.removeEventListener(event, handler, options);
                return true;
            }
            return false;
        },
        
        // Show/hide elements
        show(element) {
            if (element) {
                element.style.display = '';
                element.classList.remove('d-none');
            }
        },
        
        hide(element) {
            if (element) {
                element.style.display = 'none';
                element.classList.add('d-none');
            }
        },
        
        // Toggle element visibility
        toggle(element) {
            if (element) {
                if (element.style.display === 'none' || element.classList.contains('d-none')) {
                    this.show(element);
                } else {
                    this.hide(element);
                }
            }
        }
    },
    
    // Network utilities
    network: {
        // Check if online
        isOnline() {
            return navigator.onLine;
        },
        
        // Add online/offline listeners
        addConnectionListeners(onlineHandler, offlineHandler) {
            window.addEventListener('online', onlineHandler);
            window.addEventListener('offline', offlineHandler);
        },
        
        // Remove online/offline listeners
        removeConnectionListeners(onlineHandler, offlineHandler) {
            window.removeEventListener('online', onlineHandler);
            window.removeEventListener('offline', offlineHandler);
        },
        
        // Debounce function calls
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        // Throttle function calls
        throttle(func, limit) {
            let inThrottle;
            return function() {
                const args = arguments;
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        }
    },
    
    // Math utilities
    math: {
        // Round to specified decimals
        round(value, decimals = 2) {
            return Math.round(value * Math.pow(10, decimals)) / Math.pow(10, decimals);
        },
        
        // Calculate percentage
        percentage(value, total) {
            if (total === 0) return 0;
            return (value / total) * 100;
        },
        
        // Clamp value between min and max
        clamp(value, min, max) {
            return Math.min(Math.max(value, min), max);
        },
        
        // Linear interpolation
        lerp(start, end, factor) {
            return start + (end - start) * factor;
        },
        
        // Convert watts to kilowatts
        wattsToKilowatts(watts) {
            return watts / 1000;
        },
        
        // Convert kilowatts to watts
        kilowattsToWatts(kilowatts) {
            return kilowatts * 1000;
        },
        
        // Calculate efficiency
        calculateEfficiency(input, output) {
            if (input === 0) return 0;
            return (output / input) * 100;
        }
    }
};

// Export utilities globally
window.Utils = Utils;

// Export for use in other modules
window.SolarSyncUtils = Utils;
