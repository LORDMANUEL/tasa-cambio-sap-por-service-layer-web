# Instalación en Debian / Ubuntu

Instale el paquete generado por GitHub Actions:

```bash
sudo apt install ./sap-fx-control-center_5.0.0_amd64.deb
```

APT instala automáticamente Python 3, `python3-venv`, `python3-pip`, certificados y `xdg-utils` si faltan. Durante `postinst` se crea un entorno virtual y se instalan las dependencias Python declaradas por la aplicación.

## Rutas

- Aplicación: `/opt/sap-fx-control-center`
- Configuración: `/etc/sap-fx-control-center/app.env`
- Base de datos / uploads / clave local: `/var/lib/sap-fx-control-center`
- Logs: `/var/log/sap-fx-control-center`
- Servicio: `sap-fx-control-center.service`

## Servicio

```bash
systemctl status sap-fx-control-center
sudo systemctl restart sap-fx-control-center
```

Abra localmente `http://127.0.0.1:8787/` o ejecute `sap-fx-control-center`.

Linux cifra secretos con Fernet y una clave local protegida por permisos del sistema.
