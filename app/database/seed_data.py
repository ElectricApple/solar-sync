import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import random
import logging

logger = logging.getLogger(__name__)

async def seed_development_data(session: AsyncSession):
    """Seed database with development data"""
    
    # Check if data already exists
    existing_data = await session.execute(
        text("SELECT COUNT(*) FROM energy_data")
    )
    count = existing_data.scalar()
    
    if count > 0:
        logger.info("Database already contains data, skipping seed")
        return
    
    logger.info("Seeding development data...")
    
    # Seed devices
    await _seed_devices(session)
    
    # Seed energy data for the last 24 hours
    await _seed_energy_data(session)
    
    # Seed hourly summaries
    await _seed_hourly_summaries(session)
    
    # Seed daily summaries
    await _seed_daily_summaries(session)
    
    # Seed system events
    await _seed_system_events(session)
    
    await session.commit()
    logger.info("Development data seeded successfully")

async def _seed_devices(session: AsyncSession):
    """Seed device registry with sample devices"""
    devices = [
        {
            'device_id': 'inverter_001',
            'device_type': 'inverter',
            'name': 'Solar Inverter',
            'model': 'SMA Sunny Boy 5.0',
            'manufacturer': 'SMA Solar Technology',
            'firmware_version': '3.2.1',
            'ip_address': '192.168.1.100',
            'port': 502,
            'status': 'online',
            'last_seen': datetime.now()
        },
        {
            'device_id': 'battery_001',
            'device_type': 'battery',
            'name': 'Battery Storage',
            'model': 'Tesla Powerwall 2',
            'manufacturer': 'Tesla',
            'firmware_version': '2.1.0',
            'ip_address': '192.168.1.101',
            'port': 502,
            'status': 'online',
            'last_seen': datetime.now()
        },
        {
            'device_id': 'sensor_001',
            'device_type': 'sensor',
            'name': 'Temperature Sensor',
            'model': 'DS18B20',
            'manufacturer': 'Maxim Integrated',
            'firmware_version': '1.0.0',
            'ip_address': '192.168.1.102',
            'port': 80,
            'status': 'online',
            'last_seen': datetime.now()
        }
    ]
    
    for device in devices:
        await session.execute(
            text("""
                INSERT INTO device_registry 
                (device_id, device_type, name, model, manufacturer, firmware_version, 
                 ip_address, port, status, last_seen, created_at, updated_at)
                VALUES (:device_id, :device_type, :name, :model, :manufacturer, :firmware_version,
                        :ip_address, :port, :status, :last_seen, :created_at, :updated_at)
            """),
            {
                **device,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        )

async def _seed_energy_data(session: AsyncSession):
    """Seed energy data for the last 24 hours with realistic solar patterns"""
    now = datetime.now()
    start_time = now - timedelta(hours=24)
    
    # Generate data points every 5 minutes
    current_time = start_time
    data_points = []
    
    while current_time <= now:
        # Simulate solar power based on time of day (peak at noon)
        hour = current_time.hour
        solar_factor = _calculate_solar_factor(hour)
        
        # Base solar power (peak around 5000W)
        solar_power = int(5000 * solar_factor * random.uniform(0.8, 1.2))
        
        # Battery power (negative when charging, positive when discharging)
        battery_power = random.randint(-2000, 2000) if solar_power > 1000 else random.randint(0, 1500)
        
        # Battery SOC (between 20% and 95%)
        battery_soc = max(20, min(95, 60 + random.uniform(-10, 10)))
        
        # Battery voltage (48V system)
        battery_voltage = 48 + random.uniform(-2, 2)
        
        # Load power (household consumption)
        load_power = random.randint(800, 3000)
        
        # Grid power (negative = export, positive = import)
        grid_power = solar_power - load_power - battery_power
        
        # System efficiency (85-95%)
        efficiency = random.uniform(85, 95)
        
        # Inverter temperature
        inverter_temp = 35 + random.uniform(-5, 10)
        
        data_points.append({
            'timestamp': current_time,
            'solar_power_w': solar_power,
            'battery_power_w': battery_power,
            'battery_soc_percent': battery_soc,
            'battery_voltage_v': battery_voltage,
            'load_power_w': load_power,
            'grid_power_w': grid_power,
            'grid_voltage_v': 230 + random.uniform(-5, 5),
            'grid_frequency_hz': 50 + random.uniform(-0.1, 0.1),
            'inverter_temp_c': inverter_temp,
            'system_efficiency_percent': efficiency,
            'data_quality': random.uniform(0.95, 1.0),
            'source': 'simulator',
            'created_at': current_time
        })
        
        current_time += timedelta(minutes=5)
    
    # Insert data in batches
    for point in data_points:
        await session.execute(
            text("""
                INSERT INTO energy_data 
                (timestamp, solar_power_w, battery_power_w, battery_soc_percent, battery_voltage_v,
                 load_power_w, grid_power_w, grid_voltage_v, grid_frequency_hz, inverter_temp_c,
                 system_efficiency_percent, data_quality, source, created_at)
                VALUES (:timestamp, :solar_power_w, :battery_power_w, :battery_soc_percent, :battery_voltage_v,
                        :load_power_w, :grid_power_w, :grid_voltage_v, :grid_frequency_hz, :inverter_temp_c,
                        :system_efficiency_percent, :data_quality, :source, :created_at)
            """),
            point
        )

async def _seed_hourly_summaries(session: AsyncSession):
    """Seed hourly summaries for the last 24 hours"""
    now = datetime.now()
    start_time = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=24)
    
    current_hour = start_time
    
    while current_hour <= now:
        # Get data for this hour
        hour_start = current_hour
        hour_end = current_hour + timedelta(hours=1)
        
        # Calculate hourly averages
        result = await session.execute(
            text("""
                SELECT 
                    AVG(solar_power_w) as avg_solar,
                    MAX(solar_power_w) as max_solar,
                    SUM(solar_power_w) * 0.001 / 12 as total_solar_kwh,
                    AVG(battery_soc_percent) as avg_battery_soc,
                    SUM(load_power_w) * 0.001 / 12 as total_load_kwh,
                    AVG(system_efficiency_percent) as avg_efficiency,
                    COUNT(*) as data_points
                FROM energy_data 
                WHERE timestamp BETWEEN :start_time AND :end_time
            """),
            {'start_time': hour_start, 'end_time': hour_end}
        )
        
        data = result.first()
        
        if data and data.data_points > 0:
            await session.execute(
                text("""
                    INSERT INTO hourly_summaries 
                    (hour_start, avg_solar_power_w, max_solar_power_w, total_solar_kwh,
                     avg_battery_soc, total_load_kwh, avg_efficiency, data_points, created_at)
                    VALUES (:hour_start, :avg_solar, :max_solar, :total_solar_kwh,
                            :avg_battery_soc, :total_load_kwh, :avg_efficiency, :data_points, :created_at)
                """),
                {
                    'hour_start': hour_start,
                    'avg_solar': int(data.avg_solar or 0),
                    'max_solar': int(data.max_solar or 0),
                    'total_solar_kwh': round(data.total_solar_kwh or 0, 3),
                    'avg_battery_soc': round(data.avg_battery_soc or 0, 1),
                    'total_load_kwh': round(data.total_load_kwh or 0, 3),
                    'avg_efficiency': round(data.avg_efficiency or 0, 1),
                    'data_points': data.data_points,
                    'created_at': datetime.now()
                }
            )
        
        current_hour += timedelta(hours=1)

