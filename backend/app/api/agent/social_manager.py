"""
Social Manager API — Graph API routes per:
- pages_show_list: lista pagine utente
- pages_manage_metadata: lettura/modifica metadata pagina
- pages_read_engagement: post, commenti, reactions
- pages_messaging: invio messaggi (già in webhooks, qui endpoint manuale)
- pages_utility_messaging: template messaggi
- business_management: business assets
"""

import httpx
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from backend.app.core.config import settings
from backend.app.core.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/social", tags=["social-manager"])

GRAPH_API = "https://graph.facebook.com/v21.0"


# ────────────────────────────────────────────
# UTILS
# ────────────────────────────────────────────

def _token():
    """Restituisce il page access token."""
    t = settings.META_PAGE_ACCESS_TOKEN
    if not t:
        raise HTTPException(status_code=500, detail="META_PAGE_ACCESS_TOKEN non configurato")
    return t

def _ig_token():
    """Restituisce l'Instagram page access token."""
    t = settings.INSTAGRAM_PAGE_ACCESS_TOKEN or settings.META_PAGE_ACCESS_TOKEN
    if not t:
        raise HTTPException(status_code=500, detail="Token Instagram non configurato")
    return t

async def _graph_get(endpoint: str, params: dict = None, token: str = None) -> dict:
    """GET request alla Graph API."""
    params = params or {}
    params["access_token"] = token or _token()
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{GRAPH_API}/{endpoint}", params=params)
        if r.status_code != 200:
            logger.error(f"Graph API GET {endpoint}: {r.status_code} {r.text}")
            raise HTTPException(status_code=r.status_code, detail=r.json().get("error", {}).get("message", r.text))
        return r.json()

async def _graph_post(endpoint: str, data: dict = None, params: dict = None, token: str = None) -> dict:
    """POST request alla Graph API."""
    params = params or {}
    params["access_token"] = token or _token()
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(f"{GRAPH_API}/{endpoint}", params=params, json=data)
        if r.status_code not in (200, 201):
            logger.error(f"Graph API POST {endpoint}: {r.status_code} {r.text}")
            raise HTTPException(status_code=r.status_code, detail=r.json().get("error", {}).get("message", r.text))
        return r.json()

async def _graph_delete(endpoint: str, token: str = None) -> dict:
    """DELETE request alla Graph API."""
    params = {"access_token": token or _token()}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.delete(f"{GRAPH_API}/{endpoint}", params=params)
        if r.status_code != 200:
            logger.error(f"Graph API DELETE {endpoint}: {r.status_code} {r.text}")
            raise HTTPException(status_code=r.status_code, detail=r.json().get("error", {}).get("message", r.text))
        return r.json()


# ════════════════════════════════════════════
# PAGES_SHOW_LIST — Lista pagine
# ════════════════════════════════════════════

@router.get("/pages")
async def list_pages():
    """Restituisce le pagine Facebook collegate."""
    page_id = settings.META_PAGE_ID
    page = await _graph_get(page_id, {"fields": "id,name,category"})
    return {"pages": [page]}


# ════════════════════════════════════════════
# PAGES_MANAGE_METADATA — Metadata pagina
# ════════════════════════════════════════════

@router.get("/pages/{page_id}/metadata")
async def get_page_metadata(page_id: str):
    """Restituisce i metadata della pagina."""
    fields = "id,name,about,bio,category,category_list,description,emails,phone,website,single_line_address,hours,cover{source},picture{url},fan_count,followers_count,location"
    return await _graph_get(page_id, {"fields": fields})

@router.post("/pages/{page_id}/metadata")
async def update_page_metadata(page_id: str, data: dict):
    """Aggiorna i metadata della pagina (about, description, phone, website, ecc.)."""
    allowed = {"about", "bio", "description", "phone", "website", "emails", "single_line_address"}
    update_data = {k: v for k, v in data.items() if k in allowed}
    if not update_data:
        raise HTTPException(status_code=400, detail=f"Campi modificabili: {', '.join(allowed)}")
    return await _graph_post(page_id, data=update_data)


# ════════════════════════════════════════════
# PAGES_READ_ENGAGEMENT — Post e commenti
# ════════════════════════════════════════════

@router.get("/pages/{page_id}/posts")
async def get_page_posts(page_id: str, limit: int = Query(25, ge=1, le=100), after: str = None):
    """Restituisce i post della pagina con metriche."""
    fields = "id,message,created_time,full_picture,permalink_url,likes.summary(true),comments.summary(true),reactions.summary(true)"
    params = {"fields": fields, "limit": limit}
    if after:
        params["after"] = after
    result = await _graph_get(f"{page_id}/posts", params)
    posts = result.get("data", [])
    paging = result.get("paging", {})
    return {"posts": posts, "paging": paging}

