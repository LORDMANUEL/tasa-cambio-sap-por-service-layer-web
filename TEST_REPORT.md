# TEST REPORT — Atas V5.0.4 Candidate

## Baseline automatizado

Commit de referencia anterior al gate final: `83db7990`.

- Windows: **111 passed**, 1 warning de dependencia externa.
- Debian/Ubuntu: **111 passed**, 1 warning de dependencia externa.
- `compileall app`: OK.
- `node --check app/static/app.js`: OK.
- secret scan árbol + historial: OK.

## Distribución

Windows:
- EXE build: OK.
- instalación limpia: OK.
- /health: OK.
- wizard: OK.
- assets: OK.
- single-instance: OK.
- autostart: OK.

Portable:
- ZIP: OK.
- Python embebido: OK.
- root launcher: OK.
- /health: OK.

Debian/Ubuntu:
- DEB: OK.
- instalación: OK.
- /health: OK.
- wizard/assets: OK.

## Cobertura funcional relevante

- setup multiempresa;
- Service Layer v1/v2;
- CREATE / UPDATE / MATCH;
- SAP -4006;
- GET posterior a escritura;
- gates TEST/PROD;
- consenso mínimo por moneda;
- outliers;
- Banpaís/Ficohsa/BCH;
- HTML/API custom;
- headers secretos;
- scheduler/claim;
- tasa repetida 20/60;
- market observations;
- backup/restore;
- recuperación credenciales;
- routers extraídos;
- migraciones SQLite.

## Warnings no bloqueantes

- Starlette TestClient referencia un alias anyio deprecado.
- algunas GitHub Actions de terceros reportan transición Node runtime.

## Limitación de ambiente

CI no escribe contra un SAP privado ni depende de disponibilidad bancaria externa en tiempo real. La aceptación de red/Service Layer se ejecuta en el despliegue TEST de cada cliente.
