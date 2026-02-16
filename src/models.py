from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime, timezone
from typing import Literal
import re

TICKER_PATTERN = r"^[A-Z0-9]{3,}\.[A-Z]{1,3}$"


class AssetModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ticker_yf: str = Field(..., min_length=3)
    security_full_name: str
    asset_class: str
    macro_asset_class: str
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("ticker_yf")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        if not re.match(TICKER_PATTERN, v):
            raise ValueError("Ticker format must be 'SYMBOL.EXCHANGE' (e.g. AAPL.US)")
        return v


class TransactionModel(BaseModel):
    user_id: str
    ticker_yf: str
    transaction_type: Literal["Buy", "Sell"]
    transaction_date: datetime
    shares: int = Field(gt=0)
    price: float = Field(ge=0)
    fees: float = Field(default=0.0, ge=0)
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("ticker_yf")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        if not re.match(TICKER_PATTERN, v):
            raise ValueError("Ticker format invalid (e.g. VWCE.MI)")
        return v
