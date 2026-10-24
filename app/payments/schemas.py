from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class AccountCreate(BaseModel):
    currency: str = Field(min_length=3, max_length=3)
    @field_validator("currency")
    @classmethod
    def uppercase(cls, value: str) -> str: return value.upper()


class BalanceCredit(BaseModel):
    amount_minor: int = Field(gt=0, le=100_000_000)


class TransferRequest(BaseModel):
    source_account_id: UUID
    destination_account_id: UUID
    amount_minor: int = Field(gt=0, le=100_000_000)
    currency: str = Field(min_length=3, max_length=3)
    @field_validator("currency")
    @classmethod
    def uppercase(cls, value: str) -> str: return value.upper()
