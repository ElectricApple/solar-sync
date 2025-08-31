import asyncio
import json
import logging
from typing import Dict, Set, Any
from fastapi import WebSocket
from app.services.data_simulator import SolarDataSimulator
from app.config.settings import settings
from app.database.models import EnergyData
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and real-time data updates"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.simulator = SolarDataSimulator()
        self.update_task: asyncio.Task = None
        
    async def connect(self, websocket: WebSocket):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Send initial data
        await self.send_data_to_client(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_data_to_client(self, websocket: WebSocket):
        """Send current data to a specific client"""
        try:
            data = self.simulator.get_current_data()
            await websocket.send_text(json.dumps({
                "type": "energy_data",
                "data": data
            }))
        except Exception as e:
            logger.error(f"Error sending data to client: {e}")
            self.disconnect(websocket)
    
    async def broadcast_data(self, data: Dict[str, Any]):
        """Broadcast data to all connected clients"""
        if not self.active_connections:
            return
            
        message = json.dumps({
            "type": "energy_data",
            "data": data
        })
        
        # Send to all connected clients
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def start_update_loop(self):
        """Start the periodic update loop"""
        if self.update_task and not self.update_task.done():
            return
            
        self.update_task = asyncio.create_task(self._update_loop())
        logger.info("WebSocket update loop started")
    
    async def stop_update_loop(self):
        """Stop the periodic update loop"""
        if self.update_task and not self.update_task.done():
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
            logger.info("WebSocket update loop stopped")
    
    async def _update_loop(self):
        """Main update loop that broadcasts data periodically"""
        while True:
            try:
                # Generate current data
                data = self.simulator.get_current_data()
                
                # Broadcast to all clients
                await self.broadcast_data(data)
                
                # Wait for next update
                await asyncio.sleep(settings.websocket_update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def save_data_to_db(self, session: AsyncSession, data: Dict[str, Any]):
        """Save energy data to database"""
        try:
            from datetime import datetime
            
            energy_data = EnergyData(
                timestamp=datetime.fromisoformat(data["timestamp"]),
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
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error saving data to database: {e}")
            await session.rollback()


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
