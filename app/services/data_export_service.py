import csv
import io
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class DataExportService:
    """Handle data export to CSV and other formats"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def export_to_csv(self, period: str, custom_start=None, custom_end=None) -> str:
        """Export chart data to CSV format"""
        
        # Get the data using chart data service
        from .chart_data_service import ChartDataService
        chart_service = ChartDataService(self.db)
        
        try:
            # Fetch all relevant data
            power_flow = await chart_service.get_power_flow_data(period, custom_start, custom_end)
            battery_data = await chart_service.get_battery_performance_data(period)
            energy_summary = await chart_service.get_energy_summary_data(period)
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Timestamp',
                'Solar Power (W)',
                'Battery Power (W)', 
                'Battery SOC (%)',
                'Battery Voltage (V)',
                'Load Power (W)',
                'Grid Power (W)',
                'System Efficiency (%)',
                'Data Quality'
            ])
            
            # Write data rows
            timestamps = power_flow['datasets']['timestamps']
            for i, timestamp in enumerate(timestamps):
                # Get corresponding battery data if available
                battery_soc = ''
                battery_voltage = ''
                if i < len(battery_data['soc_data']):
                    battery_soc = battery_data['soc_data'][i]
                    battery_voltage = battery_data['voltage_data'][i]
                
                writer.writerow([
                    timestamp,
                    power_flow['datasets']['solar_power'][i],
                    power_flow['datasets']['battery_power'][i],
                    battery_soc,
                    battery_voltage,
                    power_flow['datasets']['load_power'][i],
                    power_flow['datasets']['grid_power'][i],
                    '',  # Efficiency data would need separate query
                    1.0  # Default data quality
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting CSV data: {e}")
            raise
    
    async def export_summary_csv(self, period: str, custom_start=None, custom_end=None) -> str:
        """Export summary data to CSV format"""
        
        from .chart_data_service import ChartDataService
        chart_service = ChartDataService(self.db)
        
        try:
            energy_summary = await chart_service.get_energy_summary_data(period)
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Period',
                'Solar Energy (kWh)',
                'Load Energy (kWh)',
                'Net Energy (kWh)',
                'Average Efficiency (%)'
            ])
            
            # Write data rows
            labels = energy_summary['labels']
            for i, label in enumerate(labels):
                writer.writerow([
                    label,
                    energy_summary['solar_energy'][i],
                    energy_summary['load_energy'][i],
                    energy_summary['net_energy'][i] if i < len(energy_summary['net_energy']) else 0,
                    energy_summary['efficiency'][i] if i < len(energy_summary['efficiency']) else 0
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting summary CSV data: {e}")
            raise
    
    async def export_battery_csv(self, period: str) -> str:
        """Export battery performance data to CSV format"""
        
        from .chart_data_service import ChartDataService
        chart_service = ChartDataService(self.db)
        
        try:
            battery_data = await chart_service.get_battery_performance_data(period)
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Timestamp',
                'Battery SOC (%)',
                'Battery Voltage (V)',
                'Battery Power (W)',
                'Battery State',
                'Total Cycles'
            ])
            
            # Write data rows
            timestamps = battery_data['timestamps']
            for i, timestamp in enumerate(timestamps):
                writer.writerow([
                    timestamp,
                    battery_data['soc_data'][i] if i < len(battery_data['soc_data']) else '',
                    battery_data['voltage_data'][i] if i < len(battery_data['voltage_data']) else '',
                    battery_data['power_data'][i] if i < len(battery_data['power_data']) else '',
                    battery_data['state_data'][i] if i < len(battery_data['state_data']) else '',
                    battery_data['charge_cycles'] if i == 0 else ''  # Only show cycles once
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting battery CSV data: {e}")
            raise
    
    async def get_export_filename(self, period: str, data_type: str = 'energy') -> str:
        """Generate appropriate filename for export"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if period == 'custom':
            period = 'custom_range'
        
        return f"solar_sync_{data_type}_{period}_{timestamp}.csv"
    
    async def export_system_events_csv(self, start_date: datetime = None, end_date: datetime = None) -> str:
        """Export system events to CSV format"""
        
        try:
            # Build query
            query = """
                SELECT 
                    timestamp,
                    event_type,
                    severity,
                    message,
                    source,
                    acknowledged,
                    acknowledged_at,
                    acknowledged_by
                FROM system_events 
                WHERE 1=1
            """
            params = {}
            
            if start_date:
                query += " AND timestamp >= :start_date"
                params['start_date'] = start_date
            
            if end_date:
                query += " AND timestamp <= :end_date"
                params['end_date'] = end_date
            
            query += " ORDER BY timestamp DESC"
            
            result = await self.db.execute(text(query), params)
            rows = result.fetchall()
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Timestamp',
                'Event Type',
                'Severity',
                'Message',
                'Source',
                'Acknowledged',
                'Acknowledged At',
                'Acknowledged By'
            ])
            
            # Write data rows
            for row in rows:
                writer.writerow([
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    'Yes' if row[5] else 'No',
                    row[6] if row[6] else '',
                    row[7] if row[7] else ''
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting system events CSV: {e}")
            raise
    
    async def export_device_registry_csv(self) -> str:
        """Export device registry to CSV format"""
        
        try:
            query = text("""
                SELECT 
                    device_id,
                    device_type,
                    name,
                    model,
                    manufacturer,
                    firmware_version,
                    ip_address,
                    port,
                    status,
                    last_seen,
                    created_at
                FROM device_registry 
                ORDER BY device_type, name
            """)
            
            result = await self.db.execute(query)
            rows = result.fetchall()
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Device ID',
                'Device Type',
                'Name',
                'Model',
                'Manufacturer',
                'Firmware Version',
                'IP Address',
                'Port',
                'Status',
                'Last Seen',
                'Created At'
            ])
            
            # Write data rows
            for row in rows:
                writer.writerow([
                    row[0],
                    row[1],
                    row[2],
                    row[3] if row[3] else '',
                    row[4] if row[4] else '',
                    row[5] if row[5] else '',
                    row[6] if row[6] else '',
                    row[7] if row[7] else '',
                    row[8],
                    row[9] if row[9] else '',
                    row[10]
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting device registry CSV: {e}")
            raise
