"""
DigIdentity Engine — Endpoint Stripe: checkout, webhook, success page.

Rotte:
    POST /api/payment/create-checkout   → Crea una Stripe Checkout Session (99 €)
    POST /api/payment/webhook           → Riceve eventi Stripe (webhook)
    GET  /api/payment/success           → Pagina HTML di conferma post-pagamento
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import stripe

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payment", tags=["payment"])

# ---------------------------------------------------------------------------
# Inizializza Stripe con la chiave segreta dal .env
# ---------------------------------------------------------------------------
stripe.api_key = settings.STRIPE_SECRET_KEY


# ===========================================================================
# POST /api/payment/create-checkout
# ===========================================================================
@router.post("/create-checkout")
async def create_checkout_session(request: Request):
    """
    Crea una Stripe Checkout Session per il report premium (99 €).

    Body JSON atteso:
        {
            "lead_id": "uuid-del-lead",
            "email":   "cliente@example.com"
        }

    La success_url include il placeholder {CHECKOUT_SESSION_ID} che Stripe
    sostituirà automaticamente con l'ID reale della sessione completata.
    """
    try:
        body = await request.json()
        lead_id: str = body.get("lead_id", "")
        email: str = body.get("email", "")

        if not lead_id or not email:
            raise HTTPException(
                status_code=400,
                detail="Parametri mancanti: lead_id e email sono obbligatori.",
            )

        # ----- Crea la Checkout Session su Stripe -----
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            customer_email=email,
            line_items=[
                {
                    "price": settings.STRIPE_PRICE_ID,
                    "quantity": 1,
                },
            ],
            metadata={
                "lead_id": lead_id,
            },
            success_url=(
                f"{settings.APP_BASE_URL}/api/payment/success"
                f"?session_id={{CHECKOUT_SESSION_ID}}"
            ),
            cancel_url=f"{settings.APP_BASE_URL}/api/payment/cancel",
        )

        logger.info(
            "Checkout session creata: %s per lead %s",
            checkout_session.id,
            lead_id,
        )

        return JSONResponse(
            content={
                "checkout_url": checkout_session.url,
                "session_id": checkout_session.id,
            }
        )

    except stripe.error.StripeError as e:
        logger.error("Errore Stripe nella creazione checkout: %s", str(e))
        raise HTTPException(status_code=502, detail=f"Errore Stripe: {str(e)}")
    except Exception as e:
        logger.error("Errore imprevisto create-checkout: %s", str(e))
        raise HTTPException(status_code=500, detail="Errore interno del server.")


# ===========================================================================
# POST /api/payment/webhook
# ===========================================================================
@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Riceve gli eventi webhook da Stripe.

    Flusso principale gestito:
        checkout.session.completed  →  aggiorna lo stato del lead su Supabase
                                       e avvia il task Celery `task_premium_report`.

    Sicurezza:
        Verifica la firma dell'evento con STRIPE_WEBHOOK_SECRET.
        In sviluppo (Stripe CLI), il webhook secret viene fornito
        dallo stripe listen --forward-to.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    # ----- Verifica presenza header stripe-signature -----
    if not sig_header:
        logger.error("Webhook ricevuto senza header stripe-signature.")
        raise HTTPException(
            status_code=400,
            detail="Header stripe-signature mancante.",
        )

    # ----- Verifica firma webhook -----
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Webhook payload non valido.")
        raise HTTPException(status_code=400, detail="Payload non valido.")
    except stripe.error.SignatureVerificationError:
        logger.error("Webhook firma non valida — verificare STRIPE_WEBHOOK_SECRET.")
        raise HTTPException(status_code=400, detail="Firma non valida.")

    logger.info("Webhook ricevuto: tipo=%s, id=%s", event["type"], event["id"])

    # ----- Gestisci evento checkout.session.completed -----
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        lead_id = session.get("metadata", {}).get("lead_id")
        customer_email = session.get("customer_email", "")
        payment_intent = session.get("payment_intent", "")
        amount_total = session.get("amount_total", 0)

        logger.info(
            "Pagamento completato: lead_id=%s, email=%s, payment_intent=%s, amount=%s",
            lead_id,
            customer_email,
            payment_intent,
            amount_total,
        )

        if not lead_id:
            logger.error(
                "checkout.session.completed senza lead_id nei metadata! session=%s",
                session.get("id"),
            )
            return JSONResponse(content={"status": "error", "detail": "lead_id mancante"})

        # ----- Aggiorna stato del lead su Supabase -----
        try:
            from backend.app.core.supabase_client import get_supabase

            supabase = get_supabase()
            supabase.table("leads").update(
                {
                    "status": "payment_completed",
                    "stripe_session_id": session.get("id", ""),
                    "stripe_payment_intent": payment_intent,
                }
            ).eq("id", lead_id).execute()

            logger.info("Lead %s aggiornato a payment_completed.", lead_id)
        except Exception as e:
            logger.error("Errore aggiornamento Supabase per lead %s: %s", lead_id, str(e))
            # Non blocchiamo il task premium anche se Supabase fallisce

        # ----- Avvia il task Celery per il report premium -----
        try:
            from backend.app.tasks.premium_report_task import task_premium_report

            task_premium_report.delay(lead_id)
            logger.info("Task task_premium_report avviato per lead %s.", lead_id)
        except Exception as e:
            logger.error(
                "Errore lancio task_premium_report per lead %s: %s", lead_id, str(e)
            )
            return JSONResponse(
                status_code=500,
                content={"status": "error", "detail": "Impossibile avviare il task premium."},
            )

        return JSONResponse(
            content={
                "status": "success",
                "lead_id": lead_id,
                "event": "checkout.session.completed",
            }
        )

    # ----- Altri eventi (log e ignora) -----
    logger.info("Evento Stripe non gestito: %s", event["type"])
    return JSONResponse(content={"status": "ignored", "event": event["type"]})


# ===========================================================================
# GET /api/payment/success
# ===========================================================================
@router.get("/success", response_class=HTMLResponse)
async def payment_success(session_id: str = ""):
    """
    Pagina HTML di conferma post-pagamento.
    Stripe redirige qui dopo un checkout andato a buon fine.
    Il parametro session_id viene passato in query string.
    """
    html_content = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pagamento Confermato — DigIdentity Engine</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #e2e8f0;
        }}
        .card {{
            background: rgba(30, 41, 59, 0.8);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 24px;
            padding: 48px 40px;
            max-width: 560px;
            width: 90%;
            text-align: center;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.4);
        }}
        .icon {{
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #22c55e, #16a34a);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 24px;
            box-shadow: 0 0 30px rgba(34, 197, 94, 0.3);
        }}
        .icon svg {{
            width: 40px;
            height: 40px;
            fill: none;
            stroke: white;
            stroke-width: 3;
            stroke-linecap: round;
            stroke-linejoin: round;
        }}
        h1 {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 12px;
            background: linear-gradient(135deg, #22c55e, #4ade80);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{
            font-size: 18px;
            color: #94a3b8;
            margin-bottom: 32px;
            line-height: 1.6;
        }}
        .info-box {{
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        .info-box h3 {{
            color: #818cf8;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
        }}
        .info-box p {{
            color: #cbd5e1;
            font-size: 15px;
            line-height: 1.7;
        }}
        .steps {{
            text-align: left;
            margin: 24px 0;
        }}
        .step {{
            display: flex;
            align-items: flex-start;
            gap: 16px;
            margin-bottom: 16px;
        }}
        .step-number {{
            width: 32px;
            height: 32px;
            min-width: 32px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 14px;
            color: white;
        }}
        .step-text {{
            font-size: 15px;
            color: #cbd5e1;
            line-height: 1.5;
            padding-top: 4px;
        }}
        .footer {{
            margin-top: 32px;
            padding-top: 24px;
            border-top: 1px solid rgba(99, 102, 241, 0.15);
            font-size: 13px;
            color: #64748b;
        }}
        .footer a {{
            color: #818cf8;
            text-decoration: none;
        }}
        .session-id {{
            font-family: monospace;
            font-size: 11px;
            color: #475569;
            margin-top: 12px;
            word-break: break-all;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">
            <svg viewBox="0 0 24 24">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
        </div>

        <h1>Pagamento Confermato!</h1>
        <p class="subtitle">
            Grazie per aver scelto il <strong>Report Premium DigIdentity</strong>.<br>
            Il tuo report personalizzato è in fase di preparazione.
        </p>

        <div class="info-box">
            <h3>Cosa succede adesso?</h3>
            <div class="steps">
                <div class="step">
                    <div class="step-number">1</div>
                    <div class="step-text">
                        Il nostro sistema AI sta analizzando in profondità la tua presenza digitale.
                    </div>
                </div>
                <div class="step">
                    <div class="step-number">2</div>
                    <div class="step-text">
                        Stiamo generando un piano strategico personalizzato di 40-50 pagine.
                    </div>
                </div>
                <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-text">
                        <strong>Riceverai il report completo via email entro 24 ore.</strong>
                    </div>
                </div>
            </div>
        </div>

        <div class="info-box">
            <h3>Contenuto del Report Premium</h3>
            <p>
                Analisi SWOT digitale completa &bull; Piano strategico 90 giorni &bull;
                Calendario editoriale mensile &bull; Audit SEO avanzato &bull;
                Analisi competitor &bull; Preventivo dettagliato servizi
            </p>
        </div>

        <div class="footer">
            <p>Domande? Scrivici a <a href="mailto:{settings.SMTP_USER}">{settings.SMTP_USER}</a></p>
            <p class="session-id">Riferimento sessione: {session_id if session_id else "N/A"}</p>
        </div>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content, status_code=200)


# ===========================================================================
# GET /api/payment/cancel  (opzionale — pagina di annullamento)
# ===========================================================================
@router.get("/cancel", response_class=HTMLResponse)
async def payment_cancel():
    """Pagina mostrata se l'utente annulla il checkout Stripe."""
    html = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pagamento Annullato — DigIdentity Engine</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #e2e8f0;
        }
        .card {
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 24px;
            padding: 48px 40px;
            max-width: 480px;
            width: 90%;
            text-align: center;
        }
        h1 { color: #f87171; margin-bottom: 16px; }
        p { color: #94a3b8; line-height: 1.6; margin-bottom: 24px; }
        a {
            display: inline-block;
            padding: 12px 32px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            text-decoration: none;
            border-radius: 12px;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>Pagamento Annullato</h1>
        <p>
            Non è stato effettuato alcun addebito.<br>
            Se hai bisogno di assistenza, contattaci.
        </p>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=200)
