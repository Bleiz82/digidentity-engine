"""
DigIdentity Engine — Modelli dati per i lead.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum


class LeadStatus(str, Enum):
    NEW = "new"
    SCRAPING = "scraping"
    GENERATING_FREE = "generating_free"
    FREE_SENT = "free_sent"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_COMPLETED = "payment_completed"
    GENERATING_PREMIUM = "generating_premium"
    PREMIUM_SENT = "premium_sent"
    ERROR = "error"


class LeadCreate(BaseModel):
    """Schema per la creazione di un nuovo lead."""
    company_name: str = Field(..., min_length=2, max_length=200, description="Nome dell'azienda")
    website_url: str = Field("", max_length=500, description="URL del sito web aziendale")
    email: EmailStr = Field(..., description="Email del contatto")
    contact_name: Optional[str] = Field(None, max_length=200, description="Nome del contatto")
    phone: Optional[str] = Field(None, max_length=30, description="Telefono")
    sector: Optional[str] = Field(None, max_length=100, description="Settore aziendale")
    citta: str = Field("", max_length=100, description="Città dell'attività")
    provincia: str = Field("", max_length=100, description="Provincia dell'attività")
    notes: Optional[str] = Field(None, max_length=1000, description="Note aggiuntive")


class LeadResponse(BaseModel):
    """Schema di risposta per un lead."""
    id: str
    company_name: str
    website_url: str = ""
    email: str
    contact_name: Optional[str] = None
    citta: str = ""
    provincia: str = ""
    status: LeadStatus
    created_at: Optional[str] = None
