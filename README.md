# Atas V5

**Autor:** **Luis Manuel Fajardo Rivera** · [LORDMANUEL](https://github.com/LORDMANUEL) · **Repositorio:** [tasa-cambio-sap-por-service-layer-web](https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web)


Plataforma web **local-first, multiempresa y multipaís** para controlar la tasa de cambio diaria de SAP Business One mediante Service Layer.

El proyecto consulta fuentes bancarias o APIs, exige un consenso mínimo, compara la tasa existente en SAP, aplica cambios autorizados y conserva trazabilidad de cada ejecución.

> Alcance deliberado: no pretende reemplazar un ERP ni un módulo financiero. Se especializa en una tarea pequeña pero crítica: **mantener y auditar la tasa diaria de SAP Business One**.

## Estado del proyecto

**Sitio oficial:** https://lordmanuel.github.io/tasa-cambio-sap-por-service-layer-web/

[![CI](https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web/actions/workflows/ci.yml/badge.svg)](https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web/actions/workflows/ci.yml)
[![Build installers](https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web/actions/workflows/build-installers.yml/badge.svg)](https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web/actions/workflows/build-installers.yml)

## Funciones principales

- Asistente de primera ejecución con nombre y logo de la empresa.
- Administrador web local.
- SMTP **solo saliente** opcional y lista de destinatarios.
- Service Layer global o independiente por CompanyDB.
- OData `v1` / `v2` configurable.
- SAP Business One sobre HANA o SQL Server.
- Multiempresa / multibase.
- Credenciales SAP compartidas o diferentes por base.
- Fuentes de tasa de tipo:
  - API JSON.
  - HTML con detección automática.
  - HTML con selectores CSS.
  - Regex.
  - Presets de conectores conocidos.
- Mínimo **3 fuentes válidas** antes de habilitar automatización.
- Fuente oficial + fuentes de comparación y detección de outliers.
- Programación diaria por CompanyDB y moneda.
- Separación TEST / PROD.
- Escritura con `SBOBobService_SetCurrencyRate` y GET posterior de verificación.
- Historial, auditoría, CSV, errores y logs.
- UI responsive, modo claro/oscuro, recorrido guiado y animaciones de proceso.

## Flujo de negocio

```text
Banco/API oficial + 2 o más fuentes de control
                    │
                    ▼
           Extracción / normalización
                    │
                    ▼
          Consenso y detección de outlier
                    │
                    ▼
          Lectura de la tasa actual en SAP
                    │
                    ▼
             CREATE / UPDATE / MATCH
                    │
                    ▼
             Escritura autorizada
                    │
                    ▼
              GET de verificación
                    │
                    ▼
                  Auditoría
```

## Instaladores

### Windows x64

El workflow **Build Atas installers** genera un `.exe` que incluye:

- Python 3.13 embebido.
- Dependencias Python preinstaladas.
- Aplicación completa.
- Lanzador local.
- Accesos directos.

No requiere Python previamente instalado.

[Guía de instalación Windows](docs/INSTALL_WINDOWS.md)

También existe una edición **Portable x64**: se descomprime y ejecuta con el Python 3.13 incluido; CI valida el ZIP ya descomprimido contra `/health`.

### Debian / Ubuntu amd64

El `.deb`:

- Declara Python 3 como dependencia APT.
- Crea su entorno virtual automáticamente.
- Crea un entorno virtual aislado e instala las dependencias Python durante la instalación.
- Instala un servicio `systemd`.
- Crea rutas persistentes para configuración, DB y logs.

[Guía de instalación Debian/Ubuntu](docs/INSTALL_DEBIAN.md)

Los binarios se publican como **Artifacts** del workflow:

**Actions → Build Atas installers**

Artifacts esperados:

- `Atas-Windows-x64` → `Atas-V5.0.3-Setup-x64.exe` + `BUILD_INFO.txt`.
- `Atas-Windows-Portable-x64` → `Atas-V5.0.3-Portable-x64.zip` + `BUILD_INFO_PORTABLE.txt`.
- `Atas-Debian-amd64` → `atas_5.0.3_amd64.deb` + `BUILD_INFO_DEBIAN.txt`.

## Binarios V5.0.3 verificados

| Plataforma | Archivo | Tamaño | SHA-256 |
|---|---|---:|---|
| Windows Installer x64 | `Atas-V5.0.3-Setup-x64.exe` | 18,419,585 B · 17.57 MiB | `d57b5e79cf8df9f26d2c5129dc0f22505685e53c25c890d53d4c7f9426a90df4` |
| Windows Portable x64 | `Atas-V5.0.3-Portable-x64.zip` | 25,158,001 B · 23.99 MiB | `4222dff8da2adb5fefa745bd6a4777dca3ff3b81581b1ed5ba737f08470cdba9` |
| Debian/Ubuntu amd64 | `atas_5.0.3_amd64.deb` | 76,026 B · 74.24 KiB | `d69efb3f9ad14ea64b379d8023339112115031ab7e0deadf94b68447417cd62f` |

[Manifiesto completo](docs/RELEASE_MANIFEST_V5.0.3.md)

## Release estable

**Atas V5.0.3** quedó validada en Windows y Debian/Ubuntu con **77 pruebas automáticas por plataforma**, smoke tests del producto instalado y verificación del wizard/recursos web.

La versión publicada se encuentra en:

**https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web/releases/latest**

La Release adjunta los binarios de Windows y Debian junto con sus archivos de tamaño/SHA-256.

> Estado de desarrollo: `main` está en **5.0.4-dev**. El build #192 validó 77 pruebas por plataforma, EXE, Portable y DEB. La release pública estable y GitHub Pages continúan apuntando a **V5.0.3** hasta cerrar la aceptación funcional de V5.0.4.

## Ejecución desde código fuente

### Windows

```bat
ATAS.bat
```

En la primera ejecución el BAT instala Python 3.13 mediante `winget` si hace falta, crea `.venv`, instala dependencias, ejecuta pruebas y abre:

```text
http://127.0.0.1:8787/
```

### Linux / macOS para desarrollo

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.run_server
```

## Seguridad local de secretos

- Windows: **DPAPI**.
- Linux: **Fernet** con clave local separada de SQLite y permisos restringidos.
- Las contraseñas SAP, SMTP y headers secretos de APIs no se registran en logs.
- El panel escucha en `127.0.0.1` de forma predeterminada.

## Estructura

```text
app/                    Backend FastAPI, UI, SAP, bancos, scheduler
app/providers/          Conectores conocidos
app/static/             CSS, JavaScript, uploads locales
scripts/                Bootstrap y empaquetado
installer/windows/      Proyecto Inno Setup
packaging/debian/       Archivos DEB / systemd
site/                   GitHub Pages
.github/workflows/      CI, instaladores y Pages
tests/                  Pruebas automatizadas
docs/                   Documentación técnica y operativa
```

## Documentación

- [Arquitectura](docs/01_ARQUITECTURA.md)
- [Asistente inicial](docs/02_ASISTENTE_INICIAL.md)
- [Multiempresa / Service Layer](docs/03_MULTIEMPRESA_SERVICE_LAYER.md)
- [Notificaciones](docs/04_NOTIFICACIONES.md)
- [Seguridad](docs/05_SEGURIDAD.md)
- [UX/UI](docs/06_UX_UI_CONCEPTO_4.md)
- [Rutas web](docs/07_RUTAS.md)
- [SQLite](docs/08_ESQUEMA_SQLITE.md)
- [Operación](docs/09_OPERACION.md)
- [Motor de fuentes bancarias](docs/11_MOTOR_FUENTAS_BANCARIAS.md)
- [Multipais y monedas](docs/12_MULTI_PAIS_MONEDAS.md)
- [Instalación Windows](docs/INSTALL_WINDOWS.md)
- [Instalación Debian/Ubuntu](docs/INSTALL_DEBIAN.md)
- [Distribución por GitHub](docs/GITHUB_DISTRIBUTION.md)
- [Diferencias verificadas V4.3.4 → Atas V5](docs/V4_V5_DIFERENCIAS.md)

## Pruebas

```bash
python -m compileall -q app
python -m pytest -q
```

CI ejecuta la suite en Windows y Ubuntu.

## GitHub Pages

El sitio de presentación se encuentra en `site/`. El workflow `.github/workflows/publish-pages.yml` sincroniza esa carpeta con `gh-pages`, y GitHub Pages publica automáticamente: https://lordmanuel.github.io/tasa-cambio-sap-por-service-layer-web/

## Nota sobre SAP

Este proyecto se comunica con SAP Business One mediante **Service Layer**. Antes de habilitar producción valide endpoint, versión OData, CompanyDB, permisos del usuario y certificados TLS en su propia infraestructura.

SAP y SAP Business One son marcas de sus respectivos propietarios. Este repositorio no representa una distribución oficial de SAP.


## Licencia y responsabilidad

**Atas es software propietario; no es software open source.** Copyright © 2026 Luis Manuel Fajardo Rivera. Todos los derechos reservados.

El acceso al código en GitHub no concede permiso para copiar, redistribuir, sublicenciar, vender, explotar comercialmente ni crear obras derivadas, salvo los derechos mínimos que GitHub otorgue necesariamente para operar su plataforma o una autorización escrita del titular.

El uso autorizado de Atas se realiza bajo los términos de [LICENSE](LICENSE). El software se entrega **sin garantías**, y toda integración con SAP Business One, bancos, APIs o infraestructura del usuario debe validarse en un ambiente de prueba antes de habilitar escritura en producción.

Atas no es un producto de SAP SE ni está afiliado, patrocinado, certificado o respaldado por SAP. SAP y SAP Business One son marcas o marcas registradas de SAP SE o sus afiliadas en Alemania y otros países.

Consulte también [LEGAL.md](LEGAL.md), [SECURITY.md](SECURITY.md) y [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
