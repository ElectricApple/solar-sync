import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from app.config.settings import settings
from app.config.database import init_db
from app.services.websocket_manager import websocket_manager
from app.database.seed_data import seed_development_data
from app.routers import dashboard, charts, control, settings as settings_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Solar Sync application...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Seed development data if in development mode
    if settings.environment == "development":
        from app.config.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await seed_development_data(session)
        logger.info("Development data seeded")
    
    # Start WebSocket update loop
    await websocket_manager.start_update_loop()
    logger.info("WebSocket manager started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Solar Sync application...")
    await websocket_manager.stop_update_loop()
    logger.info("WebSocket manager stopped")


# Create FastAPI application
app = FastAPI(
    title=settings.system_name,
    version=settings.system_version,
    description="Professional Solar Monitoring System",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Create templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(dashboard.router)
app.include_router(charts.router)
app.include_router(control.router)
app.include_router(settings_router.router)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/charts", response_class=HTMLResponse)
async def charts_page(request: Request):
    """Charts page"""
    return templates.TemplateResponse("charts.html", {"request": request})


@app.get("/control", response_class=HTMLResponse)
async def control_page(request: Request):
    """Control page"""
    return templates.TemplateResponse("control.html", {"request": request})


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page"""
    return templates.TemplateResponse("settings.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "system": settings.system_name,
        "version": settings.system_version,
        "environment": settings.environment,
        "simulate_hardware": settings.simulate_hardware
    }


@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "name": settings.system_name,
        "version": settings.system_version,
        "endpoints": {
            "dashboard": "/dashboard",
            "charts": "/charts", 
            "control": "/control",
            "settings": "/settings",
            "websocket": "/dashboard/ws",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )
