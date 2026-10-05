"""Hardened HTTP client helpers for public banking sources with timeouts and TLS validation."""
from __future__ import annotations
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def secure_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3,connect=3,read=2,backoff_factor=0.5,status_forcelist=(429,500,502,503,504),allowed_methods=frozenset({"GET"}),raise_on_status=False)
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent":"SAP-FX-Control-Center/1.0 (+internal finance automation)","Accept":"text/html,application/xhtml+xml","Accept-Language":"es-HN,es;q=0.9,en;q=0.5","Connection":"close"})
    return session
