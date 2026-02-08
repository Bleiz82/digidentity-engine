"""
DigIdentity Engine — Email Sender
Invio email con Gmail SMTP (primario) e Resend (fallback).
Versione 3.0 — Funnel corretto: Free → Premium 99€ → Consulenza 199€ → Contratto
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Dict, Any, Optional
from app.config import get_settings


async def send_email_free_report(
    to_email: str,
    to_name: str,
    nome_azienda: str,
    pdf_path: str,
    lead_id: str = ""
) -> Dict[str, Any]:
    """
    Invia email con report gratuito allegato + CTA per upgrade premium.
    """
    settings = get_settings()

    print(f"📧 Invio email report gratuito a: {to_email}")

    subject = f"La tua Diagnosi Digitale è pronta, {to_name}!"

    html_body = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Inter', Arial, sans-serif;
            color: #1a1a1a;
            line-height: 1.6;
            max-width: 600px;
            margin: 0 auto;
            padding: 0;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #F90100 0%, #000000 100%);
            color: white;
            padding: 35px 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 22px;
            font-weight: 800;
        }}
        .header p {{
            margin: 8px 0 0 0;
            font-size: 15px;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
            background: #ffffff;
        }}
        .content p {{
            margin-bottom: 14px;
            font-size: 15px;
        }}
        .content ul {{
            margin: 10px 0 20px 20px;
        }}
        .content li {{
            margin-bottom: 8px;
            font-size: 14px;
        }}
        .highlight-box {{
            background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%);
            border-left: 4px solid #F90100;
            padding: 18px 20px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }}
        .cta-section {{
            background: #fafafa;
            padding: 25px 30px;
            text-align: center;
            border-top: 1px solid #eee;
            border-bottom: 1px solid #eee;
        }}
        .cta-section h2 {{
            color: #F90100;
            font-size: 20px;
            margin: 0 0 10px 0;
        }}
        .cta-button {{
            display: inline-block;
            background: #F90100;
            color: white !important;
            padding: 16px 40px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 700;
            font-size: 16px;
            margin: 15px 0;
        }}
        .price-badge {{
            display: inline-block;
            background: #000;
            color: white;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        .premium-list {{
            text-align: left;
            max-width: 400px;
            margin: 15px auto;
        }}
        .premium-list li {{
            margin-bottom: 6px;
            font-size: 13px;
        }}
        .footer {{
            background: #1a1a1a;
            color: #999;
            padding: 25px 30px;
            text-align: center;
            font-size: 12px;
        }}
        .footer a {{
            color: #F90100;
            text-decoration: none;
        }}
        .footer p {{
            margin: 5px 0;
        }}
        strong {{ color: #F90100; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Diagnosi Strategica Digitale</h1>
        <p>{nome_azienda}</p>
    </div>

    <div class="content">
        <p>Ciao <strong>{to_name}</strong>,</p>

        <p>abbiamo completato l'analisi della presenza digitale di <strong>{nome_azienda}</strong>.</p>

        <div class="highlight-box">
            <strong>📄 In allegato trovi il tuo report (8-10 pagine)</strong> con la fotografia completa
            della tua situazione online: sito web, Google, social, concorrenza e le azioni
            concrete da fare subito.
        </div>

        <p>Ti consiglio di leggerlo con calma — ci sono informazioni che probabilmente
        nessuno ti ha mai mostrato sulla tua attività online.</p>

        <p>Una cosa importante: questo report è una <strong>fotografia</strong>. Ti mostra dove sei.
        Ma per sapere esattamente <strong>dove puoi arrivare</strong> e <strong>come arrivarci</strong>,
        serve andare più in profondità.</p>
    </div>

    <div class="cta-section">
        <h2>Vuoi la strategia completa?</h2>
        <div class="price-badge">Solo 99€ invece di 500-1.000€</div>
        <p style="font-size: 14px; color: #666; margin-bottom: 15px;">
            La Diagnosi Premium è un vero piano strategico su misura per {nome_azienda}
        </p>

        <ul class="premium-list">
            <li>📊 <strong>40-50 pagine</strong> di analisi approfondita</li>
            <li>🔍 Audit completo sito, SEO, social, competitor</li>
            <li>🤖 Opportunità AI & automazioni per il tuo settore</li>
            <li>📅 Piano operativo 90 giorni, settimana per settimana</li>
            <li>💰 Budget dettagliato e ROI atteso</li>
            <li>🤝 Proposta di collaborazione personalizzata</li>
        </ul>

        <a href="{settings.app_base_url}/api/payment/upgrade/{lead_id}" class="cta-button">
            Sblocca la Diagnosi Premium — 99€
        </a>

        <p style="font-size: 12px; color: #999; margin-top: 10px;">
            Pagamento sicuro con Stripe. Ricevi il report via email entro 30 minuti.
        </p>
    </div>

    <div class="content" style="padding-top: 20px;">
        <p>Hai domande sul report? Rispondi a questa email o chiamami direttamente.</p>

        <p>A presto,<br>
        <strong>Stefano Corda</strong><br>
        <span style="color: #666; font-size: 13px;">Fondatore, DigIdentity Agency</span><br>
        <span style="color: #666; font-size: 13px;">Specialista AI & Automazioni per MPMI</span></p>
    </div>

    <div class="footer">
        <p><strong style="color: #F90100;">DigIdentity Agency</strong></p>
        <p>📧 info@digidentityagency.it | 📱 +39 392 199 0215</p>
        <p>🌐 <a href="https://digidentityagency.it">digidentityagency.it</a></p>
        <p style="margin-top: 12px; font-size: 10px; color: #666;">
            Hai ricevuto questa email perché hai richiesto una Diagnosi Strategica Digitale
            su digidentityagency.it. Se non sei stato tu, puoi ignorare questo messaggio.
        </p>
    </div>
</body>
</html>
"""

    try:
        msg = MIMEMultipart('mixed')
        msg['From'] = f"{settings.sender_name} <{settings.sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with open(pdf_path, 'rb') as f:
            pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
            pdf_attachment.add_header(
                'Content-Disposition', 'attachment',
                filename='Diagnosi_Strategica_Digitale.pdf'
            )
            msg.attach(pdf_attachment)

        print(f"   Connessione a Gmail SMTP...")
        with smtplib.SMTP(settings.gmail_smtp_host, settings.gmail_smtp_port) as server:
            server.starttls()
            server.login(settings.gmail_smtp_user, settings.gmail_smtp_password)
            server.send_message(msg)

        print(f"✅ Email inviata con successo via Gmail SMTP")
        return {"success": True, "provider": "gmail_smtp", "to": to_email}

    except Exception as e:
        error_msg = f"Errore invio email: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}


