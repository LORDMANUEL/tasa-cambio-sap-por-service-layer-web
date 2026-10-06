# Calidad de código y mantenimiento

## Objetivo

Atas debe mantenerse pequeño, verificable y seguro para operar una tarea contable crítica. La prioridad del proyecto no es maximizar abstracciones, sino reducir duplicación, aislar decisiones de negocio y hacer que cada cambio pueda validarse automáticamente.

## Reglas de arquitectura

- `app/main.py` contiene la capa HTTP/UI. No debe duplicar reglas de SAP, consenso bancario ni política de escritura.
- `app/sync_engine.py` orquesta SAP + bancos y concentra las decisiones de ejecución.
- `app/sap_client.py` encapsula exclusivamente el contrato Service Layer.
- `app/market_sources.py` obtiene y valida tasas externas.
- `app/store.py` es la única capa que debe ejecutar SQL de persistencia.
- `app/policy.py` decide CREATE / UPDATE / MATCH.
- `app/version.py` + `VERSION.txt` son la fuente única de versión.

## Optimizaciones incorporadas

### Versión única

FastAPI ya no expone una versión fija independiente. La versión del API se resuelve mediante `get_version()`, evitando discrepancias entre binarios, `/health`, metadata y empaquetado.

### Retención segura de datos

`Store.cleanup()` aplica la retención operativa únicamente a `bank_checks` y devuelve el contador de filas eliminadas. La tabla `transactions` se conserva porque representa evidencia de auditoría sobre lecturas/escrituras SAP.

No se debe reutilizar `log_retention_days` para eliminar auditoría contable. Si en el futuro se requiere depuración de `transactions`, debe existir una política separada, explícita, documentada y configurable.

### Escrituras de configuración

`Store.set_settings()` usa una sola marca de tiempo y `executemany()` dentro de una transacción, reduciendo trabajo repetido y garantizando una actualización coherente del grupo de settings.

### Motor de sincronización

Se centralizaron:

- resolución de compañía;
- fecha local;
- normalización de booleanos persistidos.

Esto reduce ramas duplicadas y evita que TEST/PROD interpreten flags de forma diferente en rutas distintas.

## Criterios para refactors futuros

1. No cambiar semántica de CREATE / UPDATE / MATCH sin pruebas nuevas.
2. No mover una regla de seguridad fuera de tests existentes.
3. Mantener GET posterior a cada escritura SAP.
4. Toda optimización de SQLite debe preservar atomicidad del scheduler.
5. Los cambios de UI no deben definir reglas contables.
6. Toda función que maneje secretos debe evitar logging del valor.
7. Los refactors deben pasar Windows y Debian antes de integrarse.

## Deuda técnica pendiente

`app/main.py` sigue siendo un módulo grande. Debe dividirse progresivamente por routers funcionales (setup, companies, banks, automation, audit/settings), pero en cambios pequeños para conservar las pruebas actuales y no introducir regresiones en el wizard.

También conviene introducir tipado estático incremental y pruebas de rendimiento para consultas de auditoría cuando el volumen de transacciones sea alto.