async def _seed_daily_summaries(session: AsyncSession):
    """Seed daily summaries for the last 7 days"""
    now = datetime.now()
    
    for days_ago in range(7):
        date = (now - timedelta(days=days_ago)).date()
        date_str = date.strftime('%Y-%m-%d')
        
        # Calculate daily totals
        result = await session.execute(
            text("""
                SELECT 
                    SUM(solar_power_w) * 0.001 / 12 as total_solar_kwh,
                    SUM(load_power_w) * 0.001 / 12 as total_load_kwh,
                    MAX(solar_power_w) as peak_solar_power_w,
                    AVG(system_efficiency_percent) as avg_efficiency,
                    MIN(battery_soc_percent) as min_battery_soc,
                    MAX(battery_soc_percent) as max_battery_soc,
                    COUNT(*) as data_points
                FROM energy_data 
                WHERE DATE(timestamp) = :date
            """),
            {'date': date_str}
        )
        
        data = result.first()
        
        if data and data.data_points > 0:
            # Calculate battery cycles (simplified)
            battery_cycles = random.uniform(0.5, 2.0)
            
            await session.execute(
                text("""
                    INSERT INTO daily_summaries 
                    (date, total_solar_kwh, total_load_kwh, total_battery_cycles, peak_solar_power_w,
                     avg_efficiency, min_battery_soc, max_battery_soc, weather_score, data_quality, created_at)
                    VALUES (:date, :total_solar_kwh, :total_load_kwh, :total_battery_cycles, :peak_solar_power_w,
                            :avg_efficiency, :min_battery_soc, :max_battery_soc, :weather_score, :data_quality, :created_at)
                """),
                {
                    'date': date_str,
                    'total_solar_kwh': round(data.total_solar_kwh or 0, 3),
                    'total_load_kwh': round(data.total_load_kwh or 0, 3),
                    'total_battery_cycles': round(battery_cycles, 2),
                    'peak_solar_power_w': int(data.peak_solar_power_w or 0),
                    'avg_efficiency': round(data.avg_efficiency or 0, 1),
                    'min_battery_soc': round(data.min_battery_soc or 0, 1),
                    'max_battery_soc': round(data.max_battery_soc or 0, 1),
                    'weather_score': random.uniform(0.8, 1.0),
                    'data_quality': random.uniform(0.95, 1.0),
                    'created_at': datetime.now()
                }
            )

