"""
DigIdentity Engine — Invio email transazionali.

Gestisce l'invio di:
1. Email report gratuito con CTA per upgrade a premium
2. Email report premium post-pagamento
"""

import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


def send_free_report_email(
    to_email: str,
    company_name: str,
    contact_name: str | None,
    pdf_path: str,
    checkout_url: str,
    html_url: str = "",
) -> bool:
    """
    Invia l'email con il report gratuito e la CTA per il report premium.
    Include link alla versione HTML interattiva se disponibile.
    """
    greeting = f"Ciao {contact_name}" if contact_name else "Ciao"
    logo_url = "https://digidentityagency.it/wp-content/uploads/2023/05/digidentity_agency_light_removebg.png"
    
    subject = f"La tua Diagnosi Digitale è pronta! — {company_name}"

    # Blocco HTML interattivo (solo se html_url è disponibile)
    html_interactive_block = ""
    if html_url:
        html_interactive_block = f"""
                                <div style="background-color: #0a0a0a; border: 2px solid #F90100; border-radius: 12px; padding: 25px; margin: 30px 0; text-align: center;">
                                    <p style="font-size: 12px; letter-spacing: 2px; margin: 0 0 10px; color: #F90100; font-weight: bold;">VERSIONE INTERATTIVA</p>
                                    <p style="font-size: 16px; font-weight: 700; margin: 0 0 8px; color: #ffffff;">Visualizza la diagnosi online</p>
                                    <p style="font-size: 13px; margin: 0 0 18px; color: #999999;">Dark theme, animazioni e navigazione per sezione</p>
                                    <a href="{html_url}" style="display: inline-block; background: #F90100; color: #ffffff; padding: 12px 30px; border-radius: 8px; font-weight: 700; font-size: 15px; text-decoration: none;">APRI LA DIAGNOSI INTERATTIVA</a>
                                </div>
"""

    html_body = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <style>
            .btn {{{{
                background-color: #F90100 !important;
                color: #ffffff !important;
                padding: 18px 35px !important;
                border-radius: 8px !important;
                text-decoration: none !important;
                font-weight: bold !important;
                display: inline-block !important;
            }}}}
        </style>
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333333;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0">
            <tr>
                <td align="center" style="padding: 20px 0;">
                    <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td align="center" style="background-color: #F90100; padding: 40px 20px;">
                                <img src="{logo_url}" width="220" alt="DigIdentity Agency" style="display: block;">
                            </td>
                        </tr>
                        
                        <!-- Body -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <h1 style="font-size: 24px; color: #000000; margin-top: 0;">{greeting}, la tua diagnosi è pronta!</h1>
                                <p style="font-size: 16px; line-height: 1.6; color: #444444;">
                                    Abbiamo completato l'analisi della presenza digitale di <strong>{company_name}</strong>. 
                                    In allegato trovi il report PDF con i risultati e i primi passi suggeriti.
                                </p>

                                {html_interactive_block}
                                
                                <div style="background-color: #fff5f5; border-left: 4px solid #F90100; padding: 20px; margin: 30px 0;">
                                    <p style="margin: 0; font-weight: bold; color: #F90100;">💡 Lo sapevi?</p>
                                    <p style="margin: 5px 0 0; font-size: 14px;">
                                        Questa diagnosi è stata generata in tempo reale dalla nostra Intelligenza Artificiale specifica per le piccole attività locali.
                                    </p>
                                </div>

                                <h2 style="font-size: 20px; color: #000000; margin-top: 40px;">🚀 Vuoi passare al livello successivo?</h2>
                                <p style="font-size: 16px; line-height: 1.6; color: #444444;">
                                    La <strong>Diagnosi Premium</strong> (40-50 pagine) include il piano d'azione completo, analisi dei competitor e la strategia specifica di automazione AI per la tua attività.
                                </p>
                                
                                <div align="center" style="margin-top: 35px;">
                                    <a href="https://buy.stripe.com/aFa3cx8da0eD6hM9rWdMI01" class="btn" style="color: #ffffff;">SCOPRI LA DIAGNOSI PREMIUM — 99&euro;</a>
                                </div>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #000000; color: #ffffff; padding: 30px; text-align: center;">
                                <p style="margin: 0; font-size: 14px; font-weight: bold;">DigIdentity Agency — Specialisti AI & Automazioni</p>
                                <p style="margin: 10px 0 0; font-size: 12px; color: #aaaaaa;">
                                    Via Dettori 3, Samatzai (SU), Sardegna<br>
                                    info@digidentityagency.it | www.digidentityagency.it
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    return _send_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        attachment_path=None,
        attachment_name=None,
    )


