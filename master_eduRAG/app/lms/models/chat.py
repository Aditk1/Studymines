import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class ChatRoom(Base):
    __tablename__ = "lms_chat_rooms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    classroom_id = Column(String(36), ForeignKey("lms_classrooms.id", ondelete="CASCADE"), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    room_type = Column(String(50), nullable=False)

    last_message_at = Column(DateTime, nullable=True, index=True)
    is_pinned = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship(
        "ChatMessage",
        back_populates="room",
        cascade="all, delete-orphan",
        foreign_keys="ChatMessage.room_id",
    )

class ChatMessage(Base):
    __tablename__ = "lms_chat_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id = Column(String(36), ForeignKey("lms_chat_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    content = Column(Text, nullable=False)
    reply_to_id = Column(String(36), ForeignKey("lms_chat_messages.id", ondelete="SET NULL"), nullable=True)
    
    reactions = Column(JSON, nullable=False, default=dict)
    role_snapshot = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    room = relationship("ChatRoom", back_populates="messages", foreign_keys=[room_id])
    reply_to = relationship("ChatMessage", remote_side=[id], foreign_keys=[reply_to_id])

    __table_args__ = (
        Index("idx_lms_chat_msg_room_created", "room_id", "created_at"),
    )
