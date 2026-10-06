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

### Retención real de datos

`Store.cleanup()` ahora aplica la retención configurada tanto a `transactions` como a `bank_checks`. Antes sólo se eliminaban verificaciones bancarias y la tabla principal de auditoría podía crecer indefinidamente.

La función devuelve contadores de filas eliminadas para facilitar observabilidad futura.

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
