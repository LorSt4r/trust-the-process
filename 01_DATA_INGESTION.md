# 01_DATA_INGESTION: Network Interception & Sharp Scraping

## 1. Obiettivo e Scopo del Modulo
Il modulo è responsabile dell'approvvigionamento dei dati grezzi in tempo reale. Deve operare in totale invisibilità, estraendo le inefficienze promozionali (Superquote) dal Soft Book (Bet365) e le quote reali di mercato (Fair Odds) dagli Sharp Books (Pinnacle, Betfair Exchange). L'estrazione deve avvenire a costo zero (senza API a pagamento) e con un impatto di rete minimo per evitare blocchi IP.

## 2. Architettura di Sicurezza (Scraping Passivo)
Poiché l'esecuzione materiale della scommessa è delegata all'operatore umano via smartphone, questo modulo **non effettuerà mai il login** su alcun conto gioco.
* **Vantaggio OpSec:** Navigando la piattaforma pubblica da visitatore non loggato, il bookmaker non può bannare un account, ma al massimo limitare temporaneamente l'indirizzo IP.
* **Gestione IP:** Lo script utilizzerà chiamate ruotate su Proxy Mobile o sfrutterà i riavvii della connessione per rinnovare l'IP in caso di blocco.

## 3. Soft Book Ingestion (Bet365)
L'estrazione della Superquota non avverrà tramite la lettura visiva del codice HTML (CSS/DOM), ma intercettando la comunicazione sotterranea tra il sito web e il server del bookmaker.

### 3.1 Network Interception (Playwright)
* L'istanza di Playwright (configurata con moduli stealth base) navigherà sulla pagina pubblica delle Superquote.
* Tramite l'event listener `page.on("response")`, lo script monitorerà esclusivamente il traffico di rete di tipo XHR/Fetch.
* Lo script catturerà il payload JSON grezzo generato dal server di Bet365 prima ancora che la pagina web lo trasformi in elementi grafici.

### 3.2 Estrazione dei Limiti Promozionali (Regex)
Le Superquote hanno sempre un "Cap" di puntata (es. max 10€, 20€, 50€). Il parser interno analizzerà i campi di testo del JSON catturato.
* Ricerca tramite Espressioni Regolari (Regex) di pattern come `"Puntata di €10: vincita di €22"`.
* Estrazione del valore numerico intero (es. `10.00`) per passarlo al Modulo Matematico che lo userà come tetto massimo per il Criterio di Kelly.

### 3.3 Fallback Visivo di Emergenza (OCR)
Qualora Bet365 dovesse offuscare o crittografare i payload JSON di rete (es. payload cifrati e decodificati via JavaScript protetto):
* Lo script isolerà il container grafico della Superquota e scatterà uno screenshot locale.
* Utilizzerà la libreria Python `pytesseract` (Optical Character Recognition) per leggere i testi direttamente dall'immagine grezza, estraendo la quota vecchia, la quota nuova e il nome della partita in totale indipendenza dal codice della pagina.

## 4. Sharp Book Ingestion (Cost-Zero API)
L'acquisizione delle quote reali (Fair Odds) necessarie per il calcolo del Valore Atteso.

### 4.1 Betfair Exchange (Il Mercato Aperto)
* Utilizzo della libreria Python `httpx` (o `aiohttp` per chiamate asincrone).
* Lo script interrogherà direttamente gli endpoint JSON pubblici di Betfair (es. `https://ero.betfair.it/www/sports/exchange/readonly/v1/...`).
* Estrazione istantanea dei dati strutturati: Volumi abbinati, Quote Punta (Back) e Quote Banca (Lay).

### 4.2 Pinnacle (Il Bookmaker Sharp)
* Simulazione di traffico mobile per interrogare le "Guest API" (API interne non documentate) di Pinnacle in sola lettura.
* Estrazione delle quote del mercato principale (1X2, U/O) e dei mercati Player Props.

### 4.3 Gestione del Rate Limiting (Polite Scraping)
Essendo interrogazioni continue e gratuite, il rischio è ricevere errori HTTP 429 (Too Many Requests).
* **Exponential Backoff:** Implementazione della libreria Python `tenacity`.
* **Logica:** In caso di errore 429, lo script non crasherà. Attenderà 2 secondi prima del primo riavvio, 4 secondi per il secondo, 8 secondi per il terzo, imitando una "coda" di richieste educata che non allarma i firewall difensivi.

## 5. Output del Modulo (Standardizzazione)
Indipendentemente dalla fonte, il modulo normalizzerà i dati estratti in un dizionario Python standard (o data class) che verrà passato ai moduli successivi (Database e Math Engine).
Formato atteso:
```json
{
  "source": "Bet365",
  "match_string": "Sassuolo v Verona",
  "selection_string": "DOMENICO BERARDI/SOSTITUTO - SI",
  "old_odd": 1.72,
  "new_odd": 2.20,
  "max_stake_cap": 10.00,
  "timestamp": "2026-02-21T10:00:00Z"
}
