"""
WebSocket chat router for classroom communication and persisted message broadcasts.
"""

import json
from typing import Dict, List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.lms.models.chat import ChatMessage, ChatRoom
from app.lms.auth import get_current_user

router = APIRouter(prefix="/ws", tags=["WebSockets"])

class ConnectionManager:
    """Define the ConnectionManager data structure or service used by this module."""
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

    async def broadcast(self, message: dict, room_id: str, exclude: WebSocket = None):
        if room_id not in self.active_connections:
            return
            
        dead_connections = set()
        for connection in self.active_connections[room_id]:
            if connection == exclude:
                continue
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"DEBUG_CHAT_WS: Broadcast failed for one client: {e}")
                dead_connections.add(connection)
        
        # Cleanup disconnected sockets found during broadcast
        for dead in dead_connections:
            self.active_connections[room_id].discard(dead)
        if room_id in self.active_connections and not self.active_connections[room_id]:
            del self.active_connections[room_id]

manager = ConnectionManager()

@router.websocket("/chat/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, token: str, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time chat.
    Requires a valid JWT token passed as a query parameter (?token=...)
    """
    import jwt
    from app.lms.auth import SECRET_KEY, ALGORITHM
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_aud": False})
        user_id = payload.get("sub")
        if not user_id:
             await websocket.close(code=1008)  # Policy Violation
             return
    except Exception:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, room_id)
    try:
        print(f"DEBUG_CHAT_WS: Connection stable for room {room_id}")
        while True:
            try:
                data = await websocket.receive_text()
                print(f"DEBUG_CHAT_WS: Received data from client: {data}")
                payload = json.loads(data)
                content = payload.get("content")
                
                if content:
                    new_msg = ChatMessage(
                        room_id=room_id,
                        sender_id=user_id,
                        content=content
                    )
                    db.add(new_msg)
                    db.commit()
                    db.refresh(new_msg)
                    
                    msg_dict = {
                        "id": str(new_msg.id),
                        "room_id": str(new_msg.room_id),
                        "sender_id": str(new_msg.sender_id),
                        "content": new_msg.content,
                        "created_at": new_msg.created_at.isoformat()
                    }
                    print(f"DEBUG_CHAT_WS: Message saved and broadcasting: {content[:30]}...")
                    await manager.broadcast(msg_dict, room_id, exclude=websocket)
            except WebSocketDisconnect:
                print(f"DEBUG_CHAT_WS: Client disconnected from room {room_id}")
                break
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"DEBUG_CHAT_WS: Error processing message: {e}")
                continue
    except Exception as fatal_e:
        print(f"DEBUG_CHAT_WS: FATAL connection error: {fatal_e}")
    finally:
        manager.disconnect(websocket, room_id)
