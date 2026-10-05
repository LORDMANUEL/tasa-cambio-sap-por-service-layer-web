# Atas V5.0.0

**Atas** es una plataforma local-first para automatizar y auditar tasas de cambio de SAP Business One mediante Service Layer.

Autor: **Luis Manuel Fajardo Rivera (LORDMANUEL)**  
GitHub: https://github.com/LORDMANUEL

## Entregables

- **Atas-V5-Setup-x64.exe** — instalador Windows x64 con Python 3.13 embebido.
- **Atas-V5-Portable-x64.zip** — edición portable Windows, sin instalación de Python.
- **atas_5.0.0_amd64.deb** — paquete Debian/Ubuntu amd64.
- Archivos `BUILD_INFO*.txt` con tamaño y SHA-256 generados por CI.

## Base funcional heredada de V4

La línea V4 ya implementaba el núcleo contable: lectura/escritura de tasa por Service Layer, política Decimal, verificación posterior, separación TEST/PROD, scheduler, auditoría, logs y panel web.

## Agregado en V5

- producto genérico sin datos de una empresa específica;
- wizard de primera ejecución;
- branding configurable;
- multiempresa / multibase;
- Service Layer y OData por CompanyDB;
- HANA / SQL Server;
- credenciales compartidas o independientes;
- fuentes API JSON / WEB HTML / CSS / Regex / presets;
- consenso mínimo de tres fuentes y detección de outliers;
- SMTP saliente opcional;
- DPAPI en Windows y Fernet en Linux;
- UI responsive, modo claro/oscuro, tour guiado y flujo visual;
- EXE Windows autocontenido;
- Portable ZIP Windows;
- DEB Debian/Ubuntu con systemd;
- CI Windows + Ubuntu;
- smoke test del EXE instalado, ZIP portable y DEB instalado;
- GitHub Pages público;
- pruebas de higiene para impedir datos específicos de clientes en el release.

## Validación

Los pipelines de release deben demostrar:

- `pytest` y `compileall`;
- Windows EXE instala y levanta `/health`;
- Windows Portable ZIP descomprime y levanta `/health`;
- Debian DEB instala y levanta `/health`;
- `/health` devuelve `status=ok` y `service=Atas`.

Las pruebas automatizadas deliberadamente **no escriben en un SAP de producción** ni dependen de endpoints privados de clientes.
