# Production Readiness — Atas V5.0.4

Revisión consolidada: 2026-10-13.

## Software

Estado: **READY FOR RELEASE GATE**.

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

No quedan P0 de implementación conocidos para publicar V5.0.4. La conectividad SAP real es aceptación del despliegue, no una función faltante del código.
