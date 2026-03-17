"""
Conversation Service - Gestisce conversazioni per canale/contatto.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from backend.app.core.supabase_client import get_supabase
import logging

logger = logging.getLogger(__name__)


async def resolve_conversation(contact_id, channel_type):
    """Trova o crea una conversazione attiva per contatto/canale."""
    supabase = get_supabase()
    result = (
        supabase.table("conversations")
        .select("*")
        .eq("contact_id", contact_id)
        .eq("channel_type", channel_type)
        .neq("status", "closed")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if result.data and len(result.data) > 0:
        conv = result.data[0]
        logger.info(f"Conversazione trovata: {conv['id']}")
        return conv

    new_conv = {
        "contact_id": contact_id,
        "channel_type": channel_type,
        "status": "ai",
        "ai_enabled": True,
        "total_messages": 0,
        "unread_count": 0,
    }
    result = supabase.table("conversations").insert(new_conv).execute()
    if result.data and len(result.data) > 0:
        conv = result.data[0]
        logger.info(f"Nuova conversazione creata: {conv['id']} per {channel_type}")
        return conv
    raise Exception("Errore nella creazione della conversazione")


async def get_conversation(conversation_id):
    supabase = get_supabase()
    result = (
        supabase.table("conversations")
        .select("*, contacts(*)")
        .eq("id", conversation_id)
        .limit(1)
        .execute()
    )
    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


async def update_conversation(conversation_id, data):
    supabase = get_supabase()
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = (
        supabase.table("conversations")
        .update(data)
        .eq("id", conversation_id)
        .execute()
    )
    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


async def toggle_ai(conversation_id, active):
    """Attiva/disattiva AI su una conversazione (human takeover)."""
    data = {
        "ai_enabled": active,
        "status": "ai" if active else "human",
    }
    conv = await update_conversation(conversation_id, data)
    logger.info(f"AI {'attivata' if active else 'disattivata'} su {conversation_id}")
    return conv


async def close_conversation(conversation_id):
    data = {"status": "closed", "ai_enabled": False}
    return await update_conversation(conversation_id, data)


async def get_inbox(status=None, channel=None, ai_enabled=None, limit=50, offset=0):
    """Recupera la inbox con filtri per la dashboard."""
    supabase = get_supabase()
    q = (
        supabase.table("conversations")
        .select("*, contacts(*)", count="exact")
        .neq("status", "closed")
    )

    if status:
        q = q.eq("status", status)
    if channel:
        q = q.eq("channel_type", channel)
    if ai_enabled is not None:
        q = q.eq("ai_enabled", ai_enabled)

    result = (
        q.order("last_message_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    items = []
    for conv in (result.data or []):
        contact = conv.get("contacts", {}) or {}
        items.append({
            "conversation_id": conv["id"],
            "contact_id": conv["contact_id"],
            "contact_name": contact.get("nome"),
            "contact_phone": contact.get("telefono"),
            "contact_email": contact.get("email"),
            "business_name": contact.get("nome_attivita"),
            "channel": conv["channel_type"],
            "status": conv["status"],
            "ai_enabled": conv.get("ai_enabled", True),
            "last_message": conv.get("last_message_preview"),
            "last_message_at": conv.get("last_message_at"),
            "unread_count": conv.get("unread_count", 0),
            "lead_status": contact.get("lead_status"),
            "lead_score": contact.get("lead_score", 0),
            "has_diagnosis": contact.get("has_diagnosis", False),
            "has_geo_audit": contact.get("has_geo_audit", False),
        })

    ai_count = len([i for i in items if i["ai_enabled"]])
    human_count = len([i for i in items if not i["ai_enabled"]])
    unread = sum(i["unread_count"] for i in items)

    return {
        "items": items,
        "total": result.count or 0,
        "ai_active_count": ai_count,
        "human_active_count": human_count,
        "unread_total": unread,
    }
