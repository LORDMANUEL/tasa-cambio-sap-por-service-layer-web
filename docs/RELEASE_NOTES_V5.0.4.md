# Atas V5.0.4

V5.0.4 consolida Atas como plataforma local-first, multiempresa y extensible para automatizar tasas de cambio en SAP Business One.

## Política diaria

- fuente oficial configurable por CompanyDB;
- mínimo tres fuentes válidas por moneda;
- USD como moneda predeterminada;
- Banpaís/Ficohsa/BCH disponibles como fuentes incorporadas;
- BCH se usa como referencia TCR USD, no como cotización comercial inventada;
- fuente oficial validada contra consenso/outliers;
- tasa repetida: consultas frescas cada 20 minutos durante una ventana de 60 minutos;
- al finalizar la ventana, una tasa aún idéntica puede confirmarse como válida si el consenso continúa seguro;
- MATCH no escribe;
- CREATE/UPDATE exigen GET posterior de verificación.

## Fuentes personalizadas

Sin modificar Python se pueden agregar:

- WEB_HTML AUTO;
- WEB_HTML CSS;
- WEB_HTML REGEX;
- API_JSON AUTO;
- API_JSON MAPPING;
- headers públicos;
- headers secretos cifrados;
- TLS por fuente.

## SAP

- Service Layer v1/v2;
- endpoint global o por CompanyDB;
- HANA/SQL Server configurables;
- TLS opcional/configurable;
- TEST/PROD separados;
- gates de escritura;
- manejo de -4006 como tasa ausente.

## Seguridad y recuperación

- DPAPI en Windows;
- Fernet en Linux;
- secret scan del árbol actual y todo el historial Git;
- backup online consistente de SQLite;
- integrity_check;
- SHA-256 + manifest;
- restore offline con backup preventivo y rollback;
- reporte de recuperación de credenciales.

## Arquitectura

Se inició la separación incremental de `app/main.py`:

- auth router;
- backup router;
- runtime config;
- scheduler runtime.

La modularización continúa como mantenimiento sin cambiar el contrato funcional.

## Calidad

Baseline candidato:

- 111 tests en Windows;
- 111 tests en Debian/Ubuntu;
- EXE smoke test;
- Portable smoke test;
- DEB smoke test;
- security scan completo.

## Documentación

V5.0.4 incorpora documentos canónicos:

- PRD;
- TRD;
- UI/UX Design;
- Appflow;
- Backend Schema;
- Development Plan;
- Traceability Matrix;
- Technical Documentation;
- Final Acceptance.

## Activación PROD

La release está lista como software. Cada instalación debe validar su Service Layer real, CompanyDB, usuario/permisos, TLS y fuentes desde su propia red antes de habilitar PROD.
