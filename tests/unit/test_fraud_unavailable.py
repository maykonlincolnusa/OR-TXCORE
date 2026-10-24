from app.payments.service import PaymentService

def test_fraud_failure_policy_never_allows(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "fraudshield_unavailable_policy", "REVIEW")
    class Down:
        def assess(self, _): raise TimeoutError()
    decision = PaymentService(Down())._assess(100)
    assert decision.decision == "REVIEW"
    assert "FRAUDSHIELD_UNAVAILABLE" in decision.reason_codes