@router.get("/posts/{post_id}/comments")
async def get_post_comments(post_id: str, limit: int = Query(50, ge=1, le=200), after: str = None):
    """Restituisce i commenti di un post."""
    fields = "id,message,from{id,name,picture},created_time,like_count,comment_count,attachment{media,url,type},parent"
    params = {"fields": fields, "limit": limit}
    if after:
        params["after"] = after
    result = await _graph_get(f"{post_id}/comments", params)
    return {"comments": result.get("data", []), "paging": result.get("paging", {})}

@router.post("/posts/{post_id}/comments")
async def reply_to_post(post_id: str, data: dict):
    """Pubblica un commento sotto un post o risponde a un commento."""
    message = data.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="Campo 'message' obbligatorio")
    return await _graph_post(f"{post_id}/comments", data={"message": message})

@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str):
    """Elimina un commento."""
    return await _graph_delete(comment_id)

@router.get("/posts/{post_id}/reactions")
async def get_post_reactions(post_id: str):
    """Restituisce le reactions di un post."""
    result = await _graph_get(f"{post_id}/reactions", {"summary": "true", "limit": 0})
    return {"total": result.get("summary", {}).get("total_count", 0)}


# ════════════════════════════════════════════
# PUBBLICAZIONE POST
# ════════════════════════════════════════════

@router.post("/pages/{page_id}/posts")
async def create_post(page_id: str, data: dict):
    """Crea un nuovo post sulla pagina."""
    message = data.get("message")
    link = data.get("link")
    if not message and not link:
        raise HTTPException(status_code=400, detail="Serve almeno 'message' o 'link'")
    post_data = {}
    if message:
        post_data["message"] = message
    if link:
        post_data["link"] = link
    return await _graph_post(f"{page_id}/feed", data=post_data)

@router.post("/pages/{page_id}/photos")
async def create_photo_post(page_id: str, data: dict):
    """Pubblica una foto con caption."""
    url = data.get("url")
    caption = data.get("caption", "")
    if not url:
        raise HTTPException(status_code=400, detail="Campo 'url' obbligatorio (URL immagine)")
    return await _graph_post(f"{page_id}/photos", data={"url": url, "caption": caption})

@router.delete("/posts/{post_id}")
async def delete_post(post_id: str):
    """Elimina un post."""
    return await _graph_delete(post_id)


# ════════════════════════════════════════════
# PAGES_UTILITY_MESSAGING — Template messaggi
# ════════════════════════════════════════════

@router.get("/templates")
async def list_templates():
    """Restituisce i template messaggi da Supabase."""
    supabase = get_supabase()
    result = supabase.table("message_templates").select("*").order("created_at", desc=True).execute()
    return {"templates": result.data}

