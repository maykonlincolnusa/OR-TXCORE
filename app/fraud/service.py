from dataclasses import dataclass
from app.core.config import settings


@dataclass(frozen=True)
class RiskDecision:
    score: int
    decision: str
    reason_codes: list[str]


class DeterministicFraudEngine:
    """Pure, explainable policy; replace through this port when ML is introduced."""
    def assess(self, amount_minor: int) -> RiskDecision:
        if amount_minor >= settings.fraud_deny_amount_minor:
            return RiskDecision(100, "DENY", ["AMOUNT_HARD_LIMIT"])
        if amount_minor >= settings.fraud_review_amount_minor:
            return RiskDecision(60, "REVIEW", ["AMOUNT_REVIEW_THRESHOLD"])
        return RiskDecision(0, "ALLOW", [])
