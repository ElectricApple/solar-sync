from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional
import io

from ..config.database import get_db
from ..services.chart_data_service import ChartDataService
from ..services.data_export_service import DataExportService

router = APIRouter(prefix="/charts", tags=["charts"])

@router.get("/power-flow")
async def get_power_flow_data(
    period: str = Query(..., regex="^(live|today|week|month|custom)$"),
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get power flow chart data"""
    try:
        chart_service = ChartDataService(db)
        
        custom_start = datetime.fromisoformat(start) if start else None
        custom_end = datetime.fromisoformat(end) if end else None
        
        data = await chart_service.get_power_flow_data(period, custom_start, custom_end)
        return data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/battery-performance")
async def get_battery_performance_data(
    period: str = Query(..., regex="^(live|today|week|month|custom)$"),
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get battery performance chart data"""
    try:
        chart_service = ChartDataService(db)
        
        custom_start = datetime.fromisoformat(start) if start else None
        custom_end = datetime.fromisoformat(end) if end else None
        
        data = await chart_service.get_battery_performance_data(period)
        return data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/energy-summary") 
async def get_energy_summary_data(
    period: str = Query(..., regex="^(live|today|week|month|custom)$"),
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get energy summary chart data"""
    try:
        chart_service = ChartDataService(db)
        
        custom_start = datetime.fromisoformat(start) if start else None
        custom_end = datetime.fromisoformat(end) if end else None
        
        data = await chart_service.get_energy_summary_data(period)
        return data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system-efficiency")
async def get_system_efficiency_data(
    period: str = Query(..., regex="^(live|today|week|month|custom)$"),
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get system efficiency chart data"""
    try:
        chart_service = ChartDataService(db)
        
        custom_start = datetime.fromisoformat(start) if start else None
        custom_end = datetime.fromisoformat(end) if end else None
        
        data = await chart_service.get_system_efficiency_data(period)
        return data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_analytics_summary(
    period: str = Query(..., regex="^(live|today|week|month|custom)$"),
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive analytics summary for charts page"""
    try:
        chart_service = ChartDataService(db)
        
        custom_start = datetime.fromisoformat(start) if start else None
        custom_end = datetime.fromisoformat(end) if end else None
        
        # Get all chart data
        power_flow = await chart_service.get_power_flow_data(period, custom_start, custom_end)
        battery_data = await chart_service.get_battery_performance_data(period)
        energy_summary = await chart_service.get_energy_summary_data(period)
        efficiency_data = await chart_service.get_system_efficiency_data(period)
        
        # Calculate summary statistics
        solar_powers = power_flow['datasets']['solar_power']
        load_powers = power_flow['datasets']['load_power']
        
        analytics = {
            "period": period,
            "data_points": power_flow['data_points'],
            "peak_solar_power": max(solar_powers) if solar_powers else 0,
            "total_solar_energy": sum(energy_summary['solar_energy']) if energy_summary['solar_energy'] else 0,
            "total_load_energy": sum(energy_summary['load_energy']) if energy_summary['load_energy'] else 0,
            "avg_efficiency": sum(efficiency_data['efficiency_data']) / len(efficiency_data['efficiency_data']) if efficiency_data['efficiency_data'] else 0,
            "battery_cycles": battery_data.get('charge_cycles', 0),
            "start_time": power_flow['start_time'],
            "end_time": power_flow['end_time']
        }
        
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Export endpoints
@router.get("/export/csv")
async def export_chart_data_csv(
    period: str = Query(..., regex="^(live|today|week|month|custom)$"),
    data_type: str = Query("energy", regex="^(energy|battery|summary|events|devices)$"),
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Export chart data to CSV format"""
    try:
        export_service = DataExportService(db)
        
        custom_start = datetime.fromisoformat(start) if start else None
        custom_end = datetime.fromisoformat(end) if end else None
        
        if data_type == "energy":
            csv_content = await export_service.export_to_csv(period, custom_start, custom_end)
        elif data_type == "battery":
            csv_content = await export_service.export_battery_csv(period)
        elif data_type == "summary":
            csv_content = await export_service.export_summary_csv(period, custom_start, custom_end)
        elif data_type == "events":
            csv_content = await export_service.export_system_events_csv(custom_start, custom_end)
        elif data_type == "devices":
            csv_content = await export_service.export_device_registry_csv()
        else:
            raise HTTPException(status_code=400, detail="Invalid data type")
        
        filename = await export_service.get_export_filename(period, data_type)
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/summary")
async def export_summary_csv(
    period: str = Query(..., regex="^(live|today|week|month|custom)$"),
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Export summary data to CSV format"""
    try:
        export_service = DataExportService(db)
        
        custom_start = datetime.fromisoformat(start) if start else None
        custom_end = datetime.fromisoformat(end) if end else None
        
        csv_content = await export_service.export_summary_csv(period, custom_start, custom_end)
        filename = await export_service.get_export_filename(period, "summary")
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/battery")
async def export_battery_csv(
    period: str = Query(..., regex="^(live|today|week|month|custom)$"),
    db: AsyncSession = Depends(get_db)
):
    """Export battery performance data to CSV format"""
    try:
        export_service = DataExportService(db)
        
        csv_content = await export_service.export_battery_csv(period)
        filename = await export_service.get_export_filename(period, "battery")
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/events")
async def export_events_csv(
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Export system events to CSV format"""
    try:
        export_service = DataExportService(db)
        
        custom_start = datetime.fromisoformat(start) if start else None
        custom_end = datetime.fromisoformat(end) if end else None
        
        csv_content = await export_service.export_system_events_csv(custom_start, custom_end)
        filename = f"solar_sync_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/devices")
async def export_devices_csv(db: AsyncSession = Depends(get_db)):
    """Export device registry to CSV format"""
    try:
        export_service = DataExportService(db)
        
        csv_content = await export_service.export_device_registry_csv()
        filename = f"solar_sync_devices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
