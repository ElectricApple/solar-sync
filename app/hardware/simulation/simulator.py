"""
Simulation driver for when no real hardware is available.
Provides realistic solar data for development and testing.
"""

import asyncio
import logging
import random
import math
from datetime import datetime, timedelta
from typing import Optional

from ..drivers.base_driver import BaseDriver, DeviceInfo, DeviceData, DeviceStatus, DeviceType, DeviceControl

logger = logging.getLogger(__name__)


class SimulationDriver(BaseDriver):
    """Simulation driver that generates realistic solar data."""
    
    def __init__(self, device_info: DeviceInfo):
        super().__init__(device_info)
        self.status = DeviceStatus.SIMULATION
        self.simulation_time = datetime.now()
        self.day_start = self.simulation_time.replace(hour=6, minute=0, second=0, microsecond=0)
        self.day_end = self.simulation_time.replace(hour=18, minute=0, second=0, microsecond=0)
        
        # Simulation parameters
        self.max_solar_power = 5000  # W
        self.battery_capacity = 100  # Ah at 48V
        self.battery_voltage = 48.0  # V
        self.load_power_base = 800   # W base load
        self.grid_power_limit = 3000 # W grid limit
        
        # State variables
        self.battery_soc = 75.0  # Start at 75%
        self.last_update = datetime.now()
        
    async def connect(self) -> bool:
        """Simulate connection."""
        logger.info("Simulation driver connected")
        self.status = DeviceStatus.CONNECTED
        return True
    
    async def disconnect(self) -> None:
        """Simulate disconnection."""
        logger.info("Simulation driver disconnected")
        self.status = DeviceStatus.DISCONNECTED
    
    async def read_data(self) -> Optional[DeviceData]:
        """Generate realistic solar data."""
        now = datetime.now()
        time_diff = (now - self.last_update).total_seconds()
        self.last_update = now
        
        # Calculate solar power based on time of day
        solar_power = self._calculate_solar_power(now)
        
        # Simulate load variations
        load_power = self._calculate_load_power(now)
        
        # Simulate battery behavior
        battery_power, battery_soc = self._calculate_battery_power(solar_power, load_power, time_diff)
        
        # Calculate grid power (positive = importing, negative = exporting)
        grid_power = load_power - solar_power - battery_power
        
        # Calculate system efficiency
        efficiency = self._calculate_efficiency(solar_power, load_power)
        
        # Generate temperature data
        temperature = self._calculate_temperature(now)
        
        # Create device data
        data = DeviceData(
            timestamp=now.timestamp(),
            solar_power_w=solar_power,
            battery_power_w=battery_power,
            load_power_w=load_power,
            grid_power_w=grid_power,
            battery_soc_percent=battery_soc,
            battery_voltage_v=self.battery_voltage + random.uniform(-0.5, 0.5),
            system_efficiency_percent=efficiency,
            temperature_c=temperature,
            device_status=self.status
        )
        
        self.last_data = data
        return data
    
    async def write_control(self, control: DeviceControl) -> bool:
        """Simulate control commands."""
        logger.info(f"Simulation control command: {control}")
        # In simulation, we just log the command
        return True
    
    async def test_connection(self) -> bool:
        """Simulation is always connected."""
        return True
    
    async def get_device_info(self) -> DeviceInfo:
        """Return device information."""
        return self.device_info
    
    def _calculate_solar_power(self, now: datetime) -> float:
        """Calculate realistic solar power based on time of day."""
        # Convert to hours since sunrise
        if now < self.day_start or now > self.day_end:
            return 0.0
        
        hours_since_sunrise = (now - self.day_start).total_seconds() / 3600
        day_length = (self.day_end - self.day_start).total_seconds() / 3600
        
        # Create a bell curve for solar production
        # Peak at noon (6 hours after sunrise)
        peak_hour = 6
        time_from_peak = abs(hours_since_sunrise - peak_hour)
        
        # Gaussian curve with some randomness
        solar_factor = math.exp(-(time_from_peak ** 2) / 8)  # Bell curve
        solar_factor *= (1 + random.uniform(-0.1, 0.1))  # Add some randomness
        
        # Apply weather variations
        weather_factor = random.uniform(0.7, 1.0)  # 70-100% of clear sky
        
        solar_power = self.max_solar_power * solar_factor * weather_factor
        
        # Add some realistic fluctuations
        solar_power += random.uniform(-50, 50)
        
        return max(0, solar_power)
    
    def _calculate_load_power(self, now: datetime) -> float:
        """Calculate realistic load power."""
        base_load = self.load_power_base
        
        # Add time-based variations
        hour = now.hour
        
        # Morning peak (7-9 AM)
        if 7 <= hour <= 9:
            base_load *= random.uniform(1.2, 1.5)
        # Evening peak (18-22 PM)
        elif 18 <= hour <= 22:
            base_load *= random.uniform(1.3, 1.8)
        # Night (22-6 AM)
        elif hour >= 22 or hour <= 6:
            base_load *= random.uniform(0.3, 0.6)
        
        # Add random variations
        load_power = base_load + random.uniform(-100, 200)
        
        return max(0, load_power)
    
    def _calculate_battery_power(self, solar_power: float, load_power: float, time_diff: float) -> tuple[float, float]:
        """Calculate battery power and update SOC."""
        # Simple battery model
        excess_power = solar_power - load_power
        
        # Battery charging/discharging logic
        if excess_power > 0 and self.battery_soc < 95:
            # Charging
            charge_power = min(excess_power * 0.8, 2000)  # Max 2kW charging
            battery_power = -charge_power  # Negative = charging
            soc_change = (charge_power * time_diff) / (self.battery_capacity * self.battery_voltage * 3600) * 100
            self.battery_soc = min(95, self.battery_soc + soc_change)
            
        elif excess_power < 0 and self.battery_soc > 20:
            # Discharging
            discharge_power = min(abs(excess_power) * 0.9, 3000)  # Max 3kW discharging
            battery_power = discharge_power  # Positive = discharging
            soc_change = (discharge_power * time_diff) / (self.battery_capacity * self.battery_voltage * 3600) * 100
            self.battery_soc = max(20, self.battery_soc - soc_change)
            
        else:
            # No battery activity
            battery_power = 0
        
        # Add some realistic variations
        battery_power += random.uniform(-50, 50)
        
        return battery_power, self.battery_soc
    
    def _calculate_efficiency(self, solar_power: float, load_power: float) -> float:
        """Calculate system efficiency."""
        if solar_power == 0:
            return 0.0
        
        # Base efficiency varies with power level
        base_efficiency = 85.0  # Base 85%
        
        # Efficiency is higher at moderate power levels
        power_ratio = min(solar_power / self.max_solar_power, 1.0)
        if 0.3 <= power_ratio <= 0.7:
            base_efficiency += 5  # Peak efficiency at 30-70% power
        
        # Add some realistic variations
        efficiency = base_efficiency + random.uniform(-2, 2)
        
        return max(0, min(100, efficiency))
    
    def _calculate_temperature(self, now: datetime) -> float:
        """Calculate realistic temperature."""
        # Base temperature varies by time of day
        hour = now.hour
        
        if 6 <= hour <= 18:
            # Daytime: 20-35°C
            base_temp = 25 + 10 * math.sin((hour - 6) * math.pi / 12)
        else:
            # Nighttime: 10-20°C
            base_temp = 15 + 5 * math.sin((hour - 18) * math.pi / 12)
        
        # Add seasonal variation (simplified)
        day_of_year = now.timetuple().tm_yday
        seasonal_variation = 10 * math.sin((day_of_year - 172) * 2 * math.pi / 365)
        
        temperature = base_temp + seasonal_variation + random.uniform(-2, 2)
        
        return temperature
