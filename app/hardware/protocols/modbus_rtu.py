"""
Modbus RTU protocol handler for serial communication with inverters.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException, ConnectionException
from pymodbus.pdu import ExceptionResponse
import serial.tools.list_ports

logger = logging.getLogger(__name__)


class ModbusRTUClient:
    """Modbus RTU client for serial communication."""
    
    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.client: Optional[ModbusSerialClient] = None
        self.connected = False
        
    async def connect(self) -> bool:
        """Connect to the Modbus device."""
        try:
            self.client = ModbusSerialClient(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                retries=3,
                retry_on_empty=True
            )
            
            # Test connection
            if self.client.connect():
                self.connected = True
                logger.info(f"Connected to Modbus RTU device on {self.port}")
                return True
            else:
                logger.error(f"Failed to connect to Modbus RTU device on {self.port}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to Modbus RTU device on {self.port}: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from the Modbus device."""
        if self.client and self.connected:
            self.client.close()
            self.connected = False
            logger.info(f"Disconnected from Modbus RTU device on {self.port}")
    
    async def read_holding_registers(self, slave_id: int, address: int, count: int) -> Optional[List[int]]:
        """Read holding registers."""
        if not self.connected or not self.client:
            logger.error("Not connected to Modbus device")
            return None
            
        try:
            result = self.client.read_holding_registers(address, count, slave=slave_id)
            if result.isError():
                logger.error(f"Modbus read error: {result}")
                return None
            return result.registers
        except Exception as e:
            logger.error(f"Error reading holding registers: {e}")
            return None
    
    async def read_input_registers(self, slave_id: int, address: int, count: int) -> Optional[List[int]]:
        """Read input registers."""
        if not self.connected or not self.client:
            logger.error("Not connected to Modbus device")
            return None
            
        try:
            result = self.client.read_input_registers(address, count, slave=slave_id)
            if result.isError():
                logger.error(f"Modbus read error: {result}")
                return None
            return result.registers
        except Exception as e:
            logger.error(f"Error reading input registers: {e}")
            return None
    
    async def write_register(self, slave_id: int, address: int, value: int) -> bool:
        """Write a single register."""
        if not self.connected or not self.client:
            logger.error("Not connected to Modbus device")
            return False
            
        try:
            result = self.client.write_register(address, value, slave=slave_id)
            if result.isError():
                logger.error(f"Modbus write error: {result}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error writing register: {e}")
            return False
    
    async def write_registers(self, slave_id: int, address: int, values: List[int]) -> bool:
        """Write multiple registers."""
        if not self.connected or not self.client:
            logger.error("Not connected to Modbus device")
            return False
            
        try:
            result = self.client.write_registers(address, values, slave=slave_id)
            if result.isError():
                logger.error(f"Modbus write error: {result}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error writing registers: {e}")
            return False
    
    async def test_connection(self, slave_id: int = 1) -> bool:
        """Test if device is responding."""
        if not self.connected or not self.client:
            return False
            
        try:
            # Try to read a single register to test connection
            result = await self.read_holding_registers(slave_id, 0, 1)
            return result is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


class ModbusRTUScanner:
    """Scanner for Modbus RTU devices."""
    
    @staticmethod
    def scan_serial_ports() -> List[Dict[str, Any]]:
        """Scan for available serial ports."""
        ports = []
        for port in serial.tools.list_ports.comports():
            port_info = {
                "port": port.device,
                "description": port.description,
                "manufacturer": port.manufacturer,
                "product": port.product,
                "vid": port.vid,
                "pid": port.pid,
                "serial_number": port.serial_number
            }
            ports.append(port_info)
            logger.info(f"Found serial port: {port.device} - {port.description}")
        return ports
    
    @staticmethod
    def find_rs485_adapters() -> List[Dict[str, Any]]:
        """Find RS485 adapters by common VID/PID combinations."""
        rs485_adapters = []
        common_adapters = [
            # FTDI
            {"vid": 0x0403, "pid": 0x6001, "name": "FTDI FT232R"},
            {"vid": 0x0403, "pid": 0x6015, "name": "FTDI FT231X"},
            # Prolific
            {"vid": 0x067B, "pid": 0x2303, "name": "Prolific PL2303"},
            # Silicon Labs
            {"vid": 0x10C4, "pid": 0xEA60, "name": "Silicon Labs CP210x"},
            # CH340
            {"vid": 0x1A86, "pid": 0x7523, "name": "CH340"},
            # Growatt USB adapter
            {"vid": 0x1A86, "pid": 0x7523, "name": "Growatt USB Adapter"},
        ]
        
        for port in serial.tools.list_ports.comports():
            for adapter in common_adapters:
                if port.vid == adapter["vid"] and port.pid == adapter["pid"]:
                    rs485_adapters.append({
                        "port": port.device,
                        "description": port.description,
                        "name": adapter["name"],
                        "vid": port.vid,
                        "pid": port.pid,
                        "serial_number": port.serial_number
                    })
                    logger.info(f"Found RS485 adapter: {port.device} - {adapter['name']}")
                    break
        
        return rs485_adapters
    
    @staticmethod
    async def scan_modbus_devices(port: str, baudrates: List[int] = None, slave_ids: List[int] = None) -> List[Dict[str, Any]]:
        """Scan for Modbus devices on a specific port."""
        if baudrates is None:
            baudrates = [9600, 19200, 38400, 57600, 115200]
        if slave_ids is None:
            slave_ids = list(range(1, 248))  # Standard Modbus slave ID range
        
        found_devices = []
        
        for baudrate in baudrates:
            logger.info(f"Scanning {port} at {baudrate} baud")
            client = ModbusRTUClient(port, baudrate)
            
            if await client.connect():
                for slave_id in slave_ids:
                    try:
                        # Try to read device identification
                        if await client.test_connection(slave_id):
                            # Try to read some common identification registers
                            device_info = await ModbusRTUScanner._identify_device(client, slave_id)
                            if device_info:
                                device_info["port"] = port
                                device_info["baudrate"] = baudrate
                                device_info["slave_id"] = slave_id
                                found_devices.append(device_info)
                                logger.info(f"Found Modbus device: {device_info}")
                                break  # Found a device on this baudrate, move to next
                    except Exception as e:
                        continue
                
                await client.disconnect()
        
        return found_devices
    
    @staticmethod
    async def _identify_device(client: ModbusRTUClient, slave_id: int) -> Optional[Dict[str, Any]]:
        """Try to identify the device type by reading identification registers."""
        try:
            # Try to read device identification registers (standard Modbus function 43)
            # This is a simplified approach - real identification would be more complex
            
            # Try common identification registers
            identification_registers = [
                (0x0000, 10),  # Common device info
                (0x0100, 10),  # Alternative location
                (0x0200, 10),  # Another common location
            ]
            
            for addr, count in identification_registers:
                try:
                    registers = await client.read_holding_registers(slave_id, addr, count)
                    if registers and any(reg != 0 for reg in registers):
                        # Try to decode as ASCII
                        try:
                            ascii_str = ''.join([chr(reg) for reg in registers if 32 <= reg <= 126])
                            if len(ascii_str) > 3:  # Reasonable length
                                return {
                                    "type": "modbus_device",
                                    "identification": ascii_str.strip(),
                                    "registers": registers[:5]  # First 5 registers for debugging
                                }
                        except:
                            pass
                        
                        # Return raw data if ASCII decode fails
                        return {
                            "type": "modbus_device",
                            "identification": f"Unknown device (registers: {registers[:5]})",
                            "registers": registers[:5]
                        }
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Device identification failed for slave {slave_id}: {e}")
            return None
