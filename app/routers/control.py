from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import select

from app.config.database import get_db
from app.database.models import DeviceRegistry
from app.config.settings import settings

router = APIRouter(prefix="/control", tags=["control"])


class DeviceControl(BaseModel):
    action: str
    parameters: Dict[str, Any] = {}


@router.get("/devices")
async def get_devices(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    """Get all registered devices"""
    devices_data = await db.execute(
        select(DeviceRegistry).order_by(DeviceRegistry.device_type, DeviceRegistry.name)
    )
    devices = devices_data.scalars().all()
    
    return [
        {
            "device_id": device.device_id,
            "name": device.name,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "device_type": device.device_type,
            "is_simulated": device.is_simulated,
            "status": device.status,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "config": device.config_json
        }
        for device in devices
    ]


@router.get("/devices/{device_id}")
async def get_device(device_id: str, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Get specific device information"""
    device_data = await db.execute(
        select(DeviceRegistry).where(DeviceRegistry.device_id == device_id)
    )
    device = device_data.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    
    return {
        "device_id": device.device_id,
        "name": device.name,
        "manufacturer": device.manufacturer,
        "model": device.model,
        "device_type": device.device_type,
        "is_simulated": device.is_simulated,
        "status": device.status,
        "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        "config": device.config_json
    }


@router.post("/devices/{device_id}/control")
async def control_device(
    device_id: str,
    control: DeviceControl,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Send control command to device"""
    # Check if device exists
    device_data = await db.execute(
        select(DeviceRegistry).where(DeviceRegistry.device_id == device_id)
    )
    device = device_data.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    
    # Check if device is online
    if device.status != "online":
        raise HTTPException(status_code=400, detail=f"Device '{device_id}' is not online")
    
    # For now, this is a placeholder for future hardware integration
    # In a real implementation, this would send commands to actual hardware
    
    if settings.simulate_hardware:
        # Simulated device control
        return {
            "device_id": device_id,
            "action": control.action,
            "parameters": control.parameters,
            "status": "success",
            "message": f"Simulated {control.action} command sent to {device.name}",
            "timestamp": datetime.now().isoformat()
        }
    else:
        # Real hardware control (placeholder)
        raise HTTPException(
            status_code=501,
            detail="Hardware control not yet implemented"
        )


@router.get("/system/status")
async def get_system_status() -> Dict[str, Any]:
    """Get overall system status"""
    return {
        "system_status": "online",
        "hardware_simulation": settings.simulate_hardware,
        "environment": settings.environment,
        "last_update": datetime.now().isoformat()
    }


@router.post("/system/restart")
async def restart_system() -> Dict[str, Any]:
    """Restart the system (placeholder)"""
    if settings.simulate_hardware:
        return {
            "status": "success",
            "message": "System restart initiated (simulated)",
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(
            status_code=501,
            detail="System restart not yet implemented"
        )


@router.post("/system/shutdown")
async def shutdown_system() -> Dict[str, Any]:
    """Shutdown the system (placeholder)"""
    if settings.simulate_hardware:
        return {
            "status": "success",
            "message": "System shutdown initiated (simulated)",
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(
            status_code=501,
            detail="System shutdown not yet implemented"
        )
