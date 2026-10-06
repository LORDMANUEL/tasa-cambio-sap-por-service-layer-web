"""Offline command-line restore for Atas SQLite."""
from __future__ import annotations
import argparse
from pathlib import Path

from app.backup_manager import BackupError
from app.config import get_settings
from app.restore_manager import restore_database


def main() -> int:
    parser=argparse.ArgumentParser(description="Restaurar la base SQLite de Atas desde un backup verificado.")
    parser.add_argument("backup",help="Ruta al ZIP de backup de Atas")
    parser.add_argument("--yes",action="store_true",help="Confirmar restauración offline")
    args=parser.parse_args()

    if not args.yes:
        print("RESTORE_ABORTED: use --yes after stopping Atas and confirming the backup.")
        return 2

    settings=get_settings()
    try:
        result=restore_database(settings,Path(args.backup),settings.db_path,require_offline=True)
    except BackupError as exc:
        print(f"RESTORE_FAILED: {exc}")
        return 1

    print("ATAS_RESTORE=OK")
    print(f"DATABASE={result['database']}")
    print(f"SAFETY_BACKUP={result['safety_backup']}")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
