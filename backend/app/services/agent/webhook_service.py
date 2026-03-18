"""
Webhook Service - Riceve messaggi dai canali, normalizza, orchestra AI.
Include media processing automatico per tutti i canali.
"""

from backend.app.services.agent.contact_service import resolve_contact
from backend.app.services.agent.conversation_service import resolve_conversation
from backend.app.services.agent.message_service import save_message, get_chat_history, save_to_memory
from backend.app.services.agent.media_service import process_media
import logging

logger = logging.getLogger(__name__)


async def _process_channel(channel, contact_kwargs, message_kwargs, media_kwargs=None):
    contact = await resolve_contact(**contact_kwargs)
    conversation = await resolve_conversation(contact_id=contact["id"], channel_type=channel)
    message_kwargs["conversation_id"] = conversation["id"]
    message_kwargs["contact_id"] = contact["id"]
    message_kwargs["channel_type"] = channel

    content_type = message_kwargs.get("content_type", "text")
    if content_type in ("audio", "image", "document", "video") and media_kwargs:
        logger.info(f"Media {content_type} ricevuto da {channel} - processing...")
        media_result = await process_media(content_type=content_type, channel=channel, **media_kwargs)
        transcription = media_result.get("transcription", "")
        message_kwargs["media_transcription"] = transcription
        if content_type == "audio" and media_result.get("processed"):
            if not message_kwargs.get("content"):
                message_kwargs["content"] = transcription
        elif content_type in ("image", "document") and media_result.get("processed"):
            original = message_kwargs.get("content", "")
            if original:
                message_kwargs["content"] = original + " [Analisi: " + transcription + "]"
            else:
                message_kwargs["content"] = transcription
        logger.info(f"Media processato: {media_result.get('type', 'unknown')} - {len(transcription)} caratteri")

    msg = await save_message(**message_kwargs)
    return {"contact": contact, "conversation": conversation, "message": msg}


async def process_whatsapp_inbound(payload):
    media_kwargs = None
    content_type = payload.get("content_type", "text")
    if content_type in ("audio", "image", "document", "video"):
        media_kwargs = {"media_id": payload.get("media_id"), "media_url": payload.get("media_url"), "filename": payload.get("filename")}
    return await _process_channel(
        channel="whatsapp",
        contact_kwargs={"channel": "whatsapp", "channel_user_id": payload.get("phone", ""), "user_name": payload.get("contact_name")},
        message_kwargs={"direction": "inbound", "sender_type": "contact", "content": payload.get("content", ""), "content_type": content_type, "media_url": payload.get("media_url"), "channel_message_id": payload.get("message_id"), "sender_name": payload.get("contact_name")},
        media_kwargs=media_kwargs,
    )


async def process_chatbot_inbound(payload):
    extra_data = {}
    if payload.get("visitor_email"):
        extra_data["email"] = payload["visitor_email"]
    return await _process_channel(
        channel="chatbot",
        contact_kwargs={"channel": "chatbot", "channel_user_id": payload.get("session_id", ""), "user_name": payload.get("visitor_name"), "extra_data": extra_data},
        message_kwargs={"direction": "inbound", "sender_type": "contact", "content": payload.get("content", ""), "content_type": payload.get("content_type", "text"), "sender_name": payload.get("visitor_name")},
    )


async def process_email_inbound(payload):
    subject = payload.get("subject", "")
    body = payload.get("body", "")
    content = "[Oggetto: " + subject + "] " + body if subject else body
    return await _process_channel(
        channel="email",
        contact_kwargs={"channel": "email", "channel_user_id": payload.get("from_email", ""), "user_name": payload.get("from_name"), "extra_data": {"email": payload.get("from_email", "")}},
        message_kwargs={"direction": "inbound", "sender_type": "contact", "content": content, "content_type": "text", "sender_name": payload.get("from_name")},
    )


async def process_sms_inbound(payload):
    return await _process_channel(
        channel="sms",
        contact_kwargs={"channel": "sms", "channel_user_id": payload.get("phone", "")},
        message_kwargs={"direction": "inbound", "sender_type": "contact", "content": payload.get("content", ""), "content_type": "text"},
    )


async def process_telegram_inbound(payload):
    media_kwargs = None
    content_type = payload.get("content_type", "text")
    if content_type in ("audio", "image", "document", "video"):
        media_kwargs = {"file_id": payload.get("file_id"), "media_url": payload.get("media_url"), "filename": payload.get("filename")}
    return await _process_channel(
        channel="telegram",
        contact_kwargs={"channel": "telegram", "channel_user_id": str(payload.get("telegram_id", "")), "user_name": payload.get("user_name")},
        message_kwargs={"direction": "inbound", "sender_type": "contact", "content": payload.get("content", ""), "content_type": content_type, "media_url": payload.get("media_url"), "sender_name": payload.get("user_name")},
        media_kwargs=media_kwargs,
    )



async def process_messenger_inbound(payload):
    return await _process_channel(
        channel="messenger",
        contact_kwargs={"channel": "messenger", "channel_user_id": str(payload.get("channel_id", "")), "user_name": payload.get("sender_name", "")},
        message_kwargs={"direction": "inbound", "sender_type": "contact", "content": payload.get("message_text", ""), "content_type": "text", "sender_name": payload.get("sender_name", "")},
    )


async def process_instagram_inbound(payload):
    return await _process_channel(
        channel="instagram",
        contact_kwargs={"channel": "instagram", "channel_user_id": str(payload.get("channel_id", "")), "user_name": payload.get("sender_name", "")},
        message_kwargs={"direction": "inbound", "sender_type": "contact", "content": payload.get("message_text", ""), "content_type": "text", "sender_name": payload.get("sender_name", "")},
    )


CHANNEL_PROCESSORS = {
    "whatsapp": process_whatsapp_inbound,
    "chatbot": process_chatbot_inbound,
    "email": process_email_inbound,
    "sms": process_sms_inbound,
    "telegram": process_telegram_inbound,
    "messenger": process_messenger_inbound,
    "instagram": process_instagram_inbound,
}


async def process_inbound(channel, payload):
    processor = CHANNEL_PROCESSORS.get(channel)
    if not processor:
        raise ValueError(f"Canale non supportato: {channel}")
    result = await processor(payload)
    logger.info(f"Inbound processato: {channel} -> contact={result['contact']['id']} conv={result['conversation']['id']}")
    return result
