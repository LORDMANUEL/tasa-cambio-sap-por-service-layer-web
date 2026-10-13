# Backend Schema — Atas V5.0.4

## Persistencia

Motor: SQLite con WAL y foreign keys.

Archivo predeterminado:

```text
data/atas.db
```

## Tabla `companies`

Entidad: CompanyDB SAP y su política operativa.

Campos principales:

- `id` PK;
- `company_name`;
- `database_name` UNIQUE;
- `db_type`: HANA/SQLSERVER;
- `environment`: TEST/PROD;
- `enabled`;
- `allow_write`;
- `scheduled_write`;
- `auto_enabled`;
- `schedule_hour`, `schedule_minute`;
- `use_usd`, `use_eur`;
- `currencies_csv`;
- `primary_bank`, `secondary_bank`;
- `bank_source_codes`;
- `service_layer_root`;
- `odata_version`;
- `sap_b1_version`;
- `sap_user`;
- `sap_secret` cifrado;
- `scheduler_claim_date`;
- `scheduler_next_retry_at`;
- `scheduler_retry_count`;
- `last_run_*`;
- timestamps.

## Tabla `app_settings`

KV runtime:

- branding;
- Service Layer global;
- OData;
- TLS SAP;
- SMTP;
- gates PROD;
- parámetros de consenso;
- `same_rate_retry_minutes`;
- `same_rate_validation_window_minutes`.

PK: `key`.

## Tabla `transactions`

Auditoría de reconciliación:

- `occurred_at`;
- CompanyDB;
- ambiente;
- moneda;
- fuente oficial/secundaria;
- `sap_before`;
- `bank_rate`;
- `sap_after`;
- `decision`;
- `status`;
- `verified`;
- `error`;
- `details_json`.

FK opcional a `companies` con `ON DELETE SET NULL`.

Índices por tiempo, empresa y estado.

## Tabla `bank_sources`

Fuente configurable:

- `code` UNIQUE;
- nombre/país;
- `source_type`: PRESET / WEB_HTML / API_JSON;
- URL;
- enabled;
- `config_json`;
- `headers_json`;
- `secret_headers_blob`;
- timeout;
- TLS;
- estado/error/fecha última comprobación;
- timestamps.

## Tabla `bank_checks`

Histórico operacional de pruebas de conectores con buy/sell USD/EUR y error.

## Tabla `market_observations`

Evidencia diaria validada:

- día;
- fecha/hora fetch;
- source_code/name/url;
- moneda;
- buy/sell;
- raw_hash;
- validated;
- timestamps.

Restricción UNIQUE:

```text
(source_code, observed_day, currency)
```

## Seguridad de datos

- SAP/SMTP/API secretos no se guardan en texto claro.
- Windows: DPAPI.
- Linux: Fernet con key separada.
- backup puede contener material sensible y debe protegerse.

## Migraciones

`Store.initialize()` crea el esquema y `_migrate_companies()` agrega columnas faltantes sin borrar datos. Los cambios deben ser backward-compatible dentro de la línea V5.
