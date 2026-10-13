# Development Plan — Atas V5.0.4

## Estrategia

Desarrollo incremental, commits pequeños, CI después de cada frente y sin mezclar refactors con cambios de política cuando sea evitable.

## Fase 1 — Motor funcional V4 → V5

Estado: **COMPLETADA**

- Service Layer;
- lectura/escritura/verificación;
- bancos;
- panel;
- logs.

## Fase 2 — Producto genérico/multiempresa

Estado: **COMPLETADA**

- wizard;
- branding;
- CompanyDB múltiples;
- TEST/PROD;
- endpoint/OData por empresa;
- SMTP.

## Fase 3 — Motor de fuentes extensible

Estado: **COMPLETADA**

- PRESET;
- HTML AUTO/CSS/REGEX;
- API JSON AUTO/MAPPING;
- headers secretos;
- consenso;
- BCH USD;
- mínimo por moneda.

## Fase 4 — Operación segura diaria

Estado: **COMPLETADA**

- observaciones diarias;
- tasa repetida;
- reconsulta 20 min;
- ventana 60 min;
- MATCH sin escritura;
- claim atómico;
- crash conservador.

## Fase 5 — Distribución

Estado: **COMPLETADA**

- Windows EXE;
- Windows Portable;
- Debian DEB;
- CI;
- smoke tests;
- GitHub Pages;
- releases.

## Fase 6 — Recuperación y seguridad

Estado: **COMPLETADA**

- backup SQLite consistente;
- SHA-256;
- integrity check;
- restore offline;
- rollback;
- recuperación/reporte de credenciales;
- secret scan de árbol + historial.

## Fase 7 — Modularización

Estado: **EN CURSO, NO BLOQUEANTE PARA RELEASE**

Completado:

- auth router;
- backup router;
- runtime config;
- scheduler runtime.

Siguiente mantenimiento:

- notificaciones;
- settings;
- empresas;
- bancos;
- automatización;
- reportes.

La modularización posterior a esta release no cambia el contrato funcional.

## Fase 8 — Cierre V5.0.4

Criterios:

- [x] PRD.
- [x] TRD.
- [x] UI/UX spec.
- [x] Appflow.
- [x] Backend Schema.
- [x] trazabilidad.
- [x] documentación técnica.
- [x] 111 tests Windows.
- [x] 111 tests Debian/Ubuntu.
- [x] secret scan completo.
- [x] EXE/Portable/DEB smoke-tested.
- [x] VERSION.txt = 5.0.4.
- [x] Release V5.0.4 publicada.
- [x] manifiesto/hashes finales.
- [x] Pages V5.0.4.

Los cuatro últimos ítems se completan en el gate de release.

## Aceptación de ambiente de cliente

No es una tarea pendiente del código. Cada instalación debe validar:

- endpoint real;
- CompanyDB;
- credenciales;
- permisos SAP;
- TLS según infraestructura;
- fuente oficial;
- tres fuentes USD;
- una corrida TEST antes de PROD.
