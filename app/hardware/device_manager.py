"""
Central device manager for hardware communication.
Coordinates device discovery, connection management, and data collection.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import yaml
import os

from .drivers.base_driver import BaseDriver, DeviceInfo, DeviceData, DeviceStatus, DeviceType
from .protocols.modbus_rtu import ModbusRTUScanner
from .simulation.simulator import SimulationDriver

logger = logging.getLogger(__name__)


class DeviceManager:
    """Central manager for all hardware devices."""
    
    def __init__(self):
        self.devices: Dict[str, BaseDriver] = {}
        self.simulation_mode = False
        self.scan_interval = 30  # seconds
        self.data_interval = 5   # seconds
        self.last_scan = None
        self.scanning = False
        self.running = False
        
        # Load device profiles
        self.device_profiles = self._load_device_profiles()
        
    def _load_device_profiles(self) -> Dict[str, Any]:
        """Load device profiles from YAML files."""
        profiles = {}
        profiles_dir = "config/device_profiles"
        
        if os.path.exists(profiles_dir):
            for filename in os.listdir(profiles_dir):
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    profile_path = os.path.join(profiles_dir, filename)
                    try:
                        with open(profile_path, 'r') as f:
                            profile = yaml.safe_load(f)
                            device_type = profile.get('device', {}).get('type', 'unknown')
                            profiles[device_type] = profile
                            logger.info(f"Loaded device profile: {device_type}")
                    except Exception as e:
                        logger.error(f"Failed to load device profile {filename}: {e}")
        
        return profiles
    
    async def start(self) -> None:
        """Start the device manager."""
        logger.info("Starting device manager...")
        self.running = True
        
        # Initial device scan
        await self.scan_devices()
        
        # Start background tasks
        asyncio.create_task(self._scan_loop())
        asyncio.create_task(self._data_collection_loop())
        
        logger.info("Device manager started")
    
    async def stop(self) -> None:
        """Stop the device manager."""
        logger.info("Stopping device manager...")
        self.running = False
        
        # Disconnect all devices
        for device in self.devices.values():
            await device.disconnect()
        
        self.devices.clear()
        logger.info("Device manager stopped")
    
    async def scan_devices(self) -> Dict[str, Any]:
        """Scan for available devices."""
        if self.scanning:
            return {"status": "scanning", "devices": []}
        
        self.scanning = True
        logger.info("Starting device scan...")
        
        try:
            # Scan for RS485 adapters
            rs485_adapters = ModbusRTUScanner.find_rs485_adapters()
            logger.info(f"Found {len(rs485_adapters)} RS485 adapters")
            
            found_devices = []
            
            # Scan each adapter for Modbus devices
            for adapter in rs485_adapters:
                port = adapter["port"]
                logger.info(f"Scanning adapter: {adapter['name']} on {port}")
                
                # Scan for Modbus devices
                modbus_devices = await ModbusRTUScanner.scan_modbus_devices(port)
                
                for device in modbus_devices:
                    device_info = {
                        "adapter": adapter,
                        "modbus_device": device,
                        "port": port,
                        "baudrate": device.get("baudrate"),
                        "slave_id": device.get("slave_id"),
                        "identification": device.get("identification", "Unknown")
                    }
                    found_devices.append(device_info)
            
            # If no real devices found, enable simulation mode
            if not found_devices:
                logger.info("No real devices found, enabling simulation mode")
                await self._enable_simulation_mode()
            else:
                logger.info(f"Found {len(found_devices)} devices")
                await self._connect_to_devices(found_devices)
            
            self.last_scan = datetime.now()
            return {
                "status": "completed",
                "devices": found_devices,
                "simulation_mode": self.simulation_mode
            }
            
        except Exception as e:
            logger.error(f"Device scan failed: {e}")
            await self._enable_simulation_mode()
            return {
                "status": "error",
                "error": str(e),
                "simulation_mode": self.simulation_mode
            }
        finally:
            self.scanning = False
    
    async def _enable_simulation_mode(self) -> None:
        """Enable simulation mode when no real devices are found."""
        self.simulation_mode = True
        
        # Create simulation device
        device_info = DeviceInfo(
            name="Solar Sync Simulator",
            manufacturer="Solar Sync",
            model="Simulation Device",
            serial_number="SIM-001",
            firmware_version="1.0.0",
            device_type=DeviceType.SIMULATION,
            protocol="simulation",
            connection_string="simulation://localhost"
        )
        
        simulator = SimulationDriver(device_info)
        self.devices["simulator"] = simulator
        
        # Connect simulator
        await simulator.connect()
        logger.info("Simulation mode enabled")
    
    async def _connect_to_devices(self, found_devices: List[Dict[str, Any]]) -> None:
        """Connect to discovered devices."""
        for device_info in found_devices:
            try:
                # Try to identify device type and create appropriate driver
                driver = await self._create_driver(device_info)
                if driver:
                    device_id = f"{device_info['port']}_{device_info['slave_id']}"
                    self.devices[device_id] = driver
                    
                    # Connect to device
                    if await driver.connect():
                        logger.info(f"Connected to device: {driver.device_info.name}")
                    else:
                        logger.error(f"Failed to connect to device: {driver.device_info.name}")
                        
            except Exception as e:
                logger.error(f"Error creating driver for device: {e}")
    
    async def _create_driver(self, device_info: Dict[str, Any]) -> Optional[BaseDriver]:
        """Create appropriate driver for discovered device."""
        try:
            # Try to identify device type from identification
            identification = device_info.get("identification", "").lower()
            
            if "growatt" in identification or "spf" in identification:
                from .drivers.growatt.spf_series import GrowattSPFDriver
                return await self._create_growatt_driver(device_info)
            elif "deye" in identification or "sun" in identification:
                from .drivers.deye.sun_series import DeyeSunDriver
                return await self._create_deye_driver(device_info)
            elif "sma" in identification or "sunny" in identification:
                from .drivers.sma.sunnyboy import SMASunnyBoyDriver
                return await self._create_sma_driver(device_info)
            else:
                # Try generic Modbus driver
                from .drivers.generic.modbus_driver import GenericModbusDriver
                return await self._create_generic_driver(device_info)
                
        except Exception as e:
            logger.error(f"Error creating driver: {e}")
            return None
    
    async def _create_growatt_driver(self, device_info: Dict[str, Any]) -> Optional[BaseDriver]:
        """Create Growatt driver."""
        try:
            from .drivers.growatt.spf_series import GrowattSPFDriver
            
            driver_info = DeviceInfo(
                name=f"Growatt SPF Series",
                manufacturer="Growatt",
                model="SPF Series",
                serial_number=device_info.get("identification", "Unknown"),
                firmware_version="Unknown",
                device_type=DeviceType.GROWATT_SPF,
                protocol="modbus_rtu",
                connection_string=f"{device_info['port']}:{device_info['baudrate']}:{device_info['slave_id']}"
            )
            
            return GrowattSPFDriver(driver_info)
        except ImportError:
            logger.warning("Growatt driver not available")
            return None
    
    async def _create_deye_driver(self, device_info: Dict[str, Any]) -> Optional[BaseDriver]:
        """Create Deye driver."""
        try:
            from .drivers.deye.sun_series import DeyeSunDriver
            
            driver_info = DeviceInfo(
                name=f"Deye SUN Series",
                manufacturer="Deye",
                model="SUN Series",
                serial_number=device_info.get("identification", "Unknown"),
                firmware_version="Unknown",
                device_type=DeviceType.DEYE_SUN,
                protocol="modbus_rtu",
                connection_string=f"{device_info['port']}:{device_info['baudrate']}:{device_info['slave_id']}"
            )
            
            return DeyeSunDriver(driver_info)
        except ImportError:
            logger.warning("Deye driver not available")
            return None
    
    async def _create_sma_driver(self, device_info: Dict[str, Any]) -> Optional[BaseDriver]:
        """Create SMA driver."""
        try:
            from .drivers.sma.sunnyboy import SMASunnyBoyDriver
            
            driver_info = DeviceInfo(
                name=f"SMA Sunny Boy",
                manufacturer="SMA",
                model="Sunny Boy",
                serial_number=device_info.get("identification", "Unknown"),
                firmware_version="Unknown",
                device_type=DeviceType.SMA_SUNNYBOY,
                protocol="modbus_rtu",
                connection_string=f"{device_info['port']}:{device_info['baudrate']}:{device_info['slave_id']}"
            )
            
            return SMASunnyBoyDriver(driver_info)
        except ImportError:
            logger.warning("SMA driver not available")
            return None
    
    async def _create_generic_driver(self, device_info: Dict[str, Any]) -> Optional[BaseDriver]:
        """Create generic Modbus driver."""
        try:
            from .drivers.generic.modbus_driver import GenericModbusDriver
            
            driver_info = DeviceInfo(
                name=f"Generic Modbus Device",
                manufacturer="Unknown",
                model="Modbus Device",
                serial_number=device_info.get("identification", "Unknown"),
                firmware_version="Unknown",
                device_type=DeviceType.GENERIC_MODBUS,
                protocol="modbus_rtu",
                connection_string=f"{device_info['port']}:{device_info['baudrate']}:{device_info['slave_id']}"
            )
            
            return GenericModbusDriver(driver_info)
        except ImportError:
            logger.warning("Generic Modbus driver not available")
            return None
    
    async def _scan_loop(self) -> None:
        """Background task for periodic device scanning."""
        while self.running:
            try:
                await asyncio.sleep(self.scan_interval)
                
                # Only scan if we have no devices or all devices are disconnected
                if not self.devices or all(d.status == DeviceStatus.DISCONNECTED for d in self.devices.values()):
                    await self.scan_devices()
                    
            except Exception as e:
                logger.error(f"Error in scan loop: {e}")
    
    async def _data_collection_loop(self) -> None:
        """Background task for data collection."""
        while self.running:
            try:
                await asyncio.sleep(self.data_interval)
                
                # Collect data from all connected devices
                for device_id, device in self.devices.items():
                    try:
                        if device.status == DeviceStatus.CONNECTED:
                            data = await device.read_data()
                            if data:
                                device.last_data = data
                        elif device.status == DeviceStatus.ERROR:
                            # Try to reconnect
                            await device.auto_reconnect()
                            
                    except Exception as e:
                        logger.error(f"Error reading data from {device_id}: {e}")
                        
            except Exception as e:
                logger.error(f"Error in data collection loop: {e}")
    
    def get_device_status(self) -> Dict[str, Any]:
        """Get status of all devices."""
        devices = {}
        for device_id, device in self.devices.items():
            devices[device_id] = device.get_status_summary()
        
        return {
            "simulation_mode": self.simulation_mode,
            "total_devices": len(self.devices),
            "connected_devices": sum(1 for d in self.devices.values() if d.status == DeviceStatus.CONNECTED),
            "devices": devices,
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "scanning": self.scanning
        }
    
    def get_latest_data(self) -> Optional[DeviceData]:
        """Get latest data from any connected device."""
        latest_data = None
        latest_timestamp = 0
        
        for device in self.devices.values():
            if device.last_data and device.last_data.timestamp > latest_timestamp:
                latest_data = device.last_data
                latest_timestamp = device.last_data.timestamp
        
        return latest_data
    
    async def write_control(self, device_id: str, control_data: Dict[str, Any]) -> bool:
        """Write control settings to a specific device."""
        if device_id not in self.devices:
            logger.error(f"Device {device_id} not found")
            return False
        
        device = self.devices[device_id]
        if device.status != DeviceStatus.CONNECTED:
            logger.error(f"Device {device_id} is not connected")
            return False
        
        try:
            # Convert control data to DeviceControl object
            from .drivers.base_driver import DeviceControl
            control = DeviceControl(
                output_priority=control_data.get("output_priority", "solar"),
                battery_charge_limit=control_data.get("battery_charge_limit", 100.0),
                battery_discharge_limit=control_data.get("battery_discharge_limit", 0.0),
                grid_export_limit=control_data.get("grid_export_limit", 0.0),
                emergency_power=control_data.get("emergency_power", False)
            )
            
            return await device.write_control(control)
            
        except Exception as e:
            logger.error(f"Error writing control to {device_id}: {e}")
            return False


# Global device manager instance
device_manager = DeviceManager()
