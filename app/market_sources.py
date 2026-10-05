"""Generic market-source engine for SAP FX Control Center V5.

Supports:
- PRESET: validated built-in connectors (Banpaís/Ficohsa).
- API_JSON: REST/JSON endpoint with configurable dotted paths.
- WEB_HTML: public HTML page with AUTO, CSS or REGEX extraction.

The engine never writes SAP. It only retrieves and normalizes market rates.
The reconciliation layer requires at least three valid sources before a write.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from statistics import median
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

from app.config import Settings
from app.providers import get_provider
from app.providers.http_client import secure_session
from app.credential_store import decrypt_secret


class MarketSourceError(RuntimeError):
    pass


@dataclass
class SourceSnapshot:
    code: str
    name: str
    source_type: str
    source_url: str
    fetched_at: str
    rates: dict[str, dict[str, Decimal]]
    raw_hash: str

    def serializable(self) -> dict[str, Any]:
        d = asdict(self)
        d["rates"] = {c: {k: str(v) for k, v in pair.items()} for c, pair in self.rates.items()}
        return d


@dataclass
class MarketConsensus:
    safe: bool
    official_source: str
    official_rates: dict[str, Decimal]
    medians: dict[str, Decimal]
    deviations_percent: dict[str, Decimal]
    successful_sources: list[str]
    failed_sources: dict[str, str]
    warnings: list[str]
    snapshots: list[SourceSnapshot]


def _safe_url(url: str) -> str:
    url = (url or "").strip()
    p = urlparse(url)
    if p.scheme not in {"http", "https"} or not p.netloc:
        raise MarketSourceError("La fuente debe usar una URL http:// o https:// válida.")
    return url


def _decimal(value: Any) -> Decimal:
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    s = str(value).strip()
    s = re.sub(r"[^0-9,.-]", "", s)
    if not s:
        raise MarketSourceError("No se encontró un número válido.")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        tail = s.split(",")[-1]
        if len(tail) in {2, 3, 4, 5, 6}:
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    try:
        out = Decimal(s)
    except InvalidOperation as exc:
        raise MarketSourceError(f"Valor numérico inválido: {value}") from exc
    if out <= 0:
        raise MarketSourceError(f"La tasa debe ser mayor que cero: {value}")
    return out

