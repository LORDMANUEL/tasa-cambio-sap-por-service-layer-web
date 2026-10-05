"""Deterministic policy that decides CREATE, UPDATE or MATCH using the bank as authority."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class RateDecision:
    action: str
    reason: str

def decide_rate_action(sap_rate: Decimal, bank_rate: Decimal) -> RateDecision:
    if bank_rate <= 0: raise ValueError('La tasa bancaria oficial debe ser mayor que cero.')
    if sap_rate == bank_rate: return RateDecision('MATCH', 'SAP ya coincide exactamente con el banco oficial.')
    if sap_rate == 0: return RateDecision('CREATE', 'SAP no tiene tasa para la fecha; se debe crear con la tasa bancaria oficial.')
    return RateDecision('UPDATE', 'SAP tiene una tasa distinta; se debe reemplazar por la tasa bancaria oficial.')
