from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Dict, Any
from pydantic import BaseModel

from app.config.database import get_db
from app.database.models import SystemConfig
from app.config.settings import settings

router = APIRouter(prefix="/settings", tags=["settings"])


class ConfigUpdate(BaseModel):
    value: str
    description: str = None


@router.get("/")
async def get_all_settings(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    """Get all system configuration settings"""
    config_data = await db.execute(
        select(SystemConfig).order_by(SystemConfig.key)
    )
    configs = config_data.scalars().all()
    
    return [
        {
            "key": config.key,
            "value": config.value,
            "description": config.description,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None
        }
        for config in configs
    ]


@router.get("/{key}")
async def get_setting(key: str, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Get a specific system configuration setting"""
    config_data = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = config_data.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    
    return {
        "key": config.key,
        "value": config.value,
        "description": config.description,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None
    }


@router.put("/{key}")
async def update_setting(
    key: str,
    config_update: ConfigUpdate,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Update a system configuration setting"""
    # Check if setting exists
    existing_config = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = existing_config.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    
    # Update the setting
    await db.execute(
        update(SystemConfig)
        .where(SystemConfig.key == key)
        .values(
            value=config_update.value,
            description=config_update.description or config.description
        )
    )
    await db.commit()
    
    # Return updated setting
    updated_config = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    updated = updated_config.scalar_one()
    
    return {
        "key": updated.key,
        "value": updated.value,
        "description": updated.description,
        "updated_at": updated.updated_at.isoformat() if updated.updated_at else None
    }


@router.post("/")
async def create_setting(
    key: str,
    config_update: ConfigUpdate,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Create a new system configuration setting"""
    # Check if setting already exists
    existing_config = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    if existing_config.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Setting '{key}' already exists")
    
    # Create new setting
    new_config = SystemConfig(
        key=key,
        value=config_update.value,
        description=config_update.description
    )
    db.add(new_config)
    await db.commit()
    await db.refresh(new_config)
    
    return {
        "key": new_config.key,
        "value": new_config.value,
        "description": new_config.description,
        "updated_at": new_config.updated_at.isoformat() if new_config.updated_at else None
    }


@router.delete("/{key}")
async def delete_setting(key: str, db: AsyncSession = Depends(get_db)):
    """Delete a system configuration setting"""
    # Check if setting exists
    existing_config = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = existing_config.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    
    # Delete the setting
    await db.delete(config)
    await db.commit()
    
    return {"message": f"Setting '{key}' deleted successfully"}


@router.get("/system/info")
async def get_system_info() -> Dict[str, Any]:
    """Get system information and status"""
    return {
        "system_name": settings.system_name,
        "system_version": settings.system_version,
        "environment": settings.environment,
        "is_pi": settings.is_pi,
        "simulate_hardware": settings.simulate_hardware,
        "websocket_update_interval": settings.websocket_update_interval,
        "max_chart_points": settings.max_chart_points,
        "database_url": settings.database_url.replace("sqlite:///", "sqlite:///***"),  # Hide path
        "log_level": settings.log_level
    }
