# Changelog V5

## V5.0.4

- BCH como tercera referencia estructurada USD.
- USD como configuración predeterminada para instalaciones nuevas.
- mínimo de tres fuentes validado por moneda.
- fuente oficial configurable por CompanyDB.
- fuentes custom WEB_HTML AUTO/CSS/REGEX.
- fuentes custom API_JSON AUTO/MAPPING.
- tasa repetida: reconsulta cada 20 minutos durante una ventana de 60 minutos.
- confirmación de tasa sin cambio al cerrar la ventana si el consenso continúa seguro.
- evidencia diaria en `market_observations`.
- prevención de escrituras duplicadas.
- backup SQLite online con integrity_check y SHA-256.
- restore offline con backup preventivo y rollback.
- recuperación/reporte de credenciales.
- secret scan del árbol actual y todo el historial Git.
- proveedor BCH XLSX.
- runtime config y scheduler extraídos de `main.py`.
- routers auth y backup extraídos de `main.py`.
- documentación de fuentes personalizadas.
- PRD/TRD/UI-UX/Appflow/Backend Schema/Plan/Trazabilidad consolidados.
- 111 pruebas automáticas por plataforma antes del gate final.

## V5.0.3

- OData v1 FunctionImport implementado.
- Auditoría reforzada para fallas pre-SAP.
- Estado BLOCKED priorizado correctamente.
- Setup inicial idempotente/reintentable.
- Validación de formularios web y SMTP.
- Validación compra/venta y spread por fuente.
- Inicio único y autoarranque opcional en Windows.
- Smoke tests de wizard/assets en binarios instalados.
- Corrección de prueba SQLite específica de Windows.

## V5

- Producto genérico.
- Wizard.
- Branding.
- SMTP saliente.
- Multiempresa.
- HANA/SQL Server.
- fuentes API/HTML/preset.
- instaladores Windows/Debian.
- Dashboard integrado.
