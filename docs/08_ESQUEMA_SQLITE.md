# SQLite

Tablas:

- `companies`: CompanyDB, ambiente, tipo BD, Service Layer/OData override, usuario/secret SAP, horarios, monedas, fuentes y última ejecución.
- `app_settings`: branding, integración global, SMTP, gates PROD y parámetros generales.
- `transactions`: historial auditable SAP/banco.
- `bank_checks`: estado histórico de conectores.
- `bank_sources`: APIs/URLs/presets, configuración de extracción y headers cifrados.

No se almacenan passwords SAP/SMTP/API en texto claro.
