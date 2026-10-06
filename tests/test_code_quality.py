from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app.config import Settings
from app.store import Store
from app.version import get_version


def test_fastapi_metadata_uses_version_file():
    import app.main as main

    client = TestClient(main.app)
    assert main.app.version == get_version()


def test_cleanup_preserves_transaction_audit_and_expires_bank_checks(tmp_path):
    st = Store(tmp_path / "retention.db")
    old = (
        datetime.now(ZoneInfo(st.timezone)) - timedelta(days=45)
    ).isoformat()

    with st.conn() as con:
        con.execute(
            """INSERT INTO transactions(
                 occurred_at, company_db, currency, status, verified
               ) VALUES(?,?,?,?,?)""",
            (old, "OLD_DB", "USD", "MATCH", 1),
        )
        con.execute(
            """INSERT INTO bank_checks(
                 checked_at, bank, ok
               ) VALUES(?,?,?)""",
            (old, "OLD_BANK", 1),
        )

    deleted = st.cleanup(30)

    assert deleted == {"bank_checks": 1}
    assert len(st.list_transactions(10)) == 1
    assert st.recent_bank_checks(10) == []


def test_cleanup_never_uses_zero_day_retention(tmp_path):
    st = Store(tmp_path / "retention.db")
    result = st.cleanup(0)
    assert set(result) == {"bank_checks"}


def test_sync_engine_boolean_normalization():
    import app.sync_engine as sync

    for value in (True, 1, "1", "TRUE", "yes", "On"):
        assert sync._setting_enabled(value) is True
    for value in (False, 0, "0", "false", "no", "", None):
        assert sync._setting_enabled(value) is False


def test_sync_engine_company_lookup_has_one_domain_error(tmp_path):
    import app.sync_engine as sync

    st = Store(tmp_path / "company.db")
    try:
        sync._require_company(st, 999999)
        assert False
    except ValueError as exc:
        assert str(exc) == "Compañía no encontrada"


def test_sync_engine_local_day_is_timezone_aware():
    import app.sync_engine as sync

    settings = Settings(timezone="America/Tegucigalpa")
    day = sync._local_day(settings)
    expected = datetime.now(ZoneInfo("America/Tegucigalpa")).date()
    assert day == expected
