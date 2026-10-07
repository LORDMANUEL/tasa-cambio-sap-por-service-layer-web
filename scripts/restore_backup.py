"""Offline command-line restore for Atas SQLite."""
from __future__ import annotations
import argparse
from pathlib import Path

from app.backup_manager import BackupError
from app.config import get_settings
from app.restore_manager import restore_database, restore_support_files, credential_recovery_report


def main() -> int:
    parser=argparse.ArgumentParser(description="Restaurar la base SQLite de Atas desde un backup verificado.")
    parser.add_argument("backup",help="Ruta al ZIP de backup de Atas")
    parser.add_argument("--yes",action="store_true",help="Confirmar restauración offline")
    parser.add_argument("--with-config",action="store_true",help="Restaurar app.env y, en Linux, credential.key si existen")
    args=parser.parse_args()

    if not args.yes:
        print("RESTORE_ABORTED: use --yes after stopping Atas and confirming the backup.")
        return 2

    settings=get_settings()
    try:
        result=restore_database(settings,Path(args.backup),settings.db_path,require_offline=True)
        if args.with_config:
            restore_support_files(
                Path(args.backup),
                restore_environment=True,
                restore_credential_key=(__import__('os').name!='nt'),
            )
        credential_report=credential_recovery_report(settings.db_path)
    except BackupError as exc:
        print(f"RESTORE_FAILED: {exc}")
        return 1

    print("ATAS_RESTORE=OK")
    print(f"DATABASE={result['database']}")
    print(f"SAFETY_BACKUP={result['safety_backup']}")
    print(f"CREDENTIALS_CHECKED={credential_report['checked']}")
    print(f"CREDENTIALS_REENTRY_REQUIRED={len(credential_report['reentry_required'])}")
    for label in credential_report['reentry_required']:
        print(f"REENTER={label}")
    return 0 if credential_report['all_decryptable'] else 3


if __name__=="__main__":
    raise SystemExit(main())
