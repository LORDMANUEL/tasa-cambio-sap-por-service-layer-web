"""Common interfaces and validation helpers shared by all banking-rate providers."""
from __future__ import annotations
from abc import ABC, abstractmethod
from app.models import BankRates

class BankProviderError(RuntimeError):
    pass

class BankProvider(ABC):
    @abstractmethod
    def fetch(self) -> BankRates:
        raise NotImplementedError
