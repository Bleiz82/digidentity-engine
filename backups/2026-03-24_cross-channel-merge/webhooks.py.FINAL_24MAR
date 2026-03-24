"""
Agent Webhooks - Endpoint per ricevere messaggi dai canali + risposta AI.
"""

from fastapi.responses import PlainTextResponse, Response, JSONResponse
from fastapi import APIRouter, HTTPException, Request
from backend.app.services.agent.webhook_service import process_inbound
from backend.app.services.agent.conversation_service import get_inbox, toggle_ai, close_conversation, get_conversation
from backend.app.services.agent.message_service import get_messages, mark_as_read, save_message
from backend.app.services.agent.contact_service import search_contacts, get_contact_by_id, update_contact, get_contact_context
from backend.app.services.agent.ai_service import generate_ai_response
from backend.app.services.agent.channel_dispatcher import send_channel_response
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["agent"])


# ============================================
# WEBHOOK INBOUND + AI RESPONSE
# ============================================

async def _handle_inbound(channel, request):
    try:
        payload = await request.json()
        result = await process_inbound(channel, payload)

        conv = result["conversation"]
        contact = result["contact"]
        response_data = {
            "status": "ok",
            "contact_id": contact["id"],
            "conversation_id": conv["id"],
            "message_id": result["message"]["id"],
            "ai_response": None,
            "ai_tokens": None,
            "channel_delivery": None,
        }

        if conv.get("ai_enabled", True):
            ai_result = await generate_ai_response(
                conversation_id=conv["id"],
                contact_id=contact["id"],
                user_message=result["message"].get("content", ""),
                channel_type=channel,
            )
            response_data["ai_response"] = ai_result["response"]
            response_data["ai_tokens"] = ai_result.get("tokens_used")
            response_data["ai_message_id"] = ai_result.get("message", {}).get("id")

            # Invia la risposta al canale reale
            delivery = await send_channel_response(
                channel_type=channel,
                contact=contact,
                message=ai_result["response"],
                conversation=conv,
            )
            response_data["channel_delivery"] = delivery
            logger.info(f"Channel delivery [{channel}]: {delivery.get('status')}")

        return response_data
    except Exception as e:
        logger.error(f"Errore webhook {channel}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhook/whatsapp")
