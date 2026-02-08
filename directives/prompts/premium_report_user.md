# Genera il Report Premium Strategico Completo

## Azienda

- **Nome**: {{COMPANY_NAME}}
- **Sito web**: {{WEBSITE_URL}}

## Dati di scraping raccolti

Usa ESCLUSIVAMENTE questi dati reali per la tua analisi. Non inventare nulla.

```json
{{SCRAPING_DATA}}
```

## Report gratuito gia generato (come riferimento)

Il seguente report free e stato gia consegnato al cliente. Il report premium deve APPROFONDIRE e ESPANDERE ogni area, NON ripetere le stesse informazioni superficialmente. Vai molto piu in profondita.

```
{{FREE_REPORT}}
```

---

## Istruzioni dettagliate per ogni sezione

### SEZIONE 1 — COPERTINA E INDICE

Genera una copertina professionale in Markdown:

```
# REPORT PREMIUM — STRATEGIA DIGITALE
## {{COMPANY_NAME}}
### Sito web: {{WEBSITE_URL}}
### Data: [data odierna]
### Documento riservato
---
```

Poi genera un **indice completo** numerato di tutte le sezioni e sotto-sezioni.

---

### SEZIONE 2 — EXECUTIVE SUMMARY (2 pagine, ~800 parole)

Deve contenere:
- **Score Digitale Complessivo**: X/100 (media ponderata: Sito 25%, SEO 30%, GMB 20%, Social 15%, Brand 10%)
- **Barra visuale**: [████████░░] 80/100
- **Top 3 opportunita ad alto impatto** con stima di ROI in euro
  - Es: "Ottimizzare la SEO per 5 keyword a medio volume potrebbe generare +120 visite/mese organiche, equivalenti a ~8-12 lead/mese con un tasso di conversione del 2-3%"
- **Top 3 rischi digitali** con stima impatto negativo
  - Es: "Assenza di cookie banner espone a sanzioni GDPR fino a 20M euro o 4% del fatturato"
- **Investimento raccomandato**: range mensile e annuale
- **ROI atteso a 12 mesi**: stima conservativa e ottimistica

---

### SEZIONE 3 — ANALISI TECNICA SITO WEB (5-6 pagine)

#### 3.1 Performance
Dai dati `website`, genera una tabella dettagliata:

| Metrica | Valore Rilevato | Benchmark PMI | Valutazione |
|---------|----------------|---------------|-------------|
| Raggiungibilita | {reachable} | 100% | ✅/❌ |
| Status Code | {status_code} | 200 | ✅/❌ |
| Tempo Caricamento | {load_time_ms}ms | <2000ms | 🟢/🟡/🔴 |
| SSL/HTTPS | {has_ssl} | Obbligatorio | ✅/❌ |
| Responsive (viewport) | {has_responsive_meta} | Obbligatorio | ✅/❌ |

Per ogni metrica sotto-standard, fornisci:
1. **Spiegazione tecnica** del problema
2. **Impatto sul business** con dato (es: "Ogni secondo di ritardo = -7% conversioni")
3. **Soluzione specifica** (non generica)
4. **Costo stimato** dell'intervento
5. **Tempo** di implementazione

#### 3.2 Audit SEO On-Page Completo

Analizza in dettaglio:

| Elemento | Stato | Valore Trovato | Ottimale | Azione Richiesta |
|----------|-------|---------------|----------|-----------------|
| Title Tag | ✅/❌ | "{website.title}" | 50-60 car., keyword inclusa | {azione} |
| Meta Description | ✅/❌ | "{website.meta_description}" | 150-160 car., CTA | {azione} |
| H1 (quantita) | ✅/❌ | {len(h1_tags)} H1 | Esattamente 1 | {azione} |
| H1 (contenuto) | — | "{primo H1}" | Keyword primaria | {azione} |
| H2 (struttura) | ✅/⚠️ | {len(h2_tags)} H2 | Gerarchia logica | {azione} |
| Immagini Alt | ✅/⚠️/❌ | {images_without_alt}/{images_count} senza alt | 0% senza alt | {azione} |
| Word Count | ✅/⚠️/❌ | {word_count} parole | >500 homepage | {azione} |
| Dati Strutturati | ✅/❌ | {structured_data} | JSON-LD presente | {azione} |
| Favicon | ✅/❌ | {has_favicon} | Presente | {azione} |

#### 3.3 Tecnologie e Sicurezza
Per OGNI tecnologia in `website.technologies_detected`:
- Nome tecnologia
- Implicazioni (positive o negative)
- Raccomandazione specifica

Analizza anche:
- Google Analytics presente? Se no, criticita per il tracciamento dati
- Cookie banner presente? Se no, rischio GDPR
- CMS rilevato: versione aggiornata? Sicurezza?

#### 3.4 Navigazione e Architettura
Da `website.pages_found`, analizza:
- Struttura del menu: le pagine sono organizzate logicamente?
- Profondita: quanti click per raggiungere le pagine importanti?
- Link interni ({internal_links_count}) vs esterni ({external_links_count}): rapporto
- Informazioni di contatto: facilmente trovabili?

> **Azioni immediate:**
> 1. [Fix piu urgente basato sui dati] — Tempo: X — Costo: X
> 2. [Secondo fix] — Tempo: X — Costo: X
> 3. [Terzo fix] — Tempo: X — Costo: X

---

### SEZIONE 4 — SEO E VISIBILITA ORGANICA (5-6 pagine)

#### 4.1 Mappa Posizionamento Attuale

Per OGNI query in `seo.search_queries`, crea una tabella dettagliata dei risultati organici con posizioni, titoli, URL, snippet. Evidenzia dove appare (o non appare) il sito dell'azienda.

#### 4.2 Pagine Indicizzate
Dalla query `site:dominio`:
- Quante pagine sono indicizzate?
- E un numero adeguato per il tipo di business?
- Ci sono pagine che dovrebbero essere indicizzate e non lo sono?

#### 4.3 Knowledge Graph e Entita
- Analizza `seo.knowledge_graph`: presente? Cosa mostra?
- Se assente: strategia per ottenerlo (Google Business, Wikipedia, dati strutturati)

#### 4.4 Visibilita Locale
- Analizza `seo.local_results`: l'azienda appare?
- Rating e recensioni mostrate nelle SERP
- Competitor che appaiono nei risultati locali

#### 4.5 Strategia Keyword Raccomandata
Basandoti sul settore dell'azienda e sui dati SERP:
- Identifica 5 cluster di keyword tematici
- Per ogni cluster: keyword principale, long-tail correlate, tipo di contenuto raccomandato
- Stima tempi di posizionamento (realistici: 3-6 mesi per keyword a media competizione)

#### 4.6 Piano Contenuti SEO 6 Mesi
- 2-4 articoli/mese con titoli specifici ottimizzati SEO
- Keyword target per articolo
- Struttura H2/H3 suggerita
- Lunghezza target (1.000-2.000 parole per articolo)
- Internal linking strategy

> **Azioni immediate:**
> 1-3 azioni SEO concrete con tempi e costi

---

### SEZIONE 5 — GOOGLE BUSINESS PROFILE (3-4 pagine)

#### 5.1 Stato del Profilo
Da `google_business`:
- SE `found: true`: analisi rating, recensioni, indirizzo, categoria
  - Rating vs. benchmark settore (es: ristoranti media 4.1, professionisti 4.3)
  - Numero recensioni vs. competitor locali
- SE `found: false`: quantifica l'impatto con dati concreti
  - "46% ricerche Google hanno intento locale"
  - "Un profilo GMB ottimizzato genera 150-400 interazioni/mese"
  - Guida passo-passo alla creazione

#### 5.2 Analisi Local Pack
Da `seo.local_results`:
- Chi appare nel Local Pack per le query di brand?
- Confronto rating e recensioni con i competitor mostrati

#### 5.3 Piano d'Azione GMB Completo
- **Settimana 1**: Creazione/completamento profilo (checklist 15 punti)
- **Mese 1-3**: Strategia raccolta recensioni (template email, template WhatsApp)
- **Calendario Google Posts**: 1/settimana, con tipologia e argomento
- **Template risposte recensioni**: positive (3 varianti), negative (3 varianti), neutre (2 varianti)

> **Azioni immediate con templates**

---

### SEZIONE 6 — ANALISI SOCIAL MEDIA (4-5 pagine)

#### 6.1 Audit per Piattaforma
Per OGNI piattaforma in `social_media`:

**Facebook**
- Stato: trovato/non trovato
- URL: {url se presente}
- Linkato dal sito: si/no
- Valutazione: X/10
- Raccomandazione: {specifica per il settore}

[Ripeti per Instagram, LinkedIn, Twitter/X, YouTube, TikTok]

#### 6.2 Analisi Gap Social
- Piattaforme presenti vs. piattaforme strategiche per il settore
- Benchmark: "Nel settore {settore} in Italia, le PMI performanti sono attive su {piattaforme}"

#### 6.3 Strategia per Piattaforma
Per ogni piattaforma rilevante:
- **Obiettivo**: awareness / engagement / conversione
- **Target audience**: chi raggiungere su questa piattaforma
- **Formato contenuti**: cosa funziona meglio (video, carousel, stories, etc.)
- **Frequenza**: quanti post/settimana
- **KPI**: metriche da monitorare
- **Budget ads** consigliato per campagne test

> **Azioni immediate per i social**

---

### SEZIONE 7 — ANALISI SWOT DIGITALE (2 pagine)

Matrice SWOT basata SOLO sui dati reali:

**Strengths** (4-6 punti con dato specifico)
- Es: "SSL attivo e viewport responsive — base tecnica adeguata"

**Weaknesses** (4-6 punti con dato specifico)
- Es: "67% delle immagini senza alt tag — penalizzazione SEO e accessibilita"

**Opportunities** (4-6 punti con stima impatto)
- Es: "Google Business assente — crearlo potrebbe generare 150+ interazioni/mese"

**Threats** (4-6 punti con dato specifico)
- Es: "Competitor X appare in posizione 1 per la ricerca brand con rating 4.8 vs. nostro 3.9"

---

### SEZIONE 8 — ROADMAP 90 GIORNI (4-5 pagine)

Genera un piano dettagliato settimana per settimana per 3 mesi:

#### Mese 1 — Fondamenta

| Settimana | Attivita | Responsabile | Deliverable | KPI Target | Budget |
|-----------|----------|-------------|-------------|------------|--------|

[4 righe, una per settimana, con attivita specifiche basate sulle criticita reali trovate]

**KPI fine Mese 1**: lista 3-5 KPI misurabili
**Budget Mese 1**: range in euro

#### Mese 2 — Crescita
[Stessa struttura]

#### Mese 3 — Accelerazione
[Stessa struttura]

---

### SEZIONE 9 — CALENDARIO EDITORIALE BLOG/SEO (3-4 pagine)

Per 3 mesi, genera:

#### Mese 1
| Settimana | Titolo Articolo SEO | Keyword Target | Volume Stimato | Lunghezza | CTA Interno |
|-----------|-------------------|----------------|---------------|-----------|-------------|

- 2-4 articoli/mese
- **Titoli ottimizzati SEO** specifici per il settore dell'azienda
- **Struttura H2/H3** suggerita per ogni articolo
- **Internal linking**: a quali pagine del sito collegare

#### 20 Idee Contenuti Evergreen
Lista di 20 titoli di articoli specifici per il settore, con keyword e volume stimato.

---

### SEZIONE 10 — CALENDARIO SOCIAL MEDIA (3-4 pagine)

Per le piattaforme rilevanti, genera un calendario settimanale per il Mese 1:

| Giorno | Piattaforma | Formato | Argomento | Copy (bozza 2-3 righe) | Hashtag |
|--------|-------------|---------|-----------|------------------------|---------|

Includi:
- **Set di hashtag** da ruotare (3 gruppi di 15-20 hashtag ciascuno)
- **Orari migliori** di pubblicazione per il settore
- **Tipologie di contenuto**: 60% educational, 20% promozionale, 10% behind-the-scenes, 10% engagement
- **Template copy** per 3-4 tipologie ricorrenti

---

### SEZIONE 11 — PREVENTIVO DETTAGLIATO (4-5 pagine)

#### Opzione A — Gestione Interna (DIY)
Tabella con: attivita, ore/mese, costo orario stimato, strumenti necessari, costo strumenti

#### Opzione B — Agenzia/Freelance
Tabella con: servizio, frequenza, range prezzo mercato italiano, nota

#### Opzione C — Pacchetto Misto Raccomandato
La raccomandazione bilanciata specifica per {{COMPANY_NAME}}:
- Cosa fare internamente vs. esternamente
- Budget mensile totale raccomandato
- ROI stimato

#### Stima ROI a 12 Mesi
| Metrica | Attuale | Target 6 Mesi | Target 12 Mesi |
|---------|---------|---------------|-----------------|
[Metriche realistiche basate sul settore]

---

### SEZIONE 12 — STRUMENTI RACCOMANDATE (2 pagine)

Tabella: categoria, strumento, costo, motivazione
Focus su strumenti gratuiti o economici adatti a PMI italiane.

---

### SEZIONE 13 — KPI E MONITORAGGIO (2 pagine)

Dashboard KPI con: metrica, frequenza monitoraggio, strumento, baseline attuale, target 90gg
Template per report mensile interno.

---

### SEZIONE 14 — CONCLUSIONI (1 pagina)

- Le 3 priorita assolute
- Cosa fare questa settimana, questo mese, nei prossimi 3 mesi
- Invito a contattare per supporto all'implementazione

---

## REGOLE FINALI

1. **Lunghezza**: 15.000-20.000 parole TOTALI. Ogni sezione deve essere sostanziale.
2. **Dati reali**: OGNI raccomandazione deve citare un dato dallo scraping
3. **Costi italiani**: usa range realistici per il mercato italiano
4. **Settore specifico**: adatta TUTTO al settore dell'azienda — esempi, benchmark, contenuti editoriali
5. **Templates utilizzabili**: dove possibile, includi template pronti all'uso (copy social, risposte recensioni, email)
6. **Niente padding**: se non hai dati sufficienti per una sotto-sezione, scrivi "Dato non disponibile — da approfondire" piuttosto che riempire con testo generico
