"""Pure runtime configuration helpers for Atas."""
from __future__ import annotations

import re
from pathlib import Path


def set_env_value(root: Path, key: str, value: str) -> None:
    """Persist one key in the installation .env file without rewriting others."""
    env=Path(root)/".env"
    lines=env.read_text(encoding="utf-8").splitlines() if env.exists() else []
    out=[]
    found=False
    for line in lines:
        if line.startswith(key+"="):
            out.append(f"{key}={value}")
            found=True
        else:
            out.append(line)
    if not found:
        out.append(f"{key}={value}")
    env.write_text("\n".join(out)+"\n",encoding="utf-8")


def service_layer_endpoint(root: str, version: str) -> str:
    """Normalize a Service Layer root and append the selected OData version."""
    normalized=re.sub(r"/v\d+$","",str(root or "").strip().rstrip("/"),flags=re.I)
    od=(version or "v2").strip().lower()
    return f"{normalized}/{od}" if normalized else ""


def effective_company_endpoint(company: dict, app_config: dict) -> str:
    """Resolve per-company Service Layer overrides over global defaults."""
    return service_layer_endpoint(
        company.get("service_layer_root") or app_config.get("service_layer_root",""),
        company.get("odata_version") or app_config.get("odata_version","v2"),
    )