async def whatsapp_verify(request: Request):
    """Verifica webhook Meta (challenge handshake)."""
    from backend.app.core.config import settings
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verificato")
        return PlainTextResponse(content=challenge, status_code=200)
    logger.warning("WhatsApp verifica fallita: token non valido")
    raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """Riceve messaggi da WhatsApp Cloud API e li processa."""
    try:
        body = await request.json()

        # Meta manda diversi tipi di update
        if body.get("object") != "whatsapp_business_account":
            return {"status": "ok"}

        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                contacts = value.get("contacts", [])

                if not messages:
                    # Status update (delivered, read, etc.)
                    statuses = value.get("statuses", [])
                    for st in statuses:
                        wa_msg_id = st.get("id", "")
                        status = st.get("status", "")
                        if wa_msg_id and status in ("delivered", "read"):
                            import httpx as _httpx
                            from backend.app.core.config import settings
                            _headers = {"apikey": settings.SUPABASE_KEY, "Authorization": f"Bearer {settings.SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}
                            _base = settings.SUPABASE_URL + "/rest/v1"
                            async with _httpx.AsyncClient() as _client:
                                if status == "delivered":
                                    await _client.patch(f"{_base}/messages?channel_message_id=eq.{wa_msg_id}", json={"delivered": True}, headers=_headers)
                                elif status == "read":
                                    await _client.patch(f"{_base}/messages?channel_message_id=eq.{wa_msg_id}", json={"delivered": True, "read": True}, headers=_headers)
                            logger.info(f"WhatsApp status: {wa_msg_id} -> {status}")
                        else:
                            logger.info(f"WhatsApp status update: {status}")
                    return {"status": "ok"}

                msg = messages[0]
                wa_contact = contacts[0] if contacts else {}

                phone = msg.get("from", "")
                contact_name = wa_contact.get("profile", {}).get("name", "")
                msg_type = msg.get("type", "text")
                wa_msg_id = msg.get("id", "")

                content = ""
                content_type = "text"
                media_id = None
                filename = None

                if msg_type == "text":
                    content = msg.get("text", {}).get("body", "")
                elif msg_type == "image":
                    content_type = "image"
                    content = msg.get("image", {}).get("caption", "")
                    media_id = msg.get("image", {}).get("id")
                elif msg_type == "audio":
                    content_type = "audio"
                    media_id = msg.get("audio", {}).get("id")
                elif msg_type == "voice":
                    content_type = "audio"
                    media_id = msg.get("voice", {}).get("id")
                elif msg_type == "video":
                    content_type = "video"
                    content = msg.get("video", {}).get("caption", "")
                    media_id = msg.get("video", {}).get("id")
                elif msg_type == "document":
                    content_type = "document"
                    content = msg.get("document", {}).get("caption", "")
                    media_id = msg.get("document", {}).get("id")
                    filename = msg.get("document", {}).get("filename")
                elif msg_type == "location":
                    content_type = "location"
                    loc = msg.get("location", {})
                    content = str(loc.get("latitude", "")) + "," + str(loc.get("longitude", ""))
                elif msg_type == "contacts":
                    content_type = "contact"
                    content = str(msg.get("contacts", []))
                elif msg_type == "sticker":
                    content = "[Sticker]"
                elif msg_type == "reaction":
                    return {"status": "ok"}
                else:
                    content = "[" + msg_type + "]"

                # Normalizza telefono
                if phone and not phone.startswith("+"):
                    phone = "+" + phone

                normalized_payload = {
                    "phone": phone,
                    "contact_name": contact_name,
                    "content": content,
                    "content_type": content_type,
                    "media_id": media_id,
                    "media_url": None,
                    "filename": filename,
                    "message_id": wa_msg_id,
                }

                result = await process_inbound("whatsapp", normalized_payload)
                conv = result["conversation"]
                contact = result["contact"]

                response_data = {
                    "status": "ok",
                    "contact_id": contact["id"],
                    "conversation_id": conv["id"],
                    "message_id": result["message"]["id"],
                    "ai_response": None,
                    "channel_delivery": None,
                }

                if conv.get("ai_enabled", True):
                    ai_result = await generate_ai_response(
                        conversation_id=conv["id"],
                        contact_id=contact["id"],
                        user_message=content,
                        channel_type="whatsapp",
                    )
                    response_data["ai_response"] = ai_result["response"]

                    delivery = await send_channel_response(
                        channel_type="whatsapp",
                        contact=contact,
                        message=ai_result["response"],
                        conversation=conv,
                    )
                    response_data["channel_delivery"] = delivery
                    logger.info("WhatsApp delivery: " + delivery.get("status", "unknown"))

                return response_data

        return {"status": "ok"}

    except Exception as e:
        logger.error("Errore webhook WhatsApp: " + str(e))
        import traceback
        traceback.print_exc()
        return {"status": "ok"}

@router.post("/webhook/chatbot")
async def chatbot_webhook(request: Request):
    return await _handle_inbound("chatbot", request)

@router.post("/webhook/email")
async def email_webhook(request: Request):
    return await _handle_inbound("email", request)

@router.post("/webhook/sms")
async def sms_webhook(request: Request):
    return await _handle_inbound("sms", request)

@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Riceve update da Telegram Bot API, parsa e processa."""
    try:
        update = await request.json()
        message = update.get("message") or update.get("edited_message")
        if not message:
            return {"status": "ok", "detail": "update ignorato"}

        chat = message.get("chat", {})
        from_user = message.get("from", {})

        content = ""
        content_type = "text"
        media_url = None
        file_id = None
        filename = None

        if "text" in message:
            content = message["text"]
        elif "photo" in message:
            content_type = "image"
            content = message.get("caption", "")
            file_id = message["photo"][-1]["file_id"]
        elif "voice" in message:
            content_type = "audio"
            file_id = message["voice"]["file_id"]
        elif "audio" in message:
            content_type = "audio"
            file_id = message["audio"]["file_id"]
            filename = message["audio"].get("file_name", "audio.mp3")
        elif "video" in message:
            content_type = "video"
            file_id = message["video"]["file_id"]
        elif "document" in message:
            content_type = "document"
            content = message.get("caption", "")
            file_id = message["document"]["file_id"]
            filename = message["document"].get("file_name", "document")
        elif "sticker" in message:
            content = "[Sticker]"
        elif "location" in message:
            content_type = "location"
            loc = message["location"]
            content = str(loc.get("latitude", "")) + "," + str(loc.get("longitude", ""))

        # /start -> messaggio di benvenuto gestito dall'AI
        if content == "/start":
            content = "Ciao!"

        user_name = from_user.get("first_name", "")
        if from_user.get("last_name"):
            user_name += f" {from_user['last_name']}"
        user_name = user_name.strip() or f"Telegram_{chat['id']}"

        # Chiama direttamente process_inbound con payload normalizzato
        normalized_payload = {
            "telegram_id": str(chat["id"]),
            "user_name": user_name,
            "content": content,
            "content_type": content_type,
            "media_url": media_url,
            "file_id": file_id,
            "filename": filename,
            "message_id": str(message.get("message_id", "")),
        }

        result = await process_inbound("telegram", normalized_payload)
        conv = result["conversation"]
        contact = result["contact"]

        response_data = {
            "status": "ok",
            "contact_id": contact["id"],
            "conversation_id": conv["id"],
            "message_id": result["message"]["id"],
            "ai_response": None,
            "channel_delivery": None,
        }

        if conv.get("ai_enabled", True):
            ai_result = await generate_ai_response(
                conversation_id=conv["id"],
                contact_id=contact["id"],
                user_message=content,
                channel_type="telegram",
            )
            response_data["ai_response"] = ai_result["response"]

            delivery = await send_channel_response(
                channel_type="telegram",
                contact=contact,
                message=ai_result["response"],
                conversation=conv,
            )
            response_data["channel_delivery"] = delivery
            logger.info(f"Telegram delivery: {delivery.get('status')}")

        return response_data

    except Exception as e:
        logger.error(f"Errore webhook Telegram: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "ok"}


# ============================================
# INBOX & CONVERSATIONS (Dashboard API)
# ============================================

@router.get("/inbox")
async def get_inbox_list(
    status: str = None,
    channel: str = None,
    ai_enabled: bool = None,
    limit: int = 50,
    offset: int = 0,
):
    try:
        result = await get_inbox(
            status=status,
            channel=channel,
            ai_enabled=ai_enabled,
            limit=limit,
            offset=offset,
        )
        return result
    except Exception as e:
        logger.error(f"Errore inbox: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}")
async def get_conversation_detail(conversation_id: str):
    conv = await get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversazione non trovata")
    return conv


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str, limit: int = 50, offset: int = 0):
    return await get_messages(conversation_id, limit=limit, offset=offset)


@router.post("/conversations/{conversation_id}/messages")
async def send_human_message(conversation_id: str, request: Request):
    try:
        payload = await request.json()
        conv = await get_conversation(conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversazione non trovata")
        msg = await save_message(
            conversation_id=conversation_id,
            contact_id=conv["contact_id"],
            direction="outbound",
            sender_type="human",
            content=payload.get("content", ""),
            content_type=payload.get("content_type", "text"),
            channel_type=conv["channel_type"],
        )
        return {"status": "ok", "message": msg}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore invio messaggio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/takeover")
async def human_takeover(conversation_id: str):
    conv = await toggle_ai(conversation_id, active=False)
    return {"status": "ok", "conversation": conv}


@router.post("/conversations/{conversation_id}/handback")
async def ai_handback(conversation_id: str):
    conv = await toggle_ai(conversation_id, active=True)
    return {"status": "ok", "conversation": conv}


@router.post("/conversations/{conversation_id}/close")
async def close_conv(conversation_id: str):
    conv = await close_conversation(conversation_id)
    return {"status": "ok", "conversation": conv}


@router.post("/conversations/{conversation_id}/read")
async def mark_read(conversation_id: str):
    await mark_as_read(conversation_id)
    return {"status": "ok"}


# ============================================
# CONTACTS (Dashboard API)
# ============================================

@router.get("/contacts")
async def list_contacts(
    q: str = None,
    lead_status: str = None,
    channel: str = None,
    has_diagnosis: bool = None,
    has_geo_audit: bool = None,
    limit: int = 50,
    offset: int = 0,
):
    return await search_contacts(
        query=q,
        lead_status=lead_status,
        channel=channel,
        has_diagnosis=has_diagnosis,
        has_geo_audit=has_geo_audit,
        limit=limit,
        offset=offset,
    )


@router.get("/contacts/{contact_id}")
async def get_contact(contact_id: str):
    contact = await get_contact_by_id(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contatto non trovato")
    return contact


@router.get("/contacts/{contact_id}/context")
async def get_contact_ctx(contact_id: str):
    context = await get_contact_context(contact_id)
    if not context:
        raise HTTPException(status_code=404, detail="Contatto non trovato")
    return context


@router.patch("/contacts/{contact_id}")
async def patch_contact(contact_id: str, request: Request):
    data = await request.json()
    contact = await update_contact(contact_id, data)
    if not contact:
        raise HTTPException(status_code=404, detail="Contatto non trovato")
    return contact


# ═══════════════════════════════════════
# META MESSENGER / INSTAGRAM WEBHOOK
# ═══════════════════════════════════════

@router.get("/webhook/meta")
async def meta_verify(request: Request):
    """Verifica webhook Meta (Messenger + Instagram Direct)."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == "digidentity_meta_secure_2026":
        logger.info("Meta webhook verificato OK")
        return Response(content=challenge, media_type="text/plain")
    
    logger.warning(f"Meta webhook verifica fallita: mode={mode}, token={token}")
    return JSONResponse(status_code=403, content={"error": "Verifica fallita"})


@router.post("/webhook/meta")
async def meta_webhook(request: Request):
    """Ricevi messaggi da Messenger e Instagram Direct."""
    try:
        body = await request.json()
        logger.info(f"Meta webhook ricevuto: {body.get('object', 'unknown')}")

        if body.get("object") not in ("page", "instagram"):
            return {"status": "ignored"}

        entries = body.get("entry", [])
        for entry in entries:
            messaging_list = entry.get("messaging", [])
            
            for event in messaging_list:
                sender_id = event.get("sender", {}).get("id", "")
                recipient_id = event.get("recipient", {}).get("id", "")
                timestamp = event.get("timestamp", 0)
                
                # Determina canale
                if body.get("object") == "instagram":
                    channel = "instagram"
                    channel_id_field = "instagram_id"
                else:
                    channel = "messenger"
                    channel_id_field = "messenger_id"
                
                # Messaggio di testo
                message = event.get("message", {})
                if not message or message.get("is_echo"):
                    continue
                
                text = message.get("text", "")
                
                # Gestisci allegati (immagini, audio, video, file)
                attachments = message.get("attachments", [])
                attachment_url = ""
                attachment_type = ""
                if attachments and not text:
                    att = attachments[0]
                    attachment_type = att.get("type", "")
                    attachment_url = att.get("payload", {}).get("url", "")
                    if not text:
                        text = f"[{attachment_type}]"
                
                if not text and not attachment_url:
                    continue
                
                # Normalizza payload per il sistema
                normalized_payload = {
                    "channel": channel,
                    "channel_id": sender_id,
                    "channel_id_field": channel_id_field,
                    "sender_name": "",  # Meta non manda il nome nel webhook
                    "message_text": text,
                    "message_id": message.get("mid", ""),
                    "timestamp": timestamp,
                    "attachment_url": attachment_url,
                    "attachment_type": attachment_type,
                    "extra": {
                        "recipient_id": recipient_id,
                    }
                }
                
                # Prova a recuperare il nome del sender via Graph API
                try:
                    from backend.app.core.config import settings
                    import httpx
                    token = settings.META_PAGE_ACCESS_TOKEN
                    if token and channel == "messenger":
                        async with httpx.AsyncClient() as client:
                            resp = await client.get(
                                f"https://graph.facebook.com/{sender_id}",
                                params={"fields": "first_name,last_name", "access_token": token}
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                nome = data.get("first_name", "")
                                cognome = data.get("last_name", "")
                                normalized_payload["sender_name"] = f"{nome} {cognome}".strip()
                except Exception as e:
                    logger.debug(f"Meta: impossibile recuperare nome sender: {e}")
                
                result = await process_inbound(channel, normalized_payload)
                conv = result["conversation"]
                contact = result["contact"]

                logger.info(f"Meta {channel} messaggio da {sender_id}: {text[:50]}")

                # Genera risposta AI e invia
                if conv.get("ai_enabled", True):
                    try:
                        ai_result = await generate_ai_response(
                            conversation_id=conv["id"],
                            contact_id=contact["id"],
                            user_message=text,
                            channel_type=channel,
                        )

                        delivery = await send_channel_response(
                            channel_type=channel,
                            contact=contact,
                            message=ai_result["response"],
                            conversation=conv,
                        )
                        logger.info(f"Meta {channel} AI delivery: {delivery.get('status')}")
                    except Exception as ai_err:
                        logger.error(f"Meta {channel} AI errore: {ai_err}")

        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Meta webhook errore: {e}")
        return {"status": "ok"}  # Sempre 200 per Meta



# ── Invio manuale operatore ──────────────────────────────────────


# ── Invio manuale operatore ──────────────────────────────────────
@router.post("/conversations/{conversation_id}/send")
async def manual_send(conversation_id: str, request: Request):
    """Invia un messaggio manuale dall'operatore sul canale della conversazione."""
    import httpx
    from backend.app.core.config import settings
    from backend.app.services.agent.channel_dispatcher import send_channel_response

    body = await request.json()
    content = body.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Contenuto vuoto")

    headers = {"apikey": settings.SUPABASE_KEY, "Authorization": f"Bearer {settings.SUPABASE_KEY}"}
    base = settings.SUPABASE_URL + "/rest/v1"

    async with httpx.AsyncClient() as client:
        # Recupera conversazione
        r = await client.get(f"{base}/conversations?id=eq.{conversation_id}&select=*", headers=headers)
        convs = r.json()
        if not convs:
            raise HTTPException(status_code=404, detail="Conversazione non trovata")
        conv = convs[0]

        # Recupera contatto
        r2 = await client.get(f"{base}/contacts?id=eq.{conv['contact_id']}&select=*", headers=headers)
        contacts = r2.json()
        if not contacts:
            raise HTTPException(status_code=404, detail="Contatto non trovato")
        contact = contacts[0]

    # Invia sul canale
    result = await send_channel_response(conv["channel_type"], contact, content, conv)
    
    # Aggiorna channel_message_id per tracking delivered/read
    wa_msg_id = result.get("wa_message_id", "")
    if wa_msg_id:
        import httpx as _hx
        _h = {"apikey": settings.SUPABASE_KEY, "Authorization": f"Bearer {settings.SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}
        async with _hx.AsyncClient() as _cl:
            # Aggiorna l'ultimo messaggio outbound della conversazione
            r = await _cl.get(f"{settings.SUPABASE_URL}/rest/v1/messages?conversation_id=eq.{conversation_id}&direction=eq.outbound&order=created_at.desc&limit=1&select=id", headers=_h)
            msgs = r.json()
            if msgs:
                await _cl.patch(f"{settings.SUPABASE_URL}/rest/v1/messages?id=eq.{msgs[0]['id']}", json={"channel_message_id": wa_msg_id, "delivered": True}, headers=_h)
    
    logger.info(f"Messaggio manuale inviato su {conv['channel_type']} per conv {conversation_id}: {result}")
    return {"status": "sent", "channel": conv["channel_type"], "result": result}




# ── Polling chatbot per messaggi nuovi ──────────────────────────────────────
@router.get("/webhook/chatbot/poll/{session_id}")
async def chatbot_poll(session_id: str, after: str = ""):
    """Restituisce messaggi outbound nuovi per il chatbot widget."""
    import httpx
    from backend.app.core.config import settings
    
    headers = {"apikey": settings.SUPABASE_KEY, "Authorization": f"Bearer {settings.SUPABASE_KEY}"}
    base = settings.SUPABASE_URL + "/rest/v1"
    
    async with httpx.AsyncClient() as client:
        # Trova il contatto con questa session
        r = await client.get(f"{base}/contacts?chatbot_session=eq.{session_id}&select=id", headers=headers)
        contacts = r.json()
        if not contacts:
            return {"messages": []}
        contact_id = contacts[0]["id"]
        
        # Trova la conversazione chatbot attiva
        r2 = await client.get(f"{base}/conversations?contact_id=eq.{contact_id}&channel_type=eq.chatbot&select=id&order=created_at.desc&limit=1", headers=headers)
        convs = r2.json()
        if not convs:
            return {"messages": []}
        conv_id = convs[0]["id"]
        
        # Prendi tutti i messaggi outbound (ai + operator)
        url = f"{base}/messages?conversation_id=eq.{conv_id}&direction=eq.outbound&sender_type=in.(ai,operator)&select=id,content,content_type,media_url,sender_type,created_at&order=created_at.asc"
        r3 = await client.get(url, headers=headers)
        msgs = r3.json()
        if isinstance(msgs, list):
            return {"messages": msgs}
        return {"messages": []}

# ── Upload e invio media dall'operatore ──────────────────────────────────────
@router.post("/conversations/{conversation_id}/upload")
async def upload_and_send(conversation_id: str, request: Request):
    """Riceve un file dall'operatore, lo salva e lo invia sul canale."""
    import httpx
    import os
    import uuid
    from backend.app.core.config import settings
    from backend.app.services.agent.channel_dispatcher import send_channel_media

    form = await request.form()
    file = form.get("file")
    caption = form.get("caption", "")
    source = form.get("source", "dashboard")
    
    if not file:
        raise HTTPException(status_code=400, detail="Nessun file")
    
    # Determina tipo
    content_type_map = {
        "image/jpeg": "image", "image/png": "image", "image/gif": "image", "image/webp": "image",
        "application/pdf": "document", "application/msword": "document",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "document",
        "text/plain": "document", "text/csv": "document",
        "audio/ogg": "audio", "audio/mpeg": "audio", "audio/wav": "audio",
        "video/mp4": "video",
    }
    mime = file.content_type or "application/octet-stream"
    media_type = content_type_map.get(mime, "document")
    
    # Salva file
    ext = os.path.splitext(file.filename or "file")[1] or ".bin"
    uid = uuid.uuid4().hex[:12]
    safe_name = uid + ext
    subdir = os.path.join("/home/digidentity-v2/uploads", media_type)
    os.makedirs(subdir, exist_ok=True)
    filepath = os.path.join(subdir, safe_name)
    
    file_bytes = await file.read()
    with open(filepath, "wb") as f:
        f.write(file_bytes)
    
    # Converti audio WebM -> OGG Opus
    if media_type == "audio":
        import subprocess
        # Rinomina originale in .webm
        webm_path = os.path.join(subdir, uid + ".webm")
        os.rename(filepath, webm_path)
        ogg_name = uid + ".opus"
        ogg_path = os.path.join(subdir, ogg_name)
        try:
            result = subprocess.run(["ffmpeg", "-y", "-i", webm_path, "-c:a", "libopus", "-b:a", "64k", "-vbr", "on", "-compression_level", "10", "-application", "voip", ogg_path], capture_output=True, timeout=30)
            if os.path.exists(ogg_path) and os.path.getsize(ogg_path) > 0:
                os.remove(webm_path)
                filepath = ogg_path
                safe_name = ogg_name
                logger.info(f"Audio convertito in OGG Opus: {ogg_path}")
            else:
                logger.warning(f"ffmpeg fallito: {result.stderr.decode()}")
                os.rename(webm_path, filepath)
        except Exception as e:
            logger.warning(f"ffmpeg errore: {e}")
            if os.path.exists(webm_path):
                os.rename(webm_path, filepath)
    
    media_url = f"https://agent.digidentityagency.it/uploads/{media_type}/{safe_name}"
    
    # Recupera conversazione e contatto
    headers = {"apikey": settings.SUPABASE_KEY, "Authorization": f"Bearer {settings.SUPABASE_KEY}"}
    base = settings.SUPABASE_URL + "/rest/v1"
    
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{base}/conversations?id=eq.{conversation_id}&select=*", headers=headers)
        convs = r.json()
        if not convs:
            raise HTTPException(status_code=404, detail="Conversazione non trovata")
        conv = convs[0]
        
        r2 = await client.get(f"{base}/contacts?id=eq.{conv['contact_id']}&select=*", headers=headers)
        contacts = r2.json()
        if not contacts:
            raise HTTPException(status_code=404, detail="Contatto non trovato")
        contact = contacts[0]
        
        # Salva messaggio in Supabase
        is_widget = source == "widget"
        msg_data = {
            "conversation_id": conversation_id,
            "contact_id": conv["contact_id"],
            "direction": "inbound" if is_widget else "outbound",
            "sender_type": "contact" if is_widget else "operator",
            "sender_name": "Stefano",
            "content": caption or file.filename or "File",
            "content_type": media_type,
            "media_url": media_url,
            "media_mime_type": mime,
            "channel_type": conv["channel_type"],
            "delivered": False,
            "read": False,
            "metadata": {}
        }
        await client.post(f"{base}/messages", json=msg_data, headers={**headers, "Content-Type": "application/json", "Prefer": "return=minimal"})
        
        # Aggiorna conversazione
        update_data = {"last_message_at": __import__('datetime').datetime.utcnow().isoformat(), "last_message_preview": caption or file.filename or "File inviato"}
        await client.patch(f"{base}/conversations?id=eq.{conversation_id}", json=update_data, headers={**headers, "Content-Type": "application/json", "Prefer": "return=minimal"})
    
    # Invia sul canale
    result = await send_channel_media(conv["channel_type"], contact, media_url, media_type, caption, file.filename or "")
    
    # Aggiorna channel_message_id per tracking delivered/read
    wa_msg_id = result.get("wa_message_id", "")
    if wa_msg_id:
        async with httpx.AsyncClient() as _cl:
            r = await _cl.get(f"{base}/messages?conversation_id=eq.{conversation_id}&direction=eq.outbound&order=created_at.desc&limit=1&select=id", headers=headers)
            msgs = r.json()
            if msgs:
                await _cl.patch(f"{base}/messages?id=eq.{msgs[0]['id']}", json={"channel_message_id": wa_msg_id, "delivered": True}, headers={**headers, "Content-Type": "application/json", "Prefer": "return=minimal"})
    
    logger.info(f"Media inviato su {conv['channel_type']} per conv {conversation_id}: {result}")
    
    # Se chatbot con AI attiva: trascrivi audio/analizza immagine e rispondi
    ai_response_text = None
    logger.info(f"Upload AI check: channel={conv.get('channel_type')} ai_enabled={conv.get('ai_enabled')} media_type={media_type} filepath={filepath}")
    if conv.get("channel_type") == "chatbot" and conv.get("ai_enabled", True):
        try:
            from backend.app.services.agent.media_service import transcribe_audio, analyze_image
            from backend.app.services.agent.ai_service import generate_ai_response
            
            user_content = caption or ""
            if media_type == "audio":
                with open(filepath, "rb") as af:
                    audio_filename = os.path.basename(filepath).replace(".opus", ".ogg")
                    user_content = await transcribe_audio(af.read(), audio_filename)
                logger.info(f"Chatbot vocale trascritto: {user_content[:100]}")
            elif media_type == "image":
                user_content = f"[Immagine inviata: {media_url}]"
            
            if user_content:
                ai_result = await generate_ai_response(
                    conversation_id=conversation_id,
                    contact_id=conv["contact_id"],
                    user_message=user_content,
                    channel_type="chatbot",
                )
                ai_response_text = ai_result.get("response", "")
                logger.info(f"Chatbot AI risposta a media: {ai_response_text[:100]}")
        except Exception as e:
            logger.error(f"Errore AI su media chatbot: {e}")
    
    return {"status": "sent", "media_url": media_url, "channel": conv["channel_type"], "result": result, "ai_response": ai_response_text}
