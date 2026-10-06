# TEST REPORT — Atas V5 Complete

Validación ejecutada sobre el paquete final.

## Suite automática

- `pytest`: **77 passed**
- `compileall app`: OK
- `node --check app/static/app.js`: OK

## Validación de distribución

- Windows EXE: compilación Inno Setup + instalación silenciosa + arranque + `/health`.
- Windows Portable ZIP: descompresión limpia + arranque con Python embebido + `/health`.
- Debian/Ubuntu DEB: instalación APT + venv + servicio/aplicación + `/health`.
- GitHub Pages: publicación a `gh-pages` + verificación HTTP pública.
- Higiene de release: bloqueo de endpoints/CompanyDB específicos de clientes.

## Casos cubiertos

- instalación nueva sin datos específicos de proveedor/empresa;
- configuración multiempresa/multi-Service-Layer;
- endpoint OData efectivo por base;
- política CREATE / UPDATE / MATCH con Decimal;
- sesión web/hash;
- guard de escritura SAP;
- lectura scalar Service Layer;
- SAP `-4006` interpretado como tasa ausente;
- setup completo multiempresa;
- navegación del panel;
- parser WEB_HTML AUTO;
- parser API_JSON AUTO;
- persistencia de fuentes dinámicas;
- bloqueo con menos de 3 fuentes;
- consenso válido con 3 fuentes;
- bloqueo por outlier de fuente oficial;
- CRUD web de fuente;
- preview/escaneo web de fuente;
- headers secretos preparados para cifrado DPAPI;
- claim diario atómico por CompanyDB;
- bloqueo de segunda ejecución automática el mismo día;
- persistencia del claim ante error inesperado;
- deduplicación de errores ya registrados por el reconciliador;
- `VERSION.txt` como única fuente de versión para app, EXE, Portable, DEB y `/health`;
- bloqueo de versiones hardcodeadas en packaging.

## Limitación intencional

Las pruebas no escriben contra un SAP de producción ni dependen de sitios externos. Las conexiones reales se validan desde los botones `Probar SAP` y `Probar / escanear` en la instalación del cliente.


## Validación de desarrollo V5.0.4-dev — build #192

- Windows: 77 pruebas aprobadas.
- Debian/Ubuntu: 77 pruebas aprobadas.
- Windows Portable: arranque y `/health` aprobados.
- Windows Installer: instalación, arranque, wizard, assets y single-instance aprobados.
- Debian/Ubuntu: instalación, servicio/aplicación, wizard y assets aprobados.
- Reintento de tasa bancaria repetida: cubierto por pruebas.
- Persistencia de tasa del día anterior: cubierta por pruebas.
- Migración de campos de reintento: cubierta por pruebas.
- Estado `WAITING_BANK_UPDATE`: cubierto por pruebas.
- Límite de reintentos y transición a `ATTENTION`: cubierto por pruebas.

La validación automática no sustituye una aceptación real contra SAP Business One TEST ni valida disponibilidad futura de sitios bancarios externos.
