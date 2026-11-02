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
    with pytest.raises(BankProviderError,match="clave API"):
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


def test_bch_api_moves_encrypted_clave_to_query(monkeypatch):
    import app.providers.bch_api as api

    class Response:
        status_code=200
        content=b'[{"Nombre":"EC-TCR-01","Fecha":"2026-11-02T00:00:00Z","Valor":26.95}]'
        url=api.DEFAULT_URL
        def raise_for_status(self):
            return None
        def json(self):
            return [{"Nombre":"EC-TCR-01","Fecha":"2026-11-02T00:00:00Z","Valor":26.95}]

    seen={}
    class Session:
        def get(self,url,**kwargs):
            seen["url"]=url
            seen.update(kwargs)
            return Response()

    monkeypatch.setattr(api,"secure_session",lambda:Session())
    result=api.fetch_bch_api(
        {"url":api.DEFAULT_URL,"timeout_seconds":5,"tls_verify":1},
        Settings(),
        {"clave":"SECRET_VALUE"},
    )
    assert result["tcr"]==Decimal("26.95")
    assert seen["params"]["clave"]=="SECRET_VALUE"
    assert "clave" not in seen["headers"]


def test_store_accepts_bch_api_source_type():
    from pathlib import Path
    import tempfile
    from app.store import Store
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/"fresh.db")
        sid=st.upsert_bank_source(
            source_id=None,
            code="BCHAPI",
            name="BCH API",
            country="HN",
            source_type="BCH_API",
            url="https://bchapi-am.azure-api.net/api/v1/indicadores/97/cifras",
            enabled=True,
            config_json="{}",
            headers_json="{}",
            timeout_seconds=10,
            tls_verify=True,
        )
        assert st.get_bank_source(sid)["source_type"]=="BCH_API"


def test_store_migrates_legacy_bank_source_constraint():
    from pathlib import Path
    import tempfile
    import sqlite3
    from app.store import Store
    with tempfile.TemporaryDirectory() as d:
        path=Path(d)/"legacy.db"
        con=sqlite3.connect(path)
        con.executescript("""
        CREATE TABLE bank_sources (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          code TEXT NOT NULL UNIQUE,
          name TEXT NOT NULL,
          country TEXT NOT NULL DEFAULT '',
          source_type TEXT NOT NULL CHECK(source_type IN ('PRESET','WEB_HTML','API_JSON')),
          url TEXT NOT NULL DEFAULT '',
          enabled INTEGER NOT NULL DEFAULT 1,
          config_json TEXT NOT NULL DEFAULT '{}',
          headers_json TEXT NOT NULL DEFAULT '{}',
          secret_headers_blob TEXT,
          timeout_seconds INTEGER NOT NULL DEFAULT 15,
          tls_verify INTEGER NOT NULL DEFAULT 1,
          last_status TEXT,
          last_error TEXT,
          last_checked_at TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        INSERT INTO bank_sources(code,name,country,source_type,url,created_at,updated_at)
        VALUES('OLD','Old Source','HN','WEB_HTML','https://example.com','2026-01-01','2026-01-01');
        """)
        con.commit()
        con.close()
        st=Store(path)
        assert st.get_bank_source_by_code("OLD")["source_type"]=="WEB_HTML"
        sid=st.upsert_bank_source(
            source_id=None,
            code="BCHAPI",
            name="BCH API",
            country="HN",
            source_type="BCH_API",
            url="https://example.com",
            enabled=True,
            config_json="{}",
            headers_json="{}",
        )
        assert st.get_bank_source(sid)["source_type"]=="BCH_API"


def test_setup_step6_passes_encrypted_bch_api_secret(monkeypatch):
    from pathlib import Path
    from types import SimpleNamespace
    import tempfile
    from fastapi.testclient import TestClient
    import app.main as m
    from app.store import Store

    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/"setup.db")
        monkeypatch.setattr(m,"store",st)
        monkeypatch.setattr(m,"encrypt_secret",lambda value:"ENC::"+value)
        captured={}
        def fake_fetch(source,settings):
            captured.update(source)
            return SimpleNamespace(rates={"USD":{"buy":Decimal("26.90"),"sell":Decimal("26.95")}})
        monkeypatch.setattr(m,"fetch_source",fake_fetch)
        client=TestClient(m.app)
        r=client.post("/setup/validate-step",data={
            "_step":"6",
            "source_code":"BCHAPI",
            "source_name":"BCH API",
            "source_type":"BCH_API",
            "source_url":"https://bchapi-am.azure-api.net/api/v1/indicadores/97/cifras",
            "source_config":"{}",
            "source_secret_headers":'{"clave":"SECRET"}',
        })
        assert r.status_code==200
        assert r.json()["ok"] is True
        assert captured["secret_headers_blob"]=='ENC::{"clave":"SECRET"}'
