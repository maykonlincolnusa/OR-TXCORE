"""Integration coverage against PostgreSQL only (never SQLite)."""
import os
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from app.core.db import Base
from app.core.errors import DomainError
from app.payments import models  # noqa: F401
from app.payments.models import Account, LedgerEntry, OutboxEvent, Payment
from app.payments.service import PaymentService

pytestmark = pytest.mark.integration

@pytest.fixture
def session():
    if not os.getenv("TEST_DATABASE_URL"):
        pytest.skip("requires PostgreSQL TEST_DATABASE_URL")
    engine = create_engine(os.environ["TEST_DATABASE_URL"])
    Base.metadata.drop_all(engine); Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as db:
        source, target = Account(currency="BRL", available_balance_minor=200), Account(currency="BRL")
        db.add_all([source, target]); db.commit()
        yield db, str(source.id), str(target.id)

def payload(source, target, amount=100):
    return {"source_account_id": source, "destination_account_id": target, "amount_minor": amount, "currency": "BRL"}

def test_idempotency_and_ledger_balance(session):
    db, source, target = session
    first = PaymentService().transfer(db, payload(source, target), "same"); db.commit()
    repeated = PaymentService().transfer(db, payload(source, target), "same"); db.commit()
    assert first.id == repeated.id and repeated.status == "POSTED"
    entries = db.scalars(select(LedgerEntry).join(models.LedgerJournal).where(models.LedgerJournal.payment_id == first.id)).all()
    assert sum(e.amount_minor for e in entries if e.direction == "DEBIT") == sum(e.amount_minor for e in entries if e.direction == "CREDIT") == 100

def test_reused_key_different_payload_rejected(session):
    db, source, target = session
    PaymentService().transfer(db, payload(source, target, 100), "same"); db.commit()
    with pytest.raises(DomainError, match="different payload"):
        PaymentService().transfer(db, payload(source, target, 101), "same")
    db.rollback()

def test_insufficient_review_and_deny_never_create_ledger(session, monkeypatch):
    db, source, target = session
    assert PaymentService().transfer(db, payload(source, target, 201), "no-funds").status == "FAILED"; db.commit()
    from app.core.config import settings
    monkeypatch.setattr(settings, "fraud_review_amount_minor", 50)
    monkeypatch.setattr(settings, "fraud_deny_amount_minor", 150)
    assert PaymentService().transfer(db, payload(source, target, 60), "review").status == "PENDING"; db.commit()
    assert PaymentService().transfer(db, payload(source, target, 150), "deny").status == "DENY"; db.commit()
    assert db.scalar(select(LedgerEntry).join(models.LedgerJournal)) is None

def test_rollback_leaves_no_outbox_or_payment(session):
    db, source, target = session
    PaymentService().transfer(db, payload(source, target), "rollback")
    db.rollback()
    assert db.scalar(select(Payment)) is None
    assert db.scalar(select(OutboxEvent)) is None
