"""
DigIdentity Engine — PDF Generator
Converte HTML in PDF usando WeasyPrint.
"""

import os
from typing import Dict, Any
from weasyprint import HTML, CSS
from datetime import datetime


def generate_pdf_free(
    sections: Dict[str, str],
    lead_data: Dict[str, Any],
    scores: Dict[str, int],
    output_dir: str = "./reports/free"
) -> Dict[str, Any]:
    """
    Genera PDF del report gratuito da sezioni HTML.
    
    Args:
        sections: Dict con section_1, section_2, ..., section_5 (HTML)
        lead_data: Dati lead (per filename e metadata)
        scores: Score per footer/header
        output_dir: Directory output PDF
        
    Returns:
        dict: Path PDF generato + metadata
    """
    print(f"📄 Generazione PDF report gratuito...")
    
    try:
        # Crea directory se non esiste
        os.makedirs(output_dir, exist_ok=True)
        
        # Filename: {lead_id}_diagnosi_gratuita_{timestamp}.pdf
        lead_id = lead_data.get("id", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{lead_id}_diagnosi_gratuita_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)
        
        # Combina tutte le sezioni in un unico HTML
        full_html = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diagnosi Strategica Digitale - {lead_data.get('nome_azienda')}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700;800;900&family=Inter:wght@300;400;500;600;700&display=swap');
        
        body {{
            font-family: 'Inter', sans-serif;
            color: #000000;
            margin: 0;
            padding: 0;
            font-size: 11pt;
            line-height: 1.6;
        }}
        
        h1, h2, h3 {{
            font-family: 'Poppins', sans-serif;
            color: #F90100;
            font-weight: 800;
        }}
        
        h1 {{ font-size: 28pt; margin-bottom: 10pt; }}
        h2 {{ font-size: 20pt; margin-top: 20pt; margin-bottom: 10pt; }}
        h3 {{ font-size: 16pt; margin-top: 15pt; margin-bottom: 8pt; }}
        
        .page-break {{
            page-break-after: always;
        }}
        
        .header {{
            text-align: center;
            padding: 20pt;
            background: linear-gradient(135deg, #F90100 0%, #000000 100%);
            color: white;
            margin-bottom: 30pt;
        }}
        
        .footer {{
            position: fixed;
            bottom: 0;
            width: 100%;
            text-align: center;
            font-size: 9pt;
            color: #666;
            padding: 10pt;
            border-top: 1px solid #ddd;
        }}
        
        .section {{
            padding: 20pt;
            margin-bottom: 20pt;
        }}
        
        .score-badge {{
            display: inline-block;
            background: #F90100;
            color: white;
            padding: 5pt 15pt;
            border-radius: 20pt;
            font-weight: 700;
            font-size: 14pt;
        }}
        
        .cta-box {{
            background: #F90100;
            color: white;
            padding: 20pt;
            border-radius: 10pt;
            text-align: center;
            margin: 20pt 0;
        }}
        
        .cta-box h3 {{
            color: white;
            margin-top: 0;
        }}
        
        ul {{
            margin-left: 20pt;
        }}
        
        li {{
            margin-bottom: 8pt;
        }}
        
        strong {{
            color: #F90100;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Diagnosi Strategica Digitale</h1>
        <p style="font-size: 14pt; margin: 0;">{lead_data.get('nome_azienda')}</p>
        <p style="font-size: 10pt; margin: 5pt 0 0 0;">Report generato il {datetime.now().strftime('%d/%m/%Y')}</p>
    </div>
    
    <div class="section">
        {sections.get('section_1', '')}
    </div>
    <div class="page-break"></div>
    
    <div class="section">
        {sections.get('section_2', '')}
    </div>
    <div class="page-break"></div>
    
    <div class="section">
        {sections.get('section_3', '')}
    </div>
    <div class="page-break"></div>
    
    <div class="section">
        {sections.get('section_4', '')}
    </div>
    <div class="page-break"></div>
    
    <div class="section">
        {sections.get('section_5', '')}
    </div>
    
    <div class="footer">
        <p>DigIdentity Agency | Specialisti AI & Automazioni per MPMI</p>
        <p>📧 info@digidentityagency.it | 📱 +39 392 199 0215 | 🌐 digidentityagency.it</p>
    </div>
</body>
</html>
"""
        
        # Genera PDF con WeasyPrint
        print(f"   Rendering PDF...")
        HTML(string=full_html).write_pdf(filepath)
        
        # Verifica dimensione file
        file_size = os.path.getsize(filepath)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"✅ PDF generato: {filename}")
        print(f"   Path: {filepath}")
        print(f"   Dimensione: {file_size_mb:.2f} MB")
        
        return {
            "success": True,
            "filepath": filepath,
            "filename": filename,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size_mb, 2)
        }
    
    except Exception as e:
        error_msg = f"Errore generazione PDF: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }


def generate_pdf_premium(
    sections: Dict[str, str],
    lead_data: Dict[str, Any],
    scores: Dict[str, int],
    output_dir: str = "./reports/premium"
) -> Dict[str, Any]:
    """
    Genera PDF del report premium (40-50 pagine) da 11 sezioni HTML.

    Args:
        sections: Dict con section_1 ... section_11 (HTML)
        lead_data: Dati lead (per filename e metadata)
        scores: Score per grafici e badge
        output_dir: Directory output PDF

    Returns:
        dict: Path PDF generato + metadata
    """
    print(f"📄 Generazione PDF report PREMIUM...")

    try:
        os.makedirs(output_dir, exist_ok=True)

        lead_id = lead_data.get("id", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{lead_id}_diagnosi_premium_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)

        # Score badges HTML
        score_totale = scores.get("score_totale", 0)
        score_color = "#F90100" if score_totale < 50 else "#FF8C00" if score_totale < 75 else "#28a745"

        scores_html = ""
        score_labels = {
            "score_sito_web": "Sito Web",
            "score_seo": "SEO",
            "score_gmb": "Google My Business",
            "score_social": "Social Media",
            "score_competitivo": "Competitività"
        }
        for key, label in score_labels.items():
            val = scores.get(key, 0)
            c = "#F90100" if val < 50 else "#FF8C00" if val < 75 else "#28a745"
            scores_html += f'''
            <div style="display:inline-block;text-align:center;margin:10pt 15pt;">
                <div style="font-size:28pt;font-weight:900;color:{c};">{val}/100</div>
                <div style="font-size:10pt;color:#666;margin-top:4pt;">{label}</div>
            </div>'''

        # Genera le 11 sezioni con page break
        sections_html = ""
        section_titles = {
            "section_1": "Executive Summary",
            "section_2": "Analisi Sito Web & Performance",
            "section_3": "Analisi SEO & Visibilità",
            "section_4": "Google My Business",
            "section_5": "Social Media Audit",
            "section_6": "Analisi Competitor",
            "section_7": "Architettura Contenuti",
            "section_8": "Opportunità AI & Automazioni",
            "section_9": "Piano Strategico 90 Giorni",
            "section_10": "Budget & ROI Atteso",
            "section_11": "Proposta di Collaborazione"
        }

        for i in range(1, 12):
            key = f"section_{i}"
            content = sections.get(key, "")
            if content:
                sections_html += f'''
    <div class="section">
        {content}
    </div>
    <div class="page-break"></div>
'''

        # Indice (Table of Contents)
        toc_html = ""
        for i, (key, title) in enumerate(section_titles.items(), 1):
            toc_html += f'<div class="toc-item"><span class="toc-number">{i:02d}</span> {title}</div>\n'

        full_html = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>Diagnosi Strategica Digitale PREMIUM - {lead_data.get('nome_azienda')}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap');

        @page {{
            size: A4;
            margin: 25mm 20mm 30mm 20mm;
            @bottom-center {{
                content: counter(page) " / " counter(pages);
                font-family: 'Inter', sans-serif;
                font-size: 9pt;
                color: #999;
            }}
        }}

        body {{
            font-family: 'Inter', sans-serif;
            color: #1a1a1a;
            margin: 0;
            padding: 0;
            font-size: 11pt;
            line-height: 1.7;
        }}

        h1, h2, h3 {{
            font-family: 'Poppins', sans-serif;
            color: #F90100;
            font-weight: 800;
            page-break-after: avoid;
        }}

        h1 {{ font-size: 26pt; margin-bottom: 10pt; }}
        h2 {{ font-size: 19pt; margin-top: 25pt; margin-bottom: 12pt; border-bottom: 3px solid #F90100; padding-bottom: 8pt; }}
        h3 {{ font-size: 14pt; margin-top: 18pt; margin-bottom: 8pt; color: #333; }}

        .page-break {{ page-break-after: always; }}

        /* COPERTINA */
        .cover {{
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            background: linear-gradient(160deg, #000000 0%, #1a0000 40%, #F90100 100%);
            color: white;
            padding: 40pt;
            page-break-after: always;
        }}
        .cover h1 {{
            font-size: 36pt;
            color: white;
            margin-bottom: 5pt;
            letter-spacing: -0.5pt;
        }}
        .cover .subtitle {{
            font-size: 16pt;
            color: rgba(255,255,255,0.85);
            margin-bottom: 40pt;
            font-weight: 400;
        }}
        .cover .company-name {{
            font-size: 28pt;
            font-weight: 900;
            color: #F90100;
            background: white;
            padding: 15pt 40pt;
            border-radius: 8pt;
            margin-bottom: 20pt;
        }}
        .cover .date {{
            font-size: 11pt;
            color: rgba(255,255,255,0.6);
            margin-top: 30pt;
        }}
        .cover .badge {{
            background: #F90100;
            color: white;
            padding: 8pt 25pt;
            border-radius: 30pt;
            font-weight: 700;
            font-size: 13pt;
            margin-top: 15pt;
            letter-spacing: 2pt;
            text-transform: uppercase;
        }}

        /* INDICE */
        .toc {{
            padding: 30pt 20pt;
        }}
        .toc h2 {{
            text-align: center;
            font-size: 22pt;
            margin-bottom: 30pt;
        }}
        .toc-item {{
            padding: 12pt 0;
            border-bottom: 1px solid #eee;
            font-size: 12pt;
            color: #333;
        }}
        .toc-number {{
            display: inline-block;
            width: 35pt;
            color: #F90100;
            font-weight: 800;
            font-family: 'Poppins', sans-serif;
        }}

        /* SCORE OVERVIEW */
        .score-overview {{
            text-align: center;
            padding: 30pt 20pt;
            background: #fafafa;
            border-radius: 10pt;
            margin: 20pt 0;
        }}
        .score-total {{
            font-size: 56pt;
            font-weight: 900;
            font-family: 'Poppins', sans-serif;
            margin-bottom: 5pt;
        }}

        /* SEZIONI */
        .section {{
            padding: 15pt 0;
            page-break-inside: avoid;
        }}

        /* TABELLE */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15pt 0;
            font-size: 10pt;
        }}
        th {{
            background: #F90100;
            color: white;
            padding: 10pt;
            text-align: left;
            font-weight: 700;
        }}
        td {{
            padding: 10pt;
            border-bottom: 1px solid #eee;
        }}
        tr:nth-child(even) td {{
            background: #fafafa;
        }}

        /* CTA BOX */
        .cta-box {{
            background: linear-gradient(135deg, #F90100 0%, #cc0000 100%);
            color: white;
            padding: 25pt;
            border-radius: 10pt;
            text-align: center;
            margin: 25pt 0;
        }}
        .cta-box h3 {{
            color: white;
            margin-top: 0;
            font-size: 18pt;
        }}

        /* BADGE */
        .score-badge {{
            display: inline-block;
            background: #F90100;
            color: white;
            padding: 4pt 14pt;
            border-radius: 20pt;
            font-weight: 700;
            font-size: 11pt;
        }}

        /* DIGIDENTITY CARD CTA */
        .did-card-cta {{
            background: linear-gradient(135deg, #000 0%, #1a0000 100%);
            border: 2px solid #F90100;
            color: white;
            padding: 25pt;
            border-radius: 10pt;
            text-align: center;
            margin: 25pt 0;
        }}
        .did-card-cta h3 {{
            color: #F90100;
            margin-top: 0;
        }}

        ul {{ margin-left: 15pt; }}
        li {{ margin-bottom: 6pt; }}
        strong {{ color: #F90100; }}

        /* FOOTER PAGINA */
        .doc-footer {{
            text-align: center;
            padding: 25pt 20pt;
            border-top: 3px solid #F90100;
            margin-top: 30pt;
            font-size: 10pt;
            color: #666;
        }}
    </style>
</head>
<body>

    <!-- COPERTINA -->
    <div class="cover">
        <h1>Diagnosi Strategica Digitale</h1>
        <div class="subtitle">Analisi Completa & Piano Operativo AI-Driven</div>
        <div class="company-name">{lead_data.get('nome_azienda', 'Azienda')}</div>
        <div class="badge">★ REPORT PREMIUM</div>
        <div class="date">Generato il {datetime.now().strftime('%d/%m/%Y')} | {lead_data.get('citta', '')} ({lead_data.get('provincia', '')})</div>
    </div>

    <!-- SCORE OVERVIEW -->
    <div class="score-overview">
        <div class="score-total" style="color:{score_color};">{score_totale}/100</div>
        <div style="font-size:13pt;color:#666;margin-bottom:20pt;">Score Digitale Complessivo</div>
        {scores_html}
    </div>
    <div class="page-break"></div>

    <!-- INDICE -->
    <div class="toc">
        <h2>Indice</h2>
        {toc_html}
    </div>
    <div class="page-break"></div>

    <!-- SEZIONI 1-11 -->
    {sections_html}

    <!-- DIGIDENTITY CARD CTA -->
    <div class="did-card-cta">
        <h3>🪪 DigIdentity Card</h3>
        <p>La tua identità digitale completa, gestita e ottimizzata.<br>
        Sito, SEO, Social, AI, Automazioni — tutto in un unico ecosistema.</p>
        <p style="font-size:13pt;font-weight:700;color:#F90100;margin-top:15pt;">
            Chiedi informazioni: info@digidentityagency.it
        </p>
    </div>

    <!-- FOOTER DOCUMENTO -->
    <div class="doc-footer">
        <p><strong style="color:#F90100;">DigIdentity Agency</strong> | Specialisti AI & Automazioni per MPMI</p>
        <p>📧 info@digidentityagency.it | 📱 +39 392 199 0215 | 🌐 digidentityagency.it</p>
        <p style="margin-top:10pt;font-size:9pt;">
            Questo documento è riservato e destinato esclusivamente al destinatario indicato.
            La riproduzione o distribuzione non autorizzata è vietata.
            © {datetime.now().year} DigIdentity Agency — Tutti i diritti riservati.
        </p>
    </div>

</body>
</html>
"""

        print(f"   Rendering PDF premium...")
        HTML(string=full_html).write_pdf(filepath)

        file_size = os.path.getsize(filepath)
        file_size_mb = file_size / (1024 * 1024)

        print(f"✅ PDF PREMIUM generato: {filename}")
        print(f"   Path: {filepath}")
        print(f"   Dimensione: {file_size_mb:.2f} MB")

        return {
            "success": True,
            "filepath": filepath,
            "filename": filename,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size_mb, 2)
        }

    except Exception as e:
        error_msg = f"Errore generazione PDF premium: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }

