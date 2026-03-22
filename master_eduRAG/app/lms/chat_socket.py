import json
from typing import Dict, List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.lms.models.chat import ChatMessage, ChatRoom
from app.lms.auth import get_current_user

router = APIRouter(prefix="/ws", tags=["WebSockets"])

class ConnectionManager:
    def __init__(self):
        # room_id -> set of active WebSockets
        self.active_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, message: dict, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@router.websocket("/chat/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, db: Session = Depends(get_db)):
    # Note: In production you'd authenticate the WebSocket connection using tokens passed in query params or headers
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            # Simple auth from payload for demonstration
            # Alternatively use a token in the query params during connection
            user_id = payload.get("sender_id")
            content = payload.get("content")
            
            if user_id and content:
                # 1. Save to SQLite Database
                new_msg = ChatMessage(
                    room_id=room_id,
                    sender_id=user_id,
                    content=content
                )
                db.add(new_msg)
                db.commit()
                db.refresh(new_msg)
                
                # 2. Broadcast to room
                msg_dict = {
                    "id": new_msg.id,
                    "room_id": new_msg.room_id,
                    "sender_id": new_msg.sender_id,
                    "content": new_msg.content,
                    "created_at": new_msg.created_at.isoformat()
                }
                await manager.broadcast(msg_dict, room_id)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
