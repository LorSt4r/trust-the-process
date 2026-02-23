import asyncio
import logging
from engine.matcher import EntityMatcher
from db.models import EntityType
from db.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_matcher():
    # Ensure DB is created for saving the mappings
    await init_db()
    
    matcher = EntityMatcher()
    
    sharp_list = [
        "Manchester City FC",
        "Aston Villa",
        "Real Madrid CF",
        "Bayern Munich",
        "Viktoria Plzen"
    ]
    
    test_cases = [
        ("Man City", sharp_list),           # Should match Manchester City FC
        ("Real Madrid", sharp_list),        # Should match Real Madrid CF
        ("Viktoria P.", sharp_list),        # Edge case
        ("Random Team", sharp_list),        # Should fail
        ("Bayern Munchen", sharp_list)      # Spelling difference
    ]
    
    for soft_name, sharps in test_cases:
        print(f"\n--- Testing: '{soft_name}' ---")
        match, score, review = await matcher.match_entity(soft_name, sharps, EntityType.SQUADRA)
        if match:
             if review:
                 print(f"⚠️ UNCERTAIN: '{soft_name}' matched to '{match}' with score {score:.1f}% (Review needed)")
             else:
                 print(f"✅ CONFIDENT: '{soft_name}' matched to '{match}' with score {score:.1f}%")
        else:
             print(f"❌ REJECTED: '{soft_name}' did not meet the 65% minimum threshold. Best score was {score:.1f}%")

if __name__ == "__main__":
    asyncio.run(test_matcher())
