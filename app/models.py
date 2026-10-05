"""Pydantic domain models for bank exchange-rate values and provider results."""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class BankName(str, Enum):
    BANPAIS="BANPAIS"; FICOHSA="FICOHSA"

class CurrencyRate(BaseModel):
    buy: float = Field(gt=0); sell: float = Field(gt=0)

class BankRates(BaseModel):
    bank: BankName; fetched_at: datetime; source_url: str; usd: CurrencyRate; eur: CurrencyRate; raw_hash: str

class Comparison(BaseModel):
    primary: BankRates; secondary: BankRates|None=None
    usd_sell_diff: float|None=None; eur_sell_diff: float|None=None
    usd_sell_diff_percent: float|None=None; eur_sell_diff_percent: float|None=None
    safe_for_reference: bool; warnings: list[str]=Field(default_factory=list)
