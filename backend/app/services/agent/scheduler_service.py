"""
Scheduler Service - Reminder appuntamenti e Followup automatici.
Gira come task asyncio dentro il backend.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from backend.app.core.supabase_client import get_supabase
from backend.app.services.agent.channel_dispatcher import send_whatsapp_message, send_whatsapp_template, send_email_message, send_telegram_message
from backend.app.services.agent.email_inbound_service import check_email_inbound

logger = logging.getLogger(__name__)

REMINDER_CHECK_INTERVAL = 60  # secondi
FOLLOWUP_CHECK_INTERVAL = 300  # secondi


async def check_appointment_reminders():
    """Controlla appuntamenti e invia reminder 24h e 1h prima."""
    try:
        supabase = get_supabase()
        now = datetime.now(timezone.utc)
        in_24h = now + timedelta(hours=24, minutes=30)
        in_23h = now + timedelta(hours=23, minutes=30)
        in_1h30 = now + timedelta(hours=1, minutes=30)
        in_30m = now + timedelta(minutes=30)

        # Reminder 24h
        result = supabase.table("appointments").select("*, contacts(*)").eq("stato", "confermato").eq("reminder_24h_sent", False).gte("data_ora", in_23h.isoformat()).lte("data_ora", in_24h.isoformat()).execute()
        for apt in (result.data or []):
            contact = apt.get("contacts") or {}
            phone = contact.get("telefono") or apt.get("cliente_telefono")
            nome = contact.get("nome") or "Cliente"
            data_ora = apt.get("data_ora", "")
            modalita = apt.get("modalita", "videocall")
            titolo = apt.get("titolo", "Consulenza")
            try:
                dt = datetime.fromisoformat(data_ora)
                ora_str = dt.strftime("%H:%M")
                data_str = dt.strftime("%d/%m/%Y")
            except Exception:
                ora_str = "da definire"
                data_str = "da definire"
            msg = "Ciao " + nome + "! Ti ricordo il tuo appuntamento di domani: " + titolo + " alle " + ora_str + " del " + data_str + " (" + modalita + "). A domani!"
            if phone:
                await send_whatsapp_message(phone, msg)
                logger.info("Reminder 24h inviato a " + nome + " (" + phone + ")")
            email = contact.get("email")
            if email:
                await send_email_message(email, "Promemoria: " + titolo + " domani", msg)
            supabase.table("appointments").update({"reminder_24h_sent": True}).eq("id", apt["id"]).execute()

        # Reminder 1h
        result = supabase.table("appointments").select("*, contacts(*)").eq("stato", "confermato").eq("reminder_1h_sent", False).gte("data_ora", in_30m.isoformat()).lte("data_ora", in_1h30.isoformat()).execute()
        for apt in (result.data or []):
            contact = apt.get("contacts") or {}
            phone = contact.get("telefono") or apt.get("cliente_telefono")
            nome = contact.get("nome") or "Cliente"
            modalita = apt.get("modalita", "videocall")
            hangout = apt.get("hangout_link", "")
            msg = "Ciao " + nome + "! Tra poco il tuo appuntamento."
            if modalita == "videocall" and hangout:
                msg = msg + " Ecco il link: " + hangout
            elif modalita == "presenza":
                location = apt.get("location", "Via Dettori 3, Samatzai")
                msg = msg + " Ti aspettiamo in: " + location
            if phone:
                await send_whatsapp_message(phone, msg)
                logger.info("Reminder 1h inviato a " + nome + " (" + phone + ")")
            supabase.table("appointments").update({"reminder_1h_sent": True}).eq("id", apt["id"]).execute()

    except Exception as e:
        logger.error("Errore check_appointment_reminders: " + str(e))


async def check_followups():
    """Controlla conversazioni inattive e invia followup."""
    try:
        supabase = get_supabase()
        now = datetime.now(timezone.utc)

        # Followup dopo 24h senza risposta (lead nuovi)
        cutoff_24h = (now - timedelta(hours=24)).isoformat()
        cutoff_20h = (now - timedelta(hours=20)).isoformat()
        result = supabase.table("conversations").select("*, contacts(*)").eq("status", "ai").lte("last_message_at", cutoff_24h).gte("last_message_at", cutoff_20h).execute()
        for conv in (result.data or []):
            contact = conv.get("contacts") or {}
            # Controlla se abbiamo gia mandato followup (check metadata)
            meta = conv.get("metadata") or {}
            if meta.get("followup_24h_sent"):
                continue
            nome = contact.get("nome") or "Ciao"
            phone = contact.get("telefono")
            channel = conv.get("channel_type", "whatsapp")
            msg = "Ciao " + nome + "! Ti scrivo per sapere se hai avuto modo di pensare a quanto ci siamo detti. Se hai domande o vuoi approfondire, sono qui per te!"
            if channel == "whatsapp" and phone:
                await send_whatsapp_message(phone, msg)
            elif channel == "telegram":
                tg_id = contact.get("telegram_id")
                if tg_id:
                    await send_telegram_message(tg_id, msg)
            elif channel == "email":
                email = contact.get("email")
                if email:
                    await send_email_message(email, "Ti stavamo aspettando!", msg)
            meta["followup_24h_sent"] = True
            supabase.table("conversations").update({"metadata": meta}).eq("id", conv["id"]).execute()
            logger.info("Followup 24h inviato: " + nome + " via " + channel)

        # Followup dopo 72h (ultimo tentativo)
        cutoff_72h = (now - timedelta(hours=72)).isoformat()
        cutoff_68h = (now - timedelta(hours=68)).isoformat()
        result = supabase.table("conversations").select("*, contacts(*)").eq("status", "ai").lte("last_message_at", cutoff_72h).gte("last_message_at", cutoff_68h).execute()
        for conv in (result.data or []):
            contact = conv.get("contacts") or {}
            meta = conv.get("metadata") or {}
            if meta.get("followup_72h_sent"):
                continue
            nome = contact.get("nome") or "Ciao"
            phone = contact.get("telefono")
            channel = conv.get("channel_type", "whatsapp")
            msg = "Ciao " + nome + "! Volevo solo assicurarmi che tu abbia ricevuto le informazioni. Se hai bisogno di qualsiasi cosa, puoi scrivermi qui o prenotare una consulenza gratuita. Buona giornata!"
            if channel == "whatsapp" and phone:
                await send_whatsapp_message(phone, msg)
            elif channel == "telegram":
                tg_id = contact.get("telegram_id")
                if tg_id:
                    await send_telegram_message(tg_id, msg)
            meta["followup_72h_sent"] = True
            supabase.table("conversations").update({"metadata": meta}).eq("id", conv["id"]).execute()
            logger.info("Followup 72h inviato: " + nome + " via " + channel)

    except Exception as e:
        logger.error("Errore check_followups: " + str(e))


async def scheduler_loop():
    """Loop principale dello scheduler."""
    logger.info("Scheduler avviato")
    reminder_counter = 0
    while True:
        try:
            await check_appointment_reminders()
            await check_email_inbound()
            reminder_counter += 1
            if reminder_counter >= 5:  # ogni 5 minuti check followup
                await check_followups()
                reminder_counter = 0
        except Exception as e:
            logger.error("Errore scheduler_loop: " + str(e))
        await asyncio.sleep(REMINDER_CHECK_INTERVAL)