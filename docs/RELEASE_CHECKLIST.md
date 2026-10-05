# Checklist de Release — Atas V5

Una versión se considera publicable solamente cuando se cumplen todos los puntos:

- [x] Producto identificado como Atas.
- [x] Autor: Luis Manuel Fajardo Rivera (LORDMANUEL).
- [x] Sin IP/CompanyDB/datos específicos del cliente originador.
- [x] 3+ fuentes para automatización.
- [x] SAP Service Layer/OData configurables.
- [x] TEST/PROD separados.
- [x] Verificación GET después de escritura SAP.
- [x] SQLite/auditoría.
- [x] SMTP saliente opcional.
- [x] CI Windows.
- [x] CI Ubuntu.
- [x] 52 pruebas automáticas en Windows y 52 en Ubuntu.
- [x] EXE compilado.
- [x] EXE instalado en runner limpio.
- [x] EXE levantó Atas y pasó /health.
- [x] Portable ZIP generado.
- [x] Portable ZIP descomprimido y probado.
- [x] DEB construido.
- [x] DEB instalado con APT y probado.
- [x] GitHub Pages público y validado.
- [x] Tamaño y SHA-256 generados por CI.
- [x] Notas de versión preparadas.
- [x] VERSION.txt en 5.0.2 y Release V5.0.3 publicada.

La última casilla se completa únicamente después de que el commit candidato pase todos los workflows.


Release estable verificada: https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web/releases/tag/v5.0.3
