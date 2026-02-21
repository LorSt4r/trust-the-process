# 04_HUMAN_OPSEC_PROTOCOLS: Esecuzione, Comando e Mimetismo

## 1. Obiettivo del Modulo
Definire le "Regole d'Ingaggio" inderogabili per l'operatore umano e per il bot Telegram. Lo scopo è forzare l'algoritmo di profilazione del bookmaker (Bet365) a classificare l'account come "Square/Recreational Punter" (Giocatore Amatoriale), neutralizzando il rischio di Gubbing (limitazione dell'account o esclusione dalle promozioni).

## 2. Regole di Esecuzione (Isolamento Hardware/Rete)
L'esecuzione materiale della scommessa delega la responsabilità dell'OpSec (Operational Security) al dispositivo dell'operatore, aggirando i controlli antibot del browser.
* **Divieto Assoluto di Wi-Fi:** Non aprire mai l'app di Bet365 collegato alla rete Wi-Fi di casa, specialmente se lo script di scraping gira sulla stessa rete. L'IP deve essere sempre disaccoppiato.
* **Rete Mobile (CGNAT):** Le scommesse devono essere piazzate **esclusivamente** tramite smartphone utilizzando la rete dati cellulare 4G/5G.
* **App Ufficiale:** Utilizzare sempre l'applicazione ufficiale iOS/Android di Bet365. L'app invia telemetria "pulita" (es. dati del giroscopio, tocchi capacitivi dello schermo) che garantisce un Trust Score hardware massimo, impossibile da replicare per uno script.

## 3. Stake Masking (Offuscamento Finanziario)
L'algoritmo di Bet365 flagga istantaneamente gli account che puntano cifre decimali non tonde o importi che variano costantemente in modo matematico.
* **Regola di Arrotondamento Rigida:** Il Bot arrotonderà *sempre* il suggerimento del Kelly Criterion al multiplo intero di 5€ o 10€ più vicino (es. un calcolo di 13,80€ diventerà un alert Telegram per 15€). L'operatore **non deve mai** inserire centesimi nel carrello.
* **Cap Promozionale:** Le Superquote hanno limiti noti (es. 10€ o 20€). Raggiungere esattamente il cap è un comportamento normale e non desta sospetti.

## 4. Gestione del Trust Score (Account Warming)
Il bot monitorerà il rapporto tra le scommesse di valore estratte (Superquote) e le scommesse "spazzatura" o di copertura (Mug Bets).
* **Alert di De-Profilazione:** Se il rapporto scende sotto la soglia di sicurezza (es. 3 Superquote piazzate senza nessuna giocata normale), il bot invierà un alert: `⚠️ RICHIESTA MUG BET: Piazza 10€ sulla Serie A entro oggi.`
* **Esecuzione Mug Bet (Matched Betting):** L'operatore piazzerà la Mug Bet su eventi mainstream (es. 1X2 Champions League o Serie A) e la coprirà sull'Exchange utilizzando gli importi forniti dal calcolatore del Modulo 03, accettando la perdita qualificante (Qualifying Loss) di pochi centesimi come "costo aziendale".
* **Focus 2UP:** Le Mug Bets verranno preferibilmente indirizzate verso eventi validi per l'offerta "Pagamento Anticipato 2UP" per massimizzare il ritorno atteso (Double Win).

## 5. Interfaccia di Comando (Telegram Bot)
Il bot Telegram funge da Centro di Comando e gestisce lo stato del Database (Modulo 02) tramite comandi impartiti dall'operatore.
* **Ricezione Alert:** Il bot invia la notifica: `[SUPERQUOTA] Berardi a 2.20 | EV: +15% | Punta: 10€`. Lo stato nel DB è `PENDING`.
* **Comando `/piazzata [importo]`:** L'operatore conferma l'avvenuta scommessa (es. `/piazzata 10`). Il DB passa a `PIAZZATA` e aggiorna il bankroll virtuale.
* **Comando `/scartata`:** Se la quota è scesa o l'operatore non ha fatto in tempo, il DB registra l'opportunità mancata per le statistiche.
* **Comando `/mug [importo]`:** L'operatore notifica al bot di aver effettuato un'operazione di mascheramento, resettando il livello di allarme del Trust Score.
* **Comando `/status`:** Il bot restituisce un cruscotto istantaneo: Bankroll Attuale, EV generato nel mese, Stato di salute dell'account.

## 6. Protocollo di Prelievo (Withdrawal OpSec)
I prelievi innescano spesso revisioni manuali (Manual Review) da parte del team antifrode del bookmaker.
* **Regola del Timing:** Non prelevare mai immediatamente dopo una grossa vincita o dopo aver completato una Superquota.
* **Regola del Saldo Naturale:** Lasciare sempre una percentuale di fondi sul conto (es. non prelevare 150€ se il saldo è 152€). Prelevare cifre tonde (es. 100€) lasciando il resto per continuare l'operatività.
* 