@router.post("/templates")
async def create_template(data: dict):
    """Crea un nuovo template messaggio."""
    required = {"name", "channel", "content"}
    missing = required - set(data.keys())
    if missing:
        raise HTTPException(status_code=400, detail=f"Campi obbligatori mancanti: {', '.join(missing)}")
    supabase = get_supabase()
    template = {
        "name": data["name"],
        "channel": data["channel"],
        "category": data.get("category", "utility"),
        "content": data["content"],
        "placeholders": data.get("placeholders", []),
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    result = supabase.table("message_templates").insert(template).execute()
    return {"template": result.data[0] if result.data else template}

@router.put("/templates/{template_id}")
async def update_template(template_id: str, data: dict):
    """Aggiorna un template."""
    supabase = get_supabase()
    data["updated_at"] = datetime.utcnow().isoformat()
    result = supabase.table("message_templates").update(data).eq("id", template_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Template non trovato")
    return {"template": result.data[0]}

@router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    """Elimina un template."""
    supabase = get_supabase()
    supabase.table("message_templates").delete().eq("id", template_id).execute()
    return {"deleted": True}

@router.post("/templates/{template_id}/send")
async def send_template_message(template_id: str, data: dict):
    """Compila un template con i placeholder e invia il messaggio."""
    contact_id = data.get("contact_id")
    placeholders = data.get("placeholders", {})
    if not contact_id:
        raise HTTPException(status_code=400, detail="Campo 'contact_id' obbligatorio")
    
    supabase = get_supabase()
    
    # Recupera template
    tpl_result = supabase.table("message_templates").select("*").eq("id", template_id).limit(1).execute()
    if not tpl_result.data:
        raise HTTPException(status_code=404, detail="Template non trovato")
    template = tpl_result.data[0]
    
    # Recupera contatto
    contact_result = supabase.table("contacts").select("*").eq("id", contact_id).limit(1).execute()
    if not contact_result.data:
        raise HTTPException(status_code=404, detail="Contatto non trovato")
    contact = contact_result.data[0]
    
    # Compila il messaggio sostituendo i placeholder
    message = template["content"]
    auto_placeholders = {
        "nome": contact.get("name") or contact.get("user_name") or "",
        "email": contact.get("email") or "",
        "telefono": contact.get("phone") or "",
    }
    all_placeholders = {**auto_placeholders, **placeholders}
    for key, value in all_placeholders.items():
        message = message.replace("{{" + key + "}}", str(value))
    
    # Invia tramite il canale del template
    from backend.app.services.agent.channel_dispatcher import send_channel_response
    channel = template.get("channel", "whatsapp")
    
    # Trova o crea conversazione
    conv_result = supabase.table("conversations").select("*").eq("contact_id", contact_id).order("updated_at", desc=True).limit(1).execute()
    conversation = conv_result.data[0] if conv_result.data else None
    
    delivery = await send_channel_response(
        channel_type=channel,
        contact=contact,
        message=message,
        conversation=conversation,
    )
    
    # Salva in messages
    from backend.app.services.agent.message_service import save_message
    if conversation:
        await save_message(
            conversation_id=conversation["id"],
            contact_id=contact_id,
            direction="outbound",
            sender_type="operator",
            content=message,
            content_type="template",
            metadata={"template_id": template_id, "template_name": template["name"]},
        )
    
    return {"sent": True, "message": message, "delivery": delivery}


# ════════════════════════════════════════════
# BUSINESS_MANAGEMENT — Business assets
# ════════════════════════════════════════════

@router.get("/business")
async def get_business_info():
    """Restituisce info sul business collegato."""
    try:
        page_id = settings.META_PAGE_ID
        result = await _graph_get(page_id, {"fields": "id,name,category"})
        pages = {"data": [result]}
        
        ig_account = None
        if settings.INSTAGRAM_ACCOUNT_ID:
            try:
                ig_account = await _graph_get(
                    settings.INSTAGRAM_ACCOUNT_ID,
                    {"fields": "id,username,name,profile_picture_url,followers_count,media_count,biography"},
                    token=_ig_token()
                )
            except Exception:
                pass
        
        return {
            "user": result,
            "pages": pages.get("data", []),
            "instagram": ig_account,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════
# INSTAGRAM — Post e commenti
# ════════════════════════════════════════════

@router.get("/instagram/media")
async def get_instagram_media(limit: int = Query(25, ge=1, le=100), after: str = None):
    """Restituisce i media dell'account Instagram."""
    ig_id = settings.INSTAGRAM_ACCOUNT_ID
    if not ig_id:
        raise HTTPException(status_code=400, detail="INSTAGRAM_ACCOUNT_ID non configurato")
    fields = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,like_count,comments_count"
    params = {"fields": fields, "limit": limit}
    if after:
        params["after"] = after
    result = await _graph_get(f"{ig_id}/media", params, token=_ig_token())
    return {"media": result.get("data", []), "paging": result.get("paging", {})}

@router.get("/instagram/media/{media_id}/comments")
async def get_instagram_comments(media_id: str, limit: int = Query(50, ge=1, le=200)):
    """Restituisce i commenti di un media Instagram."""
    fields = "id,text,username,timestamp,like_count,replies{id,text,username,timestamp}"
    result = await _graph_get(f"{media_id}/comments", {"fields": fields, "limit": limit}, token=_ig_token())
    return {"comments": result.get("data", []), "paging": result.get("paging", {})}

@router.post("/instagram/media/{media_id}/comments")
async def reply_instagram_comment(media_id: str, data: dict):
    """Risponde a un commento Instagram."""
    message = data.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="Campo 'message' obbligatorio")
    return await _graph_post(f"{media_id}/replies", data={"message": message}, token=_ig_token())

@router.get("/instagram/insights")
async def get_instagram_insights():
    """Metriche base dell'account Instagram."""
    ig_id = settings.INSTAGRAM_ACCOUNT_ID
    if not ig_id:
        raise HTTPException(status_code=400, detail="INSTAGRAM_ACCOUNT_ID non configurato")
    try:
        result = await _graph_get(
            f"{ig_id}/insights",
            {"metric": "impressions,reach,profile_views", "period": "day"},
            token=_ig_token()
        )
        return {"insights": result.get("data", [])}
    except Exception as e:
        return {"insights": [], "error": str(e)}


# ════════════════════════════════════════════
# DASHBOARD STATS
# ════════════════════════════════════════════

@router.get("/stats")
async def social_stats():
    """Statistiche aggregate per la dashboard."""
    page_id = settings.META_PAGE_ID
    ig_id = settings.INSTAGRAM_ACCOUNT_ID
    stats = {"facebook": {}, "instagram": {}}
    
    try:
        fb = await _graph_get(page_id, {"fields": "id,name,category"})
        stats["facebook"] = fb
    except Exception:
        pass
    
    if ig_id:
        try:
            ig = await _graph_get(ig_id, {"fields": "followers_count,media_count"}, token=_ig_token())
            stats["instagram"] = ig
        except Exception:
            pass
    
    return stats
