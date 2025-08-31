from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func
import logging

logger = logging.getLogger(__name__)

class ChartDataService:
    """Handles data aggregation and formatting for charts"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_power_flow_data(self, period: str, custom_start: Optional[datetime] = None, 
                                custom_end: Optional[datetime] = None) -> Dict[str, Any]:
        """Get power flow data for line charts"""
        
        start_time, end_time, interval = self._get_time_range(period, custom_start, custom_end)
        
        # Choose appropriate data source based on period
        if period in ['live', 'today']:
            data = await self._get_raw_data(start_time, end_time, interval)
        elif period in ['week', 'month']:
            data = await self._get_hourly_data(start_time, end_time)
        else:
            data = await self._get_daily_data(start_time, end_time)
        
        return {
            "period": period,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "data_points": len(data),
            "datasets": {
                "timestamps": [point["timestamp"] for point in data],
                "solar_power": [point["solar_power_w"] for point in data],
                "battery_power": [point["battery_power_w"] for point in data],
                "load_power": [point["load_power_w"] for point in data],
                "grid_power": [point["grid_power_w"] for point in data],
            }
        }
    
    async def get_battery_performance_data(self, period: str) -> Dict[str, Any]:
        """Get battery performance data for combined charts"""
        start_time, end_time, _ = self._get_time_range(period)
        
        # Get battery-specific data
        query = text("""
            SELECT 
                timestamp,
                battery_soc_percent,
                battery_voltage_v,
                battery_power_w,
                CASE 
                    WHEN battery_power_w > 50 THEN 'discharging'
                    WHEN battery_power_w < -50 THEN 'charging'
                    ELSE 'idle'
                END as battery_state
            FROM energy_data 
            WHERE timestamp BETWEEN :start_time AND :end_time
            ORDER BY timestamp
        """)
        
        result = await self.db.execute(query, {
            "start_time": start_time,
            "end_time": end_time
        })
        rows = result.fetchall()
        
        return {
            "timestamps": [row[0] for row in rows],
            "soc_data": [row[1] for row in rows],
            "voltage_data": [row[2] for row in rows],
            "power_data": [row[3] for row in rows],
            "state_data": [row[4] for row in rows],
            "charge_cycles": self._calculate_battery_cycles(rows)
        }
    
    async def get_energy_summary_data(self, period: str) -> Dict[str, Any]:
        """Get daily energy summary for stacked bar charts"""
        start_time, end_time, _ = self._get_time_range(period)
        
        if period in ['week', 'month', 'custom']:
            # Use daily summaries for longer periods
            query = text("""
                SELECT 
                    date,
                    total_solar_kwh,
                    total_load_kwh,
                    total_solar_kwh - total_load_kwh as net_energy,
                    avg_efficiency
                FROM daily_summaries 
                WHERE date BETWEEN date(:start_time) AND date(:end_time)
                ORDER BY date
            """)
        else:
            # Calculate hourly summaries for today
            query = text("""
                SELECT 
                    strftime('%H:00', timestamp) as hour,
                    SUM(solar_power_w) * 0.001 as solar_kwh,
                    SUM(load_power_w) * 0.001 as load_kwh,
                    AVG(system_efficiency_percent) as avg_efficiency
                FROM energy_data 
                WHERE timestamp BETWEEN :start_time AND :end_time
                GROUP BY strftime('%H', timestamp)
                ORDER BY hour
            """)
        
        result = await self.db.execute(query, {
            "start_time": start_time,
            "end_time": end_time
        })
        rows = result.fetchall()
        
        return {
            "labels": [row[0] for row in rows],
            "solar_energy": [row[1] for row in rows],
            "load_energy": [row[2] for row in rows],
            "net_energy": [row[3] for row in rows] if len(rows) > 0 and len(rows[0]) > 3 else [],
            "efficiency": [row[4] if len(rows) > 0 and len(rows[0]) > 4 else row[3] for row in rows]
        }
    
    async def get_system_efficiency_data(self, period: str) -> Dict[str, Any]:
        """Get system efficiency data for trend analysis"""
        start_time, end_time, _ = self._get_time_range(period)
        
        query = text("""
            SELECT 
                timestamp,
                system_efficiency_percent,
                data_quality
            FROM energy_data 
            WHERE timestamp BETWEEN :start_time AND :end_time
            AND data_quality > 0.5
            ORDER BY timestamp
        """)
        
        result = await self.db.execute(query, {
            "start_time": start_time,
            "end_time": end_time
        })
        rows = result.fetchall()
        
        return {
            "timestamps": [row[0] for row in rows],
            "efficiency_data": [row[1] for row in rows],
            "data_quality": [row[2] for row in rows]
        }
    
    def _get_time_range(self, period: str, custom_start=None, custom_end=None):
        """Calculate time range and interval based on period"""
        now = datetime.now()
        
        if period == 'live':
            start_time = now - timedelta(minutes=10)
            end_time = now
            interval = timedelta(seconds=30)
        elif period == 'today':
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = now
            interval = timedelta(minutes=15)
        elif period == 'week':
            start_time = now - timedelta(days=7)
            end_time = now
            interval = timedelta(hours=1)
        elif period == 'month':
            start_time = now - timedelta(days=30)
            end_time = now
            interval = timedelta(hours=6)
        elif period == 'custom' and custom_start and custom_end:
            start_time = custom_start
            end_time = custom_end
            # Auto-select interval based on range
            days_diff = (end_time - start_time).days
            if days_diff <= 1:
                interval = timedelta(minutes=15)
            elif days_diff <= 7:
                interval = timedelta(hours=1)
            else:
                interval = timedelta(hours=6)
        else:
            raise ValueError(f"Invalid period: {period}")
        
        return start_time, end_time, interval
    
    async def _get_raw_data(self, start_time: datetime, end_time: datetime, interval: timedelta) -> List[Dict]:
        """Get raw energy data for live/today views"""
        query = text("""
            SELECT 
                timestamp,
                solar_power_w,
                battery_power_w,
                load_power_w,
                grid_power_w,
                battery_soc_percent,
                system_efficiency_percent
            FROM energy_data 
            WHERE timestamp BETWEEN :start_time AND :end_time
            ORDER BY timestamp
        """)
        
        result = await self.db.execute(query, {
            "start_time": start_time,
            "end_time": end_time
        })
        rows = result.fetchall()
        
        return [
            {
                "timestamp": row[0],
                "solar_power_w": row[1],
                "battery_power_w": row[2],
                "load_power_w": row[3],
                "grid_power_w": row[4],
                "battery_soc_percent": row[5],
                "system_efficiency_percent": row[6]
            }
            for row in rows
        ]
    
    async def _get_hourly_data(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Get hourly aggregated data for week/month views"""
        query = text("""
            SELECT 
                hour_start,
                avg_solar_power_w,
                avg_battery_soc,
                total_load_kwh,
                avg_efficiency
            FROM hourly_summaries 
            WHERE hour_start BETWEEN :start_time AND :end_time
            ORDER BY hour_start
        """)
        
        result = await self.db.execute(query, {
            "start_time": start_time,
            "end_time": end_time
        })
        rows = result.fetchall()
        
        return [
            {
                "timestamp": row[0],
                "solar_power_w": row[1],
                "battery_power_w": 0,  # Not stored in hourly summaries
                "load_power_w": int(row[3] * 1000),  # Convert kWh to W
                "grid_power_w": 0,  # Not stored in hourly summaries
                "battery_soc_percent": row[2],
                "system_efficiency_percent": row[4]
            }
            for row in rows
        ]
    
    async def _get_daily_data(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Get daily aggregated data for longer periods"""
        query = text("""
            SELECT 
                date,
                peak_solar_power_w,
                avg_efficiency,
                total_solar_kwh,
                total_load_kwh
            FROM daily_summaries 
            WHERE date BETWEEN date(:start_time) AND date(:end_time)
            ORDER BY date
        """)
        
        result = await self.db.execute(query, {
            "start_time": start_time,
            "end_time": end_time
        })
        rows = result.fetchall()
        
        return [
            {
                "timestamp": datetime.strptime(row[0], '%Y-%m-%d'),
                "solar_power_w": row[1],
                "battery_power_w": 0,  # Not stored in daily summaries
                "load_power_w": int(row[4] * 1000),  # Convert kWh to W
                "grid_power_w": 0,  # Not stored in daily summaries
                "battery_soc_percent": 0,  # Not stored in daily summaries
                "system_efficiency_percent": row[2]
            }
            for row in rows
        ]
    
    def _calculate_battery_cycles(self, data) -> float:
        """Calculate approximate battery charge/discharge cycles"""
        cycles = 0
        last_state = None
        
        for row in data:
            current_state = row[4]  # battery_state
            if last_state and last_state != current_state:
                if (last_state == 'charging' and current_state == 'discharging') or \
                   (last_state == 'discharging' and current_state == 'charging'):
                    cycles += 0.5  # Half cycle for each state change
            last_state = current_state
        
        return round(cycles, 2)
