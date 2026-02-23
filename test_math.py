import logging
from engine.calculator import Calculator
from engine.matcher import EntityMatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_calculator():
    logger.info("--- Testing Calculator ---")
    # Example 1: Devigging
    sharp_odds = [1.95, 3.50, 4.20] # 1X2
    real_probs = Calculator.devig_multiplicative(sharp_odds)
    logger.info(f"Sharp Odds: {sharp_odds} -> Real Probs: {[round(p, 4) for p in real_probs]}")
    logger.info(f"Sum of probs: {sum(real_probs)}")

    # Example 2: EV Calculation
    fair_odd = Calculator.get_fair_odd(sharp_odds, 0) # Home Win
    promo_odd = 2.40 # Bet365 Boosted Odd
    ev = Calculator.calculate_ev(promo_odd, fair_odd)
    logger.info(f"Promo Odd: {promo_odd}, Fair Odd: {fair_odd:.2f} -> EV: {ev*100:.2f}%")

    # Example 3: Kelly Sizing
    bankroll = 1000.0
    suggested_stake = Calculator.apply_kelly_criterion(promo_odd, fair_odd, bankroll, promo_cap=15.0)
    logger.info(f"Kelly Stake (Capped at 15): {suggested_stake}")

    # Example 4: Lay Stake
    back_stake = 10.0
    back_odd = 2.00
    lay_odd = 2.05
    lay_stake = Calculator.calculate_lay_stake(back_stake, back_odd, lay_odd)
    acceptable, loss = Calculator.evaluate_mug_loss(back_stake, lay_stake)
    logger.info(f"Lay Stake for 10@2.00 (Lay@2.05): {lay_stake:.2f} -> Loss: {loss:.2f} (Acceptable: {acceptable})")

def test_matcher():
    logger.info("\n--- Testing Entity Matcher ---")
    matcher = EntityMatcher()
    
    pairs = [
        ("Sassuolo v Verona", "US Sassuolo - Hellas Verona"),
        ("Sassuolo v Verona", "Juventus - Torino"),
        ("Domenico Berardi", "D. Berardi")
    ]
    
    for soft, sharp in pairs:
        is_perfect, needs_review, score = matcher.evaluate_match(soft, sharp)
        logger.info(f"'{soft}' vs '{sharp}' -> Score: {score:.1f} | Perfect: {is_perfect} | Review: {needs_review}")

if __name__ == "__main__":
    test_calculator()
    test_matcher()
