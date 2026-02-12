# DATI DELL'AZIENDA DA ANALIZZARE

**Azienda:** {{COMPANY_NAME}}
**Sito web:** {{WEBSITE_URL}}

---

## DATI RACCOLTI DALL'ANALISI AUTOMATICA

I dati qui sotto sono il risultato di un'analisi automatica multi-sorgente in formato JSON.
Usali come BASE UNICA per scrivere il report. NON aggiungere informazioni che non sono presenti qui.

{{SCRAPING_DATA}}

---

## GENERA LA DIAGNOSI STRATEGICA DIGITALE GRATUITA

Scrivi in Markdown puro (## per titoli, ** per grassetto, - per elenchi, tabelle Markdown). NON usare HTML.
Il report deve avere ESATTAMENTE 5 sezioni.

---

### SEZIONE 1 - PANORAMICA: LA TUA FOTOGRAFIA DIGITALE (minimo 2500 caratteri)

- Saluta il titolare per nome (lead.nome_contatto)
- Presenta azienda: nome, settore, citta, provincia
- Usa perplexity.analysis per storia azienda (anni attivita, specializzazioni)
- Se seo.knowledge_graph.type esiste, menziona che Google riconosce l'azienda come quel tipo
- TABELLA PUNTEGGI (Area | Punteggio | Stato): usa score_sito_web, score_seo, score_gmb, score_social, score_competitivo, score_totale. Stato: >=70 Buono, 40-69 Da migliorare, <40 Critico. Se NULL: scrivi "Non calcolato" e spiega che verranno calcolati nella Premium.

---

### SEZIONE 2 - PRESENZA ONLINE: COME TI VEDE IL MONDO (minimo 4000 caratteri)

**2A - SITO WEB** (campi: website.*):
- Tecnologia: website.technologies_detected (es. "costruito con WordPress")
- SSL: website.has_ssl (se true: "hai il certificato SSL, bene")
- Velocita: website.load_time_ms (converti in secondi, spiega impatto)
- Immagini: website.images_count e website.images_without_alt (es. "26 immagini, 4 senza testo alternativo")
- Meta description: website.meta_description (se null: spiega cos'e e perche manca)
- Analytics: website.has_analytics (se false: "stai volando alla cieca")
- Cookie banner: website.has_cookie_banner (se false: problema GDPR)
- Dati strutturati: website.structured_data (se false: spiega in modo semplice)
- Struttura: website.pages_found (commenta quante pagine e se bastano)
- Responsive: website.has_responsive_meta (se true: "si adatta ai telefoni")

**2B - GOOGLE MY BUSINESS** (campi: google_business.*, apify.google_maps.*):
- Se google_business.found=true MA rating/phone/hours sono null: "profilo esiste ma incompleto"
- Se apify.google_maps ha dati reali: usali con numeri specifici
- Se apify.google_maps.found=false: "non siamo riusciti a raccogliere dati dettagliati"
- MAI dire "non ha GMB" se google_business.found=true
- Spiega importanza GMB per impresa locale

**2C - SOCIAL MEDIA** (campi: social_media.*, apify.instagram.*, apify.facebook.*, apify.linkedin.*):
- Se campo null E apify.[social].found=false: "non siamo riusciti a verificare la presenza su [social]"
- MAI dire "non ha social" o "social assenti" - di SOLO che non sei riuscito a verificarli
- Se ci sono dati: usa numeri specifici (follower, post, engagement)
- Dai esempi concreti per il settore nella citta dell'azienda

Ogni sotto-sezione chiude con "Cosa significa per te in pratica:" + impatto business.

---

### SEZIONE 3 - POSIZIONAMENTO E CONCORRENZA (minimo 3000 caratteri)

Campi: seo.search_queries, perplexity.analysis (competitor), competitors.*

- Posizionamento SERP: per ogni query in seo.search_queries mostra posizione del sito
- Pagine indicizzate: usa query "site:dominio" per conteggio
- Competitor da perplexity.analysis: RIPORTA la tabella competitor con dettagli specifici
- Confronto diretto con nomi e numeri reali dei competitor
- Se competitors[] vuoto ma perplexity ha dati: usa quelli di Perplexity
- Costo dell'inazione: "Ogni giorno senza ottimizzare, i clienti cercano [settore] [citta] e trovano i competitor"

---

### SEZIONE 4 - OPPORTUNITA IMMEDIATE: LE COSE CHE PUOI FARE SUBITO (minimo 3000 caratteri)

5 azioni concrete basate sui PROBLEMI REALI trovati. Per ogni azione:

**[N]. [Titolo]**
- Perche: [dato specifico dall'analisi]
- Cosa fare: [passi pratici dettagliati]
- Difficolta: Facile/Media/Difficile
- Costo: Gratuito / Budget stimato
- Impatto: [cosa cambia]

Collega ogni azione ai dati reali:
- website.has_analytics=false -> Installa Google Analytics
- website.meta_description=null -> Aggiungi meta description
- website.images_without_alt>0 -> Testo alternativo immagini
- google_business incompleto -> Completa profilo GMB
- website.has_cookie_banner=false -> Cookie banner GDPR
- website.structured_data=false -> Dati strutturati LocalBusiness
- Usa suggerimenti da perplexity.analysis sezione "Opportunita"

ALMENO 2 azioni GRATUITE.

---

### SEZIONE 5 - PROSSIMI PASSI: VUOI IL QUADRO COMPLETO? (minimo 2000 caratteri)

- Riassumi 3 problemi critici trovati
- "Questa diagnosi gratuita ti ha dato una fotografia. La Diagnosi Premium ti da la mappa stradale."
- Cosa include la Premium (40-50 pagine): analisi tecnica approfondita, piano 90 giorni, calendario editoriale, analisi competitor avanzata, strategie AI e automazione, preventivo dettagliato
- Prezzo: "Una consulenza cosi costa 500-1500 euro. La Diagnosi Premium costa 99 euro."
- Link acquisto: CHECKOUT_PLACEHOLDER
- Firma: Stefano Corda - DigIdentity Agency
- Contatti: info@digidentityagency.it | www.digidentityagency.it

---

## REGOLE ASSOLUTE

1. USA SOLO DATI REALI dal JSON. Cita numeri, nomi, URL specifici.
2. MAI INVENTARE. Se campo null/vuoto/[]/error: scrivi "Non siamo riusciti ad analizzare questo aspetto" e dai consiglio generico di best practice.
3. MAI dire che qualcosa NON ESISTE solo perche il dato e null. "Dato non disponibile" NON significa "non ce l'ha".
4. LUNGHEZZA MINIMA TOTALE: 15.000 caratteri. Se corto, espandi con contesto settore e PMI locali.
5. TONO: diretto, locale, italiano. Come un consulente che conosce le PMI sarde. Ogni termine tecnico va spiegato.
6. Ogni sezione chiude con collegamento logico alla successiva.
7. NO altre agenzie. DigIdentity e l'unico partner.
8. PERPLEXITY: perplexity.analysis e la fonte piu ricca. Usala per competitor, reputazione, opportunita.
9. Contatti azienda: da website.contact_info.
10. Contatti DigIdentity: SEMPRE info@digidentityagency.it e www.digidentityagency.it (NON digidentity.it).

GENERA IL REPORT ORA. SCRIVI ALMENO 15.000 CARATTERI.
