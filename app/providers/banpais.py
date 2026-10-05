"""Banpaís public-rate adapter: fetch, parse and validate USD/EUR buy/sell values."""
from __future__ import annotations
import hashlib,re
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup
from app.config import Settings
from app.models import BankName,BankRates,CurrencyRate
from .base import BankProvider,BankProviderError
from .http_client import secure_session
URL="https://www.banpais.hn/divisas/barradolar.php"
def _number(value:str)->float:return float(value.replace(",","").strip())
def parse_banpais_html(html:str,settings:Settings)->BankRates:
    text=" ".join(BeautifulSoup(html,"html.parser").stripped_strings); normalized=re.sub(r"\s+"," ",text)
    patterns={"usd":re.compile(r"(?:PRECIO\s+D[ÓO]LAR|D[ÓO]LAR).*?Compra\s*:?\s*L?\s*([0-9]+(?:\.[0-9]+)?)\s*Venta\s*:?\s*L?\s*([0-9]+(?:\.[0-9]+)?)",re.I),"eur":re.compile(r"(?:PRECIO\s+EURO|EURO).*?Compra\s*:?\s*L?\s*([0-9]+(?:\.[0-9]+)?)\s*Venta\s*:?\s*L?\s*([0-9]+(?:\.[0-9]+)?)",re.I)}
    usd=patterns["usd"].search(normalized); eur=patterns["eur"].search(normalized)
    if not usd or not eur: raise BankProviderError("Banpaís cambió su formato o no se encontraron las cuatro tasas.")
    return BankRates(bank=BankName.BANPAIS,fetched_at=datetime.now(ZoneInfo(settings.timezone)),source_url=URL,usd=CurrencyRate(buy=_number(usd.group(1)),sell=_number(usd.group(2))),eur=CurrencyRate(buy=_number(eur.group(1)),sell=_number(eur.group(2))),raw_hash=hashlib.sha256(html.encode("utf-8",errors="ignore")).hexdigest())
class BanpaisProvider(BankProvider):
    def __init__(self,settings:Settings):self.settings=settings;self.session=secure_session()
    def fetch(self)->BankRates:
        try:
            response=self.session.get(URL,timeout=self.settings.request_timeout_seconds,verify=self.settings.tls_verify,allow_redirects=True);response.raise_for_status()
            if len(response.content)>2_000_000: raise BankProviderError("Respuesta Banpaís excede el tamaño permitido.")
            return parse_banpais_html(response.text,self.settings)
        except (requests.RequestException,ValueError) as exc: raise BankProviderError(f"No se pudo consultar Banpaís: {exc.__class__.__name__}") from exc
