# SECURITY.md

## Modelo de seguridad

Atas debe ejecutarse con privilegio mínimo y, por defecto, enlazado a `127.0.0.1`.

## Reglas obligatorias de despliegue

1. Probar primero contra CompanyDB de TEST.
2. Usar una cuenta SAP dedicada con los permisos mínimos necesarios.
3. Mantener escritura PROD deshabilitada hasta completar la aceptación.
4. Activar verificación TLS cuando la infraestructura disponga de certificados confiables.
5. No publicar `.env`, bases SQLite, logs, cookies, claves Fernet, contraseñas SAP/SMTP ni headers privados.
6. Mantener backups y un procedimiento documentado de recuperación.
7. Revisar el GET posterior a cada escritura y la auditoría generada.
8. No exponer el panel directamente a Internet. Para acceso remoto use una capa autenticada y administrada fuera de Atas.

## Secretos

- Windows: DPAPI cuando corresponde.
- Linux: Fernet con clave local separada y permisos restringidos.
- Las pruebas automáticas no deben contener credenciales reales.
- Los ejemplos deben utilizar dominios reservados, nombres ficticios y valores no operativos.

## Reporte responsable

No publique una vulnerabilidad con secretos, credenciales o información de clientes en un issue público. Use un canal privado previamente acordado con el propietario del software.

## Límites

La existencia de controles de seguridad, pruebas o CI no constituye garantía de seguridad absoluta. Cada despliegue debe someterse a la política de seguridad y gestión de cambios de la organización que lo opera.


## Escaneo preventivo de secretos

El repositorio ejecuta `.github/workflows/security.yml` en cada push y pull request a `main`.

El scanner revisa:

- árbol de trabajo actual;
- todos los blobs alcanzables del historial Git;
- claves privadas PEM/OpenSSH;
- formatos conocidos de tokens GitHub, AWS, Slack y Stripe;
- asignaciones literales de credenciales en código de aplicación.

Los fixtures bajo `tests/` se excluyen únicamente de la regla genérica de asignación literal; los patrones de tokens reales y claves privadas siguen bloqueándose también dentro de pruebas.

Ejecutar localmente:

```bash
python scripts/security/scan_secrets.py --history
```
