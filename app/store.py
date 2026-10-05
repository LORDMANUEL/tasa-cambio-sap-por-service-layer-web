"""SQLite persistence for Atas V5.

V5 is intentionally generic: a fresh installation contains no company-specific
SAP databases. The first-run wizard creates the deployment identity, Service
Layer endpoints and one or more SAP companies.
"""
from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS companies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  company_name TEXT NOT NULL,
  database_name TEXT NOT NULL UNIQUE,
  db_type TEXT NOT NULL DEFAULT 'HANA',
  environment TEXT NOT NULL CHECK(environment IN ('TEST','PROD')),
  enabled INTEGER NOT NULL DEFAULT 1,
  allow_write INTEGER NOT NULL DEFAULT 0,
  scheduled_write INTEGER NOT NULL DEFAULT 0,
  auto_enabled INTEGER NOT NULL DEFAULT 0,
  schedule_hour INTEGER NOT NULL DEFAULT 6,
  schedule_minute INTEGER NOT NULL DEFAULT 0,
  use_usd INTEGER NOT NULL DEFAULT 1,
  use_eur INTEGER NOT NULL DEFAULT 1,
  last_run_date TEXT,
  last_run_at TEXT,
  last_run_status TEXT,
  last_run_message TEXT,
  sap_user TEXT NOT NULL DEFAULT '',
  sap_secret TEXT,
  primary_bank TEXT NOT NULL DEFAULT 'BANPAIS',
  secondary_bank TEXT NOT NULL DEFAULT 'FICOHSA',
  service_layer_root TEXT,
  odata_version TEXT,
  sap_b1_version TEXT,
  bank_source_codes TEXT NOT NULL DEFAULT '',
  currencies_csv TEXT NOT NULL DEFAULT 'USD,EUR',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS app_settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  occurred_at TEXT NOT NULL,
  company_id INTEGER,
  company_db TEXT NOT NULL,
  company_name TEXT,
  environment TEXT,
  currency TEXT NOT NULL,
  primary_bank TEXT,
  secondary_bank TEXT,
  sap_before TEXT,
  bank_rate TEXT,
  sap_after TEXT,
  decision TEXT,
  status TEXT NOT NULL,
  verified INTEGER NOT NULL DEFAULT 0,
  error TEXT,
  details_json TEXT,
  FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_transactions_time ON transactions(occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_company ON transactions(company_db, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status, occurred_at DESC);
CREATE TABLE IF NOT EXISTS bank_checks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  checked_at TEXT NOT NULL,
  bank TEXT NOT NULL,
  ok INTEGER NOT NULL,
  usd_buy TEXT,
  usd_sell TEXT,
  eur_buy TEXT,
  eur_sell TEXT,
  error TEXT
);
CREATE INDEX IF NOT EXISTS idx_bank_checks_time ON bank_checks(checked_at DESC);
CREATE TABLE IF NOT EXISTS bank_sources (
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
CREATE INDEX IF NOT EXISTS idx_bank_sources_enabled ON bank_sources(enabled, code);
"""

class Store:
    def __init__(self, path: Path, timezone: str = "America/Tegucigalpa"):
        self.path = Path(path)
        self.timezone = timezone
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def now(self) -> str:
        return datetime.now(ZoneInfo(self.timezone)).isoformat()

    @contextmanager
    def conn(self):
        con = sqlite3.connect(self.path, timeout=15)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def _migrate_companies(self, con: sqlite3.Connection) -> None:
        existing = {r[1] for r in con.execute("PRAGMA table_info(companies)").fetchall()}
        additions = {
            "db_type": "TEXT NOT NULL DEFAULT 'HANA'",
            "scheduled_write": "INTEGER NOT NULL DEFAULT 0",
            "auto_enabled": "INTEGER NOT NULL DEFAULT 0",
            "schedule_hour": "INTEGER NOT NULL DEFAULT 6",
            "schedule_minute": "INTEGER NOT NULL DEFAULT 0",
            "use_usd": "INTEGER NOT NULL DEFAULT 1",
            "use_eur": "INTEGER NOT NULL DEFAULT 1",
            "last_run_date": "TEXT",
            "last_run_at": "TEXT",
            "last_run_status": "TEXT",
            "last_run_message": "TEXT",
            "service_layer_root": "TEXT",
            "odata_version": "TEXT",
            "sap_b1_version": "TEXT",
            "bank_source_codes": "TEXT NOT NULL DEFAULT ''",
            "currencies_csv": "TEXT NOT NULL DEFAULT 'USD,EUR'",
        }
        for name, ddl in additions.items():
            if name not in existing:
                con.execute(f"ALTER TABLE companies ADD COLUMN {name} {ddl}")

    def initialize(self) -> None:
        with self.conn() as con:
            con.executescript(SCHEMA)
            self._migrate_companies(con)
            defaults = {
                "log_retention_days": "30",
                "service_layer_root": "",
                "odata_version": "v2",
                "sap_b1_version": "10.0",
                "organization_name": "Mi Empresa",
                "organization_logo": "",
                "setup_complete": "false",
                "prod_automation_enabled": "false",
                "notifications_enabled": "false",
                "smtp_host": "",
                "smtp_port": "587",
                "smtp_security": "STARTTLS",
                "smtp_user": "",
                "smtp_from": "",
                "smtp_secret": "",
                "notification_recipients": "",
                "notify_success": "true",
                "notify_errors": "true",
                "min_market_sources": "3",
                "max_source_deviation_percent": "2.0",
            }
            for k, v in defaults.items():
                con.execute("INSERT OR IGNORE INTO app_settings(key,value,updated_at) VALUES(?,?,?)", (k, v, self.now()))

    def list_companies(self, enabled_only: bool = False):
        sql = "SELECT * FROM companies" + (" WHERE enabled=1" if enabled_only else "") + " ORDER BY environment, company_name"
        with self.conn() as con:
            return [dict(r) for r in con.execute(sql).fetchall()]

    def get_company(self, company_id: int):
        with self.conn() as con:
            row = con.execute("SELECT * FROM companies WHERE id=?", (company_id,)).fetchone()
            return dict(row) if row else None

    def upsert_company(self, *, company_id: int | None, company_name: str, database_name: str, environment: str,
                       enabled: bool, allow_write: bool, scheduled_write: bool, auto_enabled: bool,
                       schedule_hour: int, schedule_minute: int, use_usd: bool, use_eur: bool,
                       sap_user: str, primary_bank: str, secondary_bank: str, db_type: str = "HANA",
                       service_layer_root: str = "", odata_version: str = "", sap_b1_version: str = "",
                       bank_source_codes: str = "", currencies_csv: str = "USD,EUR") -> int:
        env = environment.upper().strip()
        if env not in {"TEST", "PROD"}: raise ValueError("environment inválido")
        dbt = db_type.upper().strip()
        if dbt not in {"HANA", "SQLSERVER", "SQL SERVER"}: raise ValueError("Tipo de BD inválido")
        dbt = "SQLSERVER" if dbt.startswith("SQL") else "HANA"
        if not company_name.strip(): raise ValueError("Nombre de empresa requerido")
        if not database_name.strip(): raise ValueError("Nombre de base requerido")
        if not sap_user.strip(): raise ValueError("Usuario SAP requerido")
        if not (use_usd or use_eur): raise ValueError("Seleccione al menos USD o EUR")
        hour=max(0,min(23,int(schedule_hour))); minute=max(0,min(59,int(schedule_minute)))
        now = self.now()
        root = service_layer_root.strip().rstrip('/')
        od = odata_version.strip().lower()
        codes=",".join(dict.fromkeys(x.strip().upper() for x in bank_source_codes.split(",") if x.strip()))
        currencies=",".join(dict.fromkeys(x.strip().upper() for x in currencies_csv.split(",") if x.strip())) or ("USD,EUR" if use_eur else "USD")
        values=(company_name.strip(),database_name.strip(),dbt,env,int(enabled),int(allow_write),int(scheduled_write),int(auto_enabled),hour,minute,int(use_usd),int(use_eur),sap_user.strip(),primary_bank.upper(),secondary_bank.upper(),root,od,sap_b1_version.strip(),codes,currencies,now)
        with self.conn() as con:
            if company_id:
                con.execute("""UPDATE companies SET company_name=?,database_name=?,db_type=?,environment=?,enabled=?,allow_write=?,scheduled_write=?,auto_enabled=?,schedule_hour=?,schedule_minute=?,use_usd=?,use_eur=?,sap_user=?,primary_bank=?,secondary_bank=?,service_layer_root=?,odata_version=?,sap_b1_version=?,bank_source_codes=?,currencies_csv=?,updated_at=? WHERE id=?""", (*values,company_id))
                return company_id
            cur = con.execute("""INSERT INTO companies(company_name,database_name,db_type,environment,enabled,allow_write,scheduled_write,auto_enabled,schedule_hour,schedule_minute,use_usd,use_eur,sap_user,primary_bank,secondary_bank,service_layer_root,odata_version,sap_b1_version,bank_source_codes,currencies_csv,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (*values,now))
            return int(cur.lastrowid)

    def set_secret_blob(self, company_id: int, blob: str) -> None:
        with self.conn() as con:
            con.execute("UPDATE companies SET sap_secret=?, updated_at=? WHERE id=?", (blob,self.now(),company_id))

    def claim_daily_run(self, company_id:int, day:str) -> bool:
        """Atomically claim a company's automatic run for one local calendar day.

        This closes the race between "is it due?" and "mark it as executed".
        Even if two scheduler loops reach the same CompanyDB simultaneously,
        SQLite allows only one UPDATE to change the row for that date.
        """
        now=self.now()
        with self.conn() as con:
            cur=con.execute(
                """UPDATE companies
                   SET last_run_date=?, last_run_at=?, last_run_status='RUNNING',
                       last_run_message='Ejecución diaria reclamada', updated_at=?
                   WHERE id=? AND COALESCE(last_run_date,'')<>?""",
                (day,now,now,company_id,day)
            )
            return cur.rowcount==1

    def mark_run_result(self, company_id:int, day:str, status:str, message:str='') -> None:
        now=self.now()
        with self.conn() as con:
            con.execute("UPDATE companies SET last_run_date=?, last_run_at=?, last_run_status=?, last_run_message=?, updated_at=? WHERE id=?", (day,now,status,message[:500],now,company_id))

    def delete_company(self, company_id: int) -> None:
        with self.conn() as con:
            con.execute("DELETE FROM companies WHERE id=?", (company_id,))

    def get_settings(self) -> dict[str,str]:
        with self.conn() as con:
            return {r["key"]: r["value"] for r in con.execute("SELECT key,value FROM app_settings")}

    def set_settings(self, values: dict[str,str]) -> None:
        with self.conn() as con:
            for k,v in values.items():
                con.execute("INSERT INTO app_settings(key,value,updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at", (k,str(v),self.now()))

    def add_transaction(self, row: dict) -> int:
        fields = ["occurred_at","company_id","company_db","company_name","environment","currency","primary_bank","secondary_bank","sap_before","bank_rate","sap_after","decision","status","verified","error","details_json"]
        row = dict(row); row.setdefault("occurred_at", self.now()); row.setdefault("verified", 0); row.setdefault("details_json", None)
        vals = [row.get(f) for f in fields]
        with self.conn() as con:
            cur = con.execute(f"INSERT INTO transactions({','.join(fields)}) VALUES({','.join(['?']*len(fields))})", vals)
            return int(cur.lastrowid)

    def list_transactions(self, limit: int=200, company_db: str|None=None, status: str|None=None, since: str|None=None):
        sql="SELECT * FROM transactions WHERE 1=1"; params=[]
        if company_db: sql+=" AND company_db=?"; params.append(company_db)
        if status: sql+=" AND status=?"; params.append(status)
        if since: sql+=" AND occurred_at>=?"; params.append(since)
        sql+=" ORDER BY occurred_at DESC LIMIT ?"; params.append(limit)
        with self.conn() as con: return [dict(r) for r in con.execute(sql,params).fetchall()]

    def add_bank_check(self, bank: str, ok: bool, rates=None, error: str|None=None):
        rates=rates or {}; usd=rates.get('usd',{}); eur=rates.get('eur',{})
        with self.conn() as con:
            con.execute("INSERT INTO bank_checks(checked_at,bank,ok,usd_buy,usd_sell,eur_buy,eur_sell,error) VALUES(?,?,?,?,?,?,?,?)", (self.now(),bank,int(ok),usd.get('buy'),usd.get('sell'),eur.get('buy'),eur.get('sell'),error))

    def recent_bank_checks(self, limit:int=50):
        with self.conn() as con: return [dict(r) for r in con.execute("SELECT * FROM bank_checks ORDER BY checked_at DESC LIMIT ?",(limit,)).fetchall()]

    def transaction_summary(self, since: str | None = None) -> dict:
        where="WHERE occurred_at>=?" if since else ""; params=(since,) if since else ()
        with self.conn() as con:
            rows=con.execute(f"SELECT status,COUNT(*) n FROM transactions {where} GROUP BY status",params).fetchall()
        d={r['status']:r['n'] for r in rows}; d['total']=sum(d.values()); return d

    def daily_activity(self, days: int = 7) -> list[dict]:
        since=(datetime.now(ZoneInfo(self.timezone))-timedelta(days=days-1)).date().isoformat()
        with self.conn() as con:
            return [dict(r) for r in con.execute("SELECT substr(occurred_at,1,10) day, COUNT(*) total, SUM(CASE WHEN status='ERROR' THEN 1 ELSE 0 END) errors FROM transactions WHERE occurred_at>=? GROUP BY day ORDER BY day",(since,)).fetchall()]

    def company_health(self) -> list[dict]:
        with self.conn() as con:
            return [dict(r) for r in con.execute("""SELECT c.*, (SELECT t.status FROM transactions t WHERE t.company_db=c.database_name ORDER BY t.occurred_at DESC LIMIT 1) latest_status, (SELECT t.occurred_at FROM transactions t WHERE t.company_db=c.database_name ORDER BY t.occurred_at DESC LIMIT 1) latest_at FROM companies c ORDER BY c.environment,c.company_name""").fetchall()]

    def status_breakdown(self, limit: int = 10000) -> list[dict]:
        with self.conn() as con:
            return [dict(r) for r in con.execute("SELECT status,COUNT(*) total FROM (SELECT status FROM transactions ORDER BY occurred_at DESC LIMIT ?) GROUP BY status ORDER BY total DESC",(limit,)).fetchall()]

    def list_bank_sources(self, enabled_only: bool = False):
        sql = "SELECT * FROM bank_sources" + (" WHERE enabled=1" if enabled_only else "") + " ORDER BY country,name"
        with self.conn() as con:
            return [dict(r) for r in con.execute(sql).fetchall()]

    def get_bank_source(self, source_id: int):
        with self.conn() as con:
            row=con.execute("SELECT * FROM bank_sources WHERE id=?",(source_id,)).fetchone()
            return dict(row) if row else None

    def get_bank_source_by_code(self, code: str):
        with self.conn() as con:
            row=con.execute("SELECT * FROM bank_sources WHERE upper(code)=upper(?)",(code,)).fetchone()
            return dict(row) if row else None

    def upsert_bank_source(self, *, source_id: int|None, code: str, name: str, country: str, source_type: str, url: str, enabled: bool, config_json: str, headers_json: str='{}', timeout_seconds: int=15, tls_verify: bool=True) -> int:
        import json
        code=code.strip().upper().replace(' ','_')
        if not code or not name.strip(): raise ValueError('Código y nombre de fuente son requeridos')
        st=source_type.strip().upper()
        if st not in {'PRESET','WEB_HTML','API_JSON'}: raise ValueError('Tipo de fuente inválido')
        try: json.loads(config_json or '{}'); json.loads(headers_json or '{}')
        except Exception as exc: raise ValueError('Configuración/headers deben ser JSON válido') from exc
        now=self.now(); vals=(code,name.strip(),country.strip(),st,url.strip(),int(enabled),config_json or '{}',headers_json or '{}',max(3,min(60,int(timeout_seconds))),int(tls_verify),now)
        with self.conn() as con:
            if source_id:
                con.execute("UPDATE bank_sources SET code=?,name=?,country=?,source_type=?,url=?,enabled=?,config_json=?,headers_json=?,timeout_seconds=?,tls_verify=?,updated_at=? WHERE id=?",(*vals,source_id)); return source_id
            cur=con.execute("INSERT INTO bank_sources(code,name,country,source_type,url,enabled,config_json,headers_json,timeout_seconds,tls_verify,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(*vals,now)); return int(cur.lastrowid)

    def set_bank_source_secret_headers(self, source_id:int, blob:str|None) -> None:
        with self.conn() as con:
            con.execute("UPDATE bank_sources SET secret_headers_blob=?,updated_at=? WHERE id=?",(blob,self.now(),source_id))

    def delete_bank_source(self, source_id: int) -> None:
        with self.conn() as con: con.execute("DELETE FROM bank_sources WHERE id=?",(source_id,))

    def mark_bank_source_result(self, source_id: int, ok: bool, message: str='') -> None:
        with self.conn() as con:
            con.execute("UPDATE bank_sources SET last_status=?,last_error=?,last_checked_at=?,updated_at=? WHERE id=?",('OK' if ok else 'ERROR','' if ok else message[:500],self.now(),self.now(),source_id))

    def cleanup(self, days:int) -> None:
        cutoff=(datetime.now(ZoneInfo(self.timezone))-timedelta(days=days)).isoformat()
        with self.conn() as con:
            con.execute("DELETE FROM bank_checks WHERE checked_at<?",(cutoff,))
