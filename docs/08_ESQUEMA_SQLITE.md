# SQLite

Tablas:

- `companies`: CompanyDB, ambiente, tipo BD, Service Layer/OData override, usuario/secret SAP, horarios, monedas, fuentes y última ejecución.
- `app_settings`: branding, integración global, SMTP, gates PROD y parámetros generales.
- `transactions`: historial auditable SAP/banco.
- `bank_checks`: estado histórico de conectores.
- `bank_sources`: APIs/URLs/presets, configuración de extracción y headers cifrados.

No se almacenan passwords SAP/SMTP/API en texto claro.


## Archivo local

Las instalaciones nuevas usan:

```text
data/atas.db
```

Compatibilidad: si una instalación histórica conserva `data/tasa_v5.db` y su configuración apunta exactamente a ese nombre, Atas migra el archivo a `data/atas.db` al iniciar. Las rutas SQLite personalizadas no se modifican.
