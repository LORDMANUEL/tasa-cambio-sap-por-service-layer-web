from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest
from openpyxl import Workbook

from app.config import Settings
from app.providers.base import BankProviderError
from app.providers.bch import parse_bch_xlsx


def _workbook(rows, headers=("Fecha","TCR")) -> bytes:
    wb=Workbook()
    ws=wb.active
    ws.title="Datos"
    ws.append(list(headers))
    for row in rows:
        ws.append(list(row))
    out=BytesIO()
    wb.save(out)
    wb.close()
    return out.getvalue()


def test_bch_parser_selects_latest_non_future_tcr():
    content=_workbook([
        (date(2026,10,5),26.8901),
        (date(2026,10,6),26.8920),
        (date(2026,10,8),26.9999),
    ])
    result=parse_bch_xlsx(content,Settings(),today=date(2026,10,7))
    assert result.observed_date==date(2026,10,6)
    assert result.tcr==Decimal("26.892")
    assert len(result.raw_hash)==64


def test_bch_parser_allows_holiday_validity_window():
    content=_workbook([(date(2026,10,6),26.8920)])
    result=parse_bch_xlsx(content,Settings(),today=date(2026,10,12),max_age_days=10)
    assert result.observed_date==date(2026,10,6)


def test_bch_parser_rejects_stale_data():
    content=_workbook([(date(2026,9,20),26.80)])
    with pytest.raises(BankProviderError,match="desactualizado"):
        parse_bch_xlsx(content,Settings(),today=date(2026,10,7),max_age_days=10)


def test_bch_parser_rejects_schema_change():
    content=_workbook([(date(2026,10,6),26.8920)],headers=("Día","Valor"))
    with pytest.raises(BankProviderError,match="estructura"):
        parse_bch_xlsx(content,Settings(),today=date(2026,10,7))


def test_bch_preset_exposes_only_usd_reference(monkeypatch):
    import app.market_sources as ms
    from types import SimpleNamespace
    from datetime import datetime
    from zoneinfo import ZoneInfo

    fake=SimpleNamespace(
        tcr=Decimal("26.8920"),
        source_url="https://www.bch.hn/example.xlsx",
        fetched_at=datetime(2026,10,7,6,0,tzinfo=ZoneInfo("America/Tegucigalpa")),
        raw_hash="a"*64,
    )
    monkeypatch.setattr(ms,"get_provider",lambda preset,settings:SimpleNamespace(fetch=lambda:fake))
    snap=ms.fetch_source({
        "code":"BCH","name":"Banco Central de Honduras","source_type":"PRESET",
        "url":"https://www.bch.hn/","config_json":"{\"preset\":\"BCH\"}",
    },Settings())
    assert snap.rates=={"USD":{"buy":Decimal("26.8920"),"sell":Decimal("26.8920")}}
    assert "EUR" not in snap.rates
