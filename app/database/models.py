from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Index
from sqlalchemy.sql import func
from app.config.database import Base


class SystemConfig(Base):
    """System configuration storage"""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text)
    description = Column(String(255))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class EnergyData(Base):
    """Energy monitoring data"""
    __tablename__ = "energy_data"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    solar_power_w = Column(Integer, default=0)
    battery_power_w = Column(Integer, default=0)  # Negative = charging
    battery_soc_percent = Column(Float, default=0)
    battery_voltage_v = Column(Float, default=0)
    load_power_w = Column(Integer, default=0)
    grid_power_w = Column(Integer, default=0)     # Negative = export
    inverter_temp_c = Column(Float, default=0)
    system_efficiency_percent = Column(Float, default=0)
    
    # Index for efficient time-based queries
    __table_args__ = (
        Index('idx_energy_data_timestamp', 'timestamp'),
    )


class DeviceRegistry(Base):
    """Device registry for connected hardware"""
    __tablename__ = "device_registry"
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    manufacturer = Column(String(50))
    model = Column(String(50))
    device_type = Column(String(20), default="inverter")
    is_simulated = Column(Boolean, default=False)
    status = Column(String(20), default="offline")
    last_seen = Column(DateTime)
    config_json = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SystemEvent(Base):
    """System events and alerts"""
    __tablename__ = "system_events"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # info, warning, error, alert
    severity = Column(String(20), default="info")    # low, medium, high, critical
    message = Column(Text, nullable=False)
    source = Column(String(50))  # system, inverter, battery, etc.
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String(50))
    
    # Index for efficient event queries
    __table_args__ = (
        Index('idx_system_events_timestamp', 'timestamp'),
        Index('idx_system_events_type', 'event_type'),
        Index('idx_system_events_severity', 'severity'),
    )
