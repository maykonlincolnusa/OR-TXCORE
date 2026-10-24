from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class UUIDModel:
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)


class Account(UUIDModel, Base):
    __tablename__ = "accounts"
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    available_balance_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (CheckConstraint("available_balance_minor >= 0", name="ck_account_nonnegative"),)


class Payment(UUIDModel, Base):
    __tablename__ = "payments"
    source_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    destination_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    risk_decision: Mapped[str] = mapped_column(String(10), nullable=False)
    correlation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (CheckConstraint("amount_minor > 0", name="ck_payment_positive"),
                      CheckConstraint("source_account_id <> destination_account_id", name="ck_payment_distinct_accounts"),
                      Index("ix_payments_source_created", "source_account_id", "created_at"))


class PaymentAttempt(UUIDModel, Base):
    __tablename__ = "payment_attempts"
    payment_id: Mapped[UUID] = mapped_column(ForeignKey("payments.id"), nullable=False)
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LedgerJournal(UUIDModel, Base):
    __tablename__ = "ledger_journals"
    payment_id: Mapped[UUID] = mapped_column(ForeignKey("payments.id"), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="POSTED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LedgerEntry(UUIDModel, Base):
    __tablename__ = "ledger_entries"
    journal_id: Mapped[UUID] = mapped_column(ForeignKey("ledger_journals.id"), nullable=False)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    direction: Mapped[str] = mapped_column(String(6), nullable=False)  # DEBIT or CREDIT
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    __table_args__ = (CheckConstraint("amount_minor > 0", name="ck_entry_positive"),
                      CheckConstraint("direction IN ('DEBIT', 'CREDIT')", name="ck_entry_direction"),
                      Index("ix_ledger_entries_journal", "journal_id"))


class IdempotencyRecord(UUIDModel, Base):
    __tablename__ = "idempotency_records"
    scope: Mapped[str] = mapped_column(String(64), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payment_id: Mapped[UUID | None] = mapped_column(ForeignKey("payments.id"))
    response_status: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("scope", "key", name="uq_idempotency_scope_key"),)


class RiskAssessment(UUIDModel, Base):
    __tablename__ = "risk_assessments"
    payment_id: Mapped[UUID] = mapped_column(ForeignKey("payments.id"), nullable=False, unique=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[str] = mapped_column(String(10), nullable=False)
    reason_codes: Mapped[list] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditEvent(UUIDModel, Base):
    __tablename__ = "audit_events"
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(50), nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OutboxEvent(UUIDModel, Base):
    __tablename__ = "outbox_events"
    aggregate_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (Index("ix_outbox_pending", "status", "created_at"),)


class ProcessedEvent(UUIDModel, Base):
    __tablename__ = "processed_events"
    consumer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("consumer_name", "event_id", name="uq_processed_event"),)
