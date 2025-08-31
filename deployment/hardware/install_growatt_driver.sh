#!/bin/bash

# Solar Sync - Growatt USB Driver Installation Script
# This script installs the necessary drivers for Growatt USB communication on Raspberry Pi

set -e

echo "🔧 Solar Sync - Installing Growatt USB Drivers..."

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "⚠️  Warning: This script is designed for Raspberry Pi"
    echo "   It may not work correctly on other systems"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system packages
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install required packages
echo "📦 Installing required packages..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    git \
    build-essential \
    libusb-1.0-0-dev \
    pkg-config \
    cmake

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install --user pymodbus pyserial pyyaml

# Create udev rules for USB devices
echo "🔌 Creating udev rules for USB devices..."
sudo tee /etc/udev/rules.d/99-solar-sync.rules > /dev/null <<EOF
# Solar Sync USB device rules
# FTDI devices
SUBSYSTEM=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6015", MODE="0666"

# Prolific devices
SUBSYSTEM=="usb", ATTRS{idVendor}=="067b", ATTRS{idProduct}=="2303", MODE="0666"

# Silicon Labs devices
SUBSYSTEM=="usb", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666"

# CH340 devices (common in Growatt adapters)
SUBSYSTEM=="usb", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE="0666"

# Generic USB serial devices
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", MODE="0666"
SUBSYSTEM=="tty", ATTRS{idVendor}=="067b", MODE="0666"
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", MODE="0666"
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", MODE="0666"
EOF

# Reload udev rules
echo "🔄 Reloading udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger

# Create systemd service for Solar Sync
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/solar-sync.service > /dev/null <<EOF
[Unit]
Description=Solar Sync - Professional Solar Monitoring System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/solar-sync
Environment=PATH=/home/pi/solar-sync/venv/bin
ExecStart=/home/pi/solar-sync/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
echo "🚀 Enabling Solar Sync service..."
sudo systemctl daemon-reload
sudo systemctl enable solar-sync.service

# Create log directory
echo "📝 Creating log directory..."
sudo mkdir -p /var/log/solar-sync
sudo chown pi:pi /var/log/solar-sync

# Create configuration directory
echo "⚙️  Creating configuration directory..."
mkdir -p /home/pi/solar-sync/config/device_profiles

# Install Growatt-specific drivers if needed
echo "🔌 Installing Growatt-specific drivers..."
if lsusb | grep -q "1a86:7523"; then
    echo "✅ CH340 device detected - installing specific driver..."
    
    # Install CH340 driver
    git clone https://github.com/juliagoda/CH341.git /tmp/ch341
    cd /tmp/ch341
    make
    sudo make install
    cd -
    rm -rf /tmp/ch341
    
    echo "✅ CH340 driver installed"
else
    echo "ℹ️  No CH340 device detected - skipping specific driver installation"
fi

# Test USB device detection
echo "🔍 Testing USB device detection..."
echo "Available USB devices:"
lsusb | grep -E "(0403|067b|10c4|1a86)" || echo "No compatible USB devices found"

echo "Available serial ports:"
ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || echo "No serial ports found"

# Create test script
echo "🧪 Creating test script..."
tee /home/pi/solar-sync/test_hardware.py > /dev/null <<EOF
#!/usr/bin/env python3
"""
Hardware test script for Solar Sync
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from hardware.protocols.modbus_rtu import ModbusRTUScanner

async def test_hardware():
    print("🔍 Testing hardware detection...")
    
    # Scan for serial ports
    ports = ModbusRTUScanner.scan_serial_ports()
    print(f"Found {len(ports)} serial ports:")
    for port in ports:
        print(f"  - {port['port']}: {port['description']}")
    
    # Scan for RS485 adapters
    adapters = ModbusRTUScanner.find_rs485_adapters()
    print(f"Found {len(adapters)} RS485 adapters:")
    for adapter in adapters:
        print(f"  - {adapter['port']}: {adapter['name']}")
    
    # Test Modbus communication on each port
    for port in ports:
        print(f"Testing Modbus communication on {port['port']}...")
        try:
            devices = await ModbusRTUScanner.scan_modbus_devices(port['port'])
            if devices:
                print(f"  Found {len(devices)} Modbus devices:")
                for device in devices:
                    print(f"    - {device['identification']}")
            else:
                print("  No Modbus devices found")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_hardware())
EOF

chmod +x /home/pi/solar-sync/test_hardware.py

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Connect your Growatt USB adapter"
echo "2. Run: python3 /home/pi/solar-sync/test_hardware.py"
echo "3. Start Solar Sync: sudo systemctl start solar-sync"
echo "4. Check status: sudo systemctl status solar-sync"
echo "5. View logs: sudo journalctl -u solar-sync -f"
echo ""
echo "🌐 Access Solar Sync at: http://your-pi-ip:8000"
echo ""
echo "🔧 For troubleshooting, check:"
echo "   - /var/log/solar-sync/"
echo "   - sudo journalctl -u solar-sync"
echo "   - lsusb (to see USB devices)"
echo "   - ls /dev/ttyUSB* (to see serial ports)"
