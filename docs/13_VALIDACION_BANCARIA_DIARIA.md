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


## Memoria del día anterior y espera de una hora

Además de consultar las fuentes nuevamente, Atas conserva en SQLite la última observación validada por fuente, moneda y día.

En una ejecución **automática**:

1. se consulta la fuente oficial del día actual;
2. se obtiene la observación validada más reciente anterior al día actual;
3. si la tasa de venta oficial actual es exactamente igual a la anterior, la moneda entra en `WAITING_BANK_UPDATE`;
4. esa moneda no se escribe en SAP;
5. el scheduler libera de forma segura el reclamo diario y establece `scheduler_next_retry_at` una hora adelante;
6. durante esa hora el loop de 30 segundos no vuelve a ejecutar la base;
7. al cumplirse la hora se consultan de nuevo todos los bancos y se vuelve a validar el consenso.

La memoria se almacena en SQLite y no únicamente en RAM, por lo que un reinicio de Atas no pierde la referencia del día anterior ni la hora del próximo reintento.

### Varias monedas

La espera es por moneda. Si USD no cambió respecto al día anterior pero EUR sí cambió, EUR puede procesarse normalmente. USD queda pendiente y se vuelve a revisar una hora después. En el reintento, cualquier moneda ya procesada se compara nuevamente contra SAP y, si coincide, queda en `MATCH` sin escritura adicional.

### Ejecución manual

Una ejecución manual autorizada no queda bloqueada por esta regla. Esto permite que Contabilidad intervenga si confirma que el banco realmente mantuvo la misma tasa para el nuevo día. La intervención manual sigue respetando consenso, permisos TEST/PROD y verificación posterior en SAP.


## Validación del contrato de escritura

Las pruebas de integración simuladas deben reproducir el contrato real del Service Layer: después de una escritura aceptada, el GET de verificación debe devolver el nuevo valor. Esto evita falsos positivos y garantiza que las pruebas cubran la verificación posterior a escritura, no sólo la llamada POST.


## Visibilidad operativa

`WAITING_BANK_UPDATE` se considera un estado de atención, no un éxito silencioso. El dashboard lo muestra como advertencia y las notificaciones lo clasifican como atención requerida para que Contabilidad sepa que Atas está esperando una publicación bancaria nueva.

La migración de una instalación existente agrega los campos de reintento sin borrar `scheduler_claim_date`, historial, credenciales ni configuración previa.


## Límite de reintentos

Para evitar un ciclo automático infinito cuando un banco conserva legítimamente la misma tasa durante todo el día, Atas limita los reintentos de tasa repetida.

El valor predeterminado es `max_same_rate_retries = 3`. Con una espera de una hora, esto permite tres comprobaciones adicionales después de la ejecución inicial.

Cuando se alcanza el límite:

- se deja de reintentar automáticamente;
- el estado pasa a `ATTENTION`;
- se limpia `scheduler_next_retry_at`;
- se notifica que requiere validación manual;
- no se escribe la tasa repetida automáticamente.

## Visualización

La pantalla de Automatización muestra, cuando aplica:

- fecha/hora del próximo intento;
- número de intento acumulado;
- estado `WAITING_BANK_UPDATE`.

Esto permite a Contabilidad distinguir entre un fallo, una espera normal del banco y una intervención manual requerida.


## Política definitiva de tasa repetida

La política operativa multiempresa queda definida así:

- cada empresa selecciona una **fuente oficial** (`primary_bank`);
- las demás fuentes validan coherencia/consenso;
- la tasa que se propone a SAP siempre es la tasa de venta de la fuente oficial seleccionada;
- la fuente oficial sólo es accionable cuando supera consenso y controles de outliers;
- cada consulta se realiza nuevamente contra las fuentes con headers `no-cache`; Atas no reutiliza una tasa bancaria guardada como respuesta de red.

Si la ejecución programada inicia a las 06:00 y la tasa oficial es exactamente igual a la última observación válida anterior:

1. no se escribe todavía;
2. estado `WAITING_BANK_UPDATE`;
3. nueva consulta a las 06:20;
4. nueva consulta a las 06:40;
5. nueva consulta a las 07:00;
6. si antes de las 07:00 cambia y pasa consenso, se procesa inmediatamente;
7. si a las 07:00 sigue idéntica pero todas las validaciones continúan correctas, se considera **tasa confirmada sin cambio** y se procesa contra SAP.

Los parámetros son configurables:

- `same_rate_retry_minutes=20`;
- `same_rate_validation_window_minutes=60`.

La ventana es relativa al horario configurado de cada empresa, por lo que una instalación SaaS puede usar otro horario manteniendo la misma política.
