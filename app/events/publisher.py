from datetime import UTC, datetime
from typing import Protocol
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.payments.models import OutboxEvent, ProcessedEvent


class EventBus(Protocol):
    def publish(self, subject: str, message: dict) -> None: ...


class OutboxPublisher:
    """Adapter-independent publisher. A NATS JetStream adapter implements EventBus."""
    def publish_batch(self, db: Session, bus: EventBus, limit: int = 100) -> int:
        events = db.scalars(select(OutboxEvent).where(OutboxEvent.status == "PENDING")
                            .order_by(OutboxEvent.created_at).limit(limit).with_for_update(skip_locked=True)).all()
        for event in events:
            bus.publish(event.event_type, event.payload)
            event.status, event.published_at = "PUBLISHED", datetime.now(UTC)
        return len(events)


def mark_processed(db: Session, consumer_name: str, event_id) -> bool:
    """Consumer calls this inside its effect transaction; unique constraint deduplicates delivery."""
    if db.scalar(select(ProcessedEvent).where(ProcessedEvent.consumer_name == consumer_name,
                 ProcessedEvent.event_id == event_id)):
        return False
    db.add(ProcessedEvent(consumer_name=consumer_name, event_id=event_id))
    return True
