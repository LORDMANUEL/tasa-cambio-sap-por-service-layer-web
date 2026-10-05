# Atas V5 — instalación en Debian / Ubuntu

Instale el paquete generado por GitHub Actions:

```bash
sudo apt install ./atas_5.0.0_amd64.deb
```

APT instala automáticamente Python 3, `python3-venv`, `python3-pip`, certificados y `xdg-utils` si faltan. Durante `postinst` se crea un entorno virtual y se instalan las dependencias Python declaradas por la aplicación. Esta fase requiere acceso a Internet para obtener los paquetes Python desde PyPI.

## Rutas

- Aplicación: `/opt/atas`
- Configuración: `/etc/atas/app.env`
- Base de datos / uploads / clave local: `/var/lib/atas`
- Logs: `/var/log/atas`
- Servicio: `atas.service`

## Servicio

```bash
systemctl status atas
sudo systemctl restart atas
```

Abra localmente `http://127.0.0.1:8787/` o ejecute `atas`.

Linux cifra secretos con Fernet y una clave local protegida por permisos del sistema.
