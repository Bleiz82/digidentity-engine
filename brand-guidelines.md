---

# DOCUMENTO 2: brand-guidelines.md

```markdown
# DigIdentity Agency — Brand Guidelines
# v2.0 — AI-First Brand Identity

---

## 1. Brand Essence

### Chi Siamo
DigIdentity Agency è lo specialista in Intelligenza Artificiale e Automazioni 
per Micro, Piccole e Medie Imprese locali italiane. Fondata da Stefano Corda 
a Samatzai (Sardegna), l'agenzia nasce dalla convinzione che ogni piccolo 
imprenditore meriti di avere accesso alle stesse tecnologie delle grandi aziende.

### Promessa di Brand
"Rendiamo l'AI e le automazioni accessibili, comprensibili e profittevoli 
per qualsiasi piccola attività locale."

### Tagline Principali
- **Primaria**: "AI & Automazioni per la Tua Impresa"
- **Secondaria**: "Rivoluziona e valorizza la tua Identità Digitale"
- **Claim**: "Il futuro della tua attività, spiegato semplice."
- **Hashtag ufficiali**: #DigIdentity #AIperMPMI #DigitalSuccess #IntelligenzaArtificiale

### Valori del Brand
1. **Accessibilità** — La tecnologia deve essere capita da tutti, non solo dagli esperti
2. **Innovazione pratica** — Non tecnologia fine a sé stessa, ma strumenti che producono risultati
3. **Onestà** — Mai vendere fumo, mai promettere ciò che non si può mantenere
4. **Vicinanza** — Conosciamo il territorio, parliamo la lingua degli imprenditori locali
5. **Risultati misurabili** — Ogni intervento deve avere un ROI chiaro e dimostrabile

### Personalità del Brand
Se DigIdentity fosse una persona, sarebbe:
- L'amico esperto di tecnologia che ti spiega le cose senza farti sentire stupido
- Appassionato e coinvolgente (Stefano è un artista/musicista — il brand ha anima)
- Diretto e pratico — va al punto, non gira intorno
- Innovativo ma con i piedi per terra
- Sardo nel cuore, italiano nella visione

---

## 2. Identità Visiva

### Logo

**Logo su sfondo chiaro (versione dark):**
URL: https://digidentityagency.it/wp-content/uploads/2023/05/digidentity_agency_dark_removebg.png Uso: Sfondi bianchi, grigi chiari, pagine web, report, documenti


**Logo su sfondo scuro (versione light):**
URL: https://digidentityagency.it/wp-content/uploads/2023/05/digidentity_agency_light_removebg.png Uso: Sfondi neri, scuri, header dark, footer, dashboard


**Logo testuale (quando non è possibile usare l'immagine):**
```html
<span style="font-family: 'Poppins', sans-serif; font-weight: 900;">
  <span style="color: #F90100;">Dig</span><span style="color: #000000;">Identity</span>
</span>
<span style="font-family: 'Inter', sans-serif; font-size: 0.6em; 
  font-weight: 600; color: #444444; display: block; letter-spacing: 3px;">
  AGENCY
</span>
Regole d'uso del logo:

