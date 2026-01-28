"""WebSocket Manager"""

from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, ws: WebSocket, channel: str):
        await ws.accept()
        if channel not in self.connections:
            self.connections[channel] = set()
        self.connections[channel].add(ws)
    
    async def disconnect(self, ws: WebSocket, channel: str):
        if channel in self.connections:
            self.connections[channel].discard(ws)
    
    async def send_to_channel(self, channel: str, message: dict):
        if channel in self.connections:
            for ws in list(self.connections[channel]):
                try:
                    await ws.send_json(message)
                except:
                    self.connections[channel].discard(ws)


ws_manager = ConnectionManager()

def get_ws_manager():
    return ws_manager
