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

### Contenuto obbligatorio:

1. **Saluto personalizzato** (50-100 parole)
   - Usa il nome dell'azienda e il settore (se disponibile)
   - Presenta il report come una "fotografia della salute digitale"
   - Tono: professionale ma accessibile, come un consulente sardo che parla a un imprenditore

2. **Presentazione dell'azienda** (200-300 parole)
   - Riporta: nome, sito web, settore (se disponibile)
   - Riporta i dati di contatto trovati: email e telefoni dal JSON di scraping
   - Se contatti non trovati: "I contatti non sono stati trovati nel sito web — consigliamo di creare una pagina 'Contatti' visibile e ottimizzata"

3. **Tabella punteggi** (Markdown table)
   - Crea una tabella con 5 righe: Sito Web, SEO Online, Social Media, Google Business, Velocità & Performance
   - Per ogni riga, assegna un punteggio 1-10 basato SUI DATI REALI

4. **Sommario per l'imprenditore** (300-400 parole)
   - Traduci i dati tecnici in linguaggio semplice
   - Esempi: "Il tuo sito carica in 2.4 secondi — più veloce della media italiana (3.2s), questo è positivo per Google"
   - Concludi con: "Nei paragrafi seguenti, analizzeremo ogni area nel dettaglio e identificheremo le migliorie prioritarie per aumentare la visibilità della tua azienda online."

---

## SEZIONE 2: PRESENZA ONLINE

**Lunghezza minima: 4.000 caratteri**

Dividi in 3 sottosezioni:

### A. IL TUO SITO WEB (minimo 1.200 caratteri)

Usa i dati da `website.*`:

1. **Raggiungibilità e Accessibilità**
   - Riporta: `website.reachable`, `website.status_code`, `website.has_ssl`
   - Se reachable=false: "**PROBLEMA CRITICO**: Il sito non è raggiungibile."
   - Se has_ssl=true: "✓ Sito protetto con HTTPS — Google ti premia per questo"

2. **Velocità di Caricamento**
   - Da `website.load_time_ms`, converti in secondi
   - Confronta con benchmark 2 secondi

3. **SEO On-Page** (Specifiche dettagliate)
   - **Title tag**: Riporta il testo esatto da `website.title`
   - **Meta description**: Riporta il testo esatto da `website.meta_description`
   - **H1 Tags**: Riporta TUTTI gli H1 trovati da `website.h1_tags`
   - **H2 Tags**: Riporta i primi 5-10 da `website.h2_tags`
   - **Word Count**: Da `website.word_count`

4. **Tecnologie Usate**
   - Da `website.technologies_detected`, lista ogni tecnologia con un commento

5. **Immagini**
   - Da `website.images_count` e `website.images_without_alt`
   - Calcola percentuale esatta

6. **Analitiche e Cookie**
   - `website.has_analytics`: se false, segnala PRIORITARIO installarla
   - `website.has_cookie_banner`: se false, indicare non conformità GDPR
   - `website.structured_data`: analizza

7. **Link e Struttura**
   - Da `website.internal_links_count` e `website.external_links_count`

### B. GOOGLE MY BUSINESS (minimo 1.200 caratteri)

Usa i dati da `google_business.*`:

**Se `google_business.found === true`**:
- Riporta: rating, reviews_count, address, phone, category
- Analizza i punteggi

**Se `google_business.found === false`**:
- **PRIORITÀ MASSIMA**: Spiega l'impatto di non avere una scheda GMB
- Il 46% delle ricerche Google ha intento locale
- GMB genera 100-300 interazioni/mese

### C. SOCIAL MEDIA (minimo 1.600 caratteri)

Usa i dati da `social_media.*`:

- Conta quanti profili social trovati
- Per OGNI piattaforma (Facebook, Instagram, LinkedIn, TikTok, YouTube):
  - Se trovato: riporta URL
  - Se NON trovato: valuta se rilevante per settore

---

## SEZIONE 3: POSIZIONAMENTO E CONCORRENZA

**Lunghezza minima: 3.000 caratteri**

1. **Posizionamento su Google**
   - Da `seo.search_queries`, analizza la query per il nome azienda
   - Se no organic results: "Sito NON appare nei risultati di Google per il nome dell'azienda "

2. **Indicizzazione (site command)**
   - Da `seo.search_queries` con query "site:dominio"

3. **Knowledge Graph**
   - Da `seo.knowledge_graph`

4. **Competitor Analysis**
   - Da `perplexity.analysis` o competitor data (se disponibile)

