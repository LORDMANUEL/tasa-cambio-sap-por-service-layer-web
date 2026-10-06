"""Offline restore helpers for Atas SQLite backups."""
from __future__ import annotations

import json
import os
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from app.backup_manager import BackupError, create_backup, sqlite_integrity, validate_backup
from app.config import Settings


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
