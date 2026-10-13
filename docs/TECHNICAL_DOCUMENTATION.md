# Documentación técnica consolidada — Atas V5.0.4

## Arranque

Código fuente:

```bash
python -m app.run_server
```

Health:

```text
GET /health
```

## Configuración

Variables estáticas en `.env`; configuración operativa en SQLite.

La resolución de endpoint usa override por CompanyDB sobre configuración global.

## SAP

Cliente: `app/sap_client.py`.

Reconciliación: `app/sync_engine.py`.

Nunca marcar una escritura como exitosa antes del GET posterior.

## Fuentes

Motor: `app/market_sources.py`.

Presets: `app/providers/`.

Custom: WEB_HTML/API_JSON.

No agregar un banco hardcodeado si puede expresarse con configuración estable.

## Persistencia

`app/store.py`.

Todas las migraciones V5 deben preservar datos.

## Seguridad

`app/credential_store.py`.

No imprimir:

- passwords;
- cookies SAP;
- session IDs;
- API keys;
- Authorization headers.

Workflow `security.yml` escanea historial completo.

## Backup/restore

Backup puede ejecutarse online porque usa API SQLite backup.

Restore debe ejecutarse offline.

## Scheduler

Runtime desacoplado en `scheduler_runtime.py`; reglas de negocio en `sync_engine.py`.

No mover reglas financieras a routers.

## Web

Routers nuevos deben vivir en `app/routes/` y recibir dependencias explícitas.

Las URLs existentes son contrato y no deben cambiar durante refactor.

## Tests

Antes de merge/release:

```bash
python -m compileall -q app
node --check app/static/app.js
python -m pytest -q
python scripts/security/scan_secrets.py --history
```

Baseline actual: 111 tests por plataforma.

## Build

- EXE/Portable: GitHub Actions + Inno Setup.
- DEB: scripts/build_deb.sh.
- Pages: site/ → gh-pages.

## Política de cambios

1. un frente funcional por commit cuando sea posible;
2. test de regresión;
3. CI verde;
4. recién después continuar;
5. release tags inmutables;
6. no editar una release estable para que apunte a otro commit.
