import math
import time
import random
from datetime import datetime, timezone
from typing import Dict, Any


class SolarDataSimulator:
    """Generates realistic solar system data for development"""
    
    def __init__(self):
        self.battery_soc = 75.0  # Starting SOC
        self.system_efficiency = 85.0
        self.base_load = 800
        self.weather_factor = 0.8
        
    def get_current_data(self) -> Dict[str, Any]:
        """Generate realistic data based on current time"""
        return self.get_data_for_time(datetime.now())
    
    def get_data_for_time(self, timestamp: datetime) -> Dict[str, Any]:
        """Generate realistic data for a specific timestamp"""
        hour = timestamp.hour + timestamp.minute / 60.0
        
        # Solar generation curve (sunrise ~6:00, sunset ~18:00)
        if 6 <= hour <= 18:
            # Sine wave for solar generation with weather variation
            solar_factor = max(0, math.sin((hour - 6) * math.pi / 12))
            weather_factor = self.weather_factor + 0.2 * math.sin(time.time() / 1800)  # 30-min weather cycles
            solar_power = int(4000 * solar_factor * weather_factor)  # 4kW max system
        else:
            solar_power = 0
        
        # Battery behavior based on solar generation
        if solar_power > 1500:  # High solar
            battery_power = -random.randint(200, 800)  # Charging
            self.battery_soc = min(100, self.battery_soc + 0.1)
        elif solar_power > 500:  # Medium solar
            battery_power = random.randint(-200, 200)  # Floating
        else:  # Low/no solar
            battery_power = random.randint(300, 1000)  # Discharging
            self.battery_soc = max(10, self.battery_soc - 0.1)
        
        # Load varies by time of day
        base_load = self.base_load + 400 * math.sin((hour - 12) * math.pi / 12)  # Peak at 6PM
        load_power = int(base_load + random.uniform(-100, 100))
        
        # Grid interaction
        net_power = solar_power + battery_power - load_power
        grid_power = -net_power  # Negative = export to grid
        
        # System temperature
        ambient_temp = 20 + 15 * math.sin((hour - 12) * math.pi / 12)
        inverter_temp = ambient_temp + (solar_power / 200)  # Heating under load
        
        return {
            "timestamp": timestamp.isoformat(),
            "solar_power_w": solar_power,
            "battery_power_w": battery_power,
            "battery_soc_percent": round(self.battery_soc, 1),
            "battery_voltage_v": round(48.0 + (self.battery_soc - 50) * 0.2, 2),
            "load_power_w": load_power,
            "grid_power_w": grid_power,
            "inverter_temp_c": round(inverter_temp, 1),
            "system_efficiency_percent": round(self.system_efficiency + random.uniform(-2, 2), 1)
        }
    
    def update_weather(self, factor: float):
        """Update weather factor (0.0 = cloudy, 1.0 = sunny)"""
        self.weather_factor = max(0.0, min(1.0, factor))
    
    def update_base_load(self, load: int):
        """Update base load consumption"""
        self.base_load = max(0, load)
    
    def reset_battery_soc(self, soc: float):
        """Reset battery state of charge"""
        self.battery_soc = max(0.0, min(100.0, soc))
