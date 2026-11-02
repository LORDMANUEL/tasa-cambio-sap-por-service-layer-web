from datetime import date
from decimal import Decimal
import json

import pytest

from app.config import Settings
from app.providers.base import BankProviderError
from app.providers.bch_api import parse_bch_api_payload, fetch_bch_api


def test_bch_api_parser_uses_latest_non_future_tcr():
    data=[
        {"Id":1,"IndicadorId":97,"Nombre":"EC-TCR-01","Fecha":"2026-10-30T00:00:00Z","Valor":26.9000},
        {"Id":2,"IndicadorId":97,"Nombre":"EC-TCR-01","Fecha":"2026-11-02T00:00:00Z","Valor":26.9500},
        {"Id":3,"IndicadorId":97,"Nombre":"EC-TCR-01","Fecha":"2026-11-03T00:00:00Z","Valor":99.0000},
    ]
    observed,tcr=parse_bch_api_payload(data,Settings(),today=date(2026,11,2))
    assert observed==date(2026,11,2)
    assert tcr==Decimal("26.95")


def test_bch_api_parser_rejects_stale_data():
    data=[{"Nombre":"EC-TCR-01","Fecha":"2026-10-01T00:00:00Z","Valor":26.90}]
    with pytest.raises(BankProviderError,match="desactualizada"):
        parse_bch_api_payload(data,Settings(),today=date(2026,11,2),max_age_days=10)


def test_bch_api_requires_encrypted_subscription_header():
    with pytest.raises(BankProviderError,match="Ocp-Apim-Subscription-Key"):
        fetch_bch_api({"url":"https://example.invalid","timeout_seconds":5,"tls_verify":1},Settings(),{})


def test_market_source_supports_bch_api(monkeypatch):
    import app.market_sources as ms
    monkeypatch.setattr(ms,"fetch_bch_api",lambda source,settings,headers:{
        "observed_date":date(2026,11,2),
        "tcr":Decimal("26.9500"),
        "source_url":"https://bchapi.example/api/v1/indicadores/97/cifras",
        "fetched_at":__import__("datetime").datetime(2026,11,2,6,0),
        "raw_hash":"abc",
    })
    monkeypatch.setattr(ms,"_headers",lambda source:{"Ocp-Apim-Subscription-Key":"secret"})
    snap=ms.fetch_source({
        "code":"BCHAPI","name":"BCH Web-API","source_type":"BCH_API",
        "url":"https://bchapi.example/api/v1/indicadores/97/cifras",
        "config_json":"{}","headers_json":"{}","timeout_seconds":10,"tls_verify":1,
    },Settings())
    assert snap.rates["USD"]["buy"]==Decimal("26.9500")
    assert snap.rates["USD"]["sell"]==Decimal("26.9500")
