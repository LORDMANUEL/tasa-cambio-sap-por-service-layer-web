# Matriz de trazabilidad — Atas V5.0.4

| ID | Requisito | Implementación principal | Evidencia / prueba | Estado |
|---|---|---|---|---|
| PRD-01 | Multiempresa | Store + Companies UI | tests multiempresa | CUMPLE |
| PRD-02 | Fuente oficial configurable | companies.primary_bank + market_sources | consenso/outlier tests | CUMPLE |
| PRD-03 | 3 fuentes por moneda | setup_validation + market_sources | tests setup coverage | CUMPLE |
| PRD-04 | USD predeterminado | setup defaults + BCH | tests BCH/setup | CUMPLE |
| PRD-05 | Fuentes HTML/API extensibles | market_sources | parser/CRUD/preview tests | CUMPLE |
| PRD-06 | Revalidación 20 min / 60 min | sync_engine | scheduler/window tests | CUMPLE |
| PRD-07 | CREATE/UPDATE/MATCH | policy + sync_engine | policy tests | CUMPLE |
| PRD-08 | GET posterior a POST | sap_client + sync_engine | read-after-write tests | CUMPLE |
| PRD-09 | TEST/PROD gates | sync_engine/store/UI | write guard tests | CUMPLE |
| PRD-10 | TLS configurable | settings/company/source | config tests | CUMPLE |
| PRD-11 | Auditoría | transactions | transaction/report tests | CUMPLE |
| PRD-12 | Backup/restore | backup_manager/restore_manager | backup/restore tests | CUMPLE |
| PRD-13 | Secretos cifrados | credential_store | credential tests | CUMPLE |
| PRD-14 | Secret scan historial | security workflow | Security scan green | CUMPLE |
| PRD-15 | Windows EXE | build workflow/Inno | smoke Windows | CUMPLE |
| PRD-16 | Portable | build workflow | portable smoke | CUMPLE |
| PRD-17 | Debian DEB | packaging/systemd | Debian smoke | CUMPLE |
| UX-01 | Responsive/theme | static UI | smoke/assets + manual design spec | CUMPLE |
| UX-02 | Estados visibles | dashboard/automation | UI tests | CUMPLE |
| OPS-01 | Crash conservador | recover_stale_running | recovery tests | CUMPLE |
| OPS-02 | Evidencia diaria | market_observations | persistence tests | CUMPLE |
| OPS-03 | GitHub Pages | site/workflow | HTTP publish workflow | CUMPLE |
| EXT-01 | SAP TEST real del cliente | instalación cliente | checklist manual | DEPENDE DEL AMBIENTE |
| EXT-02 | Branch protection administrativa | GitHub settings | regla admin | ACCIÓN ADMINISTRATIVA |

## Lectura

`DEPENDE DEL AMBIENTE` no representa código incompleto: GitHub Actions no puede alcanzar una red SAP privada.

`ACCIÓN ADMINISTRATIVA` indica una configuración de GitHub que requiere permisos de administración no expuestos por el conector usado para desarrollar el repositorio.
