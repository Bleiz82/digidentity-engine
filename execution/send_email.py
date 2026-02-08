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

    Args:
        to_email: Email del destinatario
        company_name: Nome azienda
        contact_name: Nome contatto (opzionale)
        pdf_path: Percorso del PDF del report free
        checkout_url: URL di Stripe Checkout per il pagamento premium

    Returns:
        True se l'invio è avvenuto con successo
    """
    greeting = f"Gentile {contact_name}" if contact_name else "Gentile utente"

    subject = f"La Diagnosi Digitale di {company_name} è pronta — DigIdentity"

    html_body = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="
        margin: 0; padding: 0;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        background-color: #f1f5f9;
        color: #1e293b;
    ">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">

            <!-- Header -->
            <div style="
                background: linear-gradient(135deg, #0f172a, #1e293b);
                border-radius: 16px 16px 0 0;
                padding: 32px;
                text-align: center;
            ">
                <h1 style="color: white; margin: 0; font-size: 24px;">
                    DigIdentity Engine
                </h1>
                <p style="color: #94a3b8; margin: 8px 0 0;">
                    Diagnosi della Presenza Digitale
                </p>
            </div>

            <!-- Body -->
            <div style="
                background: white;
                padding: 32px;
                border-left: 1px solid #e2e8f0;
                border-right: 1px solid #e2e8f0;
            ">
                <p style="font-size: 16px; line-height: 1.6;">
                    {greeting},
                </p>

                <p style="font-size: 16px; line-height: 1.6;">
                    la diagnosi digitale gratuita per <strong>{company_name}</strong>
                    è stata completata. In allegato trovi il report PDF con l'analisi
                    della tua presenza online.
                </p>

                <div style="
                    background: #f0fdf4;
                    border: 1px solid #bbf7d0;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 24px 0;
                ">
                    <h3 style="color: #166534; margin: 0 0 8px;">
                        &#128206; Report allegato
                    </h3>
                    <p style="color: #15803d; margin: 0; font-size: 14px;">
                        Il PDF contiene: analisi sito web, posizionamento SEO,
                        presenza social, e raccomandazioni prioritarie.
                    </p>
                </div>

                <!-- CTA Premium -->
                <div style="
                    background: linear-gradient(135deg, #eff6ff, #e0e7ff);
                    border: 2px solid #6366f1;
                    border-radius: 16px;
                    padding: 28px;
                    margin: 32px 0;
                    text-align: center;
                ">
                    <h2 style="color: #4338ca; margin: 0 0 12px; font-size: 20px;">
                        &#128640; Vuoi il Piano Strategico Completo?
                    </h2>
                    <p style="color: #475569; font-size: 15px; line-height: 1.6; margin-bottom: 20px;">
                        Il <strong>Report Premium</strong> (40-50 pagine) include:
                    </p>
                    <ul style="
                        text-align: left;
                        color: #334155;
                        font-size: 14px;
                        line-height: 2;
                        list-style: none;
                        padding: 0;
                    ">
                        <li>&#10003; Analisi approfondita di ogni canale digitale</li>
                        <li>&#10003; Piano strategico personalizzato a 6-12 mesi</li>
                        <li>&#10003; Calendario editoriale dettagliato per 3 mesi</li>
                        <li>&#10003; Analisi competitiva del tuo settore</li>
                        <li>&#10003; Preventivo dettagliato degli interventi</li>
                        <li>&#10003; Roadmap con KPI e milestone</li>
                    </ul>

                    <a href="{checkout_url}" style="
                        display: inline-block;
                        background: linear-gradient(135deg, #6366f1, #4f46e5);
                        color: white;
                        padding: 16px 40px;
                        border-radius: 12px;
                        text-decoration: none;
                        font-size: 18px;
                        font-weight: 700;
                        margin-top: 16px;
                        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
                    ">
                        Ottieni il Report Premium — 99&euro;
                    </a>

                    <p style="
                        color: #64748b;
                        font-size: 12px;
                        margin-top: 12px;
                    ">
                        Pagamento sicuro con Stripe. Consegna via email entro 24 ore.
                    </p>
                </div>
            </div>

            <!-- Footer -->
            <div style="
                background: #f8fafc;
                border-radius: 0 0 16px 16px;
                padding: 24px 32px;
                text-align: center;
                border: 1px solid #e2e8f0;
                border-top: none;
            ">
                <p style="color: #94a3b8; font-size: 12px; margin: 0;">
                    &copy; DigIdentity Engine — Sistema automatico di diagnosi digitale per PMI
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    return _send_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        attachment_path=pdf_path,
        attachment_name=f"DigIdentity_Diagnosi_{company_name.replace(' ', '_')}.pdf",
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
    greeting = f"Gentile {contact_name}" if contact_name else "Gentile utente"

    subject = f"Il tuo Report Premium per {company_name} è pronto! — DigIdentity"

    html_body = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="
        margin: 0; padding: 0;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        background-color: #f1f5f9;
        color: #1e293b;
    ">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">

            <!-- Header Premium -->
            <div style="
                background: linear-gradient(135deg, #312e81, #4338ca, #6366f1);
                border-radius: 16px 16px 0 0;
                padding: 32px;
                text-align: center;
            ">
                <div style="
                    display: inline-block;
                    background: rgba(255,255,255,0.15);
                    padding: 6px 16px;
                    border-radius: 20px;
                    font-size: 12px;
                    color: #c7d2fe;
                    margin-bottom: 12px;
                ">
                    &#11088; REPORT PREMIUM
                </div>
                <h1 style="color: white; margin: 0; font-size: 24px;">
                    DigIdentity Engine
                </h1>
                <p style="color: #a5b4fc; margin: 8px 0 0;">
                    Piano Strategico Digitale Completo
                </p>
            </div>

            <!-- Body -->
            <div style="
                background: white;
                padding: 32px;
                border-left: 1px solid #e2e8f0;
                border-right: 1px solid #e2e8f0;
            ">
                <p style="font-size: 16px; line-height: 1.6;">
                    {greeting},
                </p>

                <p style="font-size: 16px; line-height: 1.6;">
                    il tuo <strong>Report Premium</strong> per
                    <strong>{company_name}</strong> è pronto!
                    In allegato trovi il piano strategico digitale completo.
                </p>

                <div style="
                    background: linear-gradient(135deg, #faf5ff, #ede9fe);
                    border: 1px solid #c4b5fd;
                    border-radius: 12px;
                    padding: 24px;
                    margin: 24px 0;
                ">
                    <h3 style="color: #5b21b6; margin: 0 0 16px; font-size: 16px;">
                        &#128218; Il tuo report include:
                    </h3>
                    <ul style="
                        color: #4c1d95;
                        font-size: 14px;
                        line-height: 2;
                        padding-left: 20px;
                    ">
                        <li>Executive Summary con punteggio digitale</li>
                        <li>Analisi completa di ogni canale (sito, SEO, social)</li>
                        <li>Benchmark competitivo del tuo settore</li>
                        <li>Piano strategico personalizzato 6-12 mesi</li>
                        <li>Calendario editoriale dettagliato per 3 mesi</li>
                        <li>Budget stimato e proiezione ROI</li>
                        <li>Preventivo dettagliato degli interventi</li>
                        <li>Roadmap di implementazione con KPI</li>
                    </ul>
                </div>

                <div style="
                    background: #f0fdf4;
                    border: 1px solid #bbf7d0;
                    border-radius: 12px;
                    padding: 16px 20px;
                    margin: 24px 0;
                    text-align: center;
                ">
                    <p style="color: #166534; margin: 0; font-size: 15px;">
                        <strong>&#128161; Consiglio:</strong> Condividi il report con il tuo team
                        per definire insieme le priorità di intervento.
                    </p>
                </div>
            </div>

            <!-- Footer -->
            <div style="
                background: #f8fafc;
                border-radius: 0 0 16px 16px;
                padding: 24px 32px;
                text-align: center;
                border: 1px solid #e2e8f0;
                border-top: none;
            ">
                <p style="color: #64748b; font-size: 13px; margin: 0 0 8px;">
                    Hai domande sul report? Rispondi direttamente a questa email.
                </p>
                <p style="color: #94a3b8; font-size: 12px; margin: 0;">
                    &copy; DigIdentity Engine — Sistema automatico di diagnosi digitale per PMI
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    return _send_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        attachment_path=pdf_path,
        attachment_name=f"DigIdentity_Premium_{company_name.replace(' ', '_')}.pdf",
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

        logger.info(f"Email inviata con successo a {to_email}: {subject}")
        return True

    except Exception as e:
        logger.error(f"Errore invio email a {to_email}: {e}")
        return False
