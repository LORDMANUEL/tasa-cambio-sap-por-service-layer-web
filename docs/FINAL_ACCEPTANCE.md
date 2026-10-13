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

Este documento queda completo cuando V5.0.4 se publique y se registren hashes finales.
