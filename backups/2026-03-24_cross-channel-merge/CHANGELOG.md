# Cross-Channel Merge - 24 Marzo 2026

## File modificati:
1. **contact_service.py** - Aggiunto find_merge_candidate(), merge_contacts() con soft-delete, resolve_contact esteso (match per email, telefono, nome)
2. **ai_service.py** - handle_aggiorna_contatto con merge cross-canale + contact_id update post-merge, fix "slot" -> "slots" (riga 220), fix indirizzo Google Maps in email/calendar
3. **contatti/page.tsx** - Filtro .not('nome', 'like', '[MERGED]%') per nascondere contatti merged

## Bug risolti:
- Errore 'slot' (KeyError) → 'slots' nel dizionario DISPONIBILITA
- CASCADE delete su appointments durante merge → soft-delete
- lead_status check constraint → uso note + nome per marcatura merged
- company_name → nome_azienda nelle query lead

## Funzionalità aggiunte:
- Merge automatico cross-canale (email/telefono match)
- Resolve contact esteso (match per email, telefono, nome completo)
- Soft-delete contatti merged (no data loss)
- Filtro UI per nascondere [MERGED]
- Google Maps link in calendar per appuntamenti in presenza
- Indirizzo cliente in email conferma

## Contatto test unificato:
- ID: 20287525-9596-43b9-8ebe-8399d79d451f
- Canali: WhatsApp, Telegram, Instagram, Messenger, Email, Chatbot (7 conversazioni)
