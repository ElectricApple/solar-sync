from fastapi import APIRouter, WebSocket, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

from app.config.database import get_db
from app.database.models import EnergyData, SystemConfig, SystemEvent
from app.services.websocket_manager import websocket_manager
from app.services.data_simulator import SolarDataSimulator

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle any client messages
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                # Handle client messages if needed
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except Exception as e:
        pass
    finally:
        websocket_manager.disconnect(websocket)


@router.get("/current")
async def get_current_data(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Get current energy data"""
    simulator = SolarDataSimulator()
    return simulator.get_current_data()


@router.get("/summary")
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Get dashboard summary with key metrics"""
    # Get latest energy data
    latest_data = await db.execute(
        select(EnergyData).order_by(EnergyData.timestamp.desc()).limit(1)
    )
    latest = latest_data.scalar_one_or_none()
    
    if not latest:
        # Return simulated data if no database data
        simulator = SolarDataSimulator()
        current_data = simulator.get_current_data()
        return {
            "current_power": current_data["solar_power_w"],
            "battery_soc": current_data["battery_soc_percent"],
            "load_power": current_data["load_power_w"],
            "grid_power": current_data["grid_power_w"],
            "system_status": "online",
            "last_update": current_data["timestamp"]
        }
    
    # Calculate daily totals
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    daily_data = await db.execute(
        select(
            func.sum(EnergyData.solar_power_w).label("total_solar"),
            func.sum(EnergyData.load_power_w).label("total_load"),
            func.avg(EnergyData.battery_soc_percent).label("avg_battery_soc")
        ).where(EnergyData.timestamp >= today_start)
    )
    daily = daily_data.first()
    
    # Get recent events
    recent_events = await db.execute(
        select(SystemEvent)
        .order_by(SystemEvent.timestamp.desc())
        .limit(5)
    )
    events = recent_events.scalars().all()
    
    return {
        "current_power": latest.solar_power_w,
        "battery_soc": latest.battery_soc_percent,
        "load_power": latest.load_power_w,
        "grid_power": latest.grid_power_w,
        "system_status": "online",
        "last_update": latest.timestamp.isoformat(),
        "daily_solar": daily.total_solar or 0,
        "daily_load": daily.total_load or 0,
        "avg_battery_soc": round(daily.avg_battery_soc or 0, 1),
        "recent_events": [
            {
                "timestamp": event.timestamp.isoformat(),
                "type": event.event_type,
                "severity": event.severity,
                "message": event.message,
                "source": event.source
            }
            for event in events
        ]
    }


@router.get("/chart-data")
async def get_chart_data(
    hours: int = 24,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get historical data for charts"""
    if hours > 168:  # Max 1 week
        hours = 168
    
    start_time = datetime.now() - timedelta(hours=hours)
    
    # Get energy data for the time period
    energy_data = await db.execute(
        select(EnergyData)
        .where(EnergyData.timestamp >= start_time)
        .order_by(EnergyData.timestamp)
    )
    data_points = energy_data.scalars().all()
    
    # Format data for charts
    timestamps = []
    solar_power = []
    battery_power = []
    load_power = []
    grid_power = []
    battery_soc = []
    
    for point in data_points:
        timestamps.append(point.timestamp.isoformat())
        solar_power.append(point.solar_power_w)
        battery_power.append(point.battery_power_w)
        load_power.append(point.load_power_w)
        grid_power.append(point.grid_power_w)
        battery_soc.append(point.battery_soc_percent)
    
    return {
        "timestamps": timestamps,
        "solar_power": solar_power,
        "battery_power": battery_power,
        "load_power": load_power,
        "grid_power": grid_power,
        "battery_soc": battery_soc
    }


@router.post("/simulate-weather")
async def update_weather_simulation(factor: float):
    """Update weather simulation factor (0.0 = cloudy, 1.0 = sunny)"""
    if not 0.0 <= factor <= 1.0:
        raise HTTPException(status_code=400, detail="Weather factor must be between 0.0 and 1.0")
    
    websocket_manager.simulator.update_weather(factor)
    return {"message": f"Weather simulation updated to {factor}"}


@router.post("/simulate-load")
async def update_load_simulation(load: int):
    """Update base load simulation (watts)"""
    if load < 0:
        raise HTTPException(status_code=400, detail="Load must be non-negative")
    
    websocket_manager.simulator.update_base_load(load)
    return {"message": f"Base load simulation updated to {load}W"}
