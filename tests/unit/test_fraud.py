from app.fraud.service import DeterministicFraudEngine

def test_fraud_decisions_are_explainable(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "fraud_review_amount_minor", 100)
    monkeypatch.setattr(settings, "fraud_deny_amount_minor", 1000)
    engine = DeterministicFraudEngine()
    assert engine.assess(99).decision == "ALLOW"
    assert engine.assess(100).reason_codes == ["AMOUNT_REVIEW_THRESHOLD"]
    assert engine.assess(1000).decision == "DENY"
