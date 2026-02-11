"""
DigIdentity Engine — Endpoint Stripe: checkout premium, checkout consulenza, webhook, success page.
"""
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import stripe
from backend.app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payment", tags=["payment"])
stripe.api_key = settings.STRIPE_SECRET_KEY

@router.post("/create-checkout")
async def create_checkout_session(request: Request):
    try:
        body = await request.json()
        lead_id = body.get("lead_id", "")
        email = body.get("email", "")
        if not lead_id or not email:
            raise HTTPException(status_code=400, detail="lead_id e email obbligatori.")
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            customer_email=email,
            line_items=[{"price": settings.STRIPE_PRICE_ID_PREMIUM, "quantity": 1}],
            metadata={"lead_id": lead_id, "type": "premium"},
            success_url=f"{settings.APP_BASE_URL}/api/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.APP_BASE_URL}/api/payment/cancel",
        )
        logger.info("Checkout premium creata: %s per lead %s", checkout_session.id, lead_id)
        return JSONResponse(content={"checkout_url": checkout_session.url, "session_id": checkout_session.id})
    except stripe.error.StripeError as e:
        logger.error("Errore Stripe: %s", str(e))
        raise HTTPException(status_code=502, detail=f"Errore Stripe: {str(e)}")

@router.post("/create-checkout-consulenza")
async def create_checkout_consulenza(request: Request):
    try:
        body = await request.json()
        lead_id = body.get("lead_id", "")
        email = body.get("email", "")
        if not lead_id or not email:
            raise HTTPException(status_code=400, detail="lead_id e email obbligatori.")
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            customer_email=email,
            line_items=[{"price": settings.STRIPE_PRICE_ID_CONSULENZA, "quantity": 1}],
            metadata={"lead_id": lead_id, "type": "consulenza"},
            success_url=f"{settings.APP_BASE_URL}/api/payment/success-consulenza?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.APP_BASE_URL}/api/payment/cancel",
        )
        logger.info("Checkout consulenza creata: %s per lead %s", checkout_session.id, lead_id)
        return JSONResponse(content={"checkout_url": checkout_session.url, "session_id": checkout_session.id})
    except stripe.error.StripeError as e:
        logger.error("Errore Stripe: %s", str(e))
        raise HTTPException(status_code=502, detail=f"Errore Stripe: {str(e)}")

@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Header stripe-signature mancante.")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(status_code=400, detail="Payload non valido.")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Firma non valida.")
    logger.info("Webhook: tipo=%s", event["type"])
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        lead_id = session.get("metadata", {}).get("lead_id")
        payment_type = session.get("metadata", {}).get("type", "premium")
        customer_email = session.get("customer_email", "")
        payment_intent = session.get("payment_intent", "")
        logger.info("Pagamento %s completato: lead=%s email=%s", payment_type, lead_id, customer_email)
        if not lead_id:
            return JSONResponse(content={"status": "error", "detail": "lead_id mancante"})
        try:
            from backend.app.core.supabase_client import get_supabase
            supabase = get_supabase()
            supabase.table("leads").update({
                "status": "payment_completed" if payment_type == "premium" else "consulenza_paid",
                "stripe_session_id": session.get("id", ""),
                "stripe_payment_intent": payment_intent,
            }).eq("id", lead_id).execute()
        except Exception as e:
            logger.error("Errore Supabase: %s", str(e))
        if payment_type == "premium":
            try:
                from backend.app.tasks.premium_report_task import task_premium_report
                task_premium_report.delay(lead_id)
                logger.info("Task premium avviato per lead %s", lead_id)
            except Exception as e:
                logger.error("Errore task premium: %s", str(e))
        elif payment_type == "consulenza":
            logger.info("Consulenza pagata per lead %s - notifica da inviare", lead_id)
        return JSONResponse(content={"status": "success", "lead_id": lead_id, "type": payment_type})
    logger.info("Evento non gestito: %s", event["type"])
    return JSONResponse(content={"status": "ignored"})

@router.get("/success", response_class=HTMLResponse)
async def payment_success(session_id: str = ""):
    return HTMLResponse(content=f"""<!DOCTYPE html>
<html lang="it"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Pagamento Confermato</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0f172a,#1e293b);min-height:100vh;display:flex;align-items:center;justify-content:center;color:#e2e8f0}}.card{{background:rgba(30,41,59,.8);border:1px solid rgba(99,102,241,.3);border-radius:24px;padding:48px 40px;max-width:560px;width:90%;text-align:center}}h1{{font-size:28px;color:#4ade80;margin-bottom:16px}}p{{color:#94a3b8;line-height:1.6;margin-bottom:16px}}.box{{background:rgba(99,102,241,.1);border:1px solid rgba(99,102,241,.2);border-radius:16px;padding:24px;margin:24px 0}}</style></head>
<body><div class="card"><h1>Pagamento Confermato!</h1>
<p>Grazie per aver scelto il <strong>Report Premium DigIdentity</strong>.</p>
<div class="box"><p><strong>Cosa succede adesso?</strong></p>
<p>1. Il nostro AI sta analizzando la tua presenza digitale<br>
2. Stiamo generando il piano strategico (40-50 pagine)<br>
3. <strong>Riceverai il report via email entro 24 ore</strong></p></div>
<p style="font-size:13px;color:#64748b">Ref: {session_id}</p></div></body></html>""")

@router.get("/success-consulenza", response_class=HTMLResponse)
async def payment_success_consulenza(session_id: str = ""):
    return HTMLResponse(content=f"""<!DOCTYPE html>
<html lang="it"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Consulenza Prenotata</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0f172a,#1e293b);min-height:100vh;display:flex;align-items:center;justify-content:center;color:#e2e8f0}}.card{{background:rgba(30,41,59,.8);border:1px solid rgba(99,102,241,.3);border-radius:24px;padding:48px 40px;max-width:560px;width:90%;text-align:center}}h1{{font-size:28px;color:#4ade80;margin-bottom:16px}}p{{color:#94a3b8;line-height:1.6;margin-bottom:16px}}.box{{background:rgba(99,102,241,.1);border:1px solid rgba(99,102,241,.2);border-radius:16px;padding:24px;margin:24px 0}}</style></head>
<body><div class="card"><h1>Consulenza Prenotata!</h1>
<p>Grazie! La tua <strong>Consulenza Strategica Digitale</strong> e' confermata.</p>
<div class="box"><p><strong>Prossimi passi:</strong></p>
<p>1. Riceverai un'email con il link per fissare la videochiamata<br>
2. Un esperto DigIdentity analizzerà il tuo Report Premium<br>
3. <strong>45 minuti dedicati alla tua strategia digitale</strong></p></div>
<p style="font-size:13px;color:#64748b">Ref: {session_id}</p></div></body></html>""")

@router.get("/cancel", response_class=HTMLResponse)
async def payment_cancel():
    return HTMLResponse(content="""<!DOCTYPE html>
<html lang="it"><head><meta charset="UTF-8"><title>Annullato</title>
<style>body{font-family:'Segoe UI',sans-serif;background:#0f172a;min-height:100vh;display:flex;align-items:center;justify-content:center;color:#e2e8f0}.card{background:rgba(30,41,59,.8);border:1px solid rgba(239,68,68,.3);border-radius:24px;padding:48px;max-width:480px;text-align:center}h1{color:#f87171;margin-bottom:16px}p{color:#94a3b8}</style></head>
<body><div class="card"><h1>Pagamento Annullato</h1><p>Non e' stato effettuato alcun addebito.</p></div></body></html>""")
