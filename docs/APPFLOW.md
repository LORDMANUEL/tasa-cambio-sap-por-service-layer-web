# AppFlow — Atas V5.0.8

## 1. Arranque

```text
Abrir Atas
 → iniciar servicio local
 → iniciar scheduler
 → revisar setup_complete
    ├─ false → /setup
    └─ true
        → revisar sesión web
           ├─ no autenticado → /login
           └─ autenticado → Dashboard
```

## 2. Primera configuración — wizard de 8 pasos

```text
1 Empresa → nombre / logo
2 Administrador → usuario / contraseña web
3 Notificaciones → SMTP opcional
4 Service Layer → URL raíz / OData / TLS
5 Bases SAP → CompanyDB(s) → Login SAP real por base → Logout → sin escritura
6 Fuentes → PRESET / WEB_HTML / API_JSON / BCH_API → consulta real → validación
7 Automatización → horario / timezone / monedas / fuente oficial / gates
8 Finalizar → cifrar secretos → persistir → Dashboard + recorrido guiado
```

Los campos no sensibles del wizard se guardan en sessionStorage y también como borrador SQLite ligado a una cookie aleatoria. Contraseñas, secretos, API keys y archivos no se guardan en ese borrador. Cada paso se valida en backend antes de avanzar.

## 3. Regla de fuentes

- Mínimo operativo: 1 fuente válida por moneda.
- Recomendado: 3 o más fuentes para comparación independiente.
- La fuente oficial configurada por CompanyDB es obligatoria para escribir SAP.
- Si la fuente oficial no responde, las fuentes secundarias pueden mostrarse para diagnóstico, pero la escritura SAP queda bloqueada.

## 4. Dashboard

```text
Dashboard
 ├─ Bases SAP
 ├─ Fuentes
 ├─ Automatización
 ├─ Transacciones
 ├─ Reportes
 ├─ Configuración
 └─ Logs
```

El botón Ejecutar reconciliación procesa manualmente todas las compañías activas.

## 5. Bases SAP

```text
Crear / editar CompanyDB
 → TEST o PROD
 → endpoint global o propio
 → credenciales
 → monedas
 → fuentes
 → fuente oficial
 → horario
 → gates
```

### Diagnóstico SAP

```text
Probar SAP
 → Login
 → GetLocalCurrency
 → GetCurrencyRate
 → consultar fuentes
 → mostrar SAP vs fuente oficial
 → NO escribir automáticamente
 → Logout
```

Si los bancos fallan, la lectura SAP sigue mostrándose como diagnóstico independiente.

### Escritura manual

```text
Aplicar tasa
 → validar ambiente y gates
 → validar moneda
 → consultar fuente oficial
 → validar mercado
 → Login SAP
 → GET tasa actual
    ├─ MATCH → no POST
    └─ CREATE / UPDATE
        → POST SetCurrencyRate
        → GET read-after-write
        → comparación exacta
 → auditoría
 → Logout
```

TEST requiere allow_write. PROD requiere el gate global PROD y autorización de escritura de la CompanyDB.

## 6. Fuentes bancarias

```text
Bancos
 → PRESET / WEB_HTML / API_JSON / BCH_API
 → URL + configuración
 → secretos cifrados si aplica
 → Escanear sin guardar o Guardar y probar
 → validar estructura / buy-sell / spread
 → persistir estado
 → asignar a CompanyDB
```

BCH tiene dos caminos: PRESET por XLSX oficial y BCH_API mediante la Web-API oficial. BCH es referencia USD y no sustituye por defecto la tasa comercial de la fuente oficial.

## 7. Reconciliación manual

```text
Ejecutar ahora
 → consulta fresca de fuentes
 → validación
 → fuente oficial
 → Login SAP
 → GET
 → MATCH / CREATE / UPDATE
 → gates
 → POST si corresponde
 → GET de verificación
 → auditoría
 → notificación opcional
 → Logout
```

La ejecución manual no espera la ventana de tasa repetida, pero nunca omite permisos ni validaciones.

## 8. Automatización diaria

```text
Scheduler
 → detectar CompanyDB vencida
 → claim atómico
 → consulta fresca de fuentes
 → validar fuente oficial y mercado
 → comparar con observación previa
    ├─ cambió → continuar
    └─ igual → WAITING_BANK_UPDATE
              → +20 min
              → +40 min
              → +60 min
              → si sigue válida, confirmar sin cambio
 → Login SAP
 → GET tasa
 → MATCH / CREATE / UPDATE
 → escribir sólo si gate permite
 → GET posterior al POST
 → verificar
 → auditoría
 → notificación opcional
 → Logout
```

El scheduler conserva un claim diario para evitar dobles ejecuciones.

## 9. Crash / interrupción

```text
RUNNING abandonado
 → detectar stale run
 → marcar INTERRUPTED
 → conservar claim
 → NO repetir automáticamente
```

El operador revisa SAP y reejecuta manualmente si corresponde.

## 10. Transacciones, reportes y logs

- Transacciones: historial operativo.
- Reportes: resumen + CSV de transacciones + CSV de errores.
- Logs: últimas líneas técnicas.

## 11. Backup

```text
Configuración
 → Crear backup
 → integrity_check
 → SQLite online backup
 → integrity_check snapshot
 → SHA-256
 → manifest
 → ZIP
 → validar ZIP
```

## 12. Restore

El restore es offline:

```text
Detener Atas
 → validar ZIP / hash / SQLite
 → backup preventivo
 → restaurar
 → integrity_check
    ├─ OK → completar
    └─ FAIL → rollback
 → revisar credenciales
 → iniciar Atas
```

## 13. Configuración posterior

Configuración permite cambiar branding, Service Layer global, OData, TLS, timezone, SMTP, administrador web y crear backups. CompanyDB y fuentes se administran desde sus módulos.

## 14. Estados principales

- MATCH: SAP ya coincide; no hay POST.
- CREATED_VERIFIED: tasa creada y verificada.
- UPDATED_VERIFIED: tasa actualizada y verificada.
- WAITING_BANK_UPDATE: scheduler espera nueva consulta.
- BANK_VALIDATION_FAILED: fuentes no permiten continuar.
- READ_ONLY_BANK_BLOCKED: SAP pudo leerse, bancos no permiten sugerir/escribir.
- UPDATE_WRITE_BLOCKED / CREATE_WRITE_BLOCKED: existe diferencia, pero el gate impide escritura.
- INTERRUPTED: ejecución abandonada detectada conservadoramente.
- ERROR: fallo técnico registrado.

## 15. Regla de seguridad de escritura

```text
POST SetCurrencyRate
 → GET GetCurrencyRate
 → comparación exacta
    ├─ coincide → VERIFIED
    └─ no coincide → ERROR
```

Ningún POST de tasa se considera exitoso únicamente por la respuesta HTTP.