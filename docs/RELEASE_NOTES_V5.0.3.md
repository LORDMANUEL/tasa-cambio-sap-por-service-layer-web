# Atas V5.0.3

Release de corrección y endurecimiento posterior a V5.0.2.

## Correcciones

- Corrige el test de migración SQLite en Windows que podía fallar con `WinError 32` durante el cleanup de una base temporal.
- Implementa lectura real de `SBOBobService_GetCurrencyRate` para **OData v1** mediante FunctionImport POST, manteniendo GET para v2.
- Valida códigos de moneda antes de escribir en SAP.
- Corrige el estado global de ejecuciones mixtas: un `WRITE_BLOCKED` ya no queda oculto por otra moneda en `MATCH`.
- Registra en auditoría fallas de consenso bancario y credenciales ausentes antes del login SAP.
- Hace el setup inicial reintentable/idempotente para fuentes y CompanyDB ya creadas por un intento parcial.
- Evita HTTP 500 por horario inválido al guardar una base.
- Evita mensaje falso de “correo enviado” cuando SMTP/notificaciones están deshabilitados.
- Corrige manejo de errores al crear/probar una fuente bancaria nueva.
- Valida cada par compra/venta antes del consenso:
  - compra y venta > 0;
  - venta no puede ser menor que compra;
  - spread máximo configurable.
- Evita iniciar varios servidores Atas en Windows si `/health` ya responde.
- Agrega inicio automático opcional de Atas al iniciar sesión en Windows.
- Reduce runners duplicados de CI en `main`.
- Amplía smoke tests para verificar wizard inicial y assets CSS dentro del EXE/Portable/DEB instalado.

## Pruebas

La rama se publica sólo después de que **Build Atas installers** complete:

- suite Python en Windows y Debian/Ubuntu;
- `compileall`;
- sintaxis JavaScript;
- ZIP portable real;
- EXE real instalado;
- DEB real instalado;
- `/health`;
- `/setup`;
- carga de assets CSS;
- publicación inmutable de GitHub Release.

## Autor

**Luis Manuel Fajardo Rivera — LORDMANUEL**

https://github.com/LORDMANUEL
