import math

class Calculator:
    @staticmethod
    def devig_multiplicative(odds: list[float]) -> list[float]:
        """
        Removes the margin (vig) using the Multiplicative Method.
        Returns the real, implied probabilities.
        """
        implied_probs = [1.0 / o for o in odds]
        total_implied = sum(implied_probs)
        real_probs = [p / total_implied for p in implied_probs]
        return real_probs
    
    @staticmethod
    def get_fair_odd(odds: list[float], selection_index: int) -> float:
        """
        Calculates the Fair Odd for a specific selection after de-vigging.
        """
        real_probs = Calculator.devig_multiplicative(odds)
        return 1.0 / real_probs[selection_index]

    @staticmethod
    def calculate_ev(promo_odd: float, fair_odd: float) -> float:
        """
        Calculates the Expected Value percentage.
        Formula: (promo_odd / fair_odd) - 1
        """
        return (promo_odd / fair_odd) - 1.0

    @staticmethod
    def round_stake(stake: float) -> float:
        """
        Rounds the stake to the nearest multiple of 5 or 10.
        OpSec protocol: human operators don't bet decimal stakes.
        """
        if stake <= 0:
            return 0.0
        # Rounding to nearest 5
        return round(stake / 5.0) * 5.0

    @staticmethod
    def apply_kelly_criterion(
        promo_odd: float, 
        fair_odd: float, 
        bankroll: float, 
        promo_cap: float = 10.0,
        fractional_multiplier: float = 0.25
    ) -> float:
        """
        Calculates the stake size using the Fractional Kelly Criterion.
        Always capped by the promotional limit, and rounded for OpSec.
        """
        p = 1.0 / fair_odd
        b = promo_odd
        
        # Kelly Formula = (p * (b - 1) - (1 - p)) / (b - 1)
        f = (p * (b - 1) - (1 - p)) / (b - 1)
        
        if f <= 0:
            return 0.0 # -EV bet or 0 bankroll
        
        # Apply fractional multiplier for risk mitigation
        f_adj = f * fractional_multiplier
        
        suggested_stake = bankroll * f_adj
        
        # Apply promotional cap limit
        capped_stake = min(suggested_stake, promo_cap)
        
        # Round to nearest 5/10 for OpSec
        final_stake = Calculator.round_stake(capped_stake)
        
        # Ensuring we don't round 2 up to 5 and overbet a promo cap of 2, 
        # but realistically, value bets have caps of 10-50.
        if final_stake > promo_cap:
             # Drop to the lower multiple of 5
             final_stake = (final_stake - 5) if final_stake - 5 > 0 else promo_cap
        
        return float(final_stake)

    @staticmethod
    def calculate_lay_stake(back_stake: float, back_odd: float, lay_odd: float, commission: float = 0.05) -> float:
        """
        Calculates the exact amount to Lay on the Exchange to cover a Mug Bet.
        Formula: (back_stake * back_odd) / (lay_odd - commission)
        """
        return (back_stake * back_odd) / (lay_odd - commission)
    
    @staticmethod
    def evaluate_mug_loss(back_stake: float, lay_stake: float, commission: float = 0.05, max_loss_perc: float = 0.05) -> tuple[bool, float]:
        """
        Evaluates if the Qualifying loss is acceptable (< 5% of back stake).
        """
        loss = (lay_stake * (1 - commission)) - back_stake
        loss_perc = abs(loss) / back_stake if loss < 0 else 0
        
        # If loss is actually a profit (arb), it's obviously acceptable
        if loss > 0:
            return True, float(loss)
            
        is_acceptable = loss_perc <= max_loss_perc
        return is_acceptable, float(loss)
