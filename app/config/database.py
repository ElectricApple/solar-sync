from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Convert SQLite URL to async
async_database_url = settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")

# Create async engine
engine = create_async_engine(
    async_database_url,
    echo=settings.log_level == "DEBUG",
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database tables"""
    from app.database.models import Base, SystemConfig, EnergyData, DeviceRegistry, SystemEvent, HourlySummary, DailySummary
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
        # Insert default configuration
        await conn.run_sync(_insert_default_config)

def _insert_default_config(connection):
    """Insert default system configuration"""
    # Check if config already exists
    result = connection.execute(
        text("SELECT COUNT(*) FROM system_config WHERE key = 'system_name'")
    ).scalar()
    
    if result == 0:
        # Insert default configuration
        default_configs = [
            ('system_name', 'Solar Sync', 'System display name'),
            ('system_version', '2.0.0', 'System version'),
            ('data_retention_days', '90', 'Days to retain historical data'),
            ('chart_update_interval', '5', 'Chart update interval in seconds'),
            ('websocket_enabled', 'true', 'Enable WebSocket real-time updates'),
            ('simulation_enabled', 'true', 'Enable data simulation for development'),
            ('export_enabled', 'true', 'Enable data export functionality'),
            ('max_chart_points', '1000', 'Maximum data points for charts'),
            ('timezone', 'UTC', 'System timezone'),
            ('units', 'metric', 'Measurement units (metric/imperial)'),
        ]
        
        for key, value, description in default_configs:
            connection.execute(
                text("INSERT INTO system_config (key, value, description) VALUES (:key, :value, :description)"),
                {"key": key, "value": value, "description": description}
            )
        
        connection.commit()
        logger.info("Default system configuration inserted")
