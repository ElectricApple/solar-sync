"""
Hardware communication API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, List, Any, Optional
import logging

from ..hardware.device_manager import device_manager
from ..hardware.drivers.base_driver import DeviceStatus, DeviceType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hardware", tags=["hardware"])


@router.get("/status")
async def get_hardware_status():
    """Get overall hardware status."""
    try:
        status = device_manager.get_device_status()
        return {
            "status": "success",
            "data": status
        }
    except Exception as e:
        logger.error(f"Error getting hardware status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan")
async def scan_devices(background_tasks: BackgroundTasks):
    """Scan for available devices."""
    try:
        # Start scan in background
        background_tasks.add_task(device_manager.scan_devices)
        
        return {
            "status": "scanning",
            "message": "Device scan started"
        }
    except Exception as e:
        logger.error(f"Error starting device scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scan/status")
async def get_scan_status():
    """Get current scan status."""
    try:
        return {
            "status": "success",
            "scanning": device_manager.scanning,
            "last_scan": device_manager.last_scan.isoformat() if device_manager.last_scan else None
        }
    except Exception as e:
        logger.error(f"Error getting scan status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices")
async def get_devices():
    """Get list of all devices."""
    try:
        devices = {}
        for device_id, device in device_manager.devices.items():
            devices[device_id] = {
                "id": device_id,
                "name": device.device_info.name,
                "manufacturer": device.device_info.manufacturer,
                "model": device.device_info.model,
                "status": device.status.value,
                "connected": device.status == DeviceStatus.CONNECTED,
                "protocol": device.device_info.protocol,
                "connection_string": device.device_info.connection_string,
                "last_error": device.last_error,
                "last_data": device.last_data.timestamp if device.last_data else None
            }
        
        return {
            "status": "success",
            "simulation_mode": device_manager.simulation_mode,
            "total_devices": len(devices),
            "connected_devices": sum(1 for d in devices.values() if d["connected"]),
            "devices": devices
        }
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices/{device_id}")
async def get_device(device_id: str):
    """Get specific device details."""
    try:
        if device_id not in device_manager.devices:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device = device_manager.devices[device_id]
        
        return {
            "status": "success",
            "device": {
                "id": device_id,
                "name": device.device_info.name,
                "manufacturer": device.device_info.manufacturer,
                "model": device.device_info.model,
                "serial_number": device.device_info.serial_number,
                "firmware_version": device.device_info.firmware_version,
                "device_type": device.device_info.device_type.value,
                "protocol": device.device_info.protocol,
                "connection_string": device.device_info.connection_string,
                "status": device.status.value,
                "connected": device.status == DeviceStatus.CONNECTED,
                "last_error": device.last_error,
                "connection_attempts": device.connection_attempts,
                "last_data": device.last_data.timestamp if device.last_data else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices/{device_id}/data")
async def get_device_data(device_id: str):
    """Get latest data from specific device."""
    try:
        if device_id not in device_manager.devices:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device = device_manager.devices[device_id]
        
        if not device.last_data:
            return {
                "status": "no_data",
                "message": "No data available from device"
            }
        
        data = device.last_data
        return {
            "status": "success",
            "device_id": device_id,
            "data": {
                "timestamp": data.timestamp,
                "solar_power_w": data.solar_power_w,
                "battery_power_w": data.battery_power_w,
                "load_power_w": data.load_power_w,
                "grid_power_w": data.grid_power_w,
                "battery_soc_percent": data.battery_soc_percent,
                "battery_voltage_v": data.battery_voltage_v,
                "system_efficiency_percent": data.system_efficiency_percent,
                "temperature_c": data.temperature_c,
                "device_status": data.device_status.value,
                "error_code": data.error_code
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device data for {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/devices/{device_id}/control")
async def write_device_control(device_id: str, control_data: Dict[str, Any]):
    """Write control settings to device."""
    try:
        if device_id not in device_manager.devices:
            raise HTTPException(status_code=404, detail="Device not found")
        
        success = await device_manager.write_control(device_id, control_data)
        
        if success:
            return {
                "status": "success",
                "message": "Control settings written successfully"
            }
        else:
            return {
                "status": "error",
                "message": "Failed to write control settings"
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error writing control to {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/devices/{device_id}/reconnect")
async def reconnect_device(device_id: str):
    """Reconnect to a specific device."""
    try:
        if device_id not in device_manager.devices:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device = device_manager.devices[device_id]
        success = await device.auto_reconnect()
        
        if success:
            return {
                "status": "success",
                "message": "Device reconnected successfully"
            }
        else:
            return {
                "status": "error",
                "message": "Failed to reconnect device"
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reconnecting device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/latest")
async def get_latest_data():
    """Get latest data from any connected device."""
    try:
        data = device_manager.get_latest_data()
        
        if not data:
            return {
                "status": "no_data",
                "message": "No data available from any device"
            }
        
        return {
            "status": "success",
            "data": {
                "timestamp": data.timestamp,
                "solar_power_w": data.solar_power_w,
                "battery_power_w": data.battery_power_w,
                "load_power_w": data.load_power_w,
                "grid_power_w": data.grid_power_w,
                "battery_soc_percent": data.battery_soc_percent,
                "battery_voltage_v": data.battery_voltage_v,
                "system_efficiency_percent": data.system_efficiency_percent,
                "temperature_c": data.temperature_c,
                "device_status": data.device_status.value,
                "error_code": data.error_code
            }
        }
    except Exception as e:
        logger.error(f"Error getting latest data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ports")
async def get_serial_ports():
    """Get list of available serial ports."""
    try:
        from ..hardware.protocols.modbus_rtu import ModbusRTUScanner
        
        ports = ModbusRTUScanner.scan_serial_ports()
        rs485_adapters = ModbusRTUScanner.find_rs485_adapters()
        
        return {
            "status": "success",
            "ports": ports,
            "rs485_adapters": rs485_adapters
        }
    except Exception as e:
        logger.error(f"Error getting serial ports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulation/enable")
async def enable_simulation():
    """Enable simulation mode."""
    try:
        # Clear existing devices
        for device in device_manager.devices.values():
            await device.disconnect()
        device_manager.devices.clear()
        
        # Enable simulation
        await device_manager._enable_simulation_mode()
        
        return {
            "status": "success",
            "message": "Simulation mode enabled"
        }
    except Exception as e:
        logger.error(f"Error enabling simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulation/disable")
async def disable_simulation():
    """Disable simulation mode and scan for real devices."""
    try:
        # Clear simulation devices
        for device_id in list(device_manager.devices.keys()):
            if device_manager.devices[device_id].device_info.device_type == DeviceType.SIMULATION:
                await device_manager.devices[device_id].disconnect()
                del device_manager.devices[device_id]
        
        device_manager.simulation_mode = False
        
        # Scan for real devices
        await device_manager.scan_devices()
        
        return {
            "status": "success",
            "message": "Simulation mode disabled, scanning for real devices"
        }
    except Exception as e:
        logger.error(f"Error disabling simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
