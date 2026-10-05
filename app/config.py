"""Typed application configuration for Atas V5."""
from pathlib import Path
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
BASE_DIR=Path(__file__).resolve().parent.parent
class Settings(BaseSettings):
    model_config=SettingsConfigDict(env_file=BASE_DIR/'.env',env_file_encoding='utf-8',extra='ignore')
    app_name:str='Atas V5'; app_env:str='production'; app_host:str='127.0.0.1'; app_port:int=8787; app_api_key:str=''; web_admin_user:str=''; web_admin_password_hash:str=''; web_session_secret:str=''; timezone:str='America/Tegucigalpa'; request_timeout_seconds:int=Field(default=15,ge=3,le=60); tls_verify:bool=True; usd_min:float=15.0; usd_max:float=45.0; eur_min:float=15.0; eur_max:float=60.0; max_bank_spread_percent:float=8.0; log_retention_days:int=30; data_dir:str='data'; log_dir:str='logs'; database_file:str='data/tasa_v5.db'; sap_enabled:bool=True; sap_base_url:str=''; sap_verify_tls:bool=False; sap_timeout_seconds:int=30; sap_allow_prod_write:bool=False
    @property
    def log_path(self): return (BASE_DIR/self.log_dir).resolve()
    @property
    def data_path(self): return (BASE_DIR/self.data_dir).resolve()
    @property
    def db_path(self): return (BASE_DIR/self.database_file).resolve()
@lru_cache
def get_settings(): return Settings()
