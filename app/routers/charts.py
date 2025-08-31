from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.config.database import get_db
from app.database.models import EnergyData

router = APIRouter(prefix="/charts", tags=["charts"])


@router.get("/daily")
async def get_daily_chart_data(
    date: str = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get daily chart data for a specific date"""
    if date:
        try:
            target_date = datetime.fromisoformat(date).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    else:
        target_date = datetime.now().date()
    
    start_time = datetime.combine(target_date, datetime.min.time())
    end_time = datetime.combine(target_date, datetime.max.time())
    
    # Get hourly aggregated data
    hourly_data = await db.execute(
        select(
            func.strftime('%H', EnergyData.timestamp).label('hour'),
            func.avg(EnergyData.solar_power_w).label('avg_solar'),
            func.avg(EnergyData.battery_power_w).label('avg_battery'),
            func.avg(EnergyData.load_power_w).label('avg_load'),
            func.avg(EnergyData.grid_power_w).label('avg_grid'),
            func.avg(EnergyData.battery_soc_percent).label('avg_battery_soc'),
            func.avg(EnergyData.inverter_temp_c).label('avg_temp')
        )
        .where(and_(EnergyData.timestamp >= start_time, EnergyData.timestamp <= end_time))
        .group_by(func.strftime('%H', EnergyData.timestamp))
        .order_by('hour')
    )
    
    data_points = hourly_data.all()
    
    # Format data for charts
    hours = []
    solar_power = []
    battery_power = []
    load_power = []
    grid_power = []
    battery_soc = []
    temperature = []
    
    for point in data_points:
        hours.append(int(point.hour))
        solar_power.append(round(point.avg_solar or 0))
        battery_power.append(round(point.avg_battery or 0))
        load_power.append(round(point.avg_load or 0))
        grid_power.append(round(point.avg_grid or 0))
        battery_soc.append(round(point.avg_battery_soc or 0, 1))
        temperature.append(round(point.avg_temp or 0, 1))
    
    return {
        "date": target_date.isoformat(),
        "hours": hours,
        "solar_power": solar_power,
        "battery_power": battery_power,
        "load_power": load_power,
        "grid_power": grid_power,
        "battery_soc": battery_soc,
        "temperature": temperature
    }


@router.get("/weekly")
async def get_weekly_chart_data(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get weekly aggregated data"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    # Get daily aggregated data
    daily_data = await db.execute(
        select(
            func.date(EnergyData.timestamp).label('date'),
            func.sum(EnergyData.solar_power_w).label('total_solar'),
            func.sum(EnergyData.load_power_w).label('total_load'),
            func.avg(EnergyData.battery_soc_percent).label('avg_battery_soc'),
            func.max(EnergyData.solar_power_w).label('peak_solar'),
            func.avg(EnergyData.system_efficiency_percent).label('avg_efficiency')
        )
        .where(and_(
            EnergyData.timestamp >= datetime.combine(start_date, datetime.min.time()),
            EnergyData.timestamp <= datetime.combine(end_date, datetime.max.time())
        ))
        .group_by(func.date(EnergyData.timestamp))
        .order_by('date')
    )
    
    data_points = daily_data.all()
    
    # Format data for charts
    dates = []
    total_solar = []
    total_load = []
    avg_battery_soc = []
    peak_solar = []
    avg_efficiency = []
    
    for point in data_points:
        dates.append(point.date)
        total_solar.append(round(point.total_solar or 0))
        total_load.append(round(point.total_load or 0))
        avg_battery_soc.append(round(point.avg_battery_soc or 0, 1))
        peak_solar.append(round(point.peak_solar or 0))
        avg_efficiency.append(round(point.avg_efficiency or 0, 1))
    
    return {
        "dates": [d.isoformat() for d in dates],
        "total_solar": total_solar,
        "total_load": total_load,
        "avg_battery_soc": avg_battery_soc,
        "peak_solar": peak_solar,
        "avg_efficiency": avg_efficiency
    }


@router.get("/monthly")
async def get_monthly_chart_data(
    year: int = None,
    month: int = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get monthly aggregated data"""
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    
    # Get daily aggregated data for the month
    daily_data = await db.execute(
        select(
            func.date(EnergyData.timestamp).label('date'),
            func.sum(EnergyData.solar_power_w).label('total_solar'),
            func.sum(EnergyData.load_power_w).label('total_load'),
            func.avg(EnergyData.battery_soc_percent).label('avg_battery_soc'),
            func.max(EnergyData.solar_power_w).label('peak_solar')
        )
        .where(and_(
            EnergyData.timestamp >= start_date,
            EnergyData.timestamp <= end_date
        ))
        .group_by(func.date(EnergyData.timestamp))
        .order_by('date')
    )
    
    data_points = daily_data.all()
    
    # Format data for charts
    dates = []
    total_solar = []
    total_load = []
    avg_battery_soc = []
    peak_solar = []
    
    for point in data_points:
        dates.append(point.date)
        total_solar.append(round(point.total_solar or 0))
        total_load.append(round(point.total_load or 0))
        avg_battery_soc.append(round(point.avg_battery_soc or 0, 1))
        peak_solar.append(round(point.peak_solar or 0))
    
    return {
        "year": year,
        "month": month,
        "dates": [d.isoformat() for d in dates],
        "total_solar": total_solar,
        "total_load": total_load,
        "avg_battery_soc": avg_battery_soc,
        "peak_solar": peak_solar
    }


@router.get("/analytics")
async def get_analytics_summary(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get analytics summary with key performance indicators"""
    # Today's data
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_data = await db.execute(
        select(
            func.sum(EnergyData.solar_power_w).label('total_solar'),
            func.sum(EnergyData.load_power_w).label('total_load'),
            func.avg(EnergyData.battery_soc_percent).label('avg_battery_soc'),
            func.max(EnergyData.solar_power_w).label('peak_solar'),
            func.avg(EnergyData.system_efficiency_percent).label('avg_efficiency')
        )
        .where(EnergyData.timestamp >= today_start)
    )
    today = today_data.first()
    
    # This month's data
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_data = await db.execute(
        select(
            func.sum(EnergyData.solar_power_w).label('total_solar'),
            func.sum(EnergyData.load_power_w).label('total_load'),
            func.avg(EnergyData.system_efficiency_percent).label('avg_efficiency')
        )
        .where(EnergyData.timestamp >= month_start)
    )
    month = month_data.first()
    
    # Calculate efficiency
    solar_efficiency = 0
    if today.total_solar and today.total_load:
        solar_efficiency = (today.total_solar / today.total_load) * 100
    
    return {
        "today": {
            "total_solar": round(today.total_solar or 0),
            "total_load": round(today.total_load or 0),
            "avg_battery_soc": round(today.avg_battery_soc or 0, 1),
            "peak_solar": round(today.peak_solar or 0),
            "avg_efficiency": round(today.avg_efficiency or 0, 1),
            "solar_efficiency": round(solar_efficiency, 1)
        },
        "this_month": {
            "total_solar": round(month.total_solar or 0),
            "total_load": round(month.total_load or 0),
            "avg_efficiency": round(month.avg_efficiency or 0, 1)
        }
    }
