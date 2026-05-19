# subscription.py
import logging
logger = logging.getLogger(__name__)
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from database import Assinatura, SessionLocal

def criar_assinatura(user_id: int, duracao_dias: int = 30, payment_id: str = None) -> bool:
    db = SessionLocal()
    try:
        # Remove assinatura anterior se existir
        db.query(Assinatura).filter(Assinatura.user_id == user_id).delete()
        nova = Assinatura(
            user_id=user_id,
            status="ativa",
            plano="premium",
            data_inicio=datetime.now(timezone.utc),
            data_fim=datetime.now(timezone.utc) + timedelta(days=duracao_dias),
            payment_id=payment_id
        )
        db.add(nova)
        db.commit()
        return True
    except Exception as e:
        print(f"Erro ao criar assinatura: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def assinatura_ativa(user_id: int) -> bool:
    db = SessionLocal()
    try:
        ass = db.query(Assinatura).filter(
            Assinatura.user_id == user_id,
            Assinatura.status == "ativa",
            Assinatura.data_fim > datetime.now(timezone.utc)
        ).first()
        return ass is not None
    finally:
        db.close()

def cancelar_assinatura(user_id: int) -> bool:
    db = SessionLocal()
    try:
        ass = db.query(Assinatura).filter(Assinatura.user_id == user_id).first()
        if ass:
            ass.status = "cancelada"
            db.commit()
            return True
        return False
    finally:
        db.close()
def criar_assinatura(user_id: int, duracao_dias: int = 30, payment_id: str = None) -> bool:
    logger.info(f"📝 Criando assinatura para user {user_id}, {duracao_dias} dias")
    
    db = SessionLocal()
    try:
        # Remove assinatura anterior se existir
        removidas = db.query(Assinatura).filter(Assinatura.user_id == user_id).delete()
        if removidas:
            logger.info(f"Removidas {removidas} assinaturas anteriores para user {user_id}")
        
        agora = datetime.now(timezone.utc)
        nova = Assinatura(
            user_id=user_id,
            status="ativa",
            plano="premium",
            data_inicio=agora,
            data_fim=agora + timedelta(days=duracao_dias),
            payment_id=payment_id
        )
        db.add(nova)
        db.commit()
        logger.info(f"✅ Assinatura premium criada para user {user_id} até {nova.data_fim}")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao criar assinatura: {e}")
        db.rollback()
        return False
    finally:
        db.close()
