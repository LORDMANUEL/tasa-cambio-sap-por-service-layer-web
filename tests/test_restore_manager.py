from pathlib import Path
import zipfile
import pytest

from app.backup_manager import BackupError, create_backup
from app.config import Settings
from app.restore_manager import restore_database
from app.store import Store


def _add_company(store: Store, db: str):
    return store.upsert_company(
        company_id=None,
        company_name=db,
        database_name=db,
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


def test_offline_restore_replaces_database_and_creates_safety_backup(tmp_path,monkeypatch):
    active=tmp_path/"active.db"
    source=tmp_path/"source.db"

    active_store=Store(active)
    _add_company(active_store,"ACTIVE")
    source_store=Store(source)
    _add_company(source_store,"RESTORED")

    settings=Settings(database_file=str(active))
    backup=create_backup(settings,source,backup_dir=tmp_path/"incoming")
    monkeypatch.setattr("app.restore_manager.app_is_running",lambda port:False)

    result=restore_database(settings,Path(backup["path"]),active)

    restored=Store(active)
    assert restored.get_company_by_database("RESTORED") is not None
    assert restored.get_company_by_database("ACTIVE") is None
    assert Path(result["safety_backup"]).exists()
    assert result["integrity"]=="ok"


def test_restore_refuses_while_atas_is_running(tmp_path,monkeypatch):
    active=tmp_path/"active.db"
    source=tmp_path/"source.db"
    Store(active)
    Store(source)
    settings=Settings(database_file=str(active))
    backup=create_backup(settings,source,backup_dir=tmp_path/"incoming")
    monkeypatch.setattr("app.restore_manager.app_is_running",lambda port:True)

    with pytest.raises(BackupError,match="está en ejecución"):
        restore_database(settings,Path(backup["path"]),active)


def test_restore_rejects_tampered_backup_before_touching_active_db(tmp_path,monkeypatch):
    active=tmp_path/"active.db"
    source=tmp_path/"source.db"
    active_store=Store(active)
    _add_company(active_store,"ACTIVE")
    Store(source)
    settings=Settings(database_file=str(active))
    good=create_backup(settings,source,backup_dir=tmp_path/"incoming")
    tampered=tmp_path/"tampered.zip"

    with zipfile.ZipFile(good["path"],"r") as src, zipfile.ZipFile(tampered,"w") as dst:
        for name in src.namelist():
            data=src.read(name)
            if name=="atas.db":
                data+=b"bad"
            dst.writestr(name,data)

    monkeypatch.setattr("app.restore_manager.app_is_running",lambda port:False)
    with pytest.raises(BackupError,match="Backup rechazado"):
        restore_database(settings,tampered,active)

    unchanged=Store(active)
    assert unchanged.get_company_by_database("ACTIVE") is not None
