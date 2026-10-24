import hashlib
import json
from uuid import UUID, uuid4
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.errors import DomainError
from app.core.config import settings
from app.fraud.service import DeterministicFraudEngine, RiskDecision
from app.payments.models import (Account, AuditEvent, IdempotencyRecord, LedgerEntry, LedgerJournal,
                                 OutboxEvent, Payment, PaymentAttempt, RiskAssessment)
from app.shared.events import event_envelope


def request_digest(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class PaymentService:
    def __init__(self, fraud: object | None = None):
        self.fraud = fraud or DeterministicFraudEngine()

    def transfer(self, db: Session, request: dict, idempotency_key: str) -> Payment:
        digest = request_digest(request)
        # The unique key is durable; row locking serializes retries after it exists.
        record = db.scalar(select(IdempotencyRecord).where(IdempotencyRecord.scope == "transfer",
                           IdempotencyRecord.key == idempotency_key).with_for_update())
        if record:
            if record.request_hash != digest:
                raise DomainError("IDEMPOTENCY_KEY_REUSED", "key was used with a different payload", 409)
            if record.payment_id:
                return db.get(Payment, record.payment_id)
        else:
            record = IdempotencyRecord(scope="transfer", key=idempotency_key, request_hash=digest)
            db.add(record)
            try:
                db.flush()
            except IntegrityError:
                db.rollback()
                # Caller retries the entire transaction: another process won the unique insert.
                raise DomainError("IDEMPOTENCY_RACE", "retry request", 409)

        source_id, destination_id = UUID(request["source_account_id"]), UUID(request["destination_account_id"])
        if source_id == destination_id:
            raise DomainError("SAME_ACCOUNT", "source and destination must differ")
        # Stable lock order avoids lock-order deadlocks across reciprocal payments.
        ids = sorted([source_id, destination_id], key=str)
        accounts = {a.id: a for a in db.scalars(select(Account).where(Account.id.in_(ids)).order_by(Account.id).with_for_update())}
        source, destination = accounts.get(source_id), accounts.get(destination_id)
        if not source or not destination:
            raise DomainError("ACCOUNT_NOT_FOUND", "one or more accounts do not exist", 404)
        if source.currency != request["currency"] or destination.currency != request["currency"]:
            raise DomainError("CURRENCY_MISMATCH", "account and payment currency must match", 409)

        decision = self._assess(request["amount_minor"])
        payment = Payment(source_account_id=source_id, destination_account_id=destination_id,
                          amount_minor=request["amount_minor"], currency=request["currency"],
                          status="PENDING" if decision.decision == "REVIEW" else decision.decision,
                          risk_decision=decision.decision, correlation_id=uuid4())
        db.add(payment); db.flush()
        record.payment_id = payment.id; record.response_status = 201
        db.add(RiskAssessment(payment_id=payment.id, score=decision.score, decision=decision.decision,
                              reason_codes=decision.reason_codes))
        db.add(PaymentAttempt(payment_id=payment.id, outcome=decision.decision, reason=",".join(decision.reason_codes) or None))
        self._outbox(db, "payment.requested", payment, {"amount_minor": payment.amount_minor, "currency": payment.currency})
        self._outbox(db, "payment.risk_assessed", payment, {"score": decision.score, "decision": decision.decision})
        if decision.decision == "DENY":
            self._outbox(db, "payment.rejected", payment, {"reason_codes": decision.reason_codes})
            return payment
        if decision.decision == "REVIEW":
            return payment
        if source.available_balance_minor < payment.amount_minor:
            payment.status = "FAILED"
            self._outbox(db, "payment.failed", payment, {"reason": "INSUFFICIENT_FUNDS"})
            return payment
        source.available_balance_minor -= payment.amount_minor
        destination.available_balance_minor += payment.amount_minor
        source.version += 1; destination.version += 1
        payment.status = "POSTED"
        journal = LedgerJournal(payment_id=payment.id)
        db.add(journal); db.flush()
        db.add_all([LedgerEntry(journal_id=journal.id, account_id=source.id, direction="DEBIT", amount_minor=payment.amount_minor, currency=payment.currency),
                    LedgerEntry(journal_id=journal.id, account_id=destination.id, direction="CREDIT", amount_minor=payment.amount_minor, currency=payment.currency)])
        db.add(AuditEvent(action="PAYMENT_POSTED", aggregate_type="payment", aggregate_id=payment.id,
                          metadata_={"journal_id": str(journal.id)}))
        self._outbox(db, "payment.authorized", payment, {})
        self._outbox(db, "payment.posted", payment, {"journal_id": str(journal.id)})
        self._outbox(db, "ledger.journal_posted", payment, {"journal_id": str(journal.id)})
        return payment

    @staticmethod
    def _outbox(db: Session, event_type: str, payment: Payment, payload: dict) -> None:
        db.add(OutboxEvent(aggregate_id=payment.id, event_type=event_type,
                           payload=event_envelope(event_type, payment.id, payload, payment.correlation_id)))

    def _assess(self, amount_minor: int) -> RiskDecision:
        try:
            return self.fraud.assess(amount_minor)
        except Exception:
            # A risk dependency outage cannot authorise money movement.
            fallback = settings.fraudshield_unavailable_policy.upper()
            return RiskDecision(100, fallback if fallback == "DENY" else "REVIEW",
                                ["FRAUDSHIELD_UNAVAILABLE"])
