# Atas V5.0.1

Patch de confiabilidad para la automatización diaria de Atas.

Autor: **Luis Manuel Fajardo Rivera (LORDMANUEL)**  
Proyecto: https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web

## Correcciones

### Ejecución diaria idempotente

El scheduler ahora reclama cada CompanyDB de forma **atómica en SQLite** antes de iniciar el proceso automático.

Esto impide que dos ciclos del scheduler o dos procesos locales que coincidan en tiempo puedan ejecutar la misma programación diaria más de una vez.

Flujo:

```text
hora programada
      ↓
claim_daily_run(company, fecha)
      ↓
¿claim obtenido?
 ├─ no → no ejecutar
 └─ sí
      ↓
reconciliar
      ↓
guardar OK / ERROR
```

El bloqueo es únicamente para la automatización diaria. El botón manual de ejecución sigue siendo intencionalmente independiente.

### Manejo de fallo inesperado

Si la ejecución automática lanza una excepción inesperada:

- el scheduler no se cae;
- la CompanyDB queda registrada como `ERROR`;
- se conserva el claim del día;
- no se generan reintentos automáticos repetidos;
- el usuario puede revisar el error y ejecutar manualmente si corresponde.

### Auditoría de errores sin duplicados

Cuando una reconciliación ya registró un error técnico, el scheduler reconoce `error_recorded=True` y no inserta una segunda fila para el mismo fallo. Los errores inesperados externos al reconciliador se registran una sola vez desde el scheduler.

### Branding

El fallback visual del login ahora usa la marca `AT` de Atas.

## Pruebas agregadas

- claim diario atómico;
- segundo claim del mismo día rechazado;
- dos llamadas al scheduler ejecutan una sola vez;
- fallo inesperado no se repite el mismo día;
- error ya auditado no se duplica desde el scheduler.

V5.0.1 conserva todos los entregables de V5.0.0: EXE Windows, ZIP Portable, DEB Debian/Ubuntu, GitHub Pages, auditoría, multiempresa, fuentes configurables y Service Layer.
