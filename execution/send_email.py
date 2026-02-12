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
) -> bool:
    """
    Invia l'email con il report gratuito e la CTA per il report premium.
    """
    greeting = f"Ciao {contact_name}" if contact_name else "Ciao"
    logo_url = "https://digidentityagency.it/wp-content/uploads/2023/05/digidentity_agency_light_removebg.png"
    
    subject = f"La tua Diagnosi Digitale è pronta! — {company_name}"

    html_body = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <style>
            .btn {{
                background-color: #F90100 !important;
                color: #ffffff !important;
                padding: 18px 35px !important;
                border-radius: 8px !important;
                text-decoration: none !important;
                font-weight: bold !important;
                display: inline-block !important;
            }}
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
                                    <a href="{checkout_url}" class="btn" style="color: #ffffff;">SCOPRI LA DIAGNOSI PREMIUM — 99€</a>
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
        attachment_path=pdf_path,
        attachment_name=f"Diagnosi_Digitale_{company_name.replace(' ', '_')}.pdf",
    )


def send_premium_report_email(
    to_email: str,
    company_name: str,
    contact_name: str | None,
    pdf_path: str,
) -> bool:
    """
    Invia l'email con il report premium post-pagamento.
    """
    greeting = f"Ciao {contact_name}" if contact_name else "Ciao"
    logo_url = "https://digidentityagency.it/wp-content/uploads/2023/05/digidentity_agency_light_removebg.png"
    
    subject = f"Il tuo Piano Strategico AI è pronto! — {company_name}"

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

                                <div style="background-color: #f0fff4; border-left: 4px solid #10B981; padding: 20px; margin: 30px 0;">
                                    <p style="margin: 0; font-weight: bold; color: #10B981;">📅 Cosa fare ora?</p>
                                    <p style="margin: 5px 0 0; font-size: 14px;">
                                        Leggi con attenzione il report e segna i punti che vorresti approfondire. 
                                        Siamo pronti ad aiutarti nell'implementazione.
                                    </p>
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
        attachment_path=pdf_path,
        attachment_name=f"Piano_Strategico_{company_name.replace(' ', '_')}.pdf",
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
