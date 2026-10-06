# Backup y recuperación

Atas crea backups consistentes de SQLite mediante `sqlite3.Connection.backup()`, no mediante una copia simple del archivo mientras está en uso.

## Contenido

El ZIP incluye:

- `atas.db`: snapshot consistente;
- `manifest.json`: versión, fecha, zona horaria y SHA-256;
- `app.env` cuando existe;
- `credential.key` en Linux cuando existe una clave Fernet local.

En Windows las credenciales cifradas con DPAPI continúan ligadas al perfil/máquina de Windows que las generó.

## Validaciones

Antes de declarar un backup correcto Atas:

1. ejecuta `PRAGMA integrity_check` sobre la base activa;
2. genera el snapshot con la API online de SQLite;
3. ejecuta `integrity_check` sobre el snapshot;
4. calcula SHA-256 del snapshot;
5. empaqueta;
6. vuelve a abrir el ZIP;
7. verifica estructura, hash e integridad SQLite.

## Seguridad

El backup debe tratarse como información sensible. Puede incluir configuración y material criptográfico. No debe subirse a GitHub, correo ni tickets públicos.

## Restauración

La restauración automática en caliente no está habilitada. La aplicación debe detenerse antes de reemplazar la base o material criptográfico. La restauración controlada/offline se incorporará como siguiente etapa.
