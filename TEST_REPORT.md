# TEST REPORT — Atas V5 Complete

Validación ejecutada sobre el paquete final.

## Suite automática

- `pytest`: **19 passed**
- `compileall app`: OK
- `node --check app/static/app.js`: OK

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
- headers secretos preparados para cifrado DPAPI.

## Limitación intencional

Las pruebas no escriben contra un SAP de producción ni dependen de sitios externos. Las conexiones reales se validan desde los botones `Probar SAP` y `Probar / escanear` en la instalación del cliente.
