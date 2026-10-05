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

- `Atas-Windows-x64` → `Atas-V5-Setup-x64.exe` + `BUILD_INFO.txt`.
- `Atas-Debian-amd64` → `atas_5.0.0_amd64.deb` + `BUILD_INFO_DEBIAN.txt`.

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
