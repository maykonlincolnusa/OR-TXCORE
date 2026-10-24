"""Deterministic synthetic payment stream for local experiments; never real customer data."""
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
import random

UTC = timezone.utc


@dataclass(frozen=True)
class SyntheticTransaction:
    transaction_id: str
    timestamp: str
    account_id: str
    beneficiary_id: str
    amount_minor: int
    currency: str
    device_trusted: bool
    country_changed: bool
    transfers_last_hour: int
    label: str


def generate(seed: int, count: int) -> list[SyntheticTransaction]:
    rng, start = random.Random(seed), datetime(2026, 1, 1, tzinfo=UTC)
    transactions = []
    for index in range(count):
        velocity = rng.randint(0, 16)
        country_changed = rng.random() < 0.03
        high_value = rng.random() < 0.04
        amount = rng.randint(1_00, 30_000_00) if high_value else rng.randint(1_00, 75_000)
        compromised = (velocity >= 10 and country_changed) or (high_value and not rng.choice([True, False]))
        transactions.append(SyntheticTransaction(
            transaction_id=f"syn-{index:08d}", timestamp=(start + timedelta(seconds=index * 11)).isoformat(),
            account_id=f"acct-{rng.randrange(1000):04d}", beneficiary_id=f"bene-{rng.randrange(1500):04d}",
            amount_minor=amount, currency="BRL", device_trusted=not compromised or rng.random() > .7,
            country_changed=country_changed, transfers_last_hour=velocity,
            label="FRAUD" if compromised else "LEGITIMATE"))
    return transactions


def as_rows(seed: int, count: int) -> list[dict]:
    return [asdict(item) for item in generate(seed, count)]
