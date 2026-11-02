# Atas V5.0.9 — AppFlow y BCH API completamente funcional

Fecha: 2026-11-02

## Correcciones funcionales

- Alinea AppFlow y UI con el comportamiento real del producto.
- El editor de Bancos ofrece BCH Web-API oficial además de PRESET, WEB_HTML y API_JSON.
- La regla visible queda en 1 fuente mínima por moneda y 3+ recomendadas para corroboración independiente.
- La fuente oficial sigue siendo obligatoria para permitir escritura SAP.
- Si la fuente oficial no responde, las secundarias quedan sólo para diagnóstico y SAP WRITE permanece bloqueado.
- SQLite acepta BCH_API en instalaciones nuevas.
- Migración automática y conservadora actualiza instalaciones antiguas sin perder fuentes, IDs, secretos, estados ni timestamps.
- El wizard usa el secreto/API key de BCH durante la validación real del paso de fuentes.
- El texto de cifrado se mantiene agnóstico de plataforma.

## SAP

- Conserva GetCurrencyRate v2 por POST oficial con fallback FunctionImport compatible.
- SetCurrencyRate continúa protegido por gates TEST/PROD.
- Toda escritura exige GET posterior y comparación exacta antes de marcar VERIFIED.

## Validación

- Windows: 718 passed + Portable + EXE instalado + autostart + single-instance + wizard + assets.
- Debian/Ubuntu: 718 passed + instalación DEB + wizard + assets.
- Security scan: SUCCESS.

## Validación externa pendiente

La única comprobación que CI no puede realizar es conectarse al Service Layer privado del cliente. La aceptación real debe hacerse primero contra una CompanyDB TEST.