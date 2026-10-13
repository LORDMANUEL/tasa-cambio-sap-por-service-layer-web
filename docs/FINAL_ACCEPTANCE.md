# Final Acceptance — Atas V5.0.4

## Estado de entrega

La implementación de software cumple el alcance definido para V5.0.4.

Evidencia previa al gate final:

- Build installers: SUCCESS.
- Security scan: SUCCESS.
- 111 tests Windows.
- 111 tests Debian/Ubuntu.
- Windows EXE smoke: OK.
- Windows Portable smoke: OK.
- Debian DEB smoke: OK.
- Setup wizard/assets: OK.
- single-instance Windows: OK.
- secret scan árbol + historia: OK.

## Cumplimiento documental

- PRD: CUMPLE.
- TRD: CUMPLE.
- UI/UX Design: CUMPLE.
- Appflow: CUMPLE.
- Backend Schema: CUMPLE.
- Development Plan: CUMPLE.
- Changelog: CUMPLE.
- Documentación técnica: CUMPLE.
- Matriz de trazabilidad: CUMPLE.

## Restricciones externas

La activación PROD de una empresa sigue requiriendo:

1. probar SAP Service Layer desde la red de esa empresa;
2. confirmar CompanyDB/usuario/permisos;
3. configurar TLS según la infraestructura;
4. seleccionar la fuente oficial;
5. validar tres fuentes USD;
6. realizar al menos una corrida TEST;
7. habilitar gates PROD.

Esto no impide cerrar la entrega del software; es aceptación de despliegue.

## Estado de release

**COMPLETO.**

- Release: `v5.0.4`.
- Commit de release: `83167d7eac0e369421cdbab9c11906946af95703`.
- Release publicada: 2026-10-13.
- Manifiesto: `docs/RELEASE_MANIFEST_V5.0.4.md`.

La entrega de software V5.0.4 queda cerrada. Lo restante corresponde a aceptación del ambiente de cada cliente y operación normal de mantenimiento.
