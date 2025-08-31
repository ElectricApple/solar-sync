"""
Base driver interface for hardware communication.
All device drivers must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class DeviceStatus(Enum):
    """Device connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    SIMULATION = "simulation"


class DeviceType(Enum):
    """Supported device types."""
    GROWATT_SPF = "growatt_spf"
    DEYE_SUN = "deye_sun"
    SMA_SUNNYBOY = "sma_sunnyboy"
    FRONIUS_SYMO = "fronius_symo"
    GENERIC_MODBUS = "generic_modbus"
    SIMULATION = "simulation"


@dataclass
class DeviceInfo:
    """Device information."""
    name: str
    manufacturer: str
    model: str
    serial_number: str
    firmware_version: str
    device_type: DeviceType
    protocol: str
    connection_string: str


@dataclass
class DeviceData:
    """Real-time device data."""
    timestamp: float
    solar_power_w: float
    battery_power_w: float
    load_power_w: float
    grid_power_w: float
    battery_soc_percent: float
    battery_voltage_v: float
    system_efficiency_percent: float
    temperature_c: float
    device_status: DeviceStatus
    error_code: Optional[str] = None


@dataclass
class DeviceControl:
    """Device control settings."""
    output_priority: str  # "solar", "battery", "grid"
    battery_charge_limit: float  # 0-100%
    battery_discharge_limit: float  # 0-100%
    grid_export_limit: float  # W
    emergency_power: bool  # Enable/disable


class BaseDriver(ABC):
    """Abstract base class for all device drivers."""
    
    def __init__(self, device_info: DeviceInfo):
        self.device_info = device_info
        self.status = DeviceStatus.DISCONNECTED
        self.last_data: Optional[DeviceData] = None
        self.last_error: Optional[str] = None
        self.connection_attempts = 0
        self.max_retries = 3
        
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the device."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the device."""
        pass
    
    @abstractmethod
    async def read_data(self) -> Optional[DeviceData]:
        """Read current device data."""
        pass
    
    @abstractmethod
    async def write_control(self, control: DeviceControl) -> bool:
        """Write control settings to device."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if device is responding."""
        pass
    
    @abstractmethod
    async def get_device_info(self) -> DeviceInfo:
        """Get detailed device information."""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check and return status."""
        try:
            is_connected = await self.test_connection()
            if is_connected:
                self.status = DeviceStatus.CONNECTED
                self.last_error = None
                return {
                    "status": "healthy",
                    "connected": True,
                    "last_error": None,
                    "connection_attempts": self.connection_attempts
                }
            else:
                self.status = DeviceStatus.ERROR
                return {
                    "status": "unhealthy",
                    "connected": False,
                    "last_error": "Device not responding",
                    "connection_attempts": self.connection_attempts
                }
        except Exception as e:
            self.status = DeviceStatus.ERROR
            self.last_error = str(e)
            logger.error(f"Health check failed for {self.device_info.name}: {e}")
            return {
                "status": "error",
                "connected": False,
                "last_error": str(e),
                "connection_attempts": self.connection_attempts
            }
    
    async def auto_reconnect(self) -> bool:
        """Attempt to reconnect if disconnected."""
        if self.status in [DeviceStatus.CONNECTED, DeviceStatus.CONNECTING]:
            return True
            
        if self.connection_attempts >= self.max_retries:
            logger.warning(f"Max reconnection attempts reached for {self.device_info.name}")
            return False
            
        logger.info(f"Attempting to reconnect to {self.device_info.name}")
        self.status = DeviceStatus.CONNECTING
        self.connection_attempts += 1
        
        try:
            success = await self.connect()
            if success:
                self.status = DeviceStatus.CONNECTED
                self.connection_attempts = 0
                logger.info(f"Successfully reconnected to {self.device_info.name}")
                return True
            else:
                self.status = DeviceStatus.ERROR
                logger.error(f"Failed to reconnect to {self.device_info.name}")
                return False
        except Exception as e:
            self.status = DeviceStatus.ERROR
            self.last_error = str(e)
            logger.error(f"Reconnection error for {self.device_info.name}: {e}")
            return False
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get device status summary."""
        return {
            "name": self.device_info.name,
            "manufacturer": self.device_info.manufacturer,
            "model": self.device_info.model,
            "status": self.status.value,
            "connected": self.status == DeviceStatus.CONNECTED,
            "last_error": self.last_error,
            "connection_attempts": self.connection_attempts,
            "last_data": self.last_data.timestamp if self.last_data else None,
            "protocol": self.device_info.protocol,
            "connection_string": self.device_info.connection_string
        }
