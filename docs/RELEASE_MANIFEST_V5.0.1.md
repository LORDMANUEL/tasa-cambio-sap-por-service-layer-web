# Atas V5.0.1 — Release Manifest

Release pública: https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web/releases/tag/v5.0.1

Autor: **Luis Manuel Fajardo Rivera (LORDMANUEL)**

## Binarios publicados

| Archivo | Bytes | Tamaño legible | SHA-256 |
|---|---:|---:|---|
| `Atas-V5.0.1-Setup-x64.exe` | 21,273,082 | 20.29 MiB | `630ce10ff31ffcef43a5e6c5cbd8bf1a1c6f73282d09c62faa7107351a0ed50a` |
| `Atas-V5.0.1-Portable-x64.zip` | 30,541,833 | 29.13 MiB | `6ecb27ae224e2a90ae923c6fddddf63692d8c606d0194b99267de72f7abdf817` |
| `atas_5.0.1_amd64.deb` | 68,366 | 0.07 MiB | `6880335c67fb4e9a3679b8a7efe3101dd7d6879ce2b32e42e3d22588c446c9b0` |

## Pruebas verificadas antes de publicar

- **28 pruebas automáticas Windows: OK**.
- **28 pruebas automáticas Ubuntu: OK**.
- `compileall app`: OK.
- `node --check app/static/app.js`: OK.
- EXE Windows compilado e instalado silenciosamente en runner limpio: OK.
- EXE arrancó usando Python 3.13 embebido y respondió `/health`: OK.
- Portable ZIP generado, extraído y probado desde directorio limpio: OK.
- DEB construido, instalado mediante APT y probado con `/health`: OK.
- GitHub Release y GitHub Pages: OK.

## Cambio principal de V5.0.1

La automatización diaria usa un **claim atómico por CompanyDB y fecha** para impedir ejecuciones duplicadas del scheduler. Un error inesperado se registra una sola vez y no provoca reintentos automáticos repetidos durante el mismo día.

## Descargas directas

- https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web/releases/download/v5.0.1/Atas-V5.0.1-Setup-x64.exe
- https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web/releases/download/v5.0.1/Atas-V5.0.1-Portable-x64.zip
- https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web/releases/download/v5.0.1/atas_5.0.1_amd64.deb

Los tamaños y SHA-256 provienen del workflow que generó y publicó V5.0.1; no son estimaciones manuales.
