// Solar Sync - WebSocket Management

class WebSocketManager {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.isConnected = false;
        this.messageHandlers = new Map();
        
        // Bind methods
        this.connect = this.connect.bind(this);
        this.disconnect = this.disconnect.bind(this);
        this.reconnect = this.reconnect.bind(this);
        this.sendMessage = this.sendMessage.bind(this);
        
        // Auto-connect when page loads
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', this.connect);
        } else {
            this.connect();
        }
    }
    
    connect() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/dashboard/ws`;
            
            console.log('Connecting to WebSocket:', wsUrl);
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = (event) => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.reconnectDelay = 1000;
                this.updateConnectionStatus(true);
                
                // Send initial ping
                this.sendMessage({ type: 'ping' });
            };
            
            this.ws.onmessage = (event) => {
                this.handleMessage(event.data);
            };
            
            this.ws.onclose = (event) => {
                console.log('WebSocket disconnected:', event.code, event.reason);
                this.isConnected = false;
                this.updateConnectionStatus(false);
                
                // Attempt to reconnect if not a clean close
                if (event.code !== 1000) {
                    this.reconnect();
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.reconnect();
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close(1000, 'User disconnect');
            this.ws = null;
            this.isConnected = false;
            this.updateConnectionStatus(false);
        }
    }
    
    reconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.updateConnectionStatus(false, 'Connection failed');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        setTimeout(() => {
            if (!this.isConnected) {
                this.connect();
            }
        }, delay);
    }
    
    sendMessage(message) {
        if (this.ws && this.isConnected) {
            try {
                this.ws.send(JSON.stringify(message));
            } catch (error) {
                console.error('Failed to send WebSocket message:', error);
            }
        } else {
            console.warn('WebSocket not connected, message not sent:', message);
        }
    }
    
    handleMessage(data) {
        try {
            const message = JSON.parse(data);
            console.log('WebSocket message received:', message);
            
            // Handle different message types
            switch (message.type) {
                case 'energy_data':
                    this.handleEnergyData(message.data);
                    break;
                case 'pong':
                    // Handle pong response
                    break;
                case 'system_event':
                    this.handleSystemEvent(message.data);
                    break;
                default:
                    console.log('Unknown message type:', message.type);
            }
            
            // Call registered handlers
            if (this.messageHandlers.has(message.type)) {
                this.messageHandlers.get(message.type).forEach(handler => {
                    try {
                        handler(message.data);
                    } catch (error) {
                        console.error('Error in message handler:', error);
                    }
                });
            }
            
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    }
    
    handleEnergyData(data) {
        // Update dashboard metrics in real-time
        if (window.SolarSync && window.SolarSync.updateMetrics) {
            window.SolarSync.updateMetrics(data);
        }
        
        // Update chart if available
        if (window.SolarSync && window.SolarSync.updateChart) {
            window.SolarSync.updateChart(data);
        }
        
        // Update last update time
        this.updateLastUpdate();
        
        // Trigger custom event for other components
        const event = new CustomEvent('energyDataUpdate', { detail: data });
        document.dispatchEvent(event);
    }
    
    handleSystemEvent(data) {
        // Add system event to events list
        this.addSystemEvent(data);
        
        // Trigger custom event for other components
        const event = new CustomEvent('systemEvent', { detail: data });
        document.dispatchEvent(event);
    }
    
    addSystemEvent(eventData) {
        const eventsList = document.getElementById('events-list');
        if (!eventsList) return;
        
        const eventItem = document.createElement('div');
        eventItem.className = 'event-item fade-in';
        
        const iconClass = this.getEventIconClass(eventData.severity);
        const icon = this.getEventIcon(eventData.severity);
        
        eventItem.innerHTML = `
            <div class="event-icon ${iconClass}">
                <i class="fas ${icon}"></i>
            </div>
            <div class="event-content">
                <div class="event-message">${eventData.message}</div>
                <div class="event-time">${this.formatEventTime(eventData.timestamp)}</div>
            </div>
        `;
        
        // Add to top of list
        eventsList.insertBefore(eventItem, eventsList.firstChild);
        
        // Keep only last 10 events
        const events = eventsList.querySelectorAll('.event-item');
        if (events.length > 10) {
            events[events.length - 1].remove();
        }
    }
    
    getEventIconClass(severity) {
        switch (severity) {
            case 'critical':
            case 'error':
                return 'error';
            case 'warning':
                return 'warning';
            case 'success':
                return 'success';
            default:
                return 'info';
        }
    }
    
    getEventIcon(severity) {
        switch (severity) {
            case 'critical':
            case 'error':
                return 'fa-exclamation-triangle';
            case 'warning':
                return 'fa-exclamation-circle';
            case 'success':
                return 'fa-check-circle';
            default:
                return 'fa-info-circle';
        }
    }
    
    formatEventTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) {
            return 'Just now';
        } else if (diffMins < 60) {
            return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        } else {
            return date.toLocaleTimeString();
        }
    }
    
    updateConnectionStatus(connected, message = null) {
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');
        
        if (statusDot) {
            statusDot.className = `status-dot ${connected ? 'online' : 'offline'}`;
        }
        
        if (statusText) {
            statusText.textContent = connected ? 'System Online' : (message || 'System Offline');
        }
        
        // Trigger custom event
        const event = new CustomEvent('connectionStatusChange', { 
            detail: { connected, message } 
        });
        document.dispatchEvent(event);
    }
    
    updateLastUpdate() {
        const lastUpdateElement = document.getElementById('last-update');
        if (lastUpdateElement) {
            const now = new Date();
            lastUpdateElement.textContent = now.toLocaleTimeString();
        }
    }
    
    // Register message handlers
    on(messageType, handler) {
        if (!this.messageHandlers.has(messageType)) {
            this.messageHandlers.set(messageType, []);
        }
        this.messageHandlers.get(messageType).push(handler);
    }
    
    // Remove message handlers
    off(messageType, handler) {
        if (this.messageHandlers.has(messageType)) {
            const handlers = this.messageHandlers.get(messageType);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }
}

// Create global WebSocket manager instance
window.wsManager = new WebSocketManager();

// Export for use in other modules
window.WebSocketManager = WebSocketManager;
