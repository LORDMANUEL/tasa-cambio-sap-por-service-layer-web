from __future__ import annotations
import logging
import re
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler


class SecretFilter(logging.Filter):
    """Redact secret values while preserving useful diagnostic messages."""

    _secret_assignment = re.compile(
        r'''(?ix)(["']?(?:password|passwd|api[_-]?key|authorization|cookie|b1session)["']?\s*[:=]\s*["']?)([^"',}\s;]+)'''
    )

    def filter(self, record):
        message=str(record.getMessage())
        redacted=self._secret_assignment.sub(lambda m: m.group(1)+"***",message)
        if redacted != message:
            record.msg=redacted
            record.args=()
        return True


def configure_logging(settings):
    settings.log_path.mkdir(parents=True,exist_ok=True)
    root=logging.getLogger()
    root.setLevel(logging.INFO)
    fmt=logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    target=(settings.log_path/'sap_fx_service.log').resolve()

    has_file=False
    for handler in root.handlers:
        try:
            current=getattr(handler,'baseFilename',None)
            if current and Path(current).resolve()==target:
                has_file=True
        except Exception:
            pass

    if not has_file:
        fh=TimedRotatingFileHandler(
            target,when='midnight',interval=1,
            backupCount=settings.log_retention_days,encoding='utf-8',
        )
        fh.setFormatter(fmt)
        fh.addFilter(SecretFilter())
        root.addHandler(fh)

    if not any(isinstance(h,logging.StreamHandler) and not isinstance(h,TimedRotatingFileHandler) for h in root.handlers):
        ch=logging.StreamHandler()
        ch.setFormatter(fmt)
        ch.addFilter(SecretFilter())
        root.addHandler(ch)
