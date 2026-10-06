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


## Restauración offline de SQLite

La restauración de la base está disponible mediante:

```bash
python -m scripts.restore_backup RUTA/atas-backup-AAAAMMDD-HHMMSS.zip --yes
```

Antes de restaurar:

1. detener Atas;
2. conservar una copia externa del ZIP;
3. ejecutar el comando con el mismo usuario de la instalación.

El restaurador:

1. valida estructura, SHA-256 e integridad del ZIP;
2. comprueba que `http://127.0.0.1:<puerto>/health` no esté respondiendo como Atas;
3. crea un backup preventivo de la base actual en `data/backups/pre-restore/`;
4. valida la base candidata;
5. reemplaza `atas.db` de forma atómica;
6. ejecuta `PRAGMA integrity_check` sobre la base restaurada;
7. si falla, revierte automáticamente a la base anterior.

Esta etapa restaura solamente SQLite. `.env` y material criptográfico siguen requiriendo un procedimiento separado y explícito.
