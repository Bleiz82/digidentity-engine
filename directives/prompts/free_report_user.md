FORMATO OUTPUT OBBLIGATORIO:
- Scrivi SOLO in Markdown puro
- NON usare MAI tag HTML (<section>, <div>, <p>, <table>, <tr>, <td>, <span>, <ol>, <li>, <h1>, <h2>, ecc.)
- Usa SOLO sintassi Markdown: # per titoli, ** per grassetto, | per tabelle, - per liste, > per citazioni
- Se scrivi anche un solo tag HTML, il report sarà illeggibile

# DIAGNOSI DIGITALE: {{COMPANY_NAME}}

## Informazioni Azienda
- **Nome azienda**: {{COMPANY_NAME}}
- **Sito web**: {{WEBSITE_URL}}

## Dati Analisi (Sola Lettura)
Usa ESCLUSIVAMENTE questi dati reali. Se un dato è 0 o null, dichiara che non è stato trovato e spiega perché è un problema grave per l'imprenditore.

```json
{{SCRAPING_DATA}}
```

---

## ISTRUZIONI DI SCRITTURA (DA SEGUIRE ALLA LETTERA)

### 1. IL TONO "AMICO AL BAR"
Parla come un amico esperto di tecnologia che spiega le cose a un imprenditore stanco davanti a un caffè. Zero gergo tecnico. 
- Traduci ogni dato tecnico in: **Quanti clienti sto perdendo?**
- Se il sito è lento, non parlare di "milliseconds". Parla di gente che si stufa e se ne va dal concorrente.
- Se mancano i social, non parlare di "digital presence". Parla di "insegna spenta".

### 2. STRUTTURA OBBLIGATORIA (5 SEZIONI)

## 1. LA TUA FOTOGRAFIA DIGITALE
Inizia con un riassunto brutale ma onesto. Usa un'analogia (il termometro, la pagella, il motore). 
Inserisci i punteggi in questo formato esatto (uno per riga) per permettere al generatore PDF di creare i grafici:
Sito: XX/100
SEO: XX/100
Social: XX/100
Google Business: XX/100

Spiega cosa significano questi numeri per il business, non per i programmatori.

## 2. COME TI TROVANO I CLIENTI (O NON TI TROVANO)
Analizza Sito, Social e Google Business Profile usando i dati REALI del JSON.
- **Sito Web**: È la tua vetrina. Se è lento, la porta è incastrata. Se non è mobile-friendly, la vetrina è appannata.
- **Social**: È il tuo passaparola. Se hai follower ma nessuno interagisce, sei in una stanza dove tutti dormono.
- **Google Business**: È la tua posizione sulle mappe. Se found=false, non hai la scheda. Dillo chiaramente: "Non esisti su Google Maps. La gente cerca quello che fai e trova il tuo vicino."

Per ogni problema usa questo schema: **Cosa succede** → **Quanti clienti perdi** → **Cosa fare subito**.

## 3. I TUOI CONCORRENTI: COSA FANNO CHE TU NON FAI
Usa i nomi reali dei competitor trovati nel JSON. 
Fai un confronto diretto. "Mentre tu sei a pagina 2, [Nome Competitor] è primo." 
Spiega perché loro stanno prendendo i clienti che dovrebbero essere tuoi.

## 4. 5 AZIONI CHE PUOI FARE QUESTA SETTIMANA
Elenca 5 cose concrete, pratiche, che l'imprenditore può fare da solo e gratis (o quasi).
Esempio: "Scarica l'app di Google Business e rispondi alle ultime 3 recensioni. Ci metti 5 minuti. Risultato: Google ti vedrà attivo e ti premierà."
Sii specifico, dai i link se necessario, e non dire mai "chiedi a un esperto".

## 5. IL TUO PROSSIMO PASSO
Riassumi i 3 problemi più urgenti. Presenta la Diagnosi Premium come il "Piano d'attacco in 90 giorni" per smettere di regalare clienti alla concorrenza.

{{CHECKOUT_PLACEHOLDER}}

---
**Firma obbligatoria finale:**
Stefano Corda — Fondatore, DigIdentity Agency | info@digidentityagency.it | www.digidentityagency.it

---

### 3. REQUISITO DI LUNGHEZZA (Minimo 15.000 caratteri)
Per raggiungere la lunghezza richiesta:
- Espandi ogni sezione con esempi pratici e scenari reali.
- Racconta storie: "Immagina un cliente che cerca da cellulare mentre è in macchina..."
- Dettaglia il "perché" ogni piccola modifica fa la differenza nel cassetto a fine mese.
- Scrivi in modo discorsivo, amichevole e profondo.
- USA I COMPONENTI:
  - Per i punteggi usa: [BARRA_PUNTEGGIO: Nome Area: XX/100]
  - Per i problemi gravi usa: > [!CRITICAL] Messaggio
  - Per le vittorie usa: > [!SUCCESS] Messaggio
  - Per i consigli usa: > [!SUGGESTION] Messaggio
