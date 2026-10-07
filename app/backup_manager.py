"""Safe local backup helpers for Atas."""
from __future__ import annotations
import hashlib, json, os, sqlite3, tempfile, zipfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from app.config import BASE_DIR, Settings
from app.version import get_version

class BackupError(RuntimeError): pass

def sqlite_integrity(path: Path) -> tuple[bool,str]:
    db=Path(path)
    if not db.exists(): return False,"DATABASE_NOT_FOUND"
    try:
        con=sqlite3.connect(f"file:{db.as_posix()}?mode=ro",uri=True,timeout=15)
        try: rows=[str(r[0]) for r in con.execute("PRAGMA integrity_check").fetchall()]
        finally: con.close()
    except sqlite3.Error as exc: return False,str(exc)
    ok=rows==["ok"]
    return ok,"ok" if ok else "; ".join(rows[:20])

def _sha256(path: Path) -> str:
    h=hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda:fh.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def _credential_key_path() -> Path|None:
    if os.name=="nt": return None
    raw=os.environ.get("SAPFX_FERNET_KEY_FILE","").strip()
    p=Path(raw) if raw else BASE_DIR/"data"/".credential.key"
    return p if p.exists() else None

def validate_backup(archive_path: Path) -> dict:
    archive=Path(archive_path)
    if not archive.exists(): return {"valid":False,"message":"BACKUP_NOT_FOUND","manifest":None}
    try:
        with zipfile.ZipFile(archive,"r") as zf:
            names=set(zf.namelist())
            if not {"atas.db","manifest.json"}.issubset(names):
                return {"valid":False,"message":"BACKUP_STRUCTURE_INVALID","manifest":None}
            manifest=json.loads(zf.read("manifest.json").decode("utf-8"))
            with tempfile.TemporaryDirectory(prefix="atas-validate-") as td:
                db=Path(td)/"atas.db"; db.write_bytes(zf.read("atas.db"))
                if _sha256(db)!=manifest.get("database_sha256"):
                    return {"valid":False,"message":"DATABASE_HASH_MISMATCH","manifest":manifest}
                ok,message=sqlite_integrity(db)
                if not ok: return {"valid":False,"message":message,"manifest":manifest}
    except (OSError,zipfile.BadZipFile,json.JSONDecodeError,KeyError) as exc:
        return {"valid":False,"message":str(exc),"manifest":None}
    return {"valid":True,"message":"ok","manifest":manifest}

def create_backup(settings: Settings, db_path: Path, *, backup_dir: Path|None=None) -> dict:
    source=Path(db_path).resolve()
    ok,message=sqlite_integrity(source)
    if not ok: raise BackupError(f"Base SQLite no íntegra: {message}")
    target=Path(backup_dir or settings.data_path/"backups").resolve()
    target.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(ZoneInfo(settings.timezone)).strftime("%Y%m%d-%H%M%S")
    archive=target/f"atas-backup-{stamp}.zip"
    with tempfile.TemporaryDirectory(prefix="atas-backup-") as td:
        temp=Path(td); snapshot=temp/"atas.db"
        src=sqlite3.connect(source,timeout=15); dst=sqlite3.connect(snapshot)
        try: src.backup(dst)
        finally: dst.close(); src.close()
        ok,message=sqlite_integrity(snapshot)
        if not ok: raise BackupError(f"Snapshot SQLite no íntegro: {message}")
        env=BASE_DIR/".env"; key=_credential_key_path()
        files={"database":"atas.db"}
        if env.exists(): files["environment"]="app.env"
        if key: files["credential_key"]="credential.key"
        manifest={
            "product":"Atas",
            "version":get_version(),
            "created_at":datetime.now(ZoneInfo(settings.timezone)).isoformat(),
            "timezone":settings.timezone,
            "database_sha256":_sha256(snapshot),
            "database_integrity":"ok",
            "files":files,
            "credential_scheme":"DPAPI" if os.name=="nt" else "FERNET",
            "credential_portable":bool(key) if os.name!="nt" else False,
            "warning":"SENSITIVE_BACKUP_CONTAINS_CONFIGURATION_AND_ENCRYPTED_CREDENTIAL_MATERIAL",
        }
        (temp/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
        with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(snapshot,"atas.db"); zf.write(temp/"manifest.json","manifest.json")
            if env.exists(): zf.write(env,"app.env")
            if key: zf.write(key,"credential.key")
    checked=validate_backup(archive)
    if not checked["valid"]:
        archive.unlink(missing_ok=True); raise BackupError("Backup inválido: "+checked["message"])
    return {"path":str(archive),"name":archive.name,"size":archive.stat().st_size,"sha256":_sha256(archive),"manifest":checked["manifest"]}