5. **Analisi delle Ricerche Locali**
   - Da `seo.local_results`

---

## SEZIONE 4: OPPORTUNITÀ IMMEDIATE

**Lunghezza minima: 3.000 caratteri**

Basato SUI DATI REALI trovati, elenca ESATTAMENTE 5 azioni concrete:

**Formato per ogni azione**:

### AZIONE {{N}}: {{TITOLO}}

**Difficoltà**: {{Bassa/Media/Alta}}  
**Tempo stimato**: {{N}} giorni  
**Impatto**: {{Alto/Molto Alto}}  

**Descrizione**: [Descrizione concreta]
**Perché ora**: [Motivo specifico]
**Come farlo**: [Istruzioni concrete]
**Risultati attesi**: [Impatto quantificabile]

**Possibili azioni** (seleziona solo le PERTINENTI ai dati reali):
- Creare/Ottimizzare Google My Business (se non trovato)
- Ottimizzare Title Tag e Meta Description
- Aggiungere ALT tag alle immagini (se > 30% senza ALT)
- Installare Cookie Banner GDPR (se assente)
- Aumentare Velocità Sito (se > 3000ms)
- Creare Profili Social Mancanti
- Installare Google Analytics (se assente)
- Aggiungere Dati Strutturati JSON-LD (se assenti)
- Ottimizzare Struttura dei Heading H1/H2
- Espandere Contenuto Principale (se word_count < 300)

---

## SEZIONE 5: PROSSIMI PASSI

**Lunghezza minima: 2.000 caratteri**

1. **Sommario Urgenze** (200-300 parole)
   - Sintetizza i 3-5 problemi più critici dai dati

2. **Roadmap Fasi** (400-600 parole)
   - Settimana 1-2: Azioni rapide
   - Settimana 3-4: Azioni medie
   - Mese 2: Azioni complesse
   - Mese 3+: Strategie a lungo termine

3. **Diagnosi Premium** (400-600 parole)
   - Spiega cosa include il piano Premium (€99):
     1. Audit tecnico dettagliato pagina per pagina
     2. Analisi Core Web Vitals completa
     3. Checklist 50+ fattori di ranking Google
     4. Analisi competitor approfondita
     5. Piano strategico personalizzato
     6. Implementazione assistita delle prime 3 azioni
     7. Report video-presentato (20 minuti personali)

4. **Call-to-Action** (200-300 parole)

Inserisci qui il placeholder:

```
{{CHECKOUT_PLACEHOLDER}}
```

Seguito da:

"Se riconosci il valore dell'analisi che hai appena letto, il passo successivo è chiaro: passare da questa diagnosi gratuita al Piano Strategico Digitale completo.

Nel corso dei prossimi 30 giorni, il tuo sito avrà tutte le ottimizzazioni consigliate. I risultati:
- 40-80% aumento traffico organico da Google
- 3-5 nuovi lead del tuo settore ogni mese
- Posizionamento top 3 per il tuo nome e città
- Google My Business con reviews e engagement

Il costo? €99 oggi. L'investimento è minimo, il ritorno è enorme.

Clicca il bottone per procedere al checkout.

---

Se hai domande prima di procedere:
**Stefano Corda — DigIdentity Agency**
- Email: info@digidentityagency.it
- Website: www.digidentityagency.it

Attendiamo tue notizie."

---

## FIRMA E CHIUSURA

Concludi SEMPRE con:

**Stefano Corda — DigIdentity Agency**  
info@digidentityagency.it | www.digidentityagency.it

---

## NOTE CRITICHE PER IL GENERATORE IA

1. **Lunghezza MINIMA 15.000 caratteri** — Se il report è SOTTO, ESPANDI le sezioni. Non iniziare una sesta sezione, ma espandi le 5 esistenti con spiegazioni pratiche, esempi, e consigli specifici per il settore
2. **Sempre dati REALI** — Ogni numero, percentuale, posizione deve venire dal JSON. Se manca il dato, scrivi: "Dato non disponibile durante lo scraping automatico"
3. **Tono sardo-amichevole** — Scrivi come se stessi parlando a un vero imprenditore sardo, usa analogie del territorio
4. **Niente menzione competitor agenzie** — Il report è di DigIdentity Agency, solo
5. **Markdown puro** — Niente tag HTML. Solo: # ## ### **bold** *italic* `code` [link]
6. **Inserisci {{CHECKOUT_PLACEHOLDER}}** — Il sistema lo sostituirà con il vero bottone Stripe
