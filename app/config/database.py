from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
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

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    from app.database.models import SystemConfig, EnergyData, DeviceRegistry
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
        # Insert default system configuration
        await conn.run_sync(_insert_default_config)


def _insert_default_config(connection):
    """Insert default system configuration"""
    from app.database.models import SystemConfig
    from sqlalchemy import text
    
    # Check if config already exists
    result = connection.execute(
        text("SELECT COUNT(*) FROM system_config WHERE key = 'system_name'")
    ).scalar()
    
    if result == 0:
        default_configs = [
            ("system_name", settings.system_name, "System display name"),
            ("system_version", settings.system_version, "System version"),
            ("simulate_hardware", str(settings.simulate_hardware), "Hardware simulation mode"),
            ("websocket_interval", str(settings.websocket_update_interval), "WebSocket update interval"),
        ]
        
        for key, value, description in default_configs:
            connection.execute(
                text("INSERT INTO system_config (key, value, description) VALUES (:key, :value, :description)"),
                {"key": key, "value": value, "description": description}
            )
        
        connection.commit()
