from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum

class GeoAuditStatus(str, Enum):
    PENDING     = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED   = "completed"
    ERROR       = "error"

class GeoAuditPiano(str, Enum):
    SINGOLO         = "singolo"
    AGENCY_MONTHLY  = "agency_monthly"
    AGENCY_ANNUAL   = "agency_annual"

class GeoAuditCreate(BaseModel):
    url_sito:      str           = Field(..., description="URL sito")
    email_cliente: EmailStr      = Field(..., description="Email cliente")
    piano:         GeoAuditPiano = Field(GeoAuditPiano.SINGOLO)

class GeoAuditResponse(BaseModel):
    id:           str
    url_sito:     str
    email_cliente: str
    piano:        str
    status:       GeoAuditStatus
    geo_score:    Optional[int] = None
    pdf_url:      Optional[str] = None
    created_at:   Optional[str] = None
    completed_at: Optional[str] = None
