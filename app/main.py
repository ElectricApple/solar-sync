"""
Solar Sync - Main Application
Professional Solar Monitoring System
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os

from .config.database import init_db, AsyncSessionLocal
from .database.seed_data import seed_development_data
from .services.websocket_manager import websocket_manager
from .hardware.device_manager import device_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Solar Sync application...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Seed development data
    async with AsyncSessionLocal() as session:
        await seed_development_data(session)
    logger.info("Development data seeded")
    
    # Start WebSocket manager
    await websocket_manager.start_update_loop()
    logger.info("WebSocket manager started")
    
    # Start hardware device manager
    await device_manager.start()
    logger.info("Hardware device manager started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Solar Sync application...")
    
    # Stop hardware device manager
    await device_manager.stop()
    logger.info("Hardware device manager stopped")
    
    # Stop WebSocket manager
    await websocket_manager.stop_update_loop()
    logger.info("WebSocket manager stopped")


# Create FastAPI application
app = FastAPI(
    title="Solar Sync",
    description="Professional Solar Monitoring System",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Import and include routers
from .routers import dashboard, charts, control, settings, hardware

app.include_router(dashboard.router)
app.include_router(charts.router)
app.include_router(control.router)
app.include_router(settings.router)
app.include_router(hardware.router)


@app.get("/")
async def root(request: Request):
    """Root endpoint - redirect to dashboard."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "hardware_mode": "simulation" if device_manager.simulation_mode else "real_devices",
        "connected_devices": sum(1 for d in device_manager.devices.values() if d.status.value == "connected")
    }


@app.get("/api/status")
async def api_status():
    """API status endpoint."""
    return {
        "status": "operational",
        "version": "2.0.0",
        "hardware": {
            "simulation_mode": device_manager.simulation_mode,
            "total_devices": len(device_manager.devices),
            "connected_devices": sum(1 for d in device_manager.devices.values() if d.status.value == "connected")
        },
        "websocket": {
            "active_connections": len(websocket_manager.active_connections)
        }
    }
