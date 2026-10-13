# TRD — Technical Requirements Document — Atas V5.0.4

## 1. Arquitectura

```text
Browser local
   ↓
FastAPI / routers
   ↓
Servicios de aplicación
   ├─ motor de fuentes
   ├─ scheduler
   ├─ política de reconciliación
   ├─ backup/restore
   └─ notificaciones
   ↓
Persistencia SQLite WAL
   ↓
Integraciones
   ├─ SAP Business One Service Layer
   ├─ Bancos / APIs / HTML
   └─ SMTP saliente
```

## 2. Stack

- Python 3.13.
- FastAPI + Uvicorn.
- SQLite.
- requests.
- BeautifulSoup.
- openpyxl para BCH XLSX.
- cryptography/Fernet en Linux.
- DPAPI nativo en Windows.
- HTML/CSS/JavaScript local.
- pytest.
- GitHub Actions.
- Inno Setup.
- Debian package/systemd.

## 3. Componentes

### `app/main.py`

Composición FastAPI y rutas aún no extraídas. La modularización es incremental.

### `app/routes/`

- `auth.py`: login/logout.
- `backup.py`: backup web.

### `app/sync_engine.py`

Reglas de reconciliación SAP/fuentes, tasa repetida, CREATE/UPDATE/MATCH y scheduler diario.

### `app/market_sources.py`

Normaliza fuentes y construye consenso por moneda.

### `app/providers/`

Conectores PRESET. BCH es referencia USD estructurada; Banpaís/Ficohsa son fuentes comerciales históricas incluidas.

### `app/store.py`

SQLite, esquema, migraciones, claims atómicos, auditoría y evidencia diaria.

### `app/sap_client.py`

Sesión Service Layer, GET/POST y manejo de errores.

### `app/credential_store.py`

DPAPI/Fernet.

### `app/backup_manager.py` y `app/restore_manager.py`

Snapshot, SHA-256, integrity_check, rollback y recuperación de soporte.

### `app/runtime_config.py` y `app/scheduler_runtime.py`

Configuración runtime y ciclo scheduler desacoplados de la UI.

## 4. Requisitos técnicos de integración SAP

- endpoint raíz debe usar http/https e incluir `/b1s`;
- OData `v1` o `v2`;
- login por CompanyDB;
- timeout configurable;
- TLS configurable;
- logout al cerrar sesión;
- POST sólo cuando gates de escritura lo permiten;
- GET de verificación obligatorio.

## 5. Requisitos técnicos de fuentes

- timeout;
- límite de respuesta;
- TLS por fuente;
- headers públicos y secretos;
- no-cache/no-store en consultas;
- Decimal para valores;
- validación buy/sell;
- rango esperado;
- spread;
- mediana;
- outlier de oficial;
- mínimo de fuentes por moneda;
- evidencia `raw_hash`.

## 6. Scheduler

- loop local;
- claim atómico SQLite;
- una ejecución diaria por empresa salvo reintento explícito;
- reintentos de tasa repetida cada 20 minutos;
- ventana de validación 60 minutos;
- recuperación conservadora de `RUNNING` abandonado;
- no auto-repetir una operación incierta tras crash.

## 7. Seguridad

- sesión web firmada;
- cookie HttpOnly + SameSite strict;
- CSP, X-Frame-Options, nosniff;
- secretos cifrados;
- logs sin secretos;
- secret scan de árbol e historial;
- PROD con gates separados;
- backup considerado sensible.

## 8. Distribución

Windows:
- EXE x64 con Python embebido;
- Portable x64;
- single-instance;
- smoke test.

Debian/Ubuntu:
- DEB amd64;
- venv;
- systemd;
- smoke test.

## 9. Calidad

Gate mínimo:

```bash
python -m compileall -q app
node --check app/static/app.js
python -m pytest -q
python scripts/security/scan_secrets.py --history
```

Build de referencia previo al cierre V5.0.4: **701 tests por plataforma**.
