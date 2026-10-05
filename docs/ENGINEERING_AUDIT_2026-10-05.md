# Auditoría de ingeniería GitHub — 2026-10-05

Repositorio: `LORDMANUEL/tasa-cambio-sap-por-service-layer-web`

## Objetivo

Revisar el estado real del proyecto Atas, separar fallas de código de fallas de CI/documentación y dejar controles que eviten regresiones en la distribución Windows, Portable y Debian.

## Estado funcional verificado

- Release pública estable: **v5.0.3**.
- Binarios publicados: EXE x64, Portable x64 y DEB amd64.
- GitHub Pages: publicación exitosa.
- Último build completo previo a esta auditoría: workflow **Build Atas installers #180**, resultado **success**.
- Ese build ejercitó Windows y Debian/Ubuntu, incluyendo pruebas Python, compilación, JavaScript, instalación/empaquetado y smoke tests.
- El reporte del repositorio registra **53 pruebas automáticas aprobadas**.

## Incidente detectado en CI

El workflow **Build Atas installers #179** falló en Windows y Debian con tres fallas de prueba:

1. `test_consensus_blocks_outlier_official` no encontraba el mensaje esperado para el outlier oficial.
2. `test_reconcile_records_bank_validation_failure_once` usaba un mock sin el atributo `notices`.
3. `test_reconcile_records_missing_credentials_once` usaba el mismo contrato incompleto.

Causa: el modelo `MarketConsensus` evolucionó para incorporar `notices`, pero algunos tests/mocks todavía reflejaban el contrato anterior; además, el mensaje del outlier oficial había cambiado.

Resolución ya integrada en `main`:

- commit `36c256cb`: preservó compatibilidad del consenso y el mensaje de outlier oficial;
- commit `0d031d13`: alineó los mocks de reconciliación con `MarketConsensus.notices`.

Resultado: el build siguiente (#180) terminó correctamente.

## Problema de documentación encontrado

El README mezclaba información de dos releases:

- encabezado: **V5.0.2**;
- nombres de archivos: **V5.0.3**;
- tamaños y hashes: valores anteriores;
- enlace de manifiesto: **V5.0.2**;
- conteo de pruebas: **52**, mientras `TEST_REPORT.md` y el manifiesto V5.0.3 indican **53**.

Esto no rompía el runtime, pero sí rompía la trazabilidad de release y podía producir falsas alertas de integridad al comparar SHA-256.

## Corrección aplicada por esta auditoría

- README alineado con los binarios reales de **v5.0.3**.
- SHA-256 y tamaños sincronizados con `docs/RELEASE_MANIFEST_V5.0.3.md`.
- Conteo de pruebas actualizado a **53**.
- Agregado `tests/test_repository_metadata.py` para impedir que el bloque de binarios vuelva a mezclar versiones o que el conteo de pruebas diverja del reporte.

## Riesgos no bloqueantes

- La rama `main` no está protegida. Un push directo puede saltarse una revisión por PR.
- El repositorio no declara licencia. Antes de distribuirlo como software abierto conviene definir explícitamente el esquema de licencia.
- `VERSION.txt` está en `5.0.4-dev`, mientras la release estable es `v5.0.3`. Esto es correcto para desarrollo, pero debe conservarse la distinción entre versión de trabajo y release pública.

## Criterio para considerar el proyecto sano

Una revisión de release se considera aprobada cuando:

1. `python -m compileall -q app` finaliza correctamente;
2. `node --check app/static/app.js` finaliza correctamente;
3. `python -m pytest -q` queda en verde;
4. Portable arranca desde un directorio limpio y responde `/health`;
5. EXE instala y arranca con Python embebido;
6. DEB instala, crea su entorno y responde `/health`;
7. los artefactos publicados coinciden con su manifiesto SHA-256;
8. GitHub Pages publica sin error.

La automatización del repositorio cubre estos controles principales.
