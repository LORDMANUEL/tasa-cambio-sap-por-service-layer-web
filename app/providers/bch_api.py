"""Official Banco Central de Honduras Web-API TCR connector.

The BCH developer portal publishes indicator 97 (EC-TCR-01) as the daily
Reference Exchange Rate. Access requires an API key. Atas stores that key in
the source's encrypted secret-header blob and only materializes it at request time.
"""
from __future__ import annotations

import hashlib
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

import requests

from app.config import Settings
from .base import BankProviderError
from .http_client import secure_session

DEFAULT_URL="https://bchapi-am.azure-api.net/api/v1/indicadores/97/cifras"


def _parse_date(value) -> date | None:
    text=str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z","+00:00")).date()
    except ValueError:
        return None


def parse_bch_api_payload(data, settings: Settings, *, today: date | None=None, max_age_days: int=10):
    if not isinstance(data, list):
        raise BankProviderError("BCH Web-API no devolvió una lista de cifras.")
    local_today=today or datetime.now(ZoneInfo(settings.timezone)).date()
    candidates=[]
    for row in data:
        if not isinstance(row,dict):
            continue
        if str(row.get("Nombre") or "").upper() not in {"EC-TCR-01",""}:
            continue
        observed=_parse_date(row.get("Fecha"))
        try:
            value=Decimal(str(row.get("Valor")))
        except (InvalidOperation,TypeError,ValueError):
            continue
        if observed and observed<=local_today and value>0:
            candidates.append((observed,value))
    if not candidates:
        raise BankProviderError("BCH Web-API no devolvió una observación TCR utilizable.")
    observed,tcr=max(candidates,key=lambda x:x[0])
    age=(local_today-observed).days
    if age>max(1,int(max_age_days)):
        raise BankProviderError(f"BCH Web-API está desactualizada: {observed.isoformat()} ({age} días).")
    lo=Decimal(str(settings.usd_min)); hi=Decimal(str(settings.usd_max))
    if not (lo<=tcr<=hi):
        raise BankProviderError(f"BCH Web-API TCR fuera de rango esperado: {tcr}.")
    return observed,tcr


def fetch_bch_api(source: dict, settings: Settings, headers: dict[str,str]):
    url=str(source.get("url") or DEFAULT_URL).strip() or DEFAULT_URL
    secret_headers=dict(headers)
    clave=None
    for key in list(secret_headers):
        if key.lower() in {"clave","api-key","apikey"}:
            clave=secret_headers.pop(key)
            break
    has_subscription_header=any(k.lower()=="ocp-apim-subscription-key" for k in secret_headers)
    if not clave and not has_subscription_header:
        raise BankProviderError(
            "BCH Web-API requiere una clave API cifrada (clave u Ocp-Apim-Subscription-Key)."
        )

    params={"formato":"Json"}
    if clave:
        params["clave"]=clave

    session=secure_session()
    try:
        response=session.get(
            url,
            params=params,
            headers=secret_headers,
            timeout=min(max(int(source.get("timeout_seconds") or settings.request_timeout_seconds),3),60),
            verify=bool(source.get("tls_verify",1)),
            allow_redirects=True,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise BankProviderError(f"No se pudo consultar BCH Web-API: {exc.__class__.__name__}") from exc

    if len(response.content)>4_000_000:
        raise BankProviderError("Respuesta BCH Web-API excede 4 MB.")
    try:
        data=response.json()
    except Exception as exc:
        raise BankProviderError("BCH Web-API no devolvió JSON válido.") from exc

    observed,tcr=parse_bch_api_payload(data,settings)
    return {
        "observed_date":observed,
        "tcr":tcr,
        "source_url":response.url or url,
        "fetched_at":datetime.now(ZoneInfo(settings.timezone)),
        "raw_hash":hashlib.sha256(response.content).hexdigest(),
    }
