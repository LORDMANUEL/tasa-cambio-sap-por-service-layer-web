# Seguridad V5

- Panel enlazado a `127.0.0.1`.
- Windows: DPAPI para secretos SAP/SMTP/API.
- Linux: Fernet con clave local separada y permisos del sistema.
- Hash PBKDF2 para contraseña web.
- Cookie HttpOnly + SameSite Strict.
- CSP / X-Frame-Options / no-store.
- TEST/PROD diferenciados.
- Escritura PROD requiere autorización global y de CompanyDB.
- Mínimo 3 fuentes válidas antes de automatizar.
- Verificación GET posterior a cada write.
- Secrets excluidos de logs.