def send_premium_report_email(
    to_email: str,
    company_name: str,
    contact_name: str | None,
    pdf_path: str,
    consulenza_url: str = "",
    html_url: str = "",
) -> bool:
    """
    Invia l'email con il report premium post-pagamento.
    Include link alla versione HTML interattiva se disponibile.
    """
    greeting = f"Ciao {contact_name}" if contact_name else "Ciao"
    logo_url = "https://digidentityagency.it/wp-content/uploads/2023/05/digidentity_agency_light_removebg.png"
    
    subject = f"Il tuo Piano Strategico AI è pronto! — {company_name}"

    # Blocco HTML interattivo (solo se html_url è disponibile)
    html_interactive_block = ""
    if html_url:
        html_interactive_block = f"""
                                <div style="background-color: #0a0a0a; border: 2px solid #F90100; border-radius: 12px; padding: 25px; margin: 30px 0; text-align: center;">
                                    <p style="font-size: 12px; letter-spacing: 2px; margin: 0 0 10px; color: #F90100; font-weight: bold;">VERSIONE INTERATTIVA</p>
                                    <p style="font-size: 16px; font-weight: 700; margin: 0 0 8px; color: #ffffff;">Visualizza la diagnosi online</p>
                                    <p style="font-size: 13px; margin: 0 0 18px; color: #999999;">Animazioni, grafici interattivi e navigazione per sezione</p>
                                    <a href="{html_url}" style="display: inline-block; background: #F90100; color: #ffffff; padding: 12px 30px; border-radius: 8px; font-weight: 700; font-size: 15px; text-decoration: none;">APRI LA DIAGNOSI INTERATTIVA</a>
                                </div>
"""

    html_body = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333333;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0">
            <tr>
                <td align="center" style="padding: 20px 0;">
                    <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td align="center" style="background-color: #000000; padding: 40px 20px; border-bottom: 5px solid #F90100;">
                                <img src="{logo_url}" width="220" alt="DigIdentity Agency" style="display: block;">
                                <div style="color: #F90100; font-weight: bold; margin-top: 15px; font-size: 12px; letter-spacing: 2px;">REPORT PREMIUM</div>
                            </td>
                        </tr>
                        
                        <!-- Body -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <h1 style="font-size: 24px; color: #000000; margin-top: 0;">{greeting}, ecco la tua strategia!</h1>
                                <p style="font-size: 16px; line-height: 1.6; color: #444444;">
                                    Il <strong>Piano Strategico Digitale</strong> per <strong>{company_name}</strong> è finalmente pronto. 
                                    Trovi il documento allegato a questa email.
                                </p>
                                
                                <p style="font-size: 16px; line-height: 1.6; color: #444444;">
                                    All'interno troverai la roadmap dettagliata a 90 giorni, l'analisi della concorrenza 
                                    e le opportunità di integrazione AI specifiche per il tuo business.
                                </p>

                                {html_interactive_block}

                                <div style="background-color: #f0fff4; border-left: 4px solid #10B981; padding: 20px; margin: 30px 0;">
                                    <p style="margin: 0; font-weight: bold; color: #10B981;">📅 Cosa fare ora?</p>
                                    <p style="margin: 5px 0 0; font-size: 14px;">
                                        Leggi con attenzione il report e segna i punti che vorresti approfondire.
                                    </p>
                                </div>

                                <div style="background: linear-gradient(135deg, #1a0000, #8B0000); border-radius: 12px; padding: 30px; margin: 30px 0; text-align: center; color: white;">
                                    <p style="font-size: 12px; letter-spacing: 2px; margin: 0 0 10px; opacity: 0.8;">OFFERTA ESCLUSIVA</p>
                                    <p style="font-size: 22px; font-weight: 800; margin: 0 0 5px;">Consulenza Strategica 1-to-1</p>
                                    <p style="font-size: 14px; margin: 0 0 15px; opacity: 0.9;">45 minuti con Stefano per trasformare questa diagnosi in azioni concrete</p>
                                    <div style="font-size: 36px; font-weight: 800; color: #FFD700; margin: 15px 0;">&euro;199</div>
                                    <p style="font-size: 12px; margin: 0 0 20px; opacity: 0.7;">Se poi lavoriamo insieme, li scaliamo dal primo progetto</p>
                                    <a href="https://buy.stripe.com/3cI3cx3WUaTheOieMgdMI00" style="display: inline-block; background: #FFD700; color: #1a0000; padding: 14px 35px; border-radius: 8px; font-weight: 800; font-size: 16px; text-decoration: none;">PRENOTA LA CONSULENZA — &euro;199</a>
                                </div>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f9f9f9; padding: 30px; text-align: center; border-top: 1px solid #eeeeee;">
                                <p style="margin: 0; font-size: 14px; font-weight: bold; color: #000000;">DigIdentity Agency</p>
                                <p style="margin: 10px 0 0; font-size: 12px; color: #666666;">
                                    Hai domande? Rispondi direttamente a questa email.<br>
                                    tel: +39 392 199 0215
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    return _send_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        attachment_path=None,
        attachment_name=None,
    )


