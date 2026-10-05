"""Ficohsa public-rate adapter: fetch, parse and validate USD/EUR buy/sell values."""
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
URL="https://www.ficohsa.hn/"
def parse_ficohsa_html(html:str,settings:Settings)->BankRates:
    text=" ".join(BeautifulSoup(html,"html.parser").stripped_strings); normalized=re.sub(r"\s+"," ",text)
    values=re.findall(r"(?:Compra|Venta)\s+L\s*([0-9]+(?:\.[0-9]+)?)",normalized,flags=re.I)
    if len(values)<4: values=re.findall(r"L\s*([0-9]+(?:\.[0-9]+)?)",normalized,flags=re.I)
    nums=[float(x) for x in values]
    if len(nums)<4: raise BankProviderError("Ficohsa cambió su formato o no se encontraron las cuatro tasas HNL.")
    usd_buy,usd_sell,eur_buy,eur_sell=nums[:4]
    return BankRates(bank=BankName.FICOHSA,fetched_at=datetime.now(ZoneInfo(settings.timezone)),source_url=URL,usd=CurrencyRate(buy=usd_buy,sell=usd_sell),eur=CurrencyRate(buy=eur_buy,sell=eur_sell),raw_hash=hashlib.sha256(html.encode("utf-8",errors="ignore")).hexdigest())
class FicohsaProvider(BankProvider):
    def __init__(self,settings:Settings):self.settings=settings;self.session=secure_session()
    def fetch(self)->BankRates:
        try:
            response=self.session.get(URL,timeout=self.settings.request_timeout_seconds,verify=self.settings.tls_verify,allow_redirects=True);response.raise_for_status()
            if len(response.content)>4_000_000: raise BankProviderError("Respuesta Ficohsa excede el tamaño permitido.")
            return parse_ficohsa_html(response.text,self.settings)
        except (requests.RequestException,ValueError) as exc: raise BankProviderError(f"No se pudo consultar Ficohsa: {exc.__class__.__name__}") from exc
