# Atas V5.0.5 — Corrección de configuración inicial y fuentes bancarias

Fecha: 2026-10-13

## Correcciones
- Asistente inicial dividido en ocho pantallas navegables.
- Ante una validación fallida, el formulario conserva los datos ingresados y muestra el error sin abandonar el asistente.
- Borrador temporal recuperable mediante sessionStorage para campos no sensibles (nunca contraseñas ni archivos).
- Restauración de filas de CompanyDB añadidas en la configuración multiempresa.
- Mínimo de **una fuente bancaria válida** para continuar; tres o más fuentes siguen siendo configurables y aportan comparación adicional.
- Parser BCH tolerante a encabezados desplazados y columnas Fecha/TCR reordenadas, conservando validaciones de antigüedad y rangos.
- CI en Windows y Ubuntu, análisis de seguridad y ensamblado/arranque portable.

## Límites y precauciones
- El borrador es local a la pestaña/sesión y no equivale a persistencia de cada etapa en el servidor. Las contraseñas deben volver a indicarse tras recargar.
- El BCH aún requiere prueba contra su archivo XLSX oficial vigente, además de los escenarios sintéticos comprobados en CI.
- Una sola fuente no permite corroboración independiente; mantener límites de tasa, política de escritura y auditoría antes de modificar SAP.
- Versionar esta actualización como 5.0.5 evita reutilizar los archivos inmutables de la versión 5.0.4.

## Código de referencia
PR #1 (integrado), commit base `4121ab6a2ef1089eec73514be727dc32de154e59`.
