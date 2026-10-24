"""Transactional-outbox publisher for NATS JetStream (at-least-once)."""
import asyncio
import os
import structlog
import nats
from sqlalchemy import select
from app.core.db import SessionLocal
from app.payments.models import OutboxEvent

log = structlog.get_logger()

async def publish_once(js) -> int:
    # Claiming and marking happen in separate transactions: a crash after
    # JetStream acknowledgement intentionally permits redelivery.
    with SessionLocal() as db:
        events = db.scalars(select(OutboxEvent).where(OutboxEvent.status == "PENDING")
            .order_by(OutboxEvent.created_at).limit(100).with_for_update(skip_locked=True)).all()
        ids = [(event.id, event.event_type, event.payload) for event in events]
    published = []
    for event_id, subject, payload in ids:
        await js.publish(subject, __import__("json").dumps(payload).encode())
        published.append(event_id)
    if published:
        from datetime import UTC, datetime
        with SessionLocal.begin() as db:
            for event_id in published:
                event = db.get(OutboxEvent, event_id)
                if event and event.status == "PENDING":
                    event.status, event.published_at = "PUBLISHED", datetime.now(UTC)
    return len(published)

async def run() -> None:
    nc = await nats.connect(os.getenv("NATS_URL", "nats://nats:4222"), max_reconnect_attempts=-1)
    js = nc.jetstream()
    await js.add_stream(name="PAYMENTS", subjects=["payment.*", "ledger.*"])
    while True:
        try:
            count = await publish_once(js)
            if count: log.info("outbox_published", count=count)
        except Exception as error:
            log.warning("outbox_publish_failed", error=str(error))
        await asyncio.sleep(0.5)

if __name__ == "__main__": asyncio.run(run())
