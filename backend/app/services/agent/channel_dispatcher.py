"""
Channel Dispatcher — Invia messaggi ai canali esterni.
WhatsApp Cloud API, Email SMTP, (Telegram, Instagram — prossimi step)
"""

import httpx
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================================
# WHATSAPP CLOUD API
# ============================================================

async def send_whatsapp_message(phone: str, message: str) -> dict:
    """Invia messaggio testuale via WhatsApp Cloud API."""
    
    if not settings.WHATSAPP_ACCESS_TOKEN:
        logger.warning("WHATSAPP_ACCESS_TOKEN non configurato — messaggio non inviato")
        return {"status": "skipped", "reason": "token_missing"}
    
    # Normalizza numero (deve avere prefisso senza +)
    clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    
    url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": clean_phone,
        "type": "text",
        "text": {"body": message}
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=headers)
            result = response.json()
            
            if response.status_code == 200:
                wa_message_id = result.get("messages", [{}])[0].get("id", "")
                logger.info(f"WhatsApp inviato a {clean_phone}: {wa_message_id}")
                return {"status": "sent", "wa_message_id": wa_message_id}
            else:
                logger.error(f"WhatsApp errore {response.status_code}: {result}")
                return {"status": "error", "code": response.status_code, "detail": result}
                
    except Exception as e:
        logger.error(f"WhatsApp eccezione: {e}")
        return {"status": "error", "detail": str(e)}


async def send_whatsapp_template(phone: str, template_name: str, language: str = "it", components: list = None) -> dict:
    """Invia template message via WhatsApp (per messaggi fuori finestra 24h)."""
    
    if not settings.WHATSAPP_ACCESS_TOKEN:
        return {"status": "skipped", "reason": "token_missing"}
    
    clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    
    url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    template = {
        "name": template_name,
        "language": {"code": language}
    }
    if components:
        template["components"] = components
    
    payload = {
        "messaging_product": "whatsapp",
        "to": clean_phone,
        "type": "template",
        "template": template
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=headers)
            result = response.json()
            
            if response.status_code == 200:
                wa_message_id = result.get("messages", [{}])[0].get("id", "")
                logger.info(f"WhatsApp template '{template_name}' inviato a {clean_phone}: {wa_message_id}")
                return {"status": "sent", "wa_message_id": wa_message_id}
            else:
                logger.error(f"WhatsApp template errore: {result}")
                return {"status": "error", "detail": result}
    except Exception as e:
        logger.error(f"WhatsApp template eccezione: {e}")
        return {"status": "error", "detail": str(e)}


# ============================================================
# EMAIL SMTP
# ============================================================

async def send_email_message(to_email: str, subject: str, body: str, is_html: bool = False) -> dict:
    """Invia email via SMTP Gmail."""
    
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP non configurato — email non inviata")
        return {"status": "skipped", "reason": "smtp_not_configured"}
    
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        
        content_type = "html" if is_html else "plain"
        msg.attach(MIMEText(body, content_type, "utf-8"))
        
        with smtplib.SMTP(settings.SMTP_HOST, int(settings.SMTP_PORT)) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email inviata a {to_email}: {subject}")
        return {"status": "sent", "to": to_email}
        
    except Exception as e:
        logger.error(f"Email eccezione: {e}")
        return {"status": "error", "detail": str(e)}



# ============================================================
# TELEGRAM BOT API
# ============================================================

async def send_telegram_message(chat_id: str, message: str) -> dict:
    """Invia messaggio testuale via Telegram Bot API."""
    
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN non configurato — messaggio non inviato")
        return {"status": "skipped", "reason": "token_missing"}
    
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload)
            result = response.json()
            
            if result.get("ok"):
                msg_id = result.get("result", {}).get("message_id", "")
                logger.info(f"Telegram inviato a {chat_id}: msg_id={msg_id}")
                return {"status": "sent", "telegram_message_id": str(msg_id)}
            else:
                logger.error(f"Telegram errore: {result}")
                return {"status": "error", "detail": result}
                
    except Exception as e:
        logger.error(f"Telegram eccezione: {e}")
        return {"status": "error", "detail": str(e)}



# ============================================================
# META MESSENGER / INSTAGRAM SEND API
# ============================================================

async def send_meta_message(recipient_id, message, channel_type="messenger"):
    """Invia messaggio via Meta Send API (Messenger o Instagram)."""
    token = settings.META_PAGE_ACCESS_TOKEN
    if not token:
        logger.warning("META_PAGE_ACCESS_TOKEN non configurato")
        return {"status": "skipped", "reason": "token_missing"}

    if channel_type == "instagram":
        url = "https://graph.facebook.com/" + settings.WHATSAPP_API_VERSION + "/me/messages"
    else:
        url = "https://graph.facebook.com/" + settings.WHATSAPP_API_VERSION + "/me/messages"

    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    payload = {
        "recipient": {"id": recipient_id},
        "messaging_type": "RESPONSE",
        "message": {"text": message}
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=headers)
            result = response.json()
            if response.status_code == 200:
                msg_id = result.get("message_id", "")
                logger.info(channel_type + " inviato a " + recipient_id + ": " + msg_id)
                return {"status": "sent", "message_id": msg_id}
            else:
                logger.error(channel_type + " errore: " + str(result))
                return {"status": "error", "detail": result}
    except Exception as e:
        logger.error(channel_type + " eccezione: " + str(e))
        return {"status": "error", "detail": str(e)}


# ============================================================
# DISPATCHER GENERICO
# ============================================================

async def send_channel_response(channel_type: str, contact: dict, message: str, conversation: dict = None) -> dict:
    """Dispatcher — invia la risposta al canale corretto."""
    
    if channel_type == "whatsapp":
        phone = contact.get("telefono") or contact.get("whatsapp_phone") or contact.get("sms_phone")
        if not phone:
            return {"status": "error", "detail": "Nessun numero telefonico per il contatto"}
        return await send_whatsapp_message(phone, message)
    
    elif channel_type == "email":
        email = contact.get("email")
        if not email:
            return {"status": "error", "detail": "Nessuna email per il contatto"}
        subject = "DigIdentity Agency — Risposta"
        if conversation:
            preview = message[:50] + "..." if len(message) > 50 else message
            subject = f"Re: {preview}"
        return await send_email_message(email, subject, message)
    
    elif channel_type == "telegram":
        telegram_id = contact.get("telegram_id")
        if not telegram_id:
            return {"status": "error", "detail": "Nessun telegram_id per il contatto"}
        return await send_telegram_message(telegram_id, message)
    
    elif channel_type in ("messenger", "instagram"):
        recipient_id = contact.get("messenger_id") if channel_type == "messenger" else contact.get("instagram_id")
        if not recipient_id:
            return {"status": "error", "detail": "Nessun " + channel_type + "_id per il contatto"}
        return await send_meta_message(recipient_id, message, channel_type)
    
    elif channel_type == "chatbot":
        # Il chatbot riceve la risposta direttamente dal webhook response
        return {"status": "inline", "reason": "chatbot_receives_inline"}
    
    elif channel_type == "sms":
        # TODO: implementare SMS provider
        return {"status": "skipped", "reason": "sms_not_implemented"}
    
    else:
        return {"status": "error", "detail": f"Canale sconosciuto: {channel_type}"}
