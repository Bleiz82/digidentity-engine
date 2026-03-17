"""
Media Service - Gestisce vocali, immagini, documenti e video.
"""

import httpx
import tempfile
import logging
import os
from openai import AsyncOpenAI
from backend.app.core.config import settings

logger = logging.getLogger(__name__)
ai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def download_media_from_whatsapp(media_id):
    url = "https://graph.facebook.com/" + settings.WHATSAPP_API_VERSION + "/" + media_id
    headers = {"Authorization": "Bearer " + settings.WHATSAPP_ACCESS_TOKEN}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, headers=headers)
        media_url = resp.json().get("url")
        if not media_url:
            raise ValueError("URL media non trovato per " + media_id)
        resp = await client.get(media_url, headers=headers)
        return resp.content


async def download_media_from_telegram(file_id):
    token = settings.TELEGRAM_BOT_TOKEN
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get("https://api.telegram.org/bot" + token + "/getFile?file_id=" + file_id)
        result = resp.json()
        if not result.get("ok"):
            raise ValueError("File Telegram non trovato: " + file_id)
        file_path = result["result"]["file_path"]
        resp = await client.get("https://api.telegram.org/file/bot" + token + "/" + file_path)
        return resp.content


async def download_media_from_url(url):
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        return resp.content


async def transcribe_audio(audio_bytes, filename="audio.ogg"):
    tmp_path = None
    try:
        ext = os.path.splitext(filename)[1] or ".ogg"
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        with open(tmp_path, "rb") as audio_file:
            transcript = await ai.audio.transcriptions.create(model="whisper-1", file=audio_file, language="it")
        os.unlink(tmp_path)
        text = transcript.text.strip()
        logger.info("Whisper trascrizione: " + str(len(text)) + " caratteri")
        return text
    except Exception as e:
        logger.error("Errore trascrizione Whisper: " + str(e))
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return "[Vocale non trascritto]"


async def analyze_image(image_bytes=None, image_url=None, context=""):
    try:
        import base64
        system_msg = "Sei un assistente che analizza immagini per DigIdentity Agency. Descrivi cosa vedi in modo utile e conciso in italiano."
        messages = [{"role": "system", "content": system_msg}]
        content_parts = []
        if context:
            content_parts.append({"type": "text", "text": "Contesto: " + context})
        content_parts.append({"type": "text", "text": "Analizza questa immagine:"})
        if image_url:
            content_parts.append({"type": "image_url", "image_url": {"url": image_url}})
        elif image_bytes:
            b64 = base64.b64encode(image_bytes).decode()
            content_parts.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}})
        messages.append({"role": "user", "content": content_parts})
        response = await ai.chat.completions.create(model="gpt-4o", messages=messages, max_tokens=500)
        analysis = response.choices[0].message.content.strip()
        logger.info("Vision analisi: " + str(len(analysis)) + " caratteri")
        return analysis
    except Exception as e:
        logger.error("Errore Vision: " + str(e))
        return "[Immagine non analizzata]"


async def analyze_document(doc_bytes, filename="document.pdf", context=""):
    try:
        text = ""
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            try:
                import fitz
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(doc_bytes)
                    tmp_path = tmp.name
                doc = fitz.open(tmp_path)
                for page in doc:
                    text += page.get_text()
                doc.close()
                os.unlink(tmp_path)
            except ImportError:
                text = "[PDF reader non disponibile]"
        elif ext in (".txt", ".csv", ".md"):
            text = doc_bytes.decode("utf-8", errors="ignore")
        else:
            text = "[Formato " + ext + " non supportato]"
        if not text or len(text) < 10:
            return "[Documento " + filename + " ricevuto ma non leggibile]"
        if len(text) > 3000:
            text = text[:3000] + "... [troncato]"
        doc_prompt = "Documento: " + filename + " --- " + text
        response = await ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Riassumi questo documento in italiano in modo conciso e utile."},
                {"role": "user", "content": doc_prompt}
            ],
            max_tokens=300,
        )
        summary = response.choices[0].message.content.strip()
        logger.info("Documento analizzato: " + filename + " -> " + str(len(summary)) + " caratteri")
        return summary
    except Exception as e:
        logger.error("Errore analisi documento: " + str(e))
        return "[Documento " + filename + " ricevuto]"


async def process_media(content_type, channel, media_id=None, media_url=None, file_id=None, filename=None, context=""):
    try:
        media_bytes = None
        if channel == "whatsapp" and media_id:
            media_bytes = await download_media_from_whatsapp(media_id)
        elif channel == "telegram" and file_id:
            media_bytes = await download_media_from_telegram(file_id)
        elif media_url:
            media_bytes = await download_media_from_url(media_url)
        if not media_bytes:
            return {"transcription": "[Media " + content_type + " ricevuto ma non scaricabile]", "processed": False}
        if content_type == "audio":
            transcription = await transcribe_audio(media_bytes, filename or "audio.ogg")
            return {"transcription": transcription, "processed": True, "type": "whisper"}
        elif content_type == "image":
            analysis = await analyze_image(image_bytes=media_bytes, context=context)
            return {"transcription": analysis, "processed": True, "type": "vision"}
        elif content_type == "document":
            summary = await analyze_document(media_bytes, filename or "document.pdf", context)
            return {"transcription": summary, "processed": True, "type": "document"}
        elif content_type == "video":
            return {"transcription": "[Video ricevuto]", "processed": False, "type": "video"}
        else:
            return {"transcription": "[Media " + content_type + " ricevuto]", "processed": False}
    except Exception as e:
        logger.error("Errore process_media: " + str(e))
        return {"transcription": "[Errore elaborazione " + content_type + "]", "processed": False}
