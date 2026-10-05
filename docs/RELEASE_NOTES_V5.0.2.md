# Atas V5.0.2

Patch release de estabilidad y portabilidad construido sobre V5.0.1.

## Correcciones principales

- Corrige la prueba de migración SQLite en Windows: la conexión temporal ahora se cierra explícitamente y ya no produce `WinError 32`.
- Separa correctamente el **claim diario del scheduler** del historial de ejecuciones manuales.
- Evita duplicar la ejecución automática de una CompanyDB durante el mismo día.
- Las ejecuciones manuales ya no consumen el claim de la automatización diaria.
- Corrige el estado agregado cuando existen resultados mixtos: un `WRITE_BLOCKED` ya no puede quedar resumido como `OK`.
- Registra en auditoría fallos previos al login SAP, incluidos consenso bancario inseguro y credenciales no configuradas.
- Implementa lectura real de `SBOBobService_GetCurrencyRate` para **OData v1** mediante POST, conservando GET para OData v2.
- Mantiene `-4006 / Update the exchange rate` como tasa ausente tanto en v1 como v2.
- Agrega configuración web persistente para validar o no el certificado TLS del Service Layer.
- Refuerza la validación de pares compra/venta y bloquea fuentes con venta menor que compra o spreads anómalos.
- Hace el setup inicial reintentable después de un fallo parcial, reutilizando fuentes y CompanyDB ya creadas.
- Valida horarios y formularios web para devolver error controlado en lugar de HTTP 500.
- Corrige la prueba SMTP para que no muestre éxito cuando las notificaciones están deshabilitadas.
- Mejora el launcher Windows para no abrir un segundo servidor Atas cuando ya existe uno sano en `127.0.0.1:8787`.
- Agrega opción de inicio automático local en Windows.
- Conserva datos persistentes al actualizar el paquete Debian.
- Refuerza la redacción de secretos en logs.
- Actualiza GitHub Actions a runtimes compatibles con Node 24.
- Reduce ejecuciones CI duplicadas y mantiene solamente el build más reciente por rama.

## Validación

Antes de crear la release, GitHub Actions debe completar:

- suite Python completa en Windows;
- suite Python completa en Debian/Ubuntu;
- `compileall`;
- validación sintáctica JavaScript;
- portable Windows desde directorio limpio;
- instalación silenciosa del EXE;
- `/health`, `/setup` y assets CSS desde el producto instalado;
- instalación real del DEB con APT;
- `/health`, `/setup` y assets CSS desde el DEB instalado.

La release sólo se publica si ambos jobs de plataforma terminan correctamente.

## Autor

**Luis Manuel Fajardo Rivera — LORDMANUEL**

- GitHub: https://github.com/LORDMANUEL
- Proyecto: https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web
