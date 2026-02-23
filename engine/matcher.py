import logging
from rapidfuzz import process, fuzz
from sqlalchemy import select
from db.database import async_session_maker
from db.models import NameMapping, EntityType

logger = logging.getLogger(__name__)

class EntityMatcher:
    def __init__(self):
        self.high_confidence_threshold = 85.0
        self.review_threshold = 60.0 # Lowered slightly to catch more edge cases
        
        self.abbreviations = {
            "man ": "manchester ",
            "utd": "united",
            "fc": "",
            "cf": "",
            "ac ": "",
            "inter ": "internazionale "
        }

    def expand_abbreviations(self, name: str) -> str:
        """Expands common betting abbreviations to improve fuzz scores."""
        name_lower = f" {name.lower()} " # Pad for whole word replacement
        for abbr, expansion in self.abbreviations.items():
            name_lower = name_lower.replace(f" {abbr}", f" {expansion}")
        return name_lower.strip()
        
    async def get_db_mapping(self, soft_name: str, entity_type: EntityType) -> str | None:
        """Finds if a human-confirmed mapping already exists in the database."""
        async with async_session_maker() as session:
            stmt = select(NameMapping).where(
                NameMapping.stringa_soft_book == soft_name,
                NameMapping.tipo_entita == entity_type,
                NameMapping.confermato_da_umano == True
            )
            result = await session.execute(stmt)
            mapping = result.scalar_one_or_none()
            if mapping:
                return mapping.stringa_sharp_book
        return None

    async def save_db_mapping(self, soft_name: str, sharp_name: str, score: float, entity_type: EntityType, confirmed: bool = False):
        """Saves a new mapping to the database for future lookups."""
        async with async_session_maker() as session:
            # Check if it already exists to avoid duplicates
            stmt = select(NameMapping).where(
                NameMapping.stringa_soft_book == soft_name,
                NameMapping.stringa_sharp_book == sharp_name,
                NameMapping.tipo_entita == entity_type
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if not existing:
                new_mapping = NameMapping(
                    tipo_entita=entity_type,
                    stringa_soft_book=soft_name,
                    stringa_sharp_book=sharp_name,
                    score_fuzz_originale=int(score),
                    confermato_da_umano=confirmed
                )
                session.add(new_mapping)
                await session.commit()
                logger.debug(f"Saved DB Mapping: {soft_name} -> {sharp_name} (Score: {score})")

    async def match_entity(self, soft_name: str, sharp_names: list[str], entity_type: EntityType = EntityType.SQUADRA) -> tuple[str | None, float, bool]:
        """
        Attempts to match a Soft Book name (e.g. Bet365 'Man City') to a list of Sharp Book names.
        Returns: (Matched Name, Score, RequiresHumanReview)
        """
        # 1. Check if we already have a confirmed mapping in the DB
        mapped_name = await self.get_db_mapping(soft_name, entity_type)
        if mapped_name and mapped_name in sharp_names:
            logger.info(f"DB Mapping Hit: {soft_name} -> {mapped_name}")
            return mapped_name, 100.0, False

        # 2. Run NLP Fuzzy Matching
        if not sharp_names:
            return None, 0.0, False
            
        soft_expanded = self.expand_abbreviations(soft_name)
        sharp_expanded = {sharp: self.expand_abbreviations(sharp) for sharp in sharp_names}
        
        # We use Token Sort Ratio because "City Manchester" and "Manchester City" should match
        # We compare the expanded soft name against the expanded sharp names
        best_match_key = process.extractOne(
            soft_expanded, 
            list(sharp_expanded.values()), 
            scorer=fuzz.token_sort_ratio
        )
        
        if not best_match_key:
            return None, 0.0, False
            
        _, score, match_index = best_match_key
        # Retrieve original sharp name using the index
        sharp_name = sharp_names[match_index]
        
        # 3. Evaluate Thresholds
        if score >= self.high_confidence_threshold:
            # High Confidence: Auto-accept and save to DB
            logger.info(f"High Confidence Match [{score:.1f}%]: {soft_name} -> {sharp_name}")
            await self.save_db_mapping(soft_name, sharp_name, score, entity_type, confirmed=True)
            return sharp_name, score, False
            
        elif score >= self.review_threshold:
            # Uncertain Match: Requires Human Review (e.g., via Telegram inline keyboard)
            logger.warning(f"Uncertain Match [{score:.1f}%]: {soft_name} -> {sharp_name}. Requires Human Review.")
            await self.save_db_mapping(soft_name, sharp_name, score, entity_type, confirmed=False)
            return sharp_name, score, True
            
        else:
            # Low Confidence: Reject
            logger.info(f"Rejected Match [{score:.1f}%]: {soft_name} -> {sharp_name}")
            return None, score, False
