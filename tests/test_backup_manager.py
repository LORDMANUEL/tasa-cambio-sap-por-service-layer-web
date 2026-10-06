from pathlib import Path
import zipfile

from app.backup_manager import create_backup, validate_backup, sqlite_integrity
from app.config import Settings
from app.store import Store


def _company(store: Store):
    return store.upsert_company(
        company_id=None,
        company_name="Backup Test",
        database_name="BACKUP_DB",
        db_type="HANA",
        environment="TEST",
        enabled=True,
        allow_write=True,
        scheduled_write=False,
        auto_enabled=False,
        schedule_hour=6,
        schedule_minute=0,
        use_usd=True,
        use_eur=False,
        sap_user="manager",
        primary_bank="BANPAIS",
        secondary_bank="FICOHSA",
        bank_source_codes="A,B,C",
        currencies_csv="USD",
    )


def test_sqlite_backup_is_consistent_and_restorable(tmp_path):
    db=tmp_path/"live.db"
    store=Store(db)
    _company(store)
    store.add_transaction({
        "company_id":None,
        "company_db":"BACKUP_DB",
        "company_name":"Backup Test",
        "environment":"TEST",
        "currency":"USD",
        "status":"MATCH",
        "verified":1,
    })

    settings=Settings(database_file=str(db))
    result=create_backup(settings,db,backup_dir=tmp_path/"backups")

    archive=Path(result["path"])
    assert archive.exists()
    checked=validate_backup(archive)
    assert checked["valid"] is True
    assert checked["manifest"]["database_integrity"]=="ok"

    restored=tmp_path/"restored.db"
    with zipfile.ZipFile(archive,"r") as zf:
        restored.write_bytes(zf.read("atas.db"))

    restored_store=Store(restored)
    assert restored_store.get_company_by_database("BACKUP_DB") is not None
    assert restored_store.list_transactions(10)[0]["status"]=="MATCH"


def test_backup_validation_rejects_tampered_database(tmp_path):
    db=tmp_path/"live.db"
    store=Store(db)
    result=create_backup(Settings(database_file=str(db)),db,backup_dir=tmp_path/"backups")
    original=Path(result["path"])
    tampered=tmp_path/"tampered.zip"

    with zipfile.ZipFile(original,"r") as src, zipfile.ZipFile(tampered,"w") as dst:
        for name in src.namelist():
            data=src.read(name)
            if name=="atas.db":
                data+=b"tampered"
            dst.writestr(name,data)

    checked=validate_backup(tampered)
    assert checked["valid"] is False
    assert checked["message"]=="DATABASE_HASH_MISMATCH"


def test_sqlite_integrity_reports_ok(tmp_path):
    db=tmp_path/"integrity.db"
    Store(db)
    ok,message=sqlite_integrity(db)
    assert ok is True
    assert message=="ok"
