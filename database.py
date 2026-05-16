# database.py
import os
import logging
logger = logging.getLogger(__name__)
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

DATABASE_URL = os.getenv("DATABASE_URL")  # Ex: postgresql://postgres:IMdjzlVgUNOWXKVWGrHPlJXVroOJdwXx@postgres.railway.internal:5432/railway
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não definida. Adicione no Railway.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Assinatura(Base):
    __tablename__ = "assinaturas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False)
    status = Column(String, default="ativa")  # ativa, expirada, cancelada
    plano = Column(String, default="premium") # basico, premium
    data_inicio = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    data_fim = Column(DateTime, nullable=False)
    payment_id = Column(String, nullable=True)  # id da transação no MP
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
