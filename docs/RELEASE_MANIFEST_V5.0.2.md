# Atas V5.0.2 — Release Manifest

Release pública: https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web/releases/tag/v5.0.2

Autor: **Luis Manuel Fajardo Rivera (LORDMANUEL)**

## Binarios publicados

| Archivo | Bytes | Tamaño legible | SHA-256 |
|---|---:|---:|---|
| `Atas-V5.0.2-Setup-x64.exe` | 21,295,977 | 20.31 MiB | `638ea31734c7b3b79a35d21a6154d78a9783f45d046063ae1af1501ee4088cfa` |
| `Atas-V5.0.2-Portable-x64.zip` | 30,577,751 | 29.16 MiB | `cebf1f7f4574355af4099a40b597c07dcc66d8499c013bda2619778c33fcadcf` |
| `atas_5.0.2_amd64.deb` | 73,956 | 72.22 KiB | `3bd3a380b03535fa15895cc99a22db7ef31c5e4465a64e040f9a78a3545e23aa` |

## Validación de la release

- **52 pruebas Windows: OK**.
- **52 pruebas Debian/Ubuntu: OK**.
- `compileall`: OK.
- JavaScript syntax check: OK.
- Portable ZIP: extracción limpia + servidor + `/health` + wizard + CSS: OK.
- Windows EXE: instalación silenciosa + Python embebido + servidor + `/health` + wizard + CSS: OK.
- Debian DEB: instalación APT + venv + servicio/runtime + `/health` + wizard + CSS: OK.
- GitHub Release: OK.
- GitHub Pages: OK.

## Correcciones destacadas

- Compatibilidad de la prueba SQLite con bloqueo de archivos de Windows.
- Scheduler diario sin duplicados y separado de ejecuciones manuales.
- Auditoría de fallos bancarios/credenciales previos al login SAP.
- OData v1 POST y OData v2 GET para tasa de cambio.
- Estado `BLOCKED` correctamente priorizado sobre `MATCH`.
- Configuración web de TLS Service Layer.
- Setup reintentable.
- Fuentes con validación buy/sell y spread.
- Formularios web endurecidos contra entradas inválidas.
- Launcher Windows single-instance y autostart opcional.
- Persistencia Debian protegida en actualizaciones.
- Redacción reforzada de secretos en logs.

## Descargas directas

- https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web/releases/download/v5.0.2/Atas-V5.0.2-Setup-x64.exe
- https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web/releases/download/v5.0.2/Atas-V5.0.2-Portable-x64.zip
- https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web/releases/download/v5.0.2/atas_5.0.2_amd64.deb

Los tamaños y SHA-256 anteriores provienen directamente de los assets publicados por GitHub Release.
