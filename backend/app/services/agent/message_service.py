"""
Message Service - Salva e recupera messaggi, gestisce media.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from backend.app.core.supabase_client import get_supabase
import logging

logger = logging.getLogger(__name__)


async def save_message(
    conversation_id,
    contact_id,
    direction,
    sender_type,
    content,
    content_type="text",
    channel_type="whatsapp",
    media_url=None,
    media_transcription=None,
    media_mime_type=None,
    channel_message_id=None,
    ai_model=None,
    ai_confidence=None,
    ai_tokens_used=None,
    metadata=None,
    sender_name=None,
):
    supabase = get_supabase()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    msg = {
        "conversation_id": conversation_id,
        "contact_id": contact_id,
        "direction": direction,
        "sender_type": sender_type,
        "content": content,
        "content_type": content_type,
        "channel_type": channel_type,
    }

    if media_url:
        msg["media_url"] = media_url
    if media_transcription:
        msg["media_transcription"] = media_transcription
    if media_mime_type:
        msg["media_mime_type"] = media_mime_type
    if channel_message_id:
        msg["channel_message_id"] = channel_message_id
    if ai_model:
        msg["ai_model"] = ai_model
    if ai_confidence is not None:
        msg["ai_confidence"] = ai_confidence
    if ai_tokens_used is not None:
        msg["ai_tokens_used"] = ai_tokens_used
    if metadata:
        msg["metadata"] = metadata
    if sender_name:
        msg["sender_name"] = sender_name

    result = supabase.table("messages").insert(msg).execute()

    if result.data and len(result.data) > 0:
        saved = result.data[0]
        logger.info(f"Messaggio salvato: {saved["id"]} ({direction}/{sender_type})")
        return saved

    raise Exception("Errore nel salvataggio del messaggio")


async def get_messages(conversation_id, limit=50, offset=0, before=None):
    supabase = get_supabase()
    q = supabase.table("messages").select("*", count="exact").eq("conversation_id", conversation_id)
    if before:
        q = q.lt("created_at", before)
    result = q.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    messages = list(reversed(result.data or []))
    return {"messages": messages, "total": result.count or 0}


async def get_chat_history(conversation_id, limit=20):
    supabase = get_supabase()
    result = (
        supabase.table("messages")
        .select("direction, sender_type, content, content_type, media_transcription, created_at")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    messages = list(reversed(result.data or []))
    history = []
    for msg in messages:
        text = msg.get("content") or ""
        if msg.get("media_transcription"):
            text = f"[{msg["content_type"]}] {msg["media_transcription"]}"
        if msg["direction"] == "inbound":
            history.append({"role": "user", "content": text})
        else:
            history.append({"role": "assistant", "content": text})
    return history


async def mark_as_read(conversation_id):
    supabase = get_supabase()
    supabase.table("messages").update({"read": True}).eq("conversation_id", conversation_id).eq("direction", "inbound").eq("read", False).execute()
    supabase.table("conversations").update({"unread_count": 0}).eq("id", conversation_id).execute()
    logger.info(f"Messaggi segnati come letti per {conversation_id}")
    return True


async def save_to_memory(session_id, role, content, tool_calls=None):
    supabase = get_supabase()
    entry = {"session_id": session_id, "role": role, "content": content}
    if tool_calls:
        entry["tool_calls"] = tool_calls
    supabase.table("chat_memory").insert(entry).execute()


async def get_memory(session_id, limit=20):
    supabase = get_supabase()
    result = (
        supabase.table("chat_memory")
        .select("role, content, tool_calls, created_at")
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(reversed(result.data or []))
