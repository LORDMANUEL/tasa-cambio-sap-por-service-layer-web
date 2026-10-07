# Arquitectura modular de Atas

Atas se divide progresivamente en piezas pequeñas para reducir el riesgo de cambios cruzados.

## Capas actuales

- `app/main.py`: ensamblaje FastAPI y rutas todavía no extraídas.
- `app/runtime_config.py`: escritura de configuración local y normalización de Service Layer.
- `app/scheduler_runtime.py`: ciclo de vida del scheduler de fondo.
- `app/sync_engine.py`: política de reconciliación banco/SAP.
- `app/market_sources.py`: adquisición y consenso de fuentes.
- `app/providers/`: conectores concretos de bancos/fuentes.
- `app/store.py`: persistencia SQLite.
- `app/backup_manager.py` / `app/restore_manager.py`: recuperación.
- `app/credential_store.py`: cifrado de secretos.
- `app/setup_validation.py`: reglas puras del asistente.

## Regla de refactor

Cada extracción debe:

1. conservar el comportamiento público;
2. mantener tests verdes antes y después;
3. no mover simultáneamente lógica SAP y lógica bancaria;
4. exponer funciones pequeñas con entradas/salidas explícitas;
5. dejar `main.py` cada vez más cercano a un ensamblador de routers/servicios.

El siguiente objetivo será separar rutas por dominios: configuración, autenticación, empresas, bancos, automatización y auditoría.