def _send_email(
    to_email: str,
    subject: str,
    html_body: str,
    attachment_path: str | None = None,
    attachment_name: str | None = None,
) -> bool:
    """Funzione interna per l'invio effettivo dell'email via SMTP."""
    try:
        msg = MIMEMultipart("mixed")
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        # Body HTML
        html_part = MIMEText(html_body, "html", "utf-8")
        msg.attach(html_part)

        # Allegato PDF
        if attachment_path and Path(attachment_path).exists():
            with open(attachment_path, "rb") as f:
                pdf_part = MIMEApplication(f.read(), _subtype="pdf")
                pdf_part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=attachment_name or "report.pdf",
                )
                msg.attach(pdf_part)

        # Invio SMTP
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"✅ Email inviata con successo a {to_email}: {subject}")
        return True

    except Exception as e:
        logger.error(f"❌ Errore invio email a {to_email}: {e}")
        return False


def send_geo_report_email(
    to_email: str,
    url_sito: str,
    pdf_path: str,
    piano: str,
    geo_score: int
) -> bool:
    """
    Invia l'email con il report GEO Audit allegato.
    Usa un template dark coerente con l'identità visiva AI.
    """
    logo_url = "https://digidentityagency.it/wp-content/uploads/2023/05/digidentity_agency_light_removebg.png"
    subject = f"Il tuo GEO Report per {url_sito} è pronto!"
    
    # Determina colore e testo in base allo score
    if geo_score >= 70:
        score_color = "#22c55e"
        score_label = "BUONO"
    elif geo_score >= 50:
        score_color = "#f59e0b"
        score_label = "DISCRETO"
    else:
        score_color = "#ef4444"
        score_label = "CRITICO"

    html_body = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <style>
            .container {{ background-color: #0f172a; color: #e2e8f0; font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; border-radius: 16px; overflow: hidden; }}
            .header {{ background-color: #0f172a; padding: 40px; text-align: center; border-bottom: 3px solid #0ea5e9; }}
            .content {{ padding: 40px; line-height: 1.6; }}
            .score-box {{ background-color: rgba(14, 165, 233, 0.1); border: 2px solid #0ea5e9; border-radius: 12px; padding: 30px; margin: 30px 0; text-align: center; }}
            .score-num {{ font-size: 64px; font-weight: 800; color: {score_color}; margin: 0; line-height: 1; }}
            .score-text {{ font-size: 14px; font-weight: 700; color: {score_color}; margin-top: 5px; }}
            .footer {{ background-color: #1e293b; padding: 30px; text-align: center; font-size: 12px; color: #94a3b8; }}
        </style>
    </head>
    <body style="margin: 0; padding: 20px; background-color: #f1f5f9;">
        <div class="container">
            <div class="header">
                <img src="{logo_url}" width="200" alt="DigIdentity Agency">
                <p style="margin: 15px 0 0; color: #0ea5e9; font-weight: 700; font-size: 12px; letter-spacing: 2px;">GEO AUDIT — AI OPTIMIZATION</p>
            </div>
            <div class="content">
                <h1 style="color: #ffffff; font-size: 24px; margin-top: 0;">L'analisi è completata!</h1>
                <p>Abbiamo analizzato la visibilità di <strong>{url_sito}</strong> nei principali Generative Engines (ChatGPT, Claude, Perplexity, Gemini).</p>
                
                <div class="score-box">
                    <p style="margin: 0 0 10px; font-size: 12px; letter-spacing: 1px;">GEO SCORE ATTUALE</p>
                    <p class="score-num">{geo_score}</p>
                    <p class="score-text">STATUS: {score_label}</p>
                </div>

                <p>In allegato trovi il report PDF completo con:</p>
                <ul style="color: #94a3b8; font-size: 14px;">
                    <li>Analisi della Citabilità AI dei tuoi testi</li>
                    <li>Verifica accessibilità per i Crawler AI</li>
                    <li>Audit dei Dati Strutturati per le Risposte Dirette</li>
                    <li>Piano di intervento prioritario</li>
                </ul>

                <div style="background-color: rgba(34, 197, 94, 0.1); border-left: 4px solid #22c55e; padding: 15px; margin-top: 30px; border-radius: 4px;">
                    <p style="margin: 0; font-size: 14px; color: #ffffff;">💡 <strong>Prossimo passo:</strong> Implementa i suggerimenti a pagina 3 del report per aumentare drasticamente le probabilità che la tua attività venga consigliata dalle AI.</p>
                </div>
            </div>
            <div class="footer">
                <p><strong>DigIdentity Agency — Specialisti AI & Automazioni</strong></p>
                <p>Via Dettori 3, Samatzai (SU), Sardegna | info@digidentityagency.it</p>
                <p style="margin-top: 15px; font-size: 10px;">Questa email è stata inviata automaticamente dal sistema DigIdentity Engine.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Nome file allegato
    target_domain = url_sito.replace("https://", "").replace("http://", "").split("/")[0]
    attachment_name = f"GEO-Report-{target_domain}.pdf"

    return _send_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        attachment_path=pdf_path,
        attachment_name=attachment_name
    )
