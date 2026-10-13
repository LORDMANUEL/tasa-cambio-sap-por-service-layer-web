# Appflow — Atas V5.0.4

## 1. Primera ejecución

```text
Abrir Atas
 → setup incompleto
 → Wizard
 → Branding
 → Admin
 → SMTP opcional
 → Service Layer
 → CompanyDB(s)
 → Fuentes
 → validar ≥3 fuentes por moneda
 → seleccionar fuente oficial
 → horario/gates
 → guardar setup
 → Login
 → Dashboard
```

## 2. Flujo automático diario

```text
Scheduler detecta hora
 → claim atómico CompanyDB
 → consulta fresca de fuentes
 → validación buy/sell/rango/spread
 → consenso por moneda
 → validar fuente oficial
 → comparar contra observación anterior
    ├─ cambió → continuar
    └─ igual → WAITING
              → +20 min
              → +20 min
              → hasta +60 min
              → si sigue válida, confirmar sin cambio
 → login SAP
 → GET tasa SAP
    ├─ igual → MATCH / no POST
    ├─ cero → CREATE
    └─ distinta → UPDATE
 → si escritura autorizada: POST
 → GET de verificación
 → auditoría
 → notificación opcional
 → logout SAP
```

## 3. Flujo manual

```text
Usuario autenticado
 → seleccionar CompanyDB
 → ejecutar
 → consultar/validar fuentes
 → leer SAP
 → respetar gates TEST/PROD
 → escribir si corresponde
 → verificar
 → auditar
```

La ejecución manual no queda bloqueada por la espera de tasa repetida, pero sí por consenso y permisos.

## 4. Agregar una fuente

```text
Bancos/Fuentes
 → tipo PRESET / WEB_HTML / API_JSON
 → URL/config
 → headers públicos/secretos
 → Preview
 → parse
 → validar
 → guardar
 → asignar a CompanyDB
 → opcional: marcar como fuente oficial
```

## 5. Backup

```text
Configuración
 → Crear backup
 → integrity_check base
 → SQLite online backup
 → integrity_check snapshot
 → SHA-256
 → ZIP + manifest
 → validar ZIP
 → éxito
```

## 6. Restore offline

```text
Detener Atas
 → validar ZIP/hash/integridad
 → backup preventivo
 → reemplazo atómico
 → integrity_check
    ├─ OK → reporte credenciales
    └─ FAIL → rollback
 → iniciar Atas
```

## 7. Crash durante ejecución

Un claim `RUNNING` abandonado pasa a `INTERRUPTED`. Atas no repite automáticamente porque SAP pudo haber aceptado una escritura antes del crash. Se revisa SAP y se ejecuta manualmente si corresponde.
