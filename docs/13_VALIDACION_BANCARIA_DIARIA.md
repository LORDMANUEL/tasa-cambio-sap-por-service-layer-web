# Validación bancaria diaria — política vigente V5.0.4

## Fuente oficial y consenso

Cada empresa elige una fuente oficial. Las demás fuentes son controles.

SAP recibe el `sell` de la fuente oficial únicamente si:

- la fuente responde;
- la estructura es válida;
- buy/sell son válidos;
- spread está dentro de límites;
- existen al menos tres fuentes válidas para la moneda;
- la fuente oficial no es outlier respecto del consenso.

## Consulta fresca

Cada ejecución consulta nuevamente las fuentes y usa headers no-cache/no-store. La observación local se usa como evidencia/comparación, no como sustituto de una consulta de red.

## Evidencia

`market_observations` conserva la observación validada más reciente por:

- día;
- fuente;
- moneda.

## Tasa repetida

Para horario 06:00:

- 06:00: consultar;
- si tasa oficial = observación válida anterior → `WAITING_BANK_UPDATE`;
- 06:20: consultar nuevamente;
- 06:40: consultar nuevamente;
- 07:00: consultar nuevamente.

Si cambia antes del deadline y el consenso es seguro, se procesa inmediatamente.

Si al deadline sigue igual pero la fuente oficial continúa válida y coherente, Atas registra **tasa confirmada sin cambio** y continúa con SAP.

Configuración:

```text
same_rate_retry_minutes=20
same_rate_validation_window_minutes=60
```

La ventana es relativa al horario de cada CompanyDB.

## SAP

- tasa SAP = tasa validada → MATCH, cero POST;
- tasa SAP ausente/0 → CREATE;
- tasa SAP distinta → UPDATE;
- cualquier POST exige GET posterior exacto.

## Ejecución manual

No espera la ventana de tasa repetida. Sí respeta consenso, ambiente, permisos y verificación.

## Crash

Una ejecución reclamada que queda abandonada se marca `INTERRUPTED` y no se reintenta automáticamente, porque SAP podría haber recibido una escritura antes del crash.