async def _seed_system_events(session: AsyncSession):
    """Seed system events"""
    events = [
        {
            'timestamp': datetime.now() - timedelta(hours=2),
            'event_type': 'info',
            'severity': 'low',
            'message': 'System startup completed successfully',
            'source': 'system',
            'acknowledged': True,
            'acknowledged_at': datetime.now() - timedelta(hours=1, minutes=55),
            'acknowledged_by': 'system'
        },
        {
            'timestamp': datetime.now() - timedelta(hours=1, minutes=30),
            'event_type': 'warning',
            'severity': 'medium',
            'message': 'Battery temperature slightly elevated',
            'source': 'battery',
            'acknowledged': False,
            'acknowledged_at': None,
            'acknowledged_by': None
        },
        {
            'timestamp': datetime.now() - timedelta(minutes=45),
            'event_type': 'info',
            'severity': 'low',
            'message': 'Peak solar generation reached: 4.8kW',
            'source': 'inverter',
            'acknowledged': False,
            'acknowledged_at': None,
            'acknowledged_by': None
        },
        {
            'timestamp': datetime.now() - timedelta(minutes=15),
            'event_type': 'info',
            'severity': 'low',
            'message': 'Grid export mode activated',
            'source': 'system',
            'acknowledged': False,
            'acknowledged_at': None,
            'acknowledged_by': None
        }
    ]
    
    for event in events:
        await session.execute(
            text("""
                INSERT INTO system_events 
                (timestamp, event_type, severity, message, source, acknowledged, 
                 acknowledged_at, acknowledged_by, created_at)
                VALUES (:timestamp, :event_type, :severity, :message, :source, :acknowledged,
                        :acknowledged_at, :acknowledged_by, :created_at)
            """),
            {
                **event,
                'created_at': datetime.now()
            }
        )

def _calculate_solar_factor(hour):
    """Calculate solar generation factor based on hour of day"""
    # Peak at noon (12:00), zero at night
    if 6 <= hour <= 18:
        # Bell curve centered at noon
        peak_hour = 12
        factor = 1 - ((hour - peak_hour) / 6) ** 2
        return max(0, factor)
    else:
        return 0

async def clear_development_data(session: AsyncSession):
    """Clear all development data"""
    logger.info("Clearing development data...")
    
    await session.execute(text("DELETE FROM energy_data"))
    await session.execute(text("DELETE FROM hourly_summaries"))
    await session.execute(text("DELETE FROM daily_summaries"))
    await session.execute(text("DELETE FROM device_registry"))
    await session.execute(text("DELETE FROM system_events"))
    
    await session.commit()
    logger.info("Development data cleared")
