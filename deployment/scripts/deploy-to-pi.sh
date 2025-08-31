#!/bin/bash

# Solar Sync - Pi Deployment Script
# Usage: ./deploy-to-pi.sh [pi-host] [pi-user]

set -e  # Exit on any error

# Configuration
PI_HOST=${1:-"pi@raspberrypi.local"}
PI_USER=${2:-"pi"}
PI_PATH="/opt/solar-sync"
PI_SERVICE="solar-sync"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if rsync is available
check_rsync() {
    if ! command -v rsync &> /dev/null; then
        log_error "rsync is not installed. Please install it first."
        exit 1
    fi
}

# Test SSH connection
test_connection() {
    log_info "Testing SSH connection to $PI_HOST..."
    if ! ssh -o ConnectTimeout=10 -o BatchMode=yes $PI_HOST "echo 'SSH connection successful'" 2>/dev/null; then
        log_error "Cannot connect to $PI_HOST. Please check:"
        log_error "1. Pi is powered on and connected to network"
        log_error "2. SSH is enabled on Pi"
        log_error "3. SSH key authentication is set up"
        log_error "4. Hostname/IP is correct"
        exit 1
    fi
    log_success "SSH connection established"
}

# Create Pi directory structure
setup_pi_environment() {
    log_info "Setting up Pi environment..."
    
    ssh $PI_HOST "
        # Create application directory
        sudo mkdir -p $PI_PATH
        sudo chown $PI_USER:$PI_USER $PI_PATH
        
        # Create data directory
        sudo mkdir -p $PI_PATH/data
        sudo chown $PI_USER:$PI_USER $PI_PATH/data
        
        # Create logs directory
        sudo mkdir -p $PI_PATH/logs
        sudo chown $PI_USER:$PI_USER $PI_PATH/logs
        
        # Create backup directory
        sudo mkdir -p $PI_PATH/backups
        sudo chown $PI_USER:$PI_USER $PI_PATH/backups
        
        log_success 'Pi directory structure created'
    "
}

# Sync code to Pi
sync_code() {
    log_info "Syncing code to Pi..."
    
    # Sync application files (excluding dev files)
    rsync -av --delete \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.pytest_cache' \
        --exclude='data/' \
        --exclude='.env*' \
        --exclude='venv/' \
        --exclude='.vscode/' \
        --exclude='*.log' \
        --exclude='.DS_Store' \
        ./ $PI_HOST:$PI_PATH/
    
    log_success "Code synced to Pi"
}

# Install Python dependencies on Pi
install_dependencies() {
    log_info "Installing Python dependencies on Pi..."
    
    ssh $PI_HOST "
        cd $PI_PATH
        
        # Check if Python 3.9+ is available
        if ! python3 --version | grep -q 'Python 3\.[9-9]\|Python 3\.[1-9][0-9]'; then
            log_warning 'Python 3.9+ not found. Installing...'
            sudo apt-get update
            sudo apt-get install -y python3.9 python3.9-venv python3.9-dev
        fi
        
        # Create virtual environment if it doesn't exist
        if [ ! -d 'venv' ]; then
            python3 -m venv venv
        fi
        
        # Activate virtual environment and install dependencies
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        
        log_success 'Python dependencies installed'
    "
}

# Install systemd service
install_service() {
    log_info "Installing systemd service..."
    
    # Create systemd service file
    cat > /tmp/solar-sync.service << EOF
[Unit]
Description=Solar Sync - Solar Monitoring System
After=network.target

[Service]
Type=exec
User=$PI_USER
Group=$PI_USER
WorkingDirectory=$PI_PATH
Environment=PATH=$PI_PATH/venv/bin
ExecStart=$PI_PATH/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    # Copy service file to Pi
    scp /tmp/solar-sync.service $PI_HOST:/tmp/
    
    # Install service on Pi
    ssh $PI_HOST "
        sudo cp /tmp/solar-sync.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable $PI_SERVICE
        
        # Clean up
        rm /tmp/solar-sync.service
        
        log_success 'Systemd service installed and enabled'
    "
    
    # Clean up local temp file
    rm /tmp/solar-sync.service
}

# Start/restart service
restart_service() {
    log_info "Restarting Solar Sync service..."
    
    ssh $PI_HOST "
        sudo systemctl restart $PI_SERVICE
        
        # Wait for startup
        sleep 5
        
        # Check service status
        if sudo systemctl is-active --quiet $PI_SERVICE; then
            log_success 'Service started successfully'
        else
            log_error 'Service failed to start'
            sudo systemctl status $PI_SERVICE
            exit 1
        fi
    "
}

# Health check
health_check() {
    log_info "Running health check..."
    
    # Wait a bit for service to fully start
    sleep 10
    
    # Test HTTP endpoint
    if curl -f -s http://$PI_HOST:8000/health > /dev/null; then
        log_success "Health check passed - Solar Sync is running"
    else
        log_error "Health check failed - Solar Sync is not responding"
        log_info "Checking service logs..."
        ssh $PI_HOST "sudo journalctl -u $PI_SERVICE -n 20"
        exit 1
    fi
}

# Show deployment summary
show_summary() {
    log_success "Deployment completed successfully!"
    echo
    echo "🌐 Access Solar Sync at: http://$PI_HOST:8000"
    echo "📊 API Documentation: http://$PI_HOST:8000/docs"
    echo "🔧 Service Status: ssh $PI_HOST 'sudo systemctl status $PI_SERVICE'"
    echo "📝 View Logs: ssh $PI_HOST 'sudo journalctl -u $PI_SERVICE -f'"
    echo
    echo "Useful commands:"
    echo "  Stop service:    ssh $PI_HOST 'sudo systemctl stop $PI_SERVICE'"
    echo "  Start service:   ssh $PI_HOST 'sudo systemctl start $PI_SERVICE'"
    echo "  Restart service: ssh $PI_HOST 'sudo systemctl restart $PI_SERVICE'"
    echo "  View logs:       ssh $PI_HOST 'sudo journalctl -u $PI_SERVICE -f'"
}

# Main deployment process
main() {
    echo "🚀 Solar Sync - Pi Deployment"
    echo "=============================="
    echo "Target: $PI_HOST"
    echo "Path: $PI_PATH"
    echo
    
    # Run deployment steps
    check_rsync
    test_connection
    setup_pi_environment
    sync_code
    install_dependencies
    install_service
    restart_service
    health_check
    show_summary
}

# Handle script arguments
case "${1:-}" in
    -h|--help)
        echo "Usage: $0 [pi-host] [pi-user]"
        echo
        echo "Examples:"
        echo "  $0 pi@192.168.1.100"
        echo "  $0 pi@raspberrypi.local"
        echo "  $0 pi@192.168.1.100 pi"
        echo
        echo "Default values:"
        echo "  pi-host: pi@raspberrypi.local"
        echo "  pi-user: pi"
        exit 0
        ;;
    *)
        main
        ;;
esac
