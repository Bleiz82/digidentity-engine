"""
Google Calendar Service - Gestisce appuntamenti su Google Calendar.
Usato dai tool AI di Digy per verificare disponibilita, creare, modificare e cancellare eventi.
"""

import httpx
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# ─── Token Management ───────────────────────────────────────

async def _get_access_token() -> str:
    """Ottieni access token fresco usando il refresh token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.GOOGLE_CALENDAR_CLIENT_ID,
                "client_secret": settings.GOOGLE_CALENDAR_CLIENT_SECRET,
                "refresh_token": settings.GOOGLE_CALENDAR_REFRESH_TOKEN,
                "grant_type": "refresh_token",
            },
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        logger.debug("Google Calendar: access token ottenuto")
        return token


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


# ─── Calendar API ────────────────────────────────────────────

CALENDAR_ID = None  # set at runtime from settings

def _cal_id() -> str:
    global CALENDAR_ID
    if not CALENDAR_ID:
        CALENDAR_ID = settings.GOOGLE_CALENDAR_ID or "primary"
    return CALENDAR_ID


async def get_events(date_from: str, date_to: str) -> list:
    """
    Recupera eventi dal calendario tra due date ISO.
    Ritorna lista di dict con id, summary, start, end, location, hangoutLink.
    """
    token = await _get_access_token()
    
    # Assicura formato ISO con timezone
    if not date_from.endswith("Z") and "+" not in date_from:
        date_from += "+00:00"
    if not date_to.endswith("Z") and "+" not in date_to:
        date_to += "+00:00"
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://www.googleapis.com/calendar/v3/calendars/{_cal_id()}/events",
            headers=_headers(token),
            params={
                "timeMin": date_from,
                "timeMax": date_to,
                "singleEvents": "true",
                "orderBy": "startTime",
                "maxResults": 50,
            },
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
    
    events = []
    for item in items:
        start = item.get("start", {}).get("dateTime", item.get("start", {}).get("date", ""))
        end = item.get("end", {}).get("dateTime", item.get("end", {}).get("date", ""))
        events.append({
            "id": item.get("id"),
            "summary": item.get("summary", ""),
            "start": start,
            "end": end,
            "location": item.get("location", ""),
            "meet_link": item.get("hangoutLink", ""),
            "status": item.get("status", ""),
        })
    
    logger.info(f"Google Calendar: {len(events)} eventi trovati tra {date_from[:10]} e {date_to[:10]}")
    return events


async def create_event(
    summary: str,
    start_datetime: str,
    duration_minutes: int = 45,
    description: str = "",
    location: str = "",
    attendee_email: str = "",
    add_meet: bool = True,
) -> dict:
    """
    Crea un evento su Google Calendar.
    Ritorna dict con id, summary, start, end, meet_link.
    """
    token = await _get_access_token()
    
    # Parse start e calcola end
    if start_datetime.endswith("Z"):
        start_dt = datetime.fromisoformat(start_datetime.replace("Z", "+00:00"))
    elif "+" not in start_datetime and "-" not in start_datetime[10:]:
        start_dt = datetime.fromisoformat(start_datetime).replace(tzinfo=timezone(timedelta(hours=1)))
    else:
        start_dt = datetime.fromisoformat(start_datetime)
    
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    
    event_body = {
        "summary": summary,
        "description": description,
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": "Europe/Rome",
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": "Europe/Rome",
        },
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 1440},
                {"method": "popup", "minutes": 60},
            ],
        },
    }
    
    if location:
        event_body["location"] = location
    
    if attendee_email:
        event_body["attendees"] = [{"email": attendee_email}]
    
    if add_meet:
        event_body["conferenceData"] = {
            "createRequest": {
                "requestId": f"digy-{start_dt.strftime('%Y%m%d%H%M')}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        }
    
    params = {}
    if add_meet:
        params["conferenceDataVersion"] = 1
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://www.googleapis.com/calendar/v3/calendars/{_cal_id()}/events",
            headers=_headers(token),
            json=event_body,
            params=params,
        )
        resp.raise_for_status()
        created = resp.json()
    
    result = {
        "id": created.get("id"),
        "summary": created.get("summary"),
        "start": created.get("start", {}).get("dateTime", ""),
        "end": created.get("end", {}).get("dateTime", ""),
        "meet_link": created.get("hangoutLink", ""),
        "html_link": created.get("htmlLink", ""),
        "status": "confirmed",
    }
    
    logger.info(f"Google Calendar: evento creato '{summary}' il {start_dt.strftime('%d/%m/%Y %H:%M')}")
    return result


async def update_event(
    event_id: str,
    summary: Optional[str] = None,
    start_datetime: Optional[str] = None,
    duration_minutes: Optional[int] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
) -> dict:
    """Aggiorna un evento esistente su Google Calendar."""
    token = await _get_access_token()
    
    # Prima recupera l'evento attuale
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://www.googleapis.com/calendar/v3/calendars/{_cal_id()}/events/{event_id}",
            headers=_headers(token),
        )
        resp.raise_for_status()
        existing = resp.json()
    
    # Aggiorna solo i campi forniti
    if summary:
        existing["summary"] = summary
    if description:
        existing["description"] = description
    if location:
        existing["location"] = location
    
    if start_datetime:
        if start_datetime.endswith("Z"):
            start_dt = datetime.fromisoformat(start_datetime.replace("Z", "+00:00"))
        elif "+" not in start_datetime and "-" not in start_datetime[10:]:
            start_dt = datetime.fromisoformat(start_datetime).replace(tzinfo=timezone(timedelta(hours=1)))
        else:
            start_dt = datetime.fromisoformat(start_datetime)
        
        dur = duration_minutes or 45
        end_dt = start_dt + timedelta(minutes=dur)
        
        existing["start"] = {"dateTime": start_dt.isoformat(), "timeZone": "Europe/Rome"}
        existing["end"] = {"dateTime": end_dt.isoformat(), "timeZone": "Europe/Rome"}
    
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            f"https://www.googleapis.com/calendar/v3/calendars/{_cal_id()}/events/{event_id}",
            headers=_headers(token),
            json=existing,
        )
        resp.raise_for_status()
        updated = resp.json()
    
    logger.info(f"Google Calendar: evento {event_id} aggiornato")
    return {
        "id": updated.get("id"),
        "summary": updated.get("summary"),
        "start": updated.get("start", {}).get("dateTime", ""),
        "end": updated.get("end", {}).get("dateTime", ""),
        "meet_link": updated.get("hangoutLink", ""),
        "status": "updated",
    }


async def delete_event(event_id: str) -> dict:
    """Cancella un evento da Google Calendar."""
    token = await _get_access_token()
    
    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            f"https://www.googleapis.com/calendar/v3/calendars/{_cal_id()}/events/{event_id}",
            headers=_headers(token),
        )
        resp.raise_for_status()
    
    logger.info(f"Google Calendar: evento {event_id} cancellato")
    return {"id": event_id, "status": "cancelled"}


async def check_slot_available(date_str: str, hour: int, duration_minutes: int = 45) -> bool:
    """Verifica se uno slot specifico e libero su Google Calendar."""
    start = f"{date_str}T{hour:02d}:00:00+01:00"
    end_dt = datetime.fromisoformat(start) + timedelta(minutes=duration_minutes)
    end = end_dt.isoformat()
    
    events = await get_events(start, end)
    # Filtra solo eventi confermati (non cancellati)
    active = [e for e in events if e["status"] != "cancelled"]
    return len(active) == 0


async def test_connection() -> dict:
    """Testa la connessione a Google Calendar."""
    try:
        token = await _get_access_token()
        now = datetime.now(timezone.utc)
        tomorrow = now + timedelta(days=1)
        events = await get_events(now.isoformat(), tomorrow.isoformat())
        return {
            "status": "ok",
            "calendar_id": _cal_id(),
            "events_next_24h": len(events),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
