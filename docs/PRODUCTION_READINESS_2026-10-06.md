# Production Readiness — Atas V5.0.4

Revisión consolidada: 2026-10-13.

## Software

Estado: **RELEASED — V5.0.4**.

Validado:

- 111 tests Windows;
- 111 tests Debian/Ubuntu;
- EXE/Portable/DEB smoke;
- secret scan árbol + historial;
- backup/restore;
- credenciales;
- USD con 3 fuentes incorporadas posibles (Banpaís/Ficohsa/BCH);
- fuentes custom;
- política oficial configurable;
- tasa repetida 20/60;
- documentación canónica y trazabilidad.

## Deudas no bloqueantes

- continuar modularizando `main.py`;
- vigilar warnings Starlette/anyio y Actions Node;
- agregar archivado de auditoría para instalaciones de muy largo plazo.

## Acciones administrativas/ambientales

### GitHub branch protection

La rama debe protegerse con:

- require pull request;
- require successful status checks: Security scan y Build Atas installers;
- block force push;
- block deletion.

El conector usado durante el desarrollo no dispone de mutación administrativa de rulesets/branch protection, por lo que este punto requiere un administrador del repositorio.

### SAP real

Cada instalación debe validar desde su red:

- Service Layer;
- CompanyDB;
- usuario/permisos;
- TLS;
- una corrida TEST;
- autorización PROD.

## Conclusión

V5.0.4 está publicada y no quedan P0 de implementación conocidos. La conectividad SAP real, permisos, TLS y autorización PROD son aceptación del despliegue de cada cliente, no funciones faltantes del software.
