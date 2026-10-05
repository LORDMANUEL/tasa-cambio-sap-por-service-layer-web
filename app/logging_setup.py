from __future__ import annotations
import logging
from logging.handlers import TimedRotatingFileHandler
class SecretFilter(logging.Filter):
    BAD_KEYS=("password","passwd","authorization","api_key","cookie","b1session")
    def filter(self,record):
        if any(k in str(record.getMessage()).lower() for k in self.BAD_KEYS): record.msg='[REDACTED SECURITY-SENSITIVE LOG MESSAGE]'; record.args=()
        return True
def configure_logging(settings):
    settings.log_path.mkdir(parents=True,exist_ok=True); root=logging.getLogger(); root.setLevel(logging.INFO)
    if root.handlers: return
    fmt=logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    fh=TimedRotatingFileHandler(settings.log_path/'sap_fx_service.log',when='midnight',interval=1,backupCount=settings.log_retention_days,encoding='utf-8'); fh.setFormatter(fmt); fh.addFilter(SecretFilter())
    ch=logging.StreamHandler(); ch.setFormatter(fmt); ch.addFilter(SecretFilter()); root.addHandler(fh); root.addHandler(ch)
