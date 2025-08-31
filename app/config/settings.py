import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Environment-based configuration for Solar Sync"""
    
    # Environment detection
    environment: str = "development"
    is_pi: bool = os.path.exists("/sys/firmware/devicetree/base/model")
    
    # Database configuration
    database_url: str = "sqlite:///./data/solar-sync-dev.db"
    
    # Hardware simulation
    simulate_hardware: bool = True
    
    # Performance tuning
    websocket_update_interval: int = 2  # seconds
    max_chart_points: int = 5000
    
    # Hardware configuration (for Pi)
    rs485_device: str = "/dev/ttyUSB0"
    rs485_baudrate: int = 9600
    
    # System configuration
    system_name: str = "Solar Sync"
    system_version: str = "1.0.0"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Adjust settings based on environment
        if self.environment == "production" or self.is_pi:
            self.simulate_hardware = False
            self.websocket_update_interval = 5
            self.max_chart_points = 1000
            self.database_url = "sqlite:///opt/solar-sync/data/solar-sync.db"
            self.log_level = "INFO"
        else:
            # Development settings
            self.simulate_hardware = True
            self.websocket_update_interval = 2
            self.max_chart_points = 5000
            self.log_level = "DEBUG"
        
        # Create data directory if it doesn't exist
        data_dir = Path("./data")
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
