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


def _json_path(data: Any, path: str) -> Any:
    cur = data
    for token in re.findall(r"[^.\[\]]+|\[\d+\]", path.strip()):
        if token.startswith("["):
            cur = cur[int(token[1:-1])]
        elif isinstance(cur, dict):
            cur = cur[token]
        else:
            raise KeyError(path)
    return cur


def _normalize_config(source: dict) -> dict:
    raw = source.get("config_json") or "{}"
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except Exception as exc:
        raise MarketSourceError("config_json de la fuente no es JSON válido.") from exc


def _headers(source: dict) -> dict[str, str]:
    raw = source.get("headers_json") or "{}"
    try:
        obj = raw if isinstance(raw, dict) else json.loads(raw)
        headers={str(k):str(v) for k,v in obj.items()} if isinstance(obj,dict) else {}
    except Exception:
        headers={}
    secret=source.get("secret_headers_blob")
    if secret:
        try:
            obj=json.loads(decrypt_secret(secret))
            if isinstance(obj,dict): headers.update({str(k):str(v) for k,v in obj.items()})
        except Exception as exc:
            raise MarketSourceError("No se pudieron descifrar los headers secretos de la API.") from exc
    return headers


def _fetch_http(source: dict, settings: Settings) -> requests.Response:
    url = _safe_url(source.get("url", ""))
    session = secure_session()
    try:
        response = session.get(
            url,
            headers=_headers(source),
            timeout=min(max(int(source.get("timeout_seconds") or settings.request_timeout_seconds), 3), 60),
            verify=bool(source.get("tls_verify", 1)),
            allow_redirects=True,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise MarketSourceError(f"No se pudo consultar la fuente: {exc.__class__.__name__}") from exc
    if len(response.content) > 4_000_000:
        raise MarketSourceError("La respuesta excede 4 MB; no se procesará.")
    return response


def _auto_html(text: str, currency: str) -> dict[str, Decimal]:
    normalized = re.sub(r"\s+", " ", text)
    positions = [m.start() for m in re.finditer(rf"\b{re.escape(currency)}\b", normalized, re.I)]
    aliases = {"USD": ["DOLAR", "DÓLAR", "DOLLAR"], "EUR": ["EURO"]}.get(currency.upper(), [])
    for alias in aliases:
        positions.extend(m.start() for m in re.finditer(re.escape(alias), normalized, re.I))
    for pos in sorted(set(positions))[:20]:
        window = normalized[pos:pos + 500]
        nums = re.findall(r"(?<!\d)(\d{1,6}(?:[.,]\d{2,6})?)(?!\d)", window)
        vals: list[Decimal] = []
        for n in nums:
            try:
                v = _decimal(n)
                if Decimal("0.00001") < v < Decimal("1000000"):
                    vals.append(v)
            except Exception:
                pass
        buy = re.search(r"(?:compra|buy|purchase)\D{0,30}(\d{1,6}(?:[.,]\d{2,6})?)", window, re.I)
        sell = re.search(r"(?:venta|sell|sale)\D{0,30}(\d{1,6}(?:[.,]\d{2,6})?)", window, re.I)
        if buy and sell:
            return {"buy": _decimal(buy.group(1)), "sell": _decimal(sell.group(1))}
        if len(vals) >= 2:
            return {"buy": vals[0], "sell": vals[1]}
    raise MarketSourceError(f"AUTO no encontró compra/venta para {currency}.")


def _extract_html(html: str, config: dict) -> dict[str, dict[str, Decimal]]:
    soup = BeautifulSoup(html, "html.parser")
    text = " ".join(soup.stripped_strings)
    mode = str(config.get("mode", "AUTO")).upper()
    currencies = [str(x).upper() for x in config.get("currencies", ["USD", "EUR"])]
    out: dict[str, dict[str, Decimal]] = {}
    if mode == "AUTO":
        for cur in currencies:
            out[cur] = _auto_html(text, cur)
        return out
    mapping = config.get("mapping") or {}
    for cur in currencies:
        spec = mapping.get(cur) or mapping.get(cur.lower()) or {}
