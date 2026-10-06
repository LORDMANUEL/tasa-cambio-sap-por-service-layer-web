# Validación bancaria diaria y deduplicación de tasas

## Regla funcional

Atas **no reutiliza deliberadamente una tasa bancaria del día anterior** para decidir una escritura SAP.

Cada ejecución diaria:

1. realiza una consulta nueva a cada fuente configurada;
2. envía cabeceras HTTP `no-cache` para reducir la posibilidad de reutilizar una respuesta cacheada;
3. valida estructura compra/venta y límites de spread;
4. registra evidencia diaria por fuente y moneda en `market_observations`;
5. construye el consenso con el mínimo de fuentes configurado;
6. valida que la fuente oficial sea coherente con el mercado;
7. lee la tasa del día directamente desde SAP;
8. decide CREATE, UPDATE o MATCH;
9. **si SAP ya contiene exactamente la tasa bancaria validada, el estado es MATCH y no se realiza POST de escritura**;
10. si escribe, realiza un GET posterior para verificar el valor.

## Por qué una tasa idéntica no significa que el banco esté desactualizado

Una institución puede publicar legítimamente la misma tasa en dos días consecutivos. Por esa razón Atas no bloquea una fuente únicamente porque el valor numérico o el hash de la página coincidan con el día anterior.

La evidencia de frescura es que la fuente fue **consultada nuevamente ese día** y superó las validaciones.

## Evidencia diaria

La tabla `market_observations` conserva una fila por:

- día local;
- fuente;
- moneda.

Si una fuente se valida varias veces el mismo día, la fila se actualiza con la consulta más reciente. Así se evita inflar la base con duplicados y se mantiene evidencia de la última comprobación diaria.

Campos principales:

- `observed_day`
- `fetched_at`
- `source_code`
- `currency`
- `buy`
- `sell`
- `raw_hash`
- `validated`

## Escritura SAP

La política es determinista:

- SAP = 0 → `CREATE`
- SAP != banco → `UPDATE`
- SAP = banco → `MATCH` y **cero escrituras**

Esto evita colocar repetidamente la misma tasa aunque el operador ejecute manualmente el proceso más de una vez.

## Seguridad operacional

No debe usarse únicamente un cambio de hash o un cambio de tasa como requisito de frescura. Un banco puede servir el mismo HTML con datos válidos o puede conservar la misma tasa varios días. La decisión se basa en consulta nueva + validación + consenso + lectura SAP.
