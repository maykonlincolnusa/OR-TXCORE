from datetime import UTC, datetime
from uuid import UUID, uuid4


def event_envelope(event_type: str, aggregate_id: UUID, payload: dict, correlation_id: UUID | None = None,
                   causation_id: UUID | None = None) -> dict:
    timestamp = datetime.now(UTC).isoformat()
    return {"event_id": str(uuid4()), "event_type": event_type, "schema_version": 1,
            "aggregate_id": str(aggregate_id), "correlation_id": str(correlation_id or aggregate_id),
            "causation_id": str(causation_id) if causation_id else None,
            "timestamp": timestamp, "occurred_at": timestamp, "payload": payload}
