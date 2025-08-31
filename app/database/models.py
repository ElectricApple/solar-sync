from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class SystemConfig(Base):
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EnergyData(Base):
    __tablename__ = "energy_data"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    solar_power_w = Column(Integer, default=0)
    battery_power_w = Column(Integer, default=0)  # Negative = charging
    battery_soc_percent = Column(Float, default=0)
    battery_voltage_v = Column(Float, default=0)
    load_power_w = Column(Integer, default=0)
    grid_power_w = Column(Integer, default=0)  # Negative = export
    grid_voltage_v = Column(Float, default=0)
    grid_frequency_hz = Column(Float, default=50.0)
    inverter_temp_c = Column(Float, default=0)
    system_efficiency_percent = Column(Float, default=0)
    data_quality = Column(Float, default=1.0)  # Data reliability score (0-1)
    source = Column(String(50), default='simulator')  # 'simulator', 'device', 'manual'
    created_at = Column(DateTime, default=datetime.utcnow)

class HourlySummary(Base):
    __tablename__ = "hourly_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    hour_start = Column(DateTime, nullable=False, unique=True, index=True)
    avg_solar_power_w = Column(Integer, default=0)
    max_solar_power_w = Column(Integer, default=0)
    total_solar_kwh = Column(Float, default=0)
    avg_battery_soc = Column(Float, default=0)
    total_load_kwh = Column(Float, default=0)
    avg_efficiency = Column(Float, default=0)
    data_points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class DailySummary(Base):
    __tablename__ = "daily_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(10), nullable=False, unique=True, index=True)  # YYYY-MM-DD format
    total_solar_kwh = Column(Float, default=0)
    total_load_kwh = Column(Float, default=0)
    total_battery_cycles = Column(Float, default=0)
    peak_solar_power_w = Column(Integer, default=0)
    avg_efficiency = Column(Float, default=0)
    min_battery_soc = Column(Float, default=100)
    max_battery_soc = Column(Float, default=0)
    weather_score = Column(Float, default=1.0)  # Weather quality (0-1)
    data_quality = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class DeviceRegistry(Base):
    __tablename__ = "device_registry"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), unique=True, nullable=False, index=True)
    device_type = Column(String(50), nullable=False)  # 'inverter', 'battery', 'sensor'
    name = Column(String(100), nullable=False)
    model = Column(String(100))
    manufacturer = Column(String(100))
    firmware_version = Column(String(50))
    ip_address = Column(String(45))
    port = Column(Integer)
    status = Column(String(20), default='offline')  # 'online', 'offline', 'error'
    last_seen = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SystemEvent(Base):
    __tablename__ = "system_events"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # 'alert', 'warning', 'info', 'error'
    severity = Column(String(20), index=True)  # 'low', 'medium', 'high', 'critical'
    message = Column(Text, nullable=False)
    source = Column(String(50))  # 'system', 'device', 'user'
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

# Create indexes for better query performance
Index('idx_energy_timestamp', EnergyData.timestamp.desc())
Index('idx_energy_date', EnergyData.timestamp.cast(String).like('%'))
Index('idx_hourly_start', HourlySummary.hour_start.desc())
Index('idx_daily_date', DailySummary.date.desc())
Index('idx_system_events_timestamp', SystemEvent.timestamp)
Index('idx_system_events_severity', SystemEvent.severity)
Index('idx_system_events_type', SystemEvent.event_type)
