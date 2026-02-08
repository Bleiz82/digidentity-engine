"""
DigIdentity Engine — Lead Service
Logica di business per gestione lead: validazione, deduplicazione, salvataggio.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from app.db import get_supabase_client
from app.models.lead import LeadInput
from app.validators import normalize_phone



async def create_lead(lead_data: LeadInput) -> Dict[str, Any]:
    """
    Crea un nuovo lead o aggiorna uno esistente.
    Se esiste con stessa email, resetta e riprocessa sempre.
    """
    supabase = get_supabase_client()
    
    normalized_phone = normalize_phone(lead_data.telefono)
    
    lead_dict = {
        "nome_contatto": lead_data.nome_contatto,
        "email": lead_data.email.lower(),
        "telefono": normalized_phone,
        "nome_azienda": lead_data.nome_azienda,
        "settore_attivita": lead_data.settore_attivita,
        "sito_web": lead_data.sito_web,
        "citta": lead_data.citta,
        "provincia": lead_data.provincia.upper(),
        "ha_google_my_business": lead_data.ha_google_my_business,
        "ha_social_attivi": lead_data.ha_social_attivi,
        "piattaforme_social": lead_data.piattaforme_social,
        "ha_sito_web": lead_data.ha_sito_web,
        "obiettivo_principale": lead_data.obiettivo_principale,
        "urgenza": lead_data.urgenza,
        "budget_mensile_indicativo": lead_data.budget_mensile_indicativo,
        "consenso_privacy": lead_data.consenso_privacy,
        "consenso_marketing": lead_data.consenso_marketing,
        "status": "new",
        "ip_address": lead_data.ip_address,
        "user_agent": lead_data.user_agent,
        "utm_source": lead_data.utm_source,
        "utm_medium": lead_data.utm_medium,
        "utm_campaign": lead_data.utm_campaign,
    }
    
    try:
        existing = supabase.table("leads").select("id,status").eq("email", lead_dict["email"]).execute()
        
        if existing.data and len(existing.data) > 0:
            lead_id = existing.data[0]["id"]
            old_status = existing.data[0]["status"]
            print(f"[INFO] Lead esistente: {lead_id} (status: {old_status}) -> reset a 'new'")
            
            lead_dict["updated_at"] = datetime.utcnow().isoformat()
            result = supabase.table("leads").update(lead_dict).eq("id", lead_id).execute()
            
            if not result.data or len(result.data) == 0:
                raise Exception(f"Update lead {lead_id} non ha restituito dati")
            
            return result.data[0]
        else:
            print(f"[OK] Nuovo lead, inserimento...")
            result = supabase.table("leads").insert(lead_dict).execute()
            
            if not result.data or len(result.data) == 0:
                raise Exception("Insert lead non ha restituito dati")
            
            return result.data[0]
    
    except Exception as e:
        print(f"[ERROR] Errore salvataggio lead: {str(e)}")
        raise


async def get_lead_by_id(lead_id: str) -> Optional[Dict[str, Any]]:
    """
    Recupera un lead dal database tramite ID.
    
    Args:
        lead_id: UUID del lead
        
    Returns:
        dict: Dati del lead o None se non trovato
    """
    supabase = get_supabase_client()
    
    try:
        result = supabase.table("leads").select("*").eq("id", lead_id).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        
        return None
    
    except Exception as e:
        print(f"[ERROR] Errore nel recupero del lead {lead_id}: {str(e)}")
        return None


async def update_lead_status(lead_id: str, new_status: str) -> bool:
    """
    Aggiorna lo status di un lead.
    
    Args:
        lead_id: UUID del lead
        new_status: Nuovo status
        
    Returns:
        bool: True se aggiornamento riuscito, False altrimenti
    """
    supabase = get_supabase_client()
    
    try:
        result = supabase.table("leads").update({
            "status": new_status,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", lead_id).execute()
        
        if result.data and len(result.data) > 0:
            print(f"[OK] Status lead {lead_id} aggiornato a: {new_status}")
            return True
        
        return False
    
    except Exception as e:
        print(f"[ERROR] Errore nell'aggiornamento status lead {lead_id}: {str(e)}")
        return False
