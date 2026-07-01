"""Transaction extraction schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExtractedTransaction(BaseModel):
    """Structured transaction extracted from natural language text."""

    model_config = ConfigDict(str_strip_whitespace=True)

    type: Literal["expense", "income"]
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=8)
    merchant: str | None = None
    category: str | None = None
    transaction_date: date
    notes: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        """Normalize currency codes to uppercase."""
        return value.upper()
