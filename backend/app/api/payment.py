"""
DigIdentity Engine — Payment API
Stripe integration per pagamento diagnosi premium (99€).
"""

import stripe
from fastapi import APIRouter, HTTPException, Request, Header
from typing import Optional
from datetime import datetime
from app.config import get_settings
from app.db import get_supabase_client
from app.tasks.premium_report_task import task_premium_report

router = APIRouter()
settings = get_settings()

# Configura Stripe
stripe.api_key = settings.stripe_secret_key


@router.post("/api/payment/create-checkout-session")
async def create_checkout_session(request: Request):
    """
    Crea Stripe Checkout Session per pagamento diagnosi premium.
    
    Body:
        {
            "lead_id": "uuid-del-lead"
        }
    
    Returns:
        {
            "checkout_url": "https://checkout.stripe.com/...",
            "session_id": "cs_..."
        }
    """
    try:
        body = await request.json()
        lead_id = body.get("lead_id")
        
        if not lead_id:
            raise HTTPException(status_code=400, detail="lead_id richiesto")
        
        print(f"💳 Creazione Stripe Checkout Session per lead: {lead_id}")
        
        # Verifica che il lead esista
        supabase = get_supabase_client()
        response = supabase.table("leads").select("*").eq("id", lead_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Lead non trovato")
        
        lead = response.data[0]
        
        # Crea Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": settings.stripe_price_id_premium,
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{settings.app_base_url}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.app_base_url}/cancel?lead_id={lead_id}",
            customer_email=lead["email"],
            metadata={
                "lead_id": lead_id,
                "nome_azienda": lead["nome_azienda"],
                "product": "diagnosi_premium"
            },
            locale="it"
        )
        
        # Salva payment record in DB
        payment_data = {
            "lead_id": lead_id,
            "stripe_session_id": checkout_session.id,
            "amount": 99.00,
            "currency": "EUR",
            "status": "pending"
        }
        
        supabase.table("payments").insert(payment_data).execute()
        
        # Aggiorna status lead
        supabase.table("leads").update({
            "status": "payment_pending"
        }).eq("id", lead_id).execute()
        
        print(f"✅ Checkout Session creata: {checkout_session.id}")
        print(f"   URL: {checkout_session.url}")
        
        return {
            "success": True,
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }
    
    except stripe.error.StripeError as e:
        error_msg = f"Errore Stripe: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
    
    except Exception as e:
        error_msg = f"Errore generico: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/api/payment/upgrade/{lead_id}")
async def upgrade_to_premium(lead_id: str):
    """
    Endpoint GET per upgrade a premium.
    Crea Stripe Checkout Session e fa redirect diretto.
    Usato come link CTA nelle email.
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table("leads").select("*").eq("id", lead_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Lead non trovato")
        
        lead = response.data[0]
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": settings.stripe_price_id_premium,
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{settings.app_base_url}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.app_base_url}/cancel?lead_id={lead_id}",
            customer_email=lead["email"],
            metadata={
                "lead_id": lead_id,
                "nome_azienda": lead["nome_azienda"],
                "product": "diagnosi_premium"
            },
            locale="it"
        )
        
        # Salva payment record
        payment_data = {
            "lead_id": lead_id,
            "stripe_session_id": checkout_session.id,
            "amount": 99.00,
            "currency": "EUR",
            "status": "pending"
        }
        supabase.table("payments").insert(payment_data).execute()
        
        supabase.table("leads").update({
            "status": "payment_pending"
        }).eq("id", lead_id).execute()
        
        # Redirect diretto a Stripe Checkout
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=checkout_session.url, status_code=303)
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=f"Errore Stripe: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore: {str(e)}")


@router.post("/api/payment/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None)
):
    """
    Webhook Stripe per gestire eventi di pagamento.
    
    Eventi gestiti:
    - checkout.session.completed: Pagamento completato
    - payment_intent.succeeded: Pagamento confermato
    - payment_intent.payment_failed: Pagamento fallito
    """
    try:
        payload = await request.body()
        
        # Verifica firma webhook
        try:
            event = stripe.Webhook.construct_event(
                payload,
                stripe_signature,
                settings.stripe_webhook_secret
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        print(f"📨 Webhook Stripe ricevuto: {event['type']}")
        
        # Gestisci evento
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            await handle_checkout_completed(session)
        
        elif event["type"] == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]
            print(f"✅ Payment Intent succeeded: {payment_intent['id']}")
        
        elif event["type"] == "payment_intent.payment_failed":
            payment_intent = event["data"]["object"]
            await handle_payment_failed(payment_intent)
        
        return {"success": True}
    
    except Exception as e:
        error_msg = f"Errore webhook: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


async def handle_checkout_completed(session: dict):
    """
    Gestisce checkout completato con successo.
    
    Actions:
    1. Aggiorna payment record in DB
    2. Aggiorna status lead a "payment_confirmed"
    3. Triggera task Celery per pipeline premium
    """
    session_id = session["id"]
    lead_id = session["metadata"]["lead_id"]
    payment_intent_id = session.get("payment_intent")
    
    print(f"💰 Checkout completato per lead: {lead_id}")
    print(f"   Session ID: {session_id}")
    print(f"   Payment Intent: {payment_intent_id}")
    
    supabase = get_supabase_client()
    
    # Aggiorna payment record
    supabase.table("payments").update({
        "stripe_payment_intent": payment_intent_id,
        "status": "completed",
        "completed_at": datetime.now().isoformat()
    }).eq("stripe_session_id", session_id).execute()
    
    # Aggiorna lead status
    supabase.table("leads").update({
        "status": "payment_confirmed"
    }).eq("id", lead_id).execute()
    
    print(f"✅ Payment record aggiornato")
    
    # Triggera pipeline premium
    print(f"⚡ Triggering premium pipeline...")
    task = task_premium_report.delay(lead_id)
    
    print(f"   Task ID: {task.id}")
    print(f"✅ Premium pipeline avviata!")


async def handle_payment_failed(payment_intent: dict):
    """
    Gestisce pagamento fallito.
    """
    payment_intent_id = payment_intent["id"]
    
    print(f"❌ Pagamento fallito: {payment_intent_id}")
    
    supabase = get_supabase_client()
    
    # Aggiorna payment record
    supabase.table("payments").update({
        "status": "failed"
    }).eq("stripe_payment_intent", payment_intent_id).execute()
    
    # TODO: Invia email di notifica pagamento fallito
    
    print(f"   Payment record aggiornato a 'failed'")
