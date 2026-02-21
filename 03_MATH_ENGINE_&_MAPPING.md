# 03_MATH_ENGINE_&_MAPPING: Il Cervello Quantitativo e NLP

## 1. Obiettivo del Modulo
Questo modulo riceve i dati grezzi estratti dall'Ingestion (Modulo 01), standardizza le nomenclature eterogenee tra i bookmaker tramite intelligenza linguistica (Fuzzy Matching) ed esegue i calcoli finanziari. Stabilisce il Valore Atteso (+EV), calcola lo stake ottimale per minimizzare il rischio di rovina (Kelly) e fornisce gli importi di copertura esatti per le scommesse tattiche (-EV).

## 2. Allineamento delle Entità (Fuzzy String Matching)
I bookmaker non usano mai gli stessi nomi per squadre e giocatori. Il sistema utilizza la libreria Python `RapidFuzz` (basata sulla Distanza di Levenshtein) per calcolare la probabilità matematica che due stringhe rappresentino la stessa entità.

### 2.1 Pipeline di Risoluzione
1. **Filtro Temporale:** Il bot isola dal palinsesto Sharp (es. Pinnacle) solo le partite che iniziano entro un delta di `+/- 2 ore` rispetto all'orario letto sulla Superquota (Bet365).
2. **Match Scoring:** Esecuzione di `RapidFuzz` sui nomi delle squadre (es. "Sassuolo v Verona" vs "Hellas Verona - US Sassuolo").
3. **Player Scoring:** Se il match supera il test, si ripete l'operazione sul nome del giocatore (es. "Domenico Berardi" vs "D. Berardi").

### 2.2 Soglie di Confidenza e Auto-Apprendimento
* **Score $\ge 85$:** Corrispondenza perfetta. Il bot procede autonomamente.
* **Score tra $65$ e $84$ (Zona Grigia):** Il bot si ferma e invia una notifica Telegram all'operatore: *"Allineamento incerto: Confermi che 'X' = 'Y'? [SI/NO]"*.
  * Se l'operatore preme [SI], l'associazione viene storicizzata nel Database (`T_Mapping_Nomi`). Alle esecuzioni successive, il bot interrogherà il DB aggirando il calcolo probabilistico (Auto-Apprendimento).
* **Score $< 65$:** Le entità non corrispondono. Operazione scartata.

## 3. Gestione Asimmetria Mercati (La Regola del "Sostituto")
Bet365 offre spesso mercati come "Giocatore/Sostituto Segna". Pinnacle quota solo "Giocatore Segna".
* **Regola di Haircut:** Se viene rilevata l'asimmetria del sostituto, la probabilità reale della Fair Odd calcolata dallo Sharp Book deve subire un "declassamento" (Haircut) proporzionale, per compensare il vantaggio matematico offerto da Bet365.
* **Filtro Void Risk:** Se le regole di mercato (es. scommessa valida anche se il giocatore non parte titolare) non sono equiparabili con certezza o l'Haircut non è quantificabile in sicurezza, l'operazione viene etichettata come `VOID_RISK` e scartata per proteggere il bankroll.

## 4. Matematica del Value Betting (Le Superquote)
Una volta allineate le entità, il motore calcola la convenienza finanziaria.

### 4.1 De-Vigging (Estrazione della Fair Odd)
Applicazione del Metodo Moltiplicativo per rimuovere l'aggio (Vig) del bookmaker Sharp e trovare la probabilità pura.
* Siano $P_1, P_2, \dots, P_n$ le probabilità implicite lorde ($1 / Quota$).
* Probabilità reale dell'evento $p_i = \frac{P_i}{\sum P_k}$.
* Quota Equa ($F_{odd}$) = $\frac{1}{p_i}$.

### 4.2 Expected Value (EV)
Rapporto tra la Superquota ($O_{promo}$) e la Quota Equa ($F_{odd}$).
* Formula: $EV_{perc} = \left( \frac{O_{promo}}{F_{odd}} \right) - 1$.
* **Soglia Operativa:** Vengono processate solo operazioni con $EV_{perc} > 0.02$ (+2%).

### 4.3 Sizing Dinamico (Fractional Kelly Criterion)
Calcolo dell'esposizione finanziaria ottimale.
* Formula Base: $f = \frac{p \times (b - 1) - (1 - p)}{b - 1}$
  *(Dove $p$ è la probabilità reale $1/F_{odd}$, e $b$ è la Superquota).*
* **Fractional Multiplier:** Si applica un fattore protettivo del 25% ($f_{adj} = f \times 0.25$) per assorbire la naturale varianza.
* **Stake Cap:** Lo stake finale suggerito è il minimo tra la percentuale di cassa dettata dal Kelly e il Limite Massimale della promozione estratto dall'Ingestion (es. 10€).

## 5. Calcolatore Matched Betting (OpSec e Tattica 2UP)
Modulo vitale per mascherare l'identità dell'account tramite scommesse "Mug" o tattiche avanzate, minimizzando le perdite.

### 5.1 Calcolo della Bancata (Lay Stake)
Il sistema fornisce l'esatto importo da bancare sull'Exchange per pareggiare il rischio tra Soft Book ($O_b$) ed Exchange ($O_l$), tenendo conto della commissione ($c$).
* Formula Lay Stake ($S_l$): $S_l = \frac{S_b \times O_b}{O_l - c}$

### 5.2 Controllo della Qualifying Loss
* Formula Costo: $Loss = (S_l \times (1 - c)) - S_b$.
* **Filtro di Tolleranza:** Se la perdita generata dalla copertura supera il **5%** dello stake iniziale ($S_b$), l'operazione viene annullata poiché il "premio assicurativo" per il bookmaker è troppo alto.

### 5.3 Implementazione 2UP (Early Payout)
Se la Mug Bet viene piazzata su una partita eleggibile per l'Early Payout, il bot marca lo stato nel Database come `POTENZIALE_2UP` e istruisce l'operatore a NON chiudere la bancata sull'Exchange qualora la squadra andasse in vantaggio di 2 gol, creando l'opportunità di "Double Win" (Vincita sia su Bet365 che su Betfair).
