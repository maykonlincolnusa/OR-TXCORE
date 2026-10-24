"""Synchronous boundary for the independently deployable FraudShield service."""
from __future__ import annotations

from typing import Protocol
import httpx

from app.core.config import settings
from app.fraud.service import RiskDecision


class FraudAssessor(Protocol):
    def assess(self, amount_minor: int) -> RiskDecision: ...


class FraudShieldClient:
    """Small timeout-bounded client; the caller applies the fail-closed policy."""
    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        self.base_url = base_url or settings.fraudshield_url
        self.timeout = timeout or settings.fraudshield_timeout_seconds

    def assess(self, amount_minor: int) -> RiskDecision:
        if not self.base_url:
            raise RuntimeError("FraudShield endpoint is not configured")
        response = httpx.post(f"{self.base_url.rstrip('/')}/v1/assessments",
                              json={"amount_minor": amount_minor}, timeout=self.timeout)
        response.raise_for_status()
        body = response.json()
        return RiskDecision(int(body["score"]), str(body["decision"]), list(body["reason_codes"]))
