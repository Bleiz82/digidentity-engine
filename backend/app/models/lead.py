"""
DigIdentity Engine — Lead Models
Pydantic schemas per validazione input/output lead.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.validators import validate_italian_phone, validate_url



class LeadInput(BaseModel):
    """
    Schema per input del form lead (4 step).
    Validazione rigorosa di tutti i campi obbligatori.
    """
    
    # Step 1 — Dati Azienda
    nome_azienda: str = Field(..., min_length=2, max_length=200)
    settore_attivita: str = Field(..., min_length=2, max_length=100)
    sito_web: Optional[str] = Field(None, max_length=500)
    citta: str = Field(..., min_length=2, max_length=100)
    provincia: str = Field(..., min_length=2, max_length=2)  # Sigla provincia (es. CA, MI)
    
    # Step 2 — Presenza Online Attuale
    ha_google_my_business: bool = False
    ha_social_attivi: bool = False
    piattaforme_social: List[str] = Field(default_factory=list)
    ha_sito_web: bool = False
    
    # Step 3 — Obiettivi e Urgenza
    obiettivo_principale: Optional[str] = Field(None, max_length=200)
    urgenza: int = Field(..., ge=1, le=5)
    budget_mensile_indicativo: Optional[str] = Field(None, max_length=50)
    
    # Step 4 — Contatto
    nome_contatto: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    telefono: str = Field(..., min_length=9, max_length=20)
    consenso_privacy: bool = Field(..., description="Deve essere True")
    consenso_marketing: bool = False
    
    # Tracking (opzionali, aggiunti dal backend)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    
    @field_validator('telefono')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Valida formato telefono italiano."""
        if not validate_italian_phone(v):
            raise ValueError('Formato telefono non valido. Inserisci un numero italiano valido.')
        return v
    
    @field_validator('sito_web')
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        """Valida formato URL sito web."""
        if v and not validate_url(v):
            raise ValueError('Formato URL non valido. Deve iniziare con http:// o https://')
        return v
    
    @field_validator('consenso_privacy')
    @classmethod
    def validate_privacy_consent(cls, v: bool) -> bool:
        """Verifica che il consenso privacy sia stato dato."""
        if not v:
            raise ValueError('Il consenso alla privacy è obbligatorio.')
        return v
    
    @field_validator('provincia')
    @classmethod
    def validate_provincia(cls, v: str) -> str:
        """Normalizza sigla provincia in uppercase."""
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "nome_azienda": "Ristorante Da Mario",
                "settore_attivita": "Ristorazione",
                "sito_web": "https://www.ristorantedamario.it",
                "citta": "Cagliari",
                "provincia": "CA",
                "ha_google_my_business": True,
                "ha_social_attivi": True,
                "piattaforme_social": ["Facebook", "Instagram"],
                "ha_sito_web": True,
                "obiettivo_principale": "Aumentare prenotazioni online",
                "urgenza": 4,
                "budget_mensile_indicativo": "500-1000",
                "nome_contatto": "Mario Rossi",
                "email": "mario@ristorantedamario.it",
                "telefono": "+39 340 123 4567",
                "consenso_privacy": True,
                "consenso_marketing": True
            }
        }


class LeadResponse(BaseModel):
    """
    Schema per risposta dopo creazione lead.
    """
    status: str = "accepted"
    workflow_id: str
    redirect: str
    message: str = "Diagnosi in elaborazione. Riceverai il report via email tra pochi minuti."


class LeadDB(BaseModel):
    """
    Schema per lead salvato nel database (con tutti i campi).
    """
    id: str
    nome_contatto: str
    email: str
    telefono: str
    nome_azienda: str
    settore_attivita: str
    sito_web: Optional[str]
    citta: str
    provincia: str
    ha_google_my_business: bool
    ha_social_attivi: bool
    piattaforme_social: List[str]
    ha_sito_web: bool
    obiettivo_principale: Optional[str]
    urgenza: int
    budget_mensile_indicativo: Optional[str]
    consenso_privacy: bool
    consenso_marketing: bool
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
