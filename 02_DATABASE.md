# 02_DATABASE: Architettura Relazionale e State Machine

## 1. Obiettivo del Modulo
Creare la "Single Source of Truth" (Unica Fonte di Verità) del sistema in PostgreSQL. Il database deve storicizzare gli eventi sportivi, le operazioni matematiche (+EV e -EV), il dizionario di allineamento delle entità (Auto-Apprendimento) e gestire lo stato delle operazioni in attesa di conferma umana tramite Telegram.

## 2. Standard e Convenzioni
Per garantire precisione matematica nei calcoli finanziari a lungo termine:
* **Valute e Importi:** Esclusivamente `NUMERIC(10,2)` (es. `15.50`). Mai usare `FLOAT` per evitare errori di arrotondamento in virgola mobile.
* **Quote (Odds):** Esclusivamente `NUMERIC(8,3)` (es. `2.200`).
* **Date e Fusi Orari:** Esclusivamente `TIMESTAMPTZ` (Timestamp with Time Zone) per allineare correttamente i fischio d'inizio tra bookmaker che operano su server internazionali.
* **Chiavi Primarie:** Utilizzo di `UUID` v4 generati nativamente da Postgres per garantire unicità assoluta anche in scenari di ricalcolo o importazione dati.

## 3. Schema Relazionale (Tabelle Core)

### 3.1 T_Stato_Account (Il Bankroll Virtuale)
Traccia l'andamento finanziario e il livello di allarme dell'algoritmo di profilazione.
* `id_account` (UUID, PK)
* `nome_operatore` (VARCHAR) - Identificativo utente Telegram.
* `bankroll_iniziale` (NUMERIC)
* `bankroll_corrente` (NUMERIC) - Aggiornato dinamicamente alla chiusura delle scommesse.
* `trust_score` (INTEGER) - Punteggio da 0 a 100. Diminuisce ad ogni Value Bet, aumenta ad ogni Mug Bet.

### 3.2 T_Eventi_Sportivi
L'anagrafica centralizzata delle partite.
* `id_evento` (UUID, PK)
* `data_inizio` (TIMESTAMPTZ)
* `sport` (VARCHAR)
* `competizione` (VARCHAR)
* `squadra_casa` (VARCHAR)
* `squadra_trasferta` (VARCHAR)

### 3.3 T_Value_Betting (Le Superquote)
Registra le inefficienze scoperte e il loro ciclo di vita ibrido.
* `id_vb` (UUID, PK)
* `id_evento` (UUID, FK -> T_Eventi_Sportivi)
* `selezione_bet365` (VARCHAR) - Es. "Berardi/Sostituto Segna"
* `quota_giocata` (NUMERIC) - La Superquota.
* `fair_odd_calcolata` (NUMERIC) - Quota reale post-devigging.
* `expected_value_perc` (NUMERIC) - Es. +18.5%.
* `stake_suggerito` (NUMERIC) - Calcolato dal Kelly Criterion.
* `stake_effettivo` (NUMERIC) - Quanto l'operatore umano ha realmente puntato.
* `stato_operazione` (ENUM) - `PENDING` (In attesa su Telegram), `PIAZZATA` (Confermata dall'umano), `SCARTATA` (Ignorata), `VINCENTE`, `PERDENTE`.
* `timestamp_alert` (TIMESTAMPTZ)

### 3.4 T_Mug_Bets (Account Warming & OpSec)
Storicizza i costi sostenuti per il mantenimento dell'account o le operazioni tattiche (2UP).
* `id_mug` (UUID, PK)
* `id_evento` (UUID, FK -> T_Eventi_Sportivi)
* `tipo_giocata` (ENUM) - `MULTIPLA_CASUALE`, `MATCHED_BET_2UP`.
* `costo_qualificante` (NUMERIC) - La perdita matematica calcolata per la copertura (es. 0.40€).
* `stato_operazione` (ENUM) - `PENDING`, `PIAZZATA`, `ATTESA_2UP` (In attesa che la squadra vada in vantaggio di 2 gol), `CHIUSA`.

### 3.5 T_Mapping_Nomi (Auto-Apprendimento NLP)
Il dizionario che rende il bot intelligente ad ogni esecuzione, salvando l'allineamento tra i database dei vari bookmaker.
* `id_mapping` (UUID, PK)
* `tipo_entita` (ENUM) - `SQUADRA`, `GIOCATORE`.
* `stringa_soft_book` (VARCHAR) - Es. "Sassuolo v Verona" (Bet365).
* `stringa_sharp_book` (VARCHAR) - Es. "Hellas Verona - US Sassuolo" (Pinnacle/Betfair).
* `score_fuzz_originale` (INTEGER) - Il punteggio generato da RapidFuzz prima della conferma umana.
* `confermato_da_umano` (BOOLEAN) - True se l'operatore ha validato l'associazione via Telegram.

## 4. Logica di Interazione Telegram (State Transitions)
Il Database non muta mai il bankroll o gli stati senza un trigger esplicito:
1. Il modulo *Ingestion* inserisce un record in `T_Value_Betting` con stato `PENDING`.
2. Il bot Telegram legge il record `PENDING` e invia il messaggio all'utente.
3. L'utente risponde `/piazzata 10` all'alert.
4. Il backend esegue un `UPDATE` sul record portandolo a `PIAZZATA`, imposta lo `stake_effettivo` a 10 e ricalcola il `bankroll_corrente` in `T_Stato_Account`.
