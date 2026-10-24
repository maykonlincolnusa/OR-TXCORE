from uuid import uuid4
from app.shared.events import event_envelope

def test_event_contract_is_versioned_and_traceable():
    envelope = event_envelope("payment.posted", uuid4(), {"amount_minor": 100})
    assert {"event_id", "event_type", "correlation_id", "causation_id", "aggregate_id", "timestamp", "schema_version", "payload"} <= set(envelope)
    assert envelope["schema_version"] == 1
