"""Typed application configuration for Atas V5."""
from pathlib import Path
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR=Path(__file__).resolve().parent.parent
LEGACY_DB=BASE_DIR/'data'/'tasa_v5.db'
ATAS_DB=BASE_DIR/'data'/'atas.db'

class Settings(BaseSettings):
    model_config=SettingsConfigDict(env_file=BASE_DIR/'.env',env_file_encoding='utf-8',extra='ignore')
    app_name:str='Atas V5'
    app_env:str='production'
    app_port:int=8787
    web_admin_user:str=''
    web_admin_password_hash:str=''
    web_session_secret:str=''
    timezone:str='America/Tegucigalpa'
    request_timeout_seconds:int=Field(default=15,ge=3,le=60)
    tls_verify:bool=True
    usd_min:float=15.0
    usd_max:float=45.0
    eur_min:float=15.0
    eur_max:float=60.0
    max_bank_spread_percent:float=8.0
    log_retention_days:int=30
    data_dir:str='data'
    log_dir:str='logs'
    database_file:str='data/atas.db'
    sap_base_url:str=''
    sap_verify_tls:bool=False
    sap_timeout_seconds:int=30

    @property
    def log_path(self) -> Path:
        return (BASE_DIR / self.log_dir).resolve()

    @property
    def data_path(self) -> Path:
        return (BASE_DIR / self.data_dir).resolve()

    @property
    def db_path(self) -> Path:
        return (BASE_DIR / self.database_file).resolve()

def _migrate_legacy_db(settings:Settings)->Settings:
    """Migrate the historical V5 SQLite filename without discarding user data.

    New installations use data/atas.db. Older installations may still have
    data/tasa_v5.db or an old DATABASE_FILE entry in .env. When that exact
    legacy filename is detected, Atas migrates the file and updates the local
    .env entry. Custom database paths are never modified.
    """
    normalized=str(settings.database_file).replace('\\','/').strip()
    if normalized!='data/tasa_v5.db':
        return settings

    ATAS_DB.parent.mkdir(parents=True,exist_ok=True)
    if LEGACY_DB.exists() and not ATAS_DB.exists():
        LEGACY_DB.replace(ATAS_DB)

    if ATAS_DB.exists():
        settings.database_file='data/atas.db'
        env_path=BASE_DIR/'.env'
        if env_path.exists():
            lines=env_path.read_text(encoding='utf-8').splitlines()
            out=[]
            found=False
            for line in lines:
                if line.startswith('DATABASE_FILE='):
                    out.append('DATABASE_FILE=data/atas.db')
                    found=True
                else:
                    out.append(line)
            if not found:
                out.append('DATABASE_FILE=data/atas.db')
            env_path.write_text('\n'.join(out)+'\n',encoding='utf-8')
    return settings

@lru_cache
def get_settings() -> Settings:
    """Return the cached, migrated application settings."""
    return _migrate_legacy_db(Settings())
