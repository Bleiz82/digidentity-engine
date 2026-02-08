# DIRETTIVA: Generazione PDF e Invio Report

## Versione
v1.0 — Febbraio 2026

## Obiettivo
Generare PDF brandizzati DigIdentity e inviarli via Email e WhatsApp al lead.

## Generazione PDF

### Strumento
WeasyPrint (Python) — converte HTML+CSS in PDF

### Template Base
- Colori: Rosso #F90100, Nero #000000, Bianco #FFFFFF, Grigio #444444
- Logo header: https://digidentityagency.it/wp-content/uploads/2023/05/digidentity_agency_dark_removebg.png
- Logo copertina (sfondo scuro): https://digidentityagency.it/wp-content/uploads/2023/05/digidentity_agency_light_removebg.png
- Font: Inter (body), Poppins (titoli)
- Layout: A4 verticale, margini 2cm

### Report Gratuito (5 pagine)
- Copertina con nome azienda, data, score totale
- 4 pagine di contenuto
- Ultima pagina: CTA Diagnosi Premium
- Footer: "Generato da DigIdentity Agency — digidentityagency.it"

### Report Premium (40-50 pagine)
- Copertina premium con nome azienda, data, logo grande
- Indice interattivo (link interni)
- Header con logo + numero pagina
- Grafici: radar chart (scores), bar chart (confronto competitor), trend line
- Sezioni con separatori visivi
- Pagina finale: preventivo + contatti + CTA

## Invio Email (SendGrid)

### Template Email Gratuita
- Subject: "La tua Diagnosi Digitale Gratuita è pronta — {nome_azienda}"
- From: diagnosi@digidentityagency.it
- Corpo: saluto personalizzato, breve riepilogo score, PDF allegato, CTA premium
- Tono: professionale ma amichevole, in italiano semplice

### Template Email Premium
- Subject: "Diagnosi Strategica Digitale Premium — {nome_azienda}"
- From: diagnosi@digidentityagency.it
- Corpo: ringraziamento per acquisto, riepilogo valore, PDF allegato, prossimi passi, contatto diretto Stefano
- Tono: premium, esclusivo, personalizzato

## Invio WhatsApp (Twilio)

### Messaggio Gratuito
Ciao {nome_contatto}! La tua Diagnosi Digitale Gratuita per {nome_azienda} è pronta. Scaricala qui: {link_download}. Se vuoi il report completo (40+ pagine), rispondi a questo messaggio o visita: {link_premium}. — Stefano, DigIdentity Agency

### Messaggio Premium
Ciao {nome_contatto}! La tua Diagnosi Premium per {nome_azienda} è pronta. 40+ pagine di analisi, strategia e piano d'azione. Scaricala qui: {link_download}. Quando vuoi parlarne, sono a disposizione. — Stefano, DigIdentity Agency

## File di Esecuzione
- execution/generate_pdf.py (report gratuito)
- execution/generate_premium_pdf.py (report premium)
- execution/send_email.py
- execution/send_whatsapp.py