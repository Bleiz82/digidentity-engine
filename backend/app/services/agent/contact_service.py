"""
Contact Service - Risolve o crea contatti da qualsiasi canale.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
from backend.app.core.supabase_client import get_supabase
import logging

logger = logging.getLogger(__name__)

CHANNEL_ID_FIELD = {
    "whatsapp": "telefono",
    "telegram": "telegram_id",
    "messenger": "messenger_id",
    "instagram": "instagram_id",
    "chatbot": "chatbot_session",
    "vapi": "vapi_call_id",
    "email": "email_channel_id",
    "sms": "sms_phone",
}


async def resolve_contact(channel, channel_user_id, user_name=None, extra_data=None):
    supabase = get_supabase()
    field = CHANNEL_ID_FIELD.get(channel)
    if not field:
        raise ValueError(f"Canale non supportato: {channel}")

    result = supabase.table("contacts").select("*").eq(field, channel_user_id).limit(1).execute()

    if result.data and len(result.data) > 0:
        contact = result.data[0]
        logger.info(f"Contatto trovato: {contact['id']} via {channel}")
        update_data = {
            "ultimo_canale": channel,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if user_name and not contact.get("nome"):
            update_data["nome"] = user_name
        supabase.table("contacts").update(update_data).eq("id", contact["id"]).execute()
        contact.update(update_data)
        return contact

    cross_contact = None
    if channel in ("whatsapp", "sms") and channel_user_id:
        phone_clean = channel_user_id.replace("+", "").replace(" ", "")
        for phone_field in ["telefono", "sms_phone"]:
            if phone_field != field:
                cross = supabase.table("contacts").select("*").eq(phone_field, phone_clean).limit(1).execute()
                if cross.data and len(cross.data) > 0:
                    cross_contact = cross.data[0]
                    break
        if not cross_contact:
            for phone_field in ["telefono", "sms_phone"]:
                if phone_field != field:
                    cross = supabase.table("contacts").select("*").ilike(phone_field, f"%{phone_clean[-10:]}").limit(1).execute()
                    if cross.data and len(cross.data) > 0:
                        cross_contact = cross.data[0]
                        break

    if cross_contact:
        logger.info(f"Contatto trovato via ricerca incrociata: {cross_contact['id']}")
        update_data = {
            field: channel_user_id,
            "ultimo_canale": channel,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        supabase.table("contacts").update(update_data).eq("id", cross_contact["id"]).execute()
        cross_contact.update(update_data)
        return cross_contact

    new_contact = {
        field: channel_user_id,
        "canale_primo_contatto": channel,
        "ultimo_canale": channel,
        "lead_status": "new",
        "lead_score": 0,
    }
    if user_name:
        new_contact["nome"] = user_name
    if extra_data:
        allowed = ["nome","email","telefono","nome_attivita","tipo_attivita","citta","provincia","indirizzo"]
        for k, v in extra_data.items():
            if k in allowed and v:
                new_contact[k] = v
    if channel in ("whatsapp", "sms") and "telefono" not in new_contact:
        new_contact["telefono"] = channel_user_id
    if channel == "email" and "email" not in new_contact:
        new_contact["email"] = channel_user_id

    result = supabase.table("contacts").insert(new_contact).execute()
    if result.data and len(result.data) > 0:
        contact = result.data[0]
        logger.info(f"Nuovo contatto creato: {contact['id']} via {channel}")
        return contact
    raise Exception("Errore nella creazione del contatto")


async def get_contact_by_id(contact_id):
    supabase = get_supabase()
    result = supabase.table("contacts").select("*").eq("id", contact_id).limit(1).execute()
    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


async def update_contact(contact_id, data):
    supabase = get_supabase()
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = supabase.table("contacts").update(data).eq("id", contact_id).execute()
    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


async def search_contacts(query=None, lead_status=None, channel=None, has_diagnosis=None, has_geo_audit=None, limit=50, offset=0):
    supabase = get_supabase()
    q = supabase.table("contacts").select("*", count="exact")
    if query:
        q = q.or_(f"nome.ilike.%{query}%,email.ilike.%{query}%,telefono.ilike.%{query}%,nome_attivita.ilike.%{query}%")
    if lead_status:
        q = q.eq("lead_status", lead_status)
    if channel:
        q = q.eq("ultimo_canale", channel)
    if has_diagnosis is not None:
        q = q.eq("has_diagnosis", has_diagnosis)
    if has_geo_audit is not None:
        q = q.eq("has_geo_audit", has_geo_audit)
    result = q.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    return {"contacts": result.data or [], "total": result.count or 0}


async def get_contact_context(contact_id):
    supabase = get_supabase()
    contact = await get_contact_by_id(contact_id)
    if not contact:
        return {}
    context = {"contact": contact}

    if contact.get("engine_lead_id"):
        lead_result = supabase.table("leads").select("company_name, email, status, total_score, site_score, seo_score, gmb_score, social_score").eq("id", contact["engine_lead_id"]).limit(1).execute()
        if lead_result.data:
            context["engine_lead"] = lead_result.data[0]

    conv_result = supabase.table("conversations").select("id, channel_type, status, last_message_preview, last_message_at, total_messages").eq("contact_id", contact_id).order("last_message_at", desc=True).limit(5).execute()
    context["conversations"] = conv_result.data or []

    apt_result = supabase.table("appointments").select("*").eq("contact_id", contact_id).in_("stato", ["confermato", "riprogrammato"]).order("data_ora", desc=False).limit(3).execute()
    context["appointments"] = apt_result.data or []

    if contact.get("has_diagnosis") or contact.get("has_geo_audit"):
        context["scores"] = {
            "diagnosis_score": contact.get("diagnosis_score"),
            "geo_audit_score": contact.get("geo_audit_score"),
        }
    return context
