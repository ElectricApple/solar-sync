import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import EnergyData, DeviceRegistry, SystemEvent
from app.services.data_simulator import SolarDataSimulator
import logging

logger = logging.getLogger(__name__)


async def seed_development_data(session: AsyncSession):
    """Seed development database with realistic data"""
    
    # Check if data already exists
    from sqlalchemy import text
    existing_data = await session.execute(
        text("SELECT COUNT(*) FROM energy_data")
    )
    if existing_data.scalar() > 0:
        logger.info("Database already contains data, skipping seed")
        return
    
    logger.info("Seeding development database...")
    
    # Create simulated devices
    devices = [
        DeviceRegistry(
            device_id="INV001",
            name="Solar Inverter",
            manufacturer="SolarTech",
            model="ST-5000W",
            device_type="inverter",
            is_simulated=True,
            status="online",
            last_seen=datetime.now(),
            config_json='{"max_power": 5000, "efficiency": 0.95}'
        ),
        DeviceRegistry(
            device_id="BAT001",
            name="Battery Bank",
            manufacturer="PowerStore",
            model="PS-48V-200Ah",
            device_type="battery",
            is_simulated=True,
            status="online",
            last_seen=datetime.now(),
            config_json='{"capacity": 9600, "voltage": 48, "chemistry": "lithium"}'
        ),
        DeviceRegistry(
            device_id="PANEL001",
            name="Solar Array",
            manufacturer="SunPower",
            model="SP-400W",
            device_type="panel",
            is_simulated=True,
            status="online",
            last_seen=datetime.now(),
            config_json='{"total_panels": 10, "total_power": 4000}'
        )
    ]
    
    for device in devices:
        session.add(device)
    
    # Generate historical energy data (last 24 hours)
    simulator = SolarDataSimulator()
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    current_time = start_time
    while current_time <= end_time:
        # Generate data for this timestamp
        data = simulator.get_data_for_time(current_time)
        
        energy_data = EnergyData(
            timestamp=current_time,
            solar_power_w=data["solar_power_w"],
            battery_power_w=data["battery_power_w"],
            battery_soc_percent=data["battery_soc_percent"],
            battery_voltage_v=data["battery_voltage_v"],
            load_power_w=data["load_power_w"],
            grid_power_w=data["grid_power_w"],
            inverter_temp_c=data["inverter_temp_c"],
            system_efficiency_percent=data["system_efficiency_percent"]
        )
        
        session.add(energy_data)
        
        # Move to next interval (5 minutes)
        current_time += timedelta(minutes=5)
    
    # Add some system events
    events = [
        SystemEvent(
            timestamp=datetime.now() - timedelta(hours=2),
            event_type="info",
            severity="low",
            message="System started successfully",
            source="system"
        ),
        SystemEvent(
            timestamp=datetime.now() - timedelta(hours=1),
            event_type="info",
            severity="low",
            message="Solar generation peak reached: 3.8kW",
            source="inverter"
        ),
        SystemEvent(
            timestamp=datetime.now() - timedelta(minutes=30),
            event_type="warning",
            severity="medium",
            message="Battery SOC below 20%",
            source="battery"
        )
    ]
    
    for event in events:
        session.add(event)
    
    await session.commit()
    logger.info("Development data seeded successfully")


async def clear_development_data(session: AsyncSession):
    """Clear all development data"""
    logger.info("Clearing development data...")
    
    await session.execute(text("DELETE FROM energy_data"))
    await session.execute(text("DELETE FROM device_registry"))
    await session.execute(text("DELETE FROM system_events"))
    
    await session.commit()
    logger.info("Development data cleared")
