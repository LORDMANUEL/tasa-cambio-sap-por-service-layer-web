# Atas 5.0.7 — Persistencia de configuración y comprobación SAP

## Mejoras
- Guardado del avance del asistente por página en SQLite con identificador aleatorio en cookie HttpOnly, recuperable tras reiniciar el servidor.
- Exclusión de contraseñas, campos secretos y configuraciones arbitrarias de proveedor en borradores.
- Validación de credenciales de cada CompanyDB mediante operaciones Login/Logout sobre SAP Service Layer antes de avanzar del paso de bases.
- Nueva cobertura automatizada: persistencia al reabrir SQLite, exclusión de secretos y llamada simulada a la autenticación SAP.
- Los demás controles de fuente bancaria, política de escritura y validación final siguen activos.

## Validaciones
- GitHub Actions: Python 3.13 en Windows y Ubuntu + escaneo de seguridad, PR #5 aprobado.

## Limitaciones verificables
- La operación real requiere acceso de red y credenciales al Service Layer del usuario; CI prueba el contrato con mocks, no la infraestructura corporativa.
- Las credenciales no se restauran automáticamente luego de recargar y deben volver a introducirse.
- La versión del XLSX del BCH publicada hoy necesita validación contra datos reales antes de considerarla completamente aceptada.

## Referencia
- PR #5; código incorporado a `main` en commit `6ce9a99f0962255f06c58716853b03a8397b3fb0`.
