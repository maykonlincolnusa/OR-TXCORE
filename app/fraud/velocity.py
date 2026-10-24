from datetime import UTC, datetime, timedelta
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.payments.models import Payment


class PaymentVelocityReader:
    """Read-side adapter. Production can replace it with a feature-store adapter."""
    def last_hour(self, db: Session, account_id) -> tuple[int, int]:
        cutoff = datetime.now(UTC) - timedelta(hours=1)
        count, amount = db.execute(select(func.count(Payment.id), func.coalesce(func.sum(Payment.amount_minor), 0))
            .where(Payment.source_account_id == account_id, Payment.created_at >= cutoff,
                   Payment.status == "POSTED")).one()
        return int(count), int(amount)
