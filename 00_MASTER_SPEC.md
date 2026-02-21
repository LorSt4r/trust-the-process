# 00_MASTER_SPEC: Infrastruttura Ibrida per Value Betting & Superquote

## 1. Panoramica Architetturale (Il Paradigma "Cyborg")
Il sistema abbandona l'automazione totale web-based (ad altissimo rischio di blocco algoritmico) in favore di un'architettura ibrida Bot-Umano. 
* **Il Bot (Oracolo Quantitativo):** Si occupa esclusivamente del lavoro ad alta frequenza e complessità: intercettazione invisibile dei dati, allineamento semantico delle partite, calcolo delle probabilità reali (De-vigging) e dimensionamento del rischio (Kelly Criterion).
* **L'Umano (Esecutore OpSec):** Agisce come scudo per la Sicurezza Operativa (OpSec). Riceve i segnali matematicamente perfetti via Telegram e piazza materialmente le scommesse tramite il proprio smartphone (app ufficiale su rete dati), rendendo l'account indistinguibile da quello di un utente legittimo.

## 2. Stack Tecnologico
L'infrastruttura è progettata per minimizzare i costi di gestione azzerando l'uso di API a pagamento o browser Antidetect commerciali.
* **Core Logic:** Python 3.10+
* **Automazione & Rete:** `playwright` (Network Interception in sola lettura), `httpx` (Richieste API asincrone), `tenacity` (Exponential Backoff).
* **Intelligenza & NLP:** `RapidFuzz` (Fuzzy String Matching per la risoluzione dei nomi).
* **Persistenza Dati:** PostgreSQL (Architettura relazionale a stati).
* **Frontend / UI:** API Telegram (Bot per invio alert bidirezionali e ricezione comandi di aggiornamento DB).

## 3. Struttura dei Moduli
Il codice sorgente e la logica di business sono rigorosamente divisi in 4 moduli isolati:

### Modulo 1: `01_DATA_INGESTION.md`
Responsabile dell'acquisizione dei dati in tempo reale a costo zero. Intercetta i JSON di Bet365 catturando il traffico di rete (senza fare login) e interroga le API pubbliche degli Sharp Books (Pinnacle, Betfair Exchange) per estrarre le quote di mercato.

### Modulo 2: `02_DATABASE.md`
La "Single Source of Truth" del sistema. Struttura relazionale in PostgreSQL che storicizza eventi, operazioni, bankroll virtuale e implementa una *State Machine*. Le operazioni nascono in stato `PENDING` e passano a `PIAZZATA` solo previa conferma umana.

### Modulo 3: `03_MATH_ENGINE_&_MAPPING.md`
Il cervello algoritmico. Traduce le stringhe eterogenee dei bookmaker accoppiando gli eventi tramite distanza di Levenshtein (NLP). Una volta allineati i mercati, rimuove l'aggio (De-Vigging), calcola l'Expected Value (+EV), applica il Fractional Kelly per lo stake e fornisce i calcoli di copertura per le Mug Bets.

### Modulo 4: `04_HUMAN_OPSEC_PROTOCOLS.md`
Il manuale operativo di evasione. Definisce come l'operatore deve interagire con il bookmaker (es. uso esclusivo di smartphone 4G/5G, arrotondamento degli importi calcolati a multipli di 5€) e come comunicare con il bot Telegram per aggiornare gli stati del Database o mantenere alto il Trust Score dell'account.

## 4. Flusso Operativo (Workflow End-to-End)
1. **Scansione:** Il Modulo 01 intercetta l'uscita di una Superquota (es. Berardi a 2.20, Max 10€) e recupera le quote dell'Exchange.
2. **Elaborazione:** Il Modulo 03 allinea i nomi, calcola la Fair Odd (es. 1.85), verifica che l'EV sia positivo e stabilisce lo stake (10€).
3. **Storicizzazione:** Il Modulo 02 registra l'operazione in stato `PENDING`.
4. **Notifica:** Il bot Telegram invia l'alert all'operatore.
5. **Esecuzione:** L'operatore (Modulo 04) piazza i 10€ dall'app del telefono.
6. **Conferma:** L'operatore risponde `/piazzata 10` su Telegram; il DB si aggiorna, storicizzando il profitto atteso e chiudendo il loop.
7. 