Spazio di rispetto minimo: altezza della lettera "D" su tutti i lati
Mai deformare, ruotare o modificare i colori del logo
Mai posizionare su sfondi che riducono la leggibilità
Dimensione minima: 120px di larghezza per il digitale, 30mm per la stampa
Palette Colori
Colori Primari
Nome	HEX	RGB	Uso Principale
Rosso DI	#F90100	249, 1, 0	CTA, accenti, titoli, link, elementi AI
Nero DI	#000000	0, 0, 0	Testi principali, sfondi premium, header
Bianco DI	#FFFFFF	255, 255, 255	Sfondi principali, contrasti, spazi
Grigio DI	#444444	68, 68, 68	Testi secondari, body copy, sottotitoli
Colori Secondari
Nome	HEX	RGB	Uso
Rosso Scuro	#DC0000	220, 0, 0	Hover states, gradient, variante rosso
Rosso Chiaro	#FF4444	255, 68, 68	Badge, alert, variante rosso light
Grigio Chiaro	#F8F9FA	248, 249, 250	Sfondi sezioni alternate, card
Grigio Medio	#6B7280	107, 114, 128	Testi terziari, placeholder, caption
Grigio Bordo	#E5E7EB	229, 231, 235	Bordi, separatori, divider
Colori Semantici (per report e dashboard)
Nome	HEX	Uso
Verde Successo	#10B981	Score alto, successo, positivo, strengths
Giallo Warning	#F59E0B	Score medio, attenzione, suggerimenti
Arancione Alert	#F97316	Score basso, urgenza moderata
Rosso Critico	#EF4444	Score critico, errori, problemi gravi
Blu Info	#3B82F6	Informazioni, link secondari, note
Viola Premium	#8B5CF6	Elementi premium, AI, features avanzate
Oro	#FFD700	Badge, premi, valore, offerte speciali
Gradienti
Copy/* Gradient Hero (landing page, header) */
background: linear-gradient(135deg, #000000 0%, #1a1a1a 25%, #F90100 100%);

/* Gradient CTA (bottoni principali) */
background: linear-gradient(45deg, #F90100, #DC0000);
box-shadow: 0 8px 25px rgba(249, 1, 0, 0.3);

/* Gradient AI/Premium (sezioni AI, features premium) */
background: linear-gradient(135deg, #F90100 0%, #8B5CF6 100%);

/* Gradient Card Premium */
background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
border: 1px solid rgba(249, 1, 0, 0.3);
Configurazione Tailwind CSS
Copy// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        'digi': {
          'red': '#F90100',
          'red-dark': '#DC0000',
          'red-light': '#FF4444',
          'black': '#000000',
          'gray': '#444444',
          'gray-light': '#F8F9FA',
          'gray-medium': '#6B7280',
          'gray-border': '#E5E7EB',
        },
        'score': {
          'high': '#10B981',
          'medium': '#F59E0B',
          'low': '#F97316',
          'critical': '#EF4444',
        },
        'accent': {
          'blue': '#3B82F6',
          'purple': '#8B5CF6',
          'gold': '#FFD700',
        },
      },
      fontFamily: {
        'heading': ['Poppins', 'system-ui', 'sans-serif'],
        'body': ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
};
Copy
Tipografia
Font Primari
Ruolo	Font	Pesi Utilizzati	Import
Titoli	Poppins	700 (Bold), 800 (ExtraBold), 900 (Black)	Google Fonts
Body	Inter	300 (Light), 400 (Regular), 500 (Medium), 600 (SemiBold), 700 (Bold)	Google Fonts
Monospace	JetBrains Mono	400, 500	Google Fonts (per codice/dati tecnici)
Copy<!-- Google Fonts import -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@700;800;900&display=swap" rel="stylesheet">
Gerarchia Tipografica
Copy/* H1 — Titoli principali pagina/sezione */
h1 { font-family: 'Poppins'; font-weight: 900; font-size: 2.5rem; /* 40px */ }

/* H2 — Titoli sezione */
h2 { font-family: 'Poppins'; font-weight: 800; font-size: 2rem; /* 32px */ }

/* H3 — Sottotitoli */
h3 { font-family: 'Poppins'; font-weight: 700; font-size: 1.5rem; /* 24px */ }

/* H4 — Titoletti card/elementi */
h4 { font-family: 'Inter'; font-weight: 700; font-size: 1.125rem; /* 18px */ }

/* Body — Testo principale */
body { font-family: 'Inter'; font-weight: 400; font-size: 1rem; /* 16px */ line-height: 1.6; }

/* Small — Didascalie, note */
small { font-family: 'Inter'; font-weight: 400; font-size: 0.875rem; /* 14px */ }

/* Label — Label form, badge */
.label { font-family: 'Inter'; font-weight: 600; font-size: 0.875rem; letter-spacing: 0.025em; }
Iconografia
Set primario: Lucide React (per dashboard e app React)
Set secondario: Font Awesome 6 (per landing page e report)
Stile: outline/line icons (non filled) per coerenza
Colore icone: #444444 (grigio) o #F90100 (rosso) per accenti
Icone AI specifiche: robot, brain, sparkles, zap, cpu, workflow
Immagini e Fotografia
Preferire immagini di piccoli imprenditori reali al lavoro
Ambientazioni locali (botteghe, ristoranti, studi professionali)
Stile: luminoso, autentico, non stock-photo generico
Quando possibile, usare foto del territorio sardo
Per elementi AI/tech: illustrazioni flat o isometriche, non foto generiche di robot
Overlay/filtro brand: leggera tinta rossa (#F90100 al 5-10% di opacità)
3. Tono di Voce
Il Principio Fondamentale
"Come lo spiegheresti a tua nonna?"

Se tua nonna non capisce cosa stai dicendo, stai sbagliando. Ogni concetto — dall'AI alla SEO, dal funnel alle automazioni — deve essere spiegato con parole semplici, analogie dalla vita quotidiana ed esempi pratici.

Scala del Tono per Contesto
Livello 1: Comunicazione Pubblica (report gratuiti, social, landing, email marketing)
Semplicità: ████████████ 95%
Tecnicismo: █            5%
Calore:     ██████████   85%
Urgenza:    ██████       55%
Frasi corte e dirette
Analogie dalla vita quotidiana
"Immagina che il tuo sito web sia come la vetrina del tuo negozio..."
"L'AI è come avere un dipendente instancabile che lavora 24/7..."
Domande retoriche per coinvolgere: "Sai quanti clienti ti cercano su Google ogni giorno?"
Emoji con moderazione per dinamismo
Esempio — Spiegare l'AI a un imprenditore:

❌ SBAGLIATO: "Implementiamo soluzioni di NLP con modelli transformer 
   per automatizzare la customer interaction attraverso pipeline RAG."

✅ GIUSTO: "Immagina di avere un assistente che risponde ai tuoi clienti 
   su WhatsApp anche alle 3 di notte, conosce tutti i tuoi prodotti a memoria 
   e non si ammala mai. Questo è quello che l'AI può fare per te. 
   E costa meno di un caffè al giorno."
Livello 2: Comunicazione Premium (report a pagamento, consulenza, proposte)
Semplicità: ████████     70%
Tecnicismo: ████         30%
Calore:     ████████     70%
Autorità:   ████████     75%
Più dettagliato e strategico, ma sempre accessibile
Dati e numeri a supporto delle raccomandazioni
Linguaggio da "consulente amico fidato"
Ogni proposta con ROI stimato: "Investendo X, puoi aspettarti Y"
Livello 3: Comunicazione Interna/Tecnica (codice, direttive, documentazione)
Semplicità: ██████       50%
Tecnicismo: ████████     75%
Precisione: ██████████   90%
Terminologia tecnica appropriata
Strutturato, con riferimenti e link
Commenti nel codice in italiano
Parole e Frasi da Usare
✅ USA:
- "Intelligenza Artificiale" (non solo "AI" — il pubblico capisce meglio)
- "Automazioni" (evoca praticità)
- "Risparmiare tempo e soldi"
- "Risultati concreti e misurabili"
- "Semplice", "Pratico", "Veloce"
- "La tua attività", "Il tuo business"
- "Clienti", non "utenti" o "target"
- "Investimento", non "costo"
- "Strategia personalizzata su misura"
- "Come avere un dipendente che non dorme mai"
- "Il futuro è già qui — e te lo spieghiamo"
❌ EVITA:
- Gergo tecnico non spiegato (API, backend, framework, stack)
- "Sinergia", "paradigma", "leverage", "scalabilità" (parole vuote)
- Anglicismi gratuiti quando esiste l'italiano
- Promesse vaghe: "Miglioriamo la tua presenza online" (COME? QUANTO?)
- Tono accademico o corporate
- Negatività verso il cliente: mai far sentire qualcuno stupido per non sapere
Formule Ricorrenti
"Immagina che [concetto tecnico] sia come [analogia quotidiana]..."
"In parole semplici: [spiegazione]"
"Tradotto per la tua attività: [applicazione pratica]"
"Il risultato? [beneficio concreto con numero]"
"Cosa puoi fare subito: [azione immediata]"
"Quanto costa non fare nulla: [costo opportunità]"
4. Contatti e Presenze Online
Contatti Ufficiali
Canale	Dettaglio
Telefono	+39 392 199 0215
Email	info@digidentityagency.it
Email op.	digidentityagency@gmail.com
Sede	Via Dettori 3, 09020 Samatzai (SU), Sardegna
Orari	Lun-Ven 9:00-13:00 / 15:00-18:00
Presenze Web
Piattaforma	URL
Sito Web	https://digidentityagency.it
DigIdentity Card	https://www.digidentitycard.com
Facebook	https://www.facebook.com/WebAgencyDigIdentity/
Instagram	https://www.instagram.com/_digidentityagency_/
LinkedIn	https://www.linkedin.com/company/digidentityagency
LinkedIn SC	https://www.linkedin.com/in/stefano-corda-digital-marketing
Bio LinkedIn di Stefano (posizionamento attuale)
Specialista in Intelligenza Artificiale e Automazioni per MPMI 
| Founder DigIdentity Agency | Digital Marketing & AI Strategist | Sardegna
5. Applicazioni del Brand
Report PDF — Diagnosi Strategica Digitale
Copy/* Stile report */
@page { size: A4; margin: 2cm; }
body { font-family: 'Inter', sans-serif; color: #444444; line-height: 1.6; }
h1 { font-family: 'Poppins'; color: #F90100; font-size: 24pt; 
     page-break-before: always; }
h2 { font-family: 'Poppins'; color: #000000; font-size: 18pt; 
     border-bottom: 3px solid #F90100; padding-bottom: 8px; }
h3 { font-family: 'Poppins'; color: #F90100; font-size: 14pt; }

/* Tabelle */
th { background: #F90100; color: #FFFFFF; padding: 10px; }
td { padding: 8px; border-bottom: 1px solid #E5E7EB; }
tr:nth-child(even) { background: #F8F9FA; }

/* Box informativi */
.tip-box { background: #FFF3CD; border-left: 4px solid #F59E0B; }
.action-box { background: #D1FAE5; border-left: 4px solid #10B981; }
.warning-box { background: #FEE2E2; border-left: 4px solid #EF4444; }
.ai-box { background: #EDE9FE; border-left: 4px solid #8B5CF6; }

/* CTA */
.cta-box { background: linear-gradient(135deg, #F90100, #DC0000); 
           color: #FFFFFF; border-radius: 16px; }
Email Transazionali
Header: logo su sfondo bianco
CTA button: rosso #F90100, bordo arrotondato 12px, testo bianco bold
Footer: grigio chiaro, contatti, social links, unsubscribe
Max larghezza: 600px
Font fallback: Arial, Helvetica, sans-serif (compatibilità email client)
Social Media
Formato post: quadrato 1080x1080 o verticale 1080x1350
Template con fascia rossa in alto o in basso con logo
Testi su sfondo bianco/nero per massima leggibilità
Sempre includere CTA o domanda per engagement
Quando si parla di AI: usare icona viola/rossa + termini accessibili
Dashboard Admin
Sidebar: sfondo nero #000000, testo bianco, accent rosso #F90100
Card KPI: sfondo bianco, bordo grigio chiaro, ombra leggera
Grafici: rosso #F90100 come colore primario, verde #10B981 per revenue
Status badge con colori semantici (score-high, score-medium, etc.)
6. Competitors e Differenziazione
Come NON siamo
Non siamo una web agency generica che fa "un po' di tutto"
Non siamo un'agenzia enterprise che parla solo a grandi aziende
Non siamo tecnici che parlano in codice incomprensibile
Non siamo venditori di fumo con promesse irrealizzabili
Come CI posizioniamo
Siamo LO SPECIALISTA AI & Automazioni per le piccole attività locali
Parliamo la lingua degli imprenditori, non quella dei tecnici
Ogni soluzione ha un ROI chiaro e dimostrabile
Conosciamo il territorio e le sue dinamiche
Combiniamo digital marketing tradizionale con AI e automazioni
Il nostro approccio educativo (manuali, report didattici) ci rende unici
USP (Unique Selling Propositions)
AI spiegata semplice — Nessun'altra agenzia locale spiega l'AI come noi
Diagnosi automatica — Analisi a 360° generata dall'AI in minuti, non settimane
DigIdentity Card — Prodotto unico e innovativo nostro proprietario
Approccio educativo — Non vendiamo servizi, prima educhiamo e poi proponiamo
Risultati misurabili — ROI stimato per ogni singolo intervento proposto
7. Evoluzione del Brand (Roadmap)
Fase attuale (2025-2026): Transizione
Da "Web Agency Sardegna" a "Specialista AI & Automazioni per MPMI"
Il sito digidentityagency.it deve essere aggiornato per riflettere il nuovo posizionamento
LinkedIn è già allineato con il nuovo posizionamento
Nuovi servizi AI da inserire nella pagina servizi
Landing Diagnosi Strategica Digitale deve enfatizzare la componente AI
Fase futura (2026+): Consolidamento
Posizionamento nazionale come riferimento AI per MPMI
Possibile prodottizzazione: SaaS di diagnosi automatica per altre agenzie (white-label)
Espansione offerta formativa (corsi, workshop, webinar su AI per imprenditori)
Community di imprenditori locali che usano l'AI
Eventuale rebranding più marcato verso AI (da valutare)
Questo documento è la fonte di verità per qualsiasi output visivo, comunicativo o strategico prodotto per conto di DigIdentity Agency. Ogni agente, collaboratore o tool che produce contenuti per DigIdentity deve consultare e rispettare queste guidelines.

Ultimo aggiornamento: Febbraio 2026 Autore: Stefano Corda — DigIdentity Agency


---