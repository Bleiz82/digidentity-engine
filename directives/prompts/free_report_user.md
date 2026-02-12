# Diagnosi Digitale Gratuita — DigIdentity Agency

## Informazioni Azienda

- **Nome azienda**: {{COMPANY_NAME}}
- **Sito web**: {{WEBSITE_URL}}

## Dati di Scraping Raccolti

Di seguito trovi i dati REALI raccolti dall'analisi automatica. Usa ESCLUSIVAMENTE questi dati per il report. NON inventare MAI dati, statistiche, numeri o URL che non sono presenti nel JSON qui sotto.

```json
{{SCRAPING_DATA}}
```

---

## ISTRUZIONI CRITICHE

### 1. REGOLE ASSOLUTE (non violarle)

- **Usa SOLO i dati nel JSON**. Se un campo è null, vuoto o mancante, scrivi letteralmente: "Dato non disponibile" e spiega perché è importante raccoglierlo nella strategia futura
- **NON inventare MAI**:
  - Dati dal sito che non sono nel JSON
  - Statistiche di settore generiche senza riferimento ai dati reali
  - Posizioni Google, ranking, competitor, volumi di ricerca non esplicitati nei dati
  - URL o profili social non trovati dal tool di scraping
  - Percentuali di engagement senza dati concreti
- **Dati trovati vs non trovati**:
  - Se `apify.instagram.found === true`: ANALIZZA i dati (followers, posts, engagement rate)
  - Se `apify.instagram.found === false`: Scrivi "Non è stato possibile analizzare il profilo Instagram durante lo scraping automatico" e spiega perché è importante averlo
  - Idem per Facebook, LinkedIn, TikTok, YouTube
- **Se il report è più corto di 15.000 caratteri**, espandi ogni sezione con:
  - Spiegazioni pratiche del perché i dati importano
  - Analogie concrete per il settore dell'azienda
  - Consigli specifici basati SUI DATI REALI trovati
  - Esempi di cosa cambierebbe con miglioramenti

### 2. STRUTTURA OBBLIGATORIA

Il report DEVE avere ESATTAMENTE 5 sezioni in Markdown puro (no HTML):

1. **PANORAMICA** (minimo 2.500 caratteri)
2. **PRESENZA ONLINE** (minimo 4.000 caratteri)  
3. **POSIZIONAMENTO E CONCORRENZA** (minimo 3.000 caratteri)
4. **OPPORTUNITÀ IMMEDIATE** (minimo 3.000 caratteri)
5. **PROSSIMI PASSI** (minimo 2.000 caratteri)

**Lunghezza totale minima: 15.000 caratteri**

---

## SEZIONE 1: PANORAMICA AZIENDALE

**Lunghezza minima: 2.500 caratteri**

Inizia con saluto personalizzato: "Ciao {{COMPANY_NAME}}, questa è la tua Diagnosi Digitale gratuita che misura la salute digitale della tua azienda."

Poi tabella punteggi 1-10 su:
- Sito Web (valuta da: reachable, SSL, analytics, technologies)
- SEO Online (posizionamento nome azienda su Google)
- Social Media (numero profili trovati)
- Google Business (found true/false, rating)
- Velocità & Performance (load_time_ms)

Aggiungi sommario tradotto in linguaggio semplice per imprenditore.

---

## SEZIONE 2: PRESENZA ONLINE

**Lunghezza minima: 4.000 caratteri**

### A. IL TUO SITO WEB (minimo 1.200 caratteri)

Analizza campo per campo:
- Raggiungibilità: reachable, status_code, has_ssl
- Velocità: converti load_time_ms in secondi, confronta con 2s
- SEO On-Page: title, meta_description, h1_tags, h2_tags, word_count
- Tecnologie: technologies_detected lista con commenti
- Immagini: calcola % di images_without_alt
- Analytics: has_analytics (segnala PRIORITARIO se false)
- Cookie: has_cookie_banner (avvisa GDPR se false)
- Link e struttura: internal_links_count vs external_links_count

### B. GOOGLE MY BUSINESS (minimo 1.200 caratteri)

Se found === true: analizza rating, reviews_count
Se found === false: "**PRIORITÀ MASSIMA**. Il 46% ricerche Google ha intento locale. Senza GMB generi 0 interazioni locali"

### C. SOCIAL MEDIA (minimo 1.600 caratteri)

Per ogni piattaforma: specifica se trovata, dove linkato, analizza metriche se disponibili

---

## SEZIONE 3: POSIZIONAMENTO E CONCORRENZA

**Lunghezza minima: 3.000 caratteri**

Analizza:
- Posizionamento Google per nome azienda (seo.search_queries)
- Indicizzazione (site: command results)
- Knowledge Graph (presente/assente)
- Competitor analysis
- Local results

---

## SEZIONE 4: OPPORTUNITÀ IMMEDIATE

**Lunghezza minima: 3.000 caratteri**

Elenca ESATTAMENTE 5 azioni concrete:

### AZIONE {{N}}: {{TITOLO}}
**Difficoltà**: {{Bassa/Media/Alta}}  
**Tempo**: {{N}} giorni  
**Impatto**: {{Alto/Molto Alto}}  
**Descrizione**: [basato su dati reali]

Possibili azioni: GMB, title/meta, alt tag immagini, cookie banner, velocità sito, social, analytics, structured data, H1/H2, espansione contenuto

---

## SEZIONE 5: PROSSIMI PASSI

**Lunghezza minima: 2.000 caratteri**

1. Sommario urgenze (200-300 parole)
2. Roadmap fasi (Settimana 1-2, 3-4, Mese 2, Mese 3+)
3. Diagnosi Premium spiegazione (€99 include: audit, Web Vitals, 50+ checklist, competitor, piano strategico, implementazione, video report)
4. Call-to-Action:

```
{{CHECKOUT_PLACEHOLDER}}
```

Seguito da: "Se riconosci il valore... [descrizione premium]... Clicca e procedi al checkout."

Di chiusura: "Stefano Corda — DigIdentity Agency | info@digidentityagency.it | www.digidentityagency.it"

---

## NOTE CRITICHE

1. **MINIMO 15.000 caratteri** - Se sotto, ESPANDI le 5 sezioni
2. **DATI REALI SOLO** - Niente invenzione, statistiche, numeri
3. **TONO SARDO** - Linguaggio accessibile a imprenditore
4. **Niente competitor agenzie** - Solo DigIdentity Agency
5. **Markdown puro** - No HTML
6. **{{CHECKOUT_PLACEHOLDER}}** - Il sistema lo sostituirà con bottone Stripe
