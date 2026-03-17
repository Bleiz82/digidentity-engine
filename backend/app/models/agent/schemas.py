from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ChannelType(str, Enum):
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    CHATBOT = "chatbot"
    MESSENGER = "messenger"
    INSTAGRAM = "instagram"
    VAPI = "vapi"
    EMAIL = "email"
    SMS = "sms"


class ConversationStatus(str, Enum):
    BOT = "bot"
    HUMAN = "human"
    CLOSED = "closed"


class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class SenderType(str, Enum):
    USER = "user"
    AI = "ai"
    HUMAN_AGENT = "human_agent"
    SYSTEM = "system"


class ContentType(str, Enum):
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    LOCATION = "location"


class AppointmentStatus(str, Enum):
    CONFERMATO = "confermato"
    CANCELLATO = "cancellato"
    RIPROGRAMMATO = "riprogrammato"
    COMPLETATO = "completato"
    NO_SHOW = "no_show"


class LeadStatus(str, Enum):
    NEW = "new"
    ENGAGED = "engaged"
    QUALIFIED = "qualified"
    APPOINTMENT_SET = "appointment_set"
    CONVERTED = "converted"
    LOST = "lost"


class ContactResponse(BaseModel):
    id: str
    nome: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    nome_attivita: Optional[str] = None
    lead_status: Optional[str] = "new"
    lead_score: Optional[int] = 0
    canale_primo_contatto: Optional[str] = None
    ultimo_canale: Optional[str] = None
    has_diagnosis: Optional[bool] = False
    has_geo_audit: Optional[bool] = False
    created_at: Optional[datetime] = None


class ConversationResponse(BaseModel):
    id: str
    contact_id: str
    channel_type: str
    status: str = "bot"
    is_ai_active: bool = True
    last_message_preview: Optional[str] = None
    last_message_at: Optional[datetime] = None
    messages_count: int = 0
    unread_count: int = 0
    created_at: Optional[datetime] = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    direction: str
    sender_type: str
    content: Optional[str] = None
    content_type: str = "text"
    media_url: Optional[str] = None
    created_at: Optional[datetime] = None


class InboxItem(BaseModel):
    conversation_id: str
    contact_id: str
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    channel: str
    status: str
    is_ai_active: bool
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    lead_status: Optional[str] = None
    has_diagnosis: bool = False
    has_geo_audit: bool = False


class InboxResponse(BaseModel):
    items: List[InboxItem]
    total: int
    ai_active_count: int = 0
    human_active_count: int = 0
    unread_total: int = 0
