"""
DigIdentity Engine — WhatsApp Sender
Invio messaggi WhatsApp tramite Meta WhatsApp Business API.
"""

import httpx
from typing import Dict, Any
from app.config import get_settings


async def send_whatsapp_free_report(
    to_phone: str,
    to_name: str,
    nome_azienda: str,
    pdf_url: str = None
) -> Dict[str, Any]:
    """
    Invia messaggio WhatsApp con notifica report gratuito.
    
    NOTA: Meta WhatsApp Business API richiede template pre-approvati.
    Per ora invia messaggio semplice. Per allegati PDF serve hosting pubblico.
    
    Args:
        to_phone: Numero telefono (formato internazionale +39...)
        to_name: Nome destinatario
        nome_azienda: Nome azienda
        pdf_url: URL pubblico del PDF (opzionale)
        
    Returns:
        dict: Success status + message ID
    """
    settings = get_settings()
    
    print(f"📱 Invio WhatsApp a: {to_phone}")
    
    # Messaggio
    message_text = f"""🚀 *Diagnosi Strategica Digitale Completata!*

Ciao {to_name}! 👋

Abbiamo analizzato la presenza digitale di *{nome_azienda}* e il tuo report è pronto!

📄 Troverai tutto nella email che ti abbiamo appena inviato.

Il report include:
✅ Analisi sito web e SEO
✅ Posizionamento Google
✅ Google My Business
✅ Social Media
✅ Competitor locali
✅ 5 azioni concrete da fare SUBITO

🔥 *Vuoi la versione Premium?*
Strategia completa + Piano AI personalizzato → 99€

Hai domande? Rispondi a questo messaggio!

_Stefano Corda_
_DigIdentity Agency_
_Specialisti AI & Automazioni per MPMI_
"""
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Endpoint Meta WhatsApp Business API
            url = f"https://graph.facebook.com/v18.0/{settings.whatsapp_phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {settings.whatsapp_access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to_phone,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": message_text
                }
            }
            
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            message_id = data.get("messages", [{}])[0].get("id")
            
            print(f"✅ WhatsApp inviato con successo")
            print(f"   Message ID: {message_id}")
            
            return {
                "success": True,
                "message_id": message_id,
                "to": to_phone
            }
    
    except httpx.HTTPStatusError as e:
        error_msg = f"Errore HTTP {e.response.status_code}: {e.response.text}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }
    
    except Exception as e:
        error_msg = f"Errore invio WhatsApp: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }


async def send_whatsapp_premium_report(
    to_phone: str,
    to_name: str,
    nome_azienda: str,
    pdf_url: str = None
) -> Dict[str, Any]:
    """
    Invia messaggio WhatsApp con notifica report premium completato.

    Args:
        to_phone: Numero telefono (formato internazionale +39...)
        to_name: Nome destinatario
        nome_azienda: Nome azienda
        pdf_url: URL pubblico del PDF (opzionale)

    Returns:
        dict: Success status + message ID
    """
    settings = get_settings()

    print(f"📱 Invio WhatsApp PREMIUM a: {to_phone}")

    message_text = f"""⭐ *Diagnosi Premium Completata!*

Ciao {to_name}! 🎉

La tua *Diagnosi Strategica Digitale PREMIUM* per *{nome_azienda}* è pronta!

📄 Ti abbiamo appena inviato via email il report completo (40-50 pagine) con:

📊 Score digitale complessivo
🌐 Analisi sito web approfondita
🔍 Audit SEO completo
📍 Ottimizzazione Google My Business
📱 Strategia Social Media
⚔️ Analisi competitor dettagliata
🤖 Piano AI & Automazioni su misura
📅 Piano operativo 90 giorni
💰 Budget e ROI atteso
🤝 Proposta di collaborazione

🚀 *Prossimo passo consigliato:*
Prenota una call gratuita di 30 min per discutere la strategia insieme!

📞 Chiamami: +39 392 199 0215
📧 Email: info@digidentityagency.it
🌐 digidentityagency.it/contatti-digidentity

Grazie per aver scelto DigIdentity Agency! 🙏

_Stefano Corda_
_DigIdentity Agency_
_Specialisti AI & Automazioni per MPMI_
"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"https://graph.facebook.com/v18.0/{settings.whatsapp_phone_number_id}/messages"

            headers = {
                "Authorization": f"Bearer {settings.whatsapp_access_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "messaging_product": "whatsapp",
                "to": to_phone,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": message_text
                }
            }

            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            message_id = data.get("messages", [{}])[0].get("id")

            print(f"✅ WhatsApp PREMIUM inviato con successo")
            print(f"   Message ID: {message_id}")

            return {
                "success": True,
                "message_id": message_id,
                "to": to_phone
            }

    except httpx.HTTPStatusError as e:
        error_msg = f"Errore HTTP {e.response.status_code}: {e.response.text}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }

    except Exception as e:
        error_msg = f"Errore invio WhatsApp premium: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }

