"""Feature contracts separated from the transactional write model.

Feature values are snapshots: a later balance or velocity update must never alter
the evidence that produced a historical risk decision.
"""
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID


@dataclass(frozen=True)
class TransferFeatures:
    payment_id: UUID
    account_id: UUID
    amount_minor: int
    currency: str
    beneficiary_is_new: bool
    transfers_last_hour: int
    amount_last_hour_minor: int
    device_trusted: bool | None = None
    country_changed: bool | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    schema_version: int = 1

    def evidence_hash(self) -> str:
        # Stable, auditable fingerprint—no secrets or raw personal data.
        payload = asdict(self)
        payload["payment_id"] = str(self.payment_id)
        payload["account_id"] = str(self.account_id)
        payload["occurred_at"] = self.occurred_at.isoformat()
        return sha256(repr(sorted(payload.items())).encode()).hexdigest()
