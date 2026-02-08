# Genera la Diagnosi Digitale Gratuita

## Azienda da analizzare

- **Nome azienda**: {{COMPANY_NAME}}
- **Sito web**: {{WEBSITE_URL}}

## Dati di scraping raccolti

Di seguito trovi i dati REALI raccolti dallo scraping automatico del sito web, dei motori di ricerca e dei profili social. Usa ESCLUSIVAMENTE questi dati per la tua analisi. Non inventare nulla.

```json
{{SCRAPING_DATA}}
```

## Istruzioni dettagliate per ogni sezione

### SITO WEB — Cosa analizzare nei dati

1. **Performance e raggiungibilita**:
   - `website.reachable`: il sito risponde? Se no, e una criticita massima (punteggio 1/10)
   - `website.status_code`: 200 = OK, altro = problema
   - `website.load_time_ms`: confrontalo con benchmark 2000ms. Scrivi la formula: "{valore}ms, cioe {percentuale}% {sopra/sotto} la soglia consigliata di 2000ms"
   - `website.has_ssl`: HTTPS attivo? Se no, penalizzazione Google confermata

2. **SEO On-Page** — sii ESTREMAMENTE specifico:
   - `website.title`: riporta il title ESATTO. Analizza: contiene il nome azienda? Contiene keyword di settore? Lunghezza in caratteri (ottimale: 50-60)?
   - `website.meta_description`: riporta il testo ESATTO. Lunghezza? Contiene una CTA? E' unica o generica?
   - `website.h1_tags`: riporta TUTTI gli H1 trovati. Regola: dovrebbe essercene UNO SOLO contenente la keyword primaria. Se ce ne sono 0 o >1, e un errore SEO
   - `website.h2_tags`: lista i primi 5-10 H2. Sono descrittivi? Contengono keyword? Seguono una gerarchia logica?
   - `website.word_count`: riporta il numero esatto. Sotto 300 parole = contenuto troppo scarso per SEO. Tra 300-800 = sufficiente. Sopra 800 = buono

3. **Immagini**:
   - `website.images_count` e `website.images_without_alt`: calcola la percentuale ESATTA di immagini senza alt
   - Formula: "{senza_alt} immagini su {totale} non hanno l'attributo alt ({percentuale}%)"
   - Spiega perche e un problema: accessibilita, SEO per Google Immagini

4. **Tecnologia e Infrastruttura**:
   - `website.technologies_detected`: lista OGNI tecnologia trovata con un breve commento
   - Esempio: "WordPress rilevato — CMS adeguato per PMI, verificare aggiornamenti sicurezza"
   - Esempio: "Google Analytics rilevato — positivo, il tracciamento dati e attivo"
   - Esempio: "Nessun cookie banner/GDPR rilevato — possibile non conformita al GDPR"
   - `website.has_analytics`: se False, segnala come criticita importante
   - `website.has_cookie_banner`: se False, rischio legale GDPR
   - `website.structured_data`: se False, opportunita mancata per rich snippet Google

5. **Navigazione**:
   - `website.pages_found`: lista le pagine trovate nel menu. Commenta se la struttura e logica
   - `website.internal_links_count` / `website.external_links_count`: rapporto link interni/esterni
   - `website.contact_info`: informazioni di contatto trovate (email, telefoni)

### SEO E VISIBILITA — Cosa analizzare nei dati

1. **Risultati ricerca brand** (`seo.search_queries`):
   - Per la query con il nome azienda: in che posizione appare il sito? Appare nei primi 3 risultati?
   - Se NON appare nemmeno per il proprio nome, e una criticita GRAVE

2. **Pagine indicizzate** (`seo.search_queries` con query "site:dominio"):
   - Quanti risultati totali? Sotto 10 = scarsa indicizzazione. 10-50 = nella media PMI. >50 = buona

3. **Knowledge Graph** (`seo.knowledge_graph`):
   - Presente o assente? Se presente, cosa mostra?
   - Se assente: "Nessun Knowledge Graph rilevato — Google non riconosce ancora {company_name} come entita. L'ottimizzazione della scheda Google Business e dei dati strutturati puo attivarlo."

4. **Local results** (`seo.local_results`):
   - Azienda presente? Rating, recensioni, indirizzo mostrati?
   - Se assente: impatto sulla visibilita locale

5. **Tabella risultati**: per OGNI query in `seo.search_queries`, crea una tabella con posizione, titolo, link, dominio dei risultati organici trovati

### GOOGLE BUSINESS — Cosa analizzare nei dati

- `google_business.found`: presente o no?
- Se SI: riporta `rating`, `reviews_count`, `address`, `category`
  - Rating: confronta con benchmark settore (sotto 4.0 = attenzione, sopra 4.5 = eccellente)
  - Recensioni: sotto 10 = poche, 10-50 = nella media, >50 = buone per PMI
- Se NO: spiega concretamente cosa perde l'azienda:
  - "Il 46% delle ricerche Google ha intento locale"
  - "Un profilo Google Business nel settore {settore} genera in media 100-300 interazioni/mese"
  - "Senza GMB, l'azienda e invisibile su Google Maps"

### SOCIAL MEDIA — Cosa analizzare nei dati

Per OGNI piattaforma in `social_media` (facebook, instagram, linkedin, twitter, youtube, tiktok):
- Se trovato: riporta URL, specifica se era linkato dal sito web (`found_on_website`)
- Se NON trovato: valuta se e rilevante per il settore dell'azienda e spiega perche
- Piattaforme chiave per settore:
  - Ristorazione/Food: Instagram (priorita massima), Facebook, TikTok
  - B2B/Servizi: LinkedIn (priorita massima), Facebook
  - Retail/E-commerce: Instagram, Facebook, TikTok
  - Turismo: Instagram, Facebook, YouTube
  - Professionisti: LinkedIn, Twitter/X

### TOP 5 AZIONI — Criteri di selezione

Scegli le 5 azioni piu urgenti basandoti SOLO sulle criticita reali trovate, ordinate per:
1. **Impatto alto + Sforzo basso** (quick wins) per prime
2. **Impatto alto + Sforzo medio** per seconde
3. **Impatto alto + Sforzo alto** per ultime

Possibili azioni (usa solo quelle pertinenti ai problemi REALI trovati):
- Creare/ottimizzare Google Business (se assente)
- Ottimizzare title tag e meta description (se mancanti o non ottimali)
- Aggiungere alt tag alle immagini (se >30% senza alt)
- Installare cookie banner GDPR (se assente)
- Creare profili social mancanti ma rilevanti per il settore
- Migliorare velocita sito (se >3000ms)
- Aggiungere Google Analytics (se assente)
- Creare dati strutturati JSON-LD (se assenti)
- Ottimizzare struttura heading H1/H2 (se problematica)
- Aumentare contenuto testuale (se word_count < 300)

### ERRORI DI SCRAPING

Se il campo `errors` contiene errori, menzionali come "Limitazioni dell'analisi automatica" e spiega che quei dati andrebbero verificati manualmente.

## Output

Genera il report completo in formato Markdown, seguendo ESATTAMENTE la struttura definita nel system prompt. Il report deve essere di 8-12 pagine (3.000-5.000 parole). Sii specifico, cita ogni dato numerico, e assicurati che ogni punteggio sia giustificato con almeno 3 dati concreti.