async def send_email_premium_report(
    to_email: str,
    to_name: str,
    nome_azienda: str,
    pdf_path: str
) -> Dict[str, Any]:
    """
    Invia email con report premium allegato + CTA per consulenza 199€.
    """
    settings = get_settings()

    print(f"📧 Invio email report PREMIUM a: {to_email}")

    subject = f"Il tuo Piano Strategico Digitale è pronto, {to_name}!"

    html_body = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Inter', Arial, sans-serif;
            color: #1a1a1a;
            line-height: 1.6;
            max-width: 600px;
            margin: 0 auto;
            padding: 0;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(160deg, #000000 0%, #1a0000 40%, #F90100 100%);
            color: white;
            padding: 35px 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 22px;
            font-weight: 800;
        }}
        .header p {{
            margin: 8px 0 0 0;
            font-size: 15px;
            opacity: 0.9;
        }}
        .premium-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.15);
            border: 2px solid rgba(255,255,255,0.4);
            color: white;
            padding: 5px 18px;
            border-radius: 30px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 12px;
        }}
        .content {{
            padding: 30px;
            background: #ffffff;
        }}
        .content p {{
            margin-bottom: 14px;
            font-size: 15px;
        }}
        .highlight-box {{
            background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%);
            border-left: 4px solid #F90100;
            padding: 18px 20px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }}
        .sections-grid {{
            margin: 20px 0;
        }}
        .sections-grid table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .sections-grid td {{
            padding: 8px 12px;
            font-size: 13px;
            border-bottom: 1px solid #f0f0f0;
            vertical-align: top;
        }}
        .sections-grid .icon {{
            width: 30px;
            text-align: center;
        }}
        .cta-section {{
            background: linear-gradient(135deg, #000 0%, #1a0000 100%);
            padding: 30px;
            text-align: center;
            color: white;
        }}
        .cta-section h2 {{
            color: #F90100;
            font-size: 20px;
            margin: 0 0 8px 0;
        }}
        .cta-section p {{
            color: rgba(255,255,255,0.85);
            font-size: 14px;
            margin: 8px 0;
        }}
        .cta-button {{
            display: inline-block;
            background: #F90100;
            color: white !important;
            padding: 16px 40px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 700;
            font-size: 16px;
            margin: 18px 0 8px 0;
        }}
        .price-big {{
            font-size: 32px;
            font-weight: 900;
            color: #F90100;
            margin: 10px 0;
        }}
        .guarantee {{
            background: #f0fdf4;
            border: 1px solid #86efac;
            border-radius: 8px;
            padding: 15px 20px;
            margin: 20px 0;
            font-size: 13px;
            color: #166534;
        }}
        .footer {{
            background: #1a1a1a;
            color: #999;
            padding: 25px 30px;
            text-align: center;
            font-size: 12px;
        }}
        .footer a {{
            color: #F90100;
            text-decoration: none;
        }}
        strong {{ color: #F90100; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="premium-badge">★ Premium</div>
        <h1>Diagnosi Strategica Digitale</h1>
        <p>{nome_azienda}</p>
        <p style="font-size: 12px; opacity: 0.7; margin-top: 5px;">
            Report completo — 40-50 pagine di strategia su misura
        </p>
    </div>

    <div class="content">
        <p>Ciao <strong>{to_name}</strong>,</p>

        <p>grazie per aver scelto la <strong>Diagnosi Premium</strong>. Hai fatto una scelta
        intelligente — ora hai in mano un vero piano strategico per far crescere
        {nome_azienda} online.</p>

        <div class="highlight-box">
            <strong>📄 In allegato trovi il report completo</strong> con 11 sezioni di analisi
            approfondita, piano operativo 90 giorni, opportunità AI & automazioni,
            e proposta di collaborazione personalizzata.
        </div>

        <p><strong>Come leggerlo:</strong> prenditi 30-40 minuti di tranquillità.
        Leggi prima l'Executive Summary per il quadro generale, poi approfondisci
        le sezioni che ti interessano di più. L'ultima sezione contiene la proposta
        di collaborazione.</p>

        <div class="sections-grid">
            <table>
                <tr><td class="icon">📊</td><td><strong>Sez. 1</strong> — Executive Summary</td></tr>
                <tr><td class="icon">🌐</td><td><strong>Sez. 2</strong> — Identità Digitale</td></tr>
                <tr><td class="icon">💻</td><td><strong>Sez. 3</strong> — Audit Sito Web</td></tr>
                <tr><td class="icon">🔍</td><td><strong>Sez. 4</strong> — SEO & Posizionamento</td></tr>
                <tr><td class="icon">📍</td><td><strong>Sez. 5</strong> — Google My Business</td></tr>
                <tr><td class="icon">📱</td><td><strong>Sez. 6</strong> — Social Media</td></tr>
                <tr><td class="icon">⚔️</td><td><strong>Sez. 7</strong> — Analisi Concorrenza</td></tr>
                <tr><td class="icon">🤖</td><td><strong>Sez. 8</strong> — AI & Automazioni</td></tr>
                <tr><td class="icon">📅</td><td><strong>Sez. 9</strong> — Piano 90 Giorni</td></tr>
                <tr><td class="icon">💰</td><td><strong>Sez. 10</strong> — Costo dell'Inazione</td></tr>
                <tr><td class="icon">🤝</td><td><strong>Sez. 11</strong> — Proposta Collaborazione</td></tr>
            </table>
        </div>
    </div>

    <div class="cta-section">
        <h2>Il Prossimo Passo</h2>
        <p>Hai il report. Hai i dati. Hai la strategia.<br>
        Ora serve <strong style="color: white;">parlarne insieme</strong> per trasformare tutto in azione.</p>

        <div class="price-big">199€</div>
        <p style="font-size: 13px; margin-top: 0;">Consulenza Strategica — 45 minuti con Stefano Corda</p>

        <p style="font-size: 13px; text-align: left; max-width: 380px; margin: 15px auto;">
            ✅ Revisione del report insieme, priorità per priorità<br>
            ✅ Roadmap personalizzata per la tua situazione<br>
            ✅ Preventivo dettagliato per ogni intervento<br>
            ✅ Risposte a tutte le tue domande<br>
            ✅ Piano concreto: cosa fare, in che ordine, con che budget
        </p>

        <a href="https://digidentityagency.it/consulenza-strategica/" class="cta-button">
            Prenota la Consulenza Strategica
        </a>

        <p style="font-size: 11px; opacity: 0.6; margin-top: 8px;">
            Pagamento sicuro. Appuntamento entro 48 ore.
        </p>
    </div>

    <div class="content" style="padding-top: 20px;">
        <div class="guarantee">
            <strong style="color: #166534;">🛡️ Garanzia soddisfazione:</strong> se dopo la consulenza
            senti di non aver ricevuto valore, ti restituiamo i 199€. Zero rischi.
        </div>

        <p>Hai domande sul report? Rispondi a questa email o chiamami direttamente
        al <strong>+39 392 199 0215</strong>.</p>

        <p>A presto,<br>
        <strong>Stefano Corda</strong><br>
        <span style="color: #666; font-size: 13px;">Fondatore, DigIdentity Agency</span><br>
        <span style="color: #666; font-size: 13px;">Specialista AI & Automazioni per MPMI</span></p>
    </div>

    <div class="footer">
        <p><strong style="color: #F90100;">DigIdentity Agency</strong></p>
        <p>📧 info@digidentityagency.it | 📱 +39 392 199 0215</p>
        <p>🌐 <a href="https://digidentityagency.it">digidentityagency.it</a></p>
        <p style="margin-top: 12px; font-size: 10px; color: #666;">
            Hai ricevuto questa email perché hai acquistato la Diagnosi Premium
            su digidentityagency.it.
        </p>
    </div>
</body>
</html>
"""

    try:
        msg = MIMEMultipart('mixed')
        msg['From'] = f"{settings.sender_name} <{settings.sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with open(pdf_path, 'rb') as f:
            pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
            pdf_attachment.add_header(
                'Content-Disposition', 'attachment',
                filename='Diagnosi_Strategica_Digitale_PREMIUM.pdf'
            )
            msg.attach(pdf_attachment)

        print(f"   Connessione a Gmail SMTP...")
        with smtplib.SMTP(settings.gmail_smtp_host, settings.gmail_smtp_port) as server:
            server.starttls()
            server.login(settings.gmail_smtp_user, settings.gmail_smtp_password)
            server.send_message(msg)

        print(f"✅ Email PREMIUM inviata con successo via Gmail SMTP")
        return {"success": True, "provider": "gmail_smtp", "to": to_email}

    except Exception as e:
        error_msg = f"Errore invio email premium: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}
