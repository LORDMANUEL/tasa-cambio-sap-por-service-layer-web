"""Offline restore helpers for Atas SQLite backups."""
from __future__ import annotations

import json
import os
import tempfile
import urllib.error
import urllib.request
import zipfile
import sqlite3
from pathlib import Path

from app.backup_manager import BackupError, create_backup, sqlite_integrity, validate_backup
from app.config import BASE_DIR, Settings
from app.credential_store import CredentialError, decrypt_secret


def app_is_running(port: int, timeout: float=0.75) -> bool:
    """Return True only when the local Atas health endpoint is responding."""
    url=f"http://127.0.0.1:{int(port)}/health"
    try:
        with urllib.request.urlopen(url,timeout=timeout) as response:
            payload=json.loads(response.read().decode("utf-8"))
        return payload.get("status")=="ok" and payload.get("service")=="Atas"
    except (OSError,urllib.error.URLError,json.JSONDecodeError,ValueError):
        return False


def _database_from_archive(archive: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive,"r") as zf:
        destination.write_bytes(zf.read("atas.db"))


def restore_database(
    settings: Settings,
    archive_path: Path,
    db_path: Path,
    *,
    require_offline: bool=True,
) -> dict:
    """Restore only atas.db from a verified backup.

    Atas must be stopped. A verified safety backup of the current database is
    created first. Configuration and encryption material are deliberately not
    replaced by this function.
    """
    archive=Path(archive_path).resolve()
    target=Path(db_path).resolve()

    checked=validate_backup(archive)
    if not checked["valid"]:
        raise BackupError("Backup rechazado: "+checked["message"])
    if require_offline and app_is_running(settings.app_port):
        raise BackupError("Atas está en ejecución. Detenga el servicio antes de restaurar.")
    if not target.exists():
        raise BackupError("No existe la base activa que se desea reemplazar.")

    safety_dir=target.parent/"backups"/"pre-restore"
    safety=create_backup(settings,target,backup_dir=safety_dir)

    with tempfile.TemporaryDirectory(prefix="atas-restore-") as td:
        temp=Path(td)
        candidate=temp/"atas.db"
        _database_from_archive(archive,candidate)
        ok,message=sqlite_integrity(candidate)
        if not ok:
            raise BackupError("La base candidata no es íntegra: "+message)

        rollback=temp/"current.db"
        os.replace(target,rollback)
        try:
            os.replace(candidate,target)
            ok,message=sqlite_integrity(target)
            if not ok:
                raise BackupError("La base restaurada falló integrity_check: "+message)
        except Exception:
            if target.exists():
                target.unlink(missing_ok=True)
            os.replace(rollback,target)
            raise

    return {
        "restored":True,
        "database":str(target),
        "source_backup":str(archive),
        "safety_backup":safety["path"],
        "source_manifest":checked["manifest"],
        "integrity":"ok",
    }



def restore_support_files(
    archive_path: Path,
    *,
    restore_environment: bool=False,
    restore_credential_key: bool=False,
    environment_target: Path | None=None,
    credential_key_target: Path | None=None,
) -> dict:
    """Restore optional support files without exposing their contents."""
    archive=Path(archive_path).resolve()
    checked=validate_backup(archive)
    if not checked["valid"]:
        raise BackupError("Backup rechazado: "+checked["message"])

    restored=[]
    with zipfile.ZipFile(archive,"r") as zf:
        names=set(zf.namelist())
        if restore_environment and "app.env" in names:
            target=Path(environment_target or (BASE_DIR/".env"))
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(zf.read("app.env"))
            restored.append(str(target))

        if restore_credential_key:
            if os.name=="nt":
                raise BackupError(
                    "Windows usa DPAPI: no existe una clave portable que pueda restaurarse. "
                    "Si cambia de equipo/usuario, reingrese las credenciales."
                )
            if "credential.key" not in names:
                raise BackupError("El backup no contiene credential.key.")
            raw=os.environ.get("SAPFX_FERNET_KEY_FILE","").strip()
            target=Path(credential_key_target or (Path(raw) if raw else BASE_DIR/"data"/".credential.key"))
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(zf.read("credential.key"))
            target.chmod(0o600)
            restored.append(str(target))

    return {"restored_support_files":restored}


def credential_recovery_report(db_path: Path) -> dict:
    """Verify encrypted blobs after restore without exposing secret values."""
    db=Path(db_path)
    con=sqlite3.connect(db)
    con.row_factory=sqlite3.Row
    items=[]
    try:
        for row in con.execute("SELECT id,database_name,sap_secret FROM companies WHERE sap_secret IS NOT NULL AND sap_secret<>''"):
            items.append((f"company:{row['database_name']}:sap",row["sap_secret"]))
        for row in con.execute("SELECT code,secret_headers_blob FROM bank_sources WHERE secret_headers_blob IS NOT NULL AND secret_headers_blob<>''"):
            items.append((f"bank:{row['code']}:headers",row["secret_headers_blob"]))
        row=con.execute("SELECT value FROM app_settings WHERE key='smtp_secret'").fetchone()
        if row and row["value"]:
            items.append(("settings:smtp",row["value"]))
    finally:
        con.close()

    ok=[]; reentry=[]
    for label,blob in items:
        try:
            decrypt_secret(str(blob))
            ok.append(label)
        except (CredentialError,ValueError,TypeError):
            reentry.append(label)

    return {
        "checked":len(items),
        "decryptable":ok,
        "reentry_required":reentry,
        "all_decryptable":not reentry,
    }
