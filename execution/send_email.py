"""
DigIdentity Engine — Email Sender
Invio email con Gmail SMTP (primario) e Resend (fallback).
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
    Invia email con report gratuito allegato.
    
    Args:
        to_email: Email destinatario
        to_name: Nome destinatario
        nome_azienda: Nome azienda
        pdf_path: Path del PDF da allegare
        
    Returns:
        dict: Success status + metadata
    """
    settings = get_settings()
    
    print(f"📧 Invio email report gratuito a: {to_email}")
    
    # Subject
    subject = f"🚀 La tua Diagnosi Strategica Digitale è pronta, {to_name}!"
    
    # HTML Body
    html_body = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Inter', Arial, sans-serif;
            color: #000000;
            line-height: 1.6;
            max-width: 600px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #F90100 0%, #000000 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .content {{
            padding: 30px;
            background: #ffffff;
        }}
        .cta-button {{
            display: inline-block;
            background: #F90100;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 700;
            margin: 20px 0;
        }}
        .footer {{
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666;
        }}
        h1 {{ margin: 0; font-size: 24px; }}
        h2 {{ color: #F90100; font-size: 20px; }}
        strong {{ color: #F90100; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 La tua Diagnosi Strategica Digitale</h1>
        <p style="margin: 10px 0 0 0; font-size: 16px;">{nome_azienda}</p>
    </div>
    
    <div class="content">
        <p>Ciao <strong>{to_name}</strong>,</p>
        
        <p>Abbiamo completato l'analisi della presenza digitale di <strong>{nome_azienda}</strong>!</p>
        
        <p>📄 <strong>In allegato trovi il tuo report completo (5 pagine)</strong> con:</p>
        <ul>
            <li>✅ Analisi del tuo sito web (performance, SEO, mobile)</li>
            <li>✅ Posizionamento su Google e Google My Business</li>
            <li>✅ Presenza social media</li>
            <li>✅ Confronto con i tuoi competitor locali</li>
            <li>✅ 5 azioni concrete da fare SUBITO (gratis!)</li>
        </ul>
        
        <h2>🎯 Vuoi andare oltre?</h2>
        <p>Questa è solo la <strong>diagnosi gratuita</strong>. Se vuoi una <strong>strategia completa su misura</strong> con:</p>
        <ul>
            <li>📊 Analisi approfondita (40-50 pagine)</li>
            <li>🤖 Piano AI & Automazioni personalizzato</li>
            <li>📅 Calendario editoriale 3 mesi</li>
            <li>💰 Budget dettagliato e ROI atteso</li>
            <li>🚀 Proposta di collaborazione dedicata</li>
        </ul>
        
        <p style="text-align: center;">
            <a href="{settings.app_base_url}/api/payment/upgrade/{lead_id}" class="cta-button">
                🔥 Sblocca la Diagnosi Premium (99€)
            </a>
        </p>
        
        <p>Hai domande? Rispondi a questa email o chiamami direttamente!</p>
        
        <p>A presto,<br>
        <strong>Stefano Corda</strong><br>
        Specialista AI & Automazioni per MPMI<br>
        DigIdentity Agency</p>
    </div>
    
    <div class="footer">
        <p><strong>DigIdentity Agency</strong><br>
        Via Dettori 3, 09020 Samatzai (SU), Sardegna</p>
        <p>📧 info@digidentityagency.it | 📱 +39 392 199 0215<br>
        🌐 <a href="https://digidentityagency.it">digidentityagency.it</a></p>
        <p style="font-size: 10px; margin-top: 15px;">
        Hai ricevuto questa email perché hai richiesto una Diagnosi Strategica Digitale su digidentityagency.it.
        </p>
    </div>
</body>
</html>
"""
    
    try:
        # Crea messaggio
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{settings.sender_name} <{settings.sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Aggiungi HTML body
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        # Aggiungi PDF allegato
        with open(pdf_path, 'rb') as f:
            pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
            pdf_attachment.add_header('Content-Disposition', 'attachment', filename='Diagnosi_Strategica_Digitale.pdf')
            msg.attach(pdf_attachment)
        
        # Invia con Gmail SMTP
        print(f"   Connessione a Gmail SMTP...")
        with smtplib.SMTP(settings.gmail_smtp_host, settings.gmail_smtp_port) as server:
            server.starttls()
            server.login(settings.gmail_smtp_user, settings.gmail_smtp_password)
            server.send_message(msg)
        
        print(f"✅ Email inviata con successo via Gmail SMTP")
        
        return {
            "success": True,
            "provider": "gmail_smtp",
            "to": to_email
        }
    
    except Exception as e:
        error_msg = f"Errore invio email: {str(e)}"
        print(f"❌ {error_msg}")
        
        # TODO: Fallback a Resend se Gmail fallisce
        
        return {
            "success": False,
            "error": error_msg
        }


async def send_email_premium_report(
    to_email: str,
    to_name: str,
    nome_azienda: str,
    pdf_path: str
) -> Dict[str, Any]:
    """
    Invia email con report premium allegato.

    Args:
        to_email: Email destinatario
        to_name: Nome destinatario
        nome_azienda: Nome azienda
        pdf_path: Path del PDF premium da allegare

    Returns:
        dict: Success status + metadata
    """
    settings = get_settings()

    print(f"📧 Invio email report PREMIUM a: {to_email}")

    subject = f"⭐ La tua Diagnosi Premium è pronta, {to_name}!"

    html_body = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Inter', Arial, sans-serif;
            color: #000000;
            line-height: 1.6;
            max-width: 600px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(160deg, #000000 0%, #1a0000 40%, #F90100 100%);
            color: white;
            padding: 35px;
            text-align: center;
        }}
        .premium-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.15);
            border: 2px solid rgba(255,255,255,0.4);
            color: white;
            padding: 6px 20px;
            border-radius: 30px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 15px;
        }}
        .content {{
            padding: 30px;
            background: #ffffff;
        }}
        .highlight-box {{
            background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%);
            border-left: 4px solid #F90100;
            padding: 20px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }}
        .cta-button {{
            display: inline-block;
            background: #F90100;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 700;
            margin: 20px 0;
        }}
        .footer {{
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666;
        }}
        h1 {{ margin: 0; font-size: 24px; }}
        h2 {{ color: #F90100; font-size: 20px; }}
        strong {{ color: #F90100; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="premium-badge">★ PREMIUM</div>
        <h1>La tua Diagnosi Strategica Digitale</h1>
        <p style="margin: 10px 0 0 0; font-size: 16px;">{nome_azienda}</p>
        <p style="margin: 5px 0 0 0; font-size: 13px; opacity: 0.8;">Report completo — 40-50 pagine di strategia</p>
    </div>

    <div class="content">
        <p>Ciao <strong>{to_name}</strong>,</p>

        <p>Grazie per aver scelto la <strong>Diagnosi Premium</strong>! Hai fatto una scelta intelligente:
        ora hai in mano una <strong>vera roadmap strategica</strong> per far crescere {nome_azienda} online.</p>

        <div class="highlight-box">
            <strong>📄 In allegato trovi il tuo report completo</strong> con 11 sezioni di analisi approfondita,
            piano operativo 90 giorni, budget dettagliato e proposta di collaborazione personalizzata.
        </div>

        <h2>📋 Cosa trovi nel report:</h2>
        <ul>
            <li>📊 <strong>Executive Summary</strong> — quadro generale e score digitale</li>
            <li>🌐 <strong>Analisi Sito Web</strong> — performance, UX, mobile, velocità</li>
            <li>🔍 <strong>Audit SEO Completo</strong> — keyword, posizionamento, opportunità</li>
            <li>📍 <strong>Google My Business</strong> — ottimizzazione scheda locale</li>
            <li>📱 <strong>Social Media Audit</strong> — presenza e strategia</li>
            <li>⚔️ <strong>Analisi Competitor</strong> — posizionamento vs concorrenza</li>
            <li>📝 <strong>Architettura Contenuti</strong> — strategia editoriale</li>
            <li>🤖 <strong>Opportunità AI & Automazioni</strong> — cosa automatizzare</li>
            <li>📅 <strong>Piano Strategico 90 Giorni</strong> — azioni concrete, settimana per settimana</li>
            <li>💰 <strong>Budget & ROI</strong> — investimento e ritorno atteso</li>
            <li>🤝 <strong>Proposta di Collaborazione</strong> — come possiamo aiutarti</li>
        </ul>

        <h2>🚀 Prossimi passi</h2>
        <p>Ti consiglio di leggere il report con calma e poi fissare una <strong>call gratuita di 30 minuti</strong>
        con me per discutere insieme la strategia e rispondere alle tue domande.</p>

        <p style="text-align: center;">
            <a href="https://digidentityagency.it/contatti-digidentity/" class="cta-button">
                📞 Prenota la Call Gratuita
            </a>
        </p>

        <p>Hai domande? Rispondi a questa email o chiamami direttamente al <strong>+39 392 199 0215</strong>.</p>

        <p>A presto,<br>
        <strong>Stefano Corda</strong><br>
        Specialista AI & Automazioni per MPMI<br>
        DigIdentity Agency</p>
    </div>

    <div class="footer">
        <p><strong>DigIdentity Agency</strong><br>
        Specialisti AI & Automazioni per Micro e Piccole Imprese</p>
        <p>📧 info@digidentityagency.it | 📱 +39 392 199 0215<br>
        🌐 <a href="https://digidentityagency.it">digidentityagency.it</a></p>
        <p style="font-size: 10px; margin-top: 15px;">
        Hai ricevuto questa email perché hai acquistato la Diagnosi Premium su digidentityagency.it.
        </p>
    </div>
</body>
</html>
"""

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{settings.sender_name} <{settings.sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        # Allega PDF premium
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

        return {
            "success": True,
            "provider": "gmail_smtp",
            "to": to_email
        }

    except Exception as e:
        error_msg = f"Errore invio email premium: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }

