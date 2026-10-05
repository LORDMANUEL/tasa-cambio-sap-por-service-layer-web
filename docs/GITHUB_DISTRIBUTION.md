# Distribución con GitHub

El repositorio incluye automatización para CI, instaladores y GitHub Pages.

## Workflows

- `ci.yml`: compila y ejecuta pruebas en Windows y Ubuntu.
- `build-installers.yml`: genera EXE para Windows y DEB para Debian/Ubuntu y los publica como artifacts.
- `pages.yml`: publica `site/` en GitHub Pages.

## Descargas

Abra **Actions → Build installers**, seleccione la ejecución exitosa más reciente y descargue:

- `SAP-FX-Control-Center-Windows-x64`
- `SAP-FX-Control-Center-Debian-amd64`

Para releases estables se recomienda etiquetar la versión y adjuntar esos binarios a una GitHub Release.
