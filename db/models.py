import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Numeric, Enum, ForeignKey, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class OpsState(enum.Enum):
    PENDING = "PENDING"
    PIAZZATA = "PIAZZATA"
    SCARTATA = "SCARTATA"
    VINCENTE = "VINCENTE"
    PERDENTE = "PERDENTE"

class MugState(enum.Enum):
    PENDING = "PENDING"
    PIAZZATA = "PIAZZATA"
    ATTESA_2UP = "ATTESA_2UP"
    CHIUSA = "CHIUSA"

class MugType(enum.Enum):
    MULTIPLA_CASUALE = "MULTIPLA_CASUALE"
    MATCHED_BET_2UP = "MATCHED_BET_2UP"

class EntityType(enum.Enum):
    SQUADRA = "SQUADRA"
    GIOCATORE = "GIOCATORE"

class AccountState(Base):
    __tablename__ = 't_stato_account'
    
    id_account = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome_operatore = Column(String, nullable=False)
    bankroll_iniziale = Column(Numeric(10, 2), nullable=False)
    bankroll_corrente = Column(Numeric(10, 2), nullable=False)
    trust_score = Column(Integer, default=100)

class SportEvent(Base):
    __tablename__ = 't_eventi_sportivi'
    
    id_evento = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data_inizio = Column(DateTime(timezone=True), nullable=False)
    sport = Column(String, nullable=False)
    competizione = Column(String, nullable=False)
    squadra_casa = Column(String, nullable=False)
    squadra_trasferta = Column(String, nullable=False)

class ValueBetting(Base):
    __tablename__ = 't_value_betting'
    
    id_vb = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_evento = Column(UUID(as_uuid=True), ForeignKey('t_eventi_sportivi.id_evento'), nullable=False)
    selezione_bet365 = Column(String, nullable=False)
    dettaglio = Column(String, nullable=True)
    mercato = Column(String, nullable=True)
    quota_normale = Column(Numeric(8, 3), nullable=True)
    quota_giocata = Column(Numeric(8, 3), nullable=False)
    fair_odd_calcolata = Column(Numeric(8, 3), nullable=False)
    expected_value_perc = Column(Numeric(8, 3), nullable=False)
    stake_suggerito = Column(Numeric(10, 2), nullable=False)
    stake_effettivo = Column(Numeric(10, 2), nullable=True)
    stato_operazione = Column(Enum(OpsState), default=OpsState.PENDING, nullable=False)
    timestamp_alert = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    evento = relationship("SportEvent")

class MugBet(Base):
    __tablename__ = 't_mug_bets'
    
    id_mug = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_evento = Column(UUID(as_uuid=True), ForeignKey('t_eventi_sportivi.id_evento'), nullable=False)
    tipo_giocata = Column(Enum(MugType), nullable=False)
    costo_qualificante = Column(Numeric(10, 2), nullable=False)
    stato_operazione = Column(Enum(MugState), default=MugState.PENDING, nullable=False)
    
    evento = relationship("SportEvent")

class NameMapping(Base):
    __tablename__ = 't_mapping_nomi'
    
    id_mapping = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo_entita = Column(Enum(EntityType), nullable=False)
    stringa_soft_book = Column(String, nullable=False)
    stringa_sharp_book = Column(String, nullable=False)
    score_fuzz_originale = Column(Integer, nullable=False)
    confermato_da_umano = Column(Boolean, default=False, nullable=False)
