# Atas V5.0.8 — SAP FX y fuentes oficiales

Release estable sobre V5.0.7.

## Cambios

- Service Layer v2 usa primero el POST oficial de SAP para GetCurrencyRate.
- Fallback compatible a FunctionImport GET para instalaciones antiguas.
- GetLocalCurrency v2 también prioriza POST oficial.
- SetCurrencyRate continúa como POST y toda escritura conserva GET posterior de verificación.
- Soporte opcional para BCH Web-API oficial mediante API key cifrada.
- BCH XLSX se mantiene como fallback sin credenciales.
- Una fuente válida sigue siendo suficiente para configurar y leer.
- Si la fuente oficial no responde, las fuentes de respaldo se muestran pero la escritura SAP queda bloqueada.
- Wizard aclara que 3+ fuentes son recomendadas, no obligatorias.

## Validación de release

- CI Windows: 714 pruebas + smoke EXE/Portable.
- CI Debian/Ubuntu: 714 pruebas + smoke DEB.
- Security scan: SUCCESS.
- prueba real contra Service Layer TEST del cliente.
