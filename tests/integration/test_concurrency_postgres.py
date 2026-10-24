"""Requires a disposable PostgreSQL database; never use SQLite for locking tests.

Run with: TEST_DATABASE_URL=postgresql+psycopg://... pytest -m integration
The production test suite will create two independent sessions and assert that only
one debit posts when both requests contend for the same funded source account.
"""
import os
import threading
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from app.core.db import Base
from app.payments import models  # noqa: F401
from app.payments.models import Account, LedgerEntry, Payment
from app.payments.service import PaymentService

pytestmark = pytest.mark.integration

@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="requires PostgreSQL TEST_DATABASE_URL")
def test_only_one_contending_transfer_posts():
    """Two real database connections compete for one 100-unit balance."""
    engine = create_engine(os.environ["TEST_DATABASE_URL"], pool_size=5)
    Base.metadata.drop_all(engine); Base.metadata.create_all(engine)
    Session = sessionmaker(engine, expire_on_commit=False)
    with Session.begin() as db:
        source, first, second = Account(currency="BRL", available_balance_minor=100), Account(currency="BRL"), Account(currency="BRL")
        db.add_all([source, first, second]); db.flush()
        ids = str(source.id), str(first.id), str(second.id)
    barrier, statuses = threading.Barrier(2), []
    def submit(destination, key):
        with Session() as db:
            barrier.wait()
            payment = PaymentService().transfer(db, {"source_account_id": ids[0], "destination_account_id": destination,
                "amount_minor": 100, "currency": "BRL"}, key)
            db.commit(); statuses.append(payment.status)
    threads = [threading.Thread(target=submit, args=(ids[1], "one")), threading.Thread(target=submit, args=(ids[2], "two"))]
    [thread.start() for thread in threads]; [thread.join() for thread in threads]
    assert sorted(statuses) == ["FAILED", "POSTED"]
    with Session() as db:
        assert db.get(Account, ids[0]).available_balance_minor == 0
        posted = db.scalars(select(Payment).where(Payment.status == "POSTED")).one()
        entries = db.scalars(select(LedgerEntry).join(models.LedgerJournal).where(models.LedgerJournal.payment_id == posted.id)).all()
        assert sum(e.amount_minor for e in entries if e.direction == "DEBIT") == sum(e.amount_minor for e in entries if e.direction == "CREDIT")
