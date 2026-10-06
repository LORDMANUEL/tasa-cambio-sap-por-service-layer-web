# Operación diaria

1. Scheduler detecta CompanyDB activa y hora cumplida.
2. Consulta todas las fuentes asignadas.
3. Exige 3+ lecturas válidas.
4. Calcula mediana, desviación y outliers.
5. Valida que la fuente oficial sea segura.
6. Resuelve Service Layer efectivo de esa empresa.
7. Login SAP.
8. GET tasa del día.
9. Decide MATCH / CREATE / UPDATE.
10. Si está autorizado, escribe.
11. GET posterior verifica Decimal exacto.
12. Registra transacción y última ejecución.
13. Si SMTP está habilitado, envía resumen.


## Backup e integridad

Desde **Configuración → Backup e integridad** se crea un snapshot consistente mediante la API online de SQLite. Atas valida la base antes del snapshot, valida nuevamente el snapshot, calcula SHA-256 y vuelve a validar el ZIP final.

Los archivos se guardan en `data/backups/` y son sensibles. En Linux el backup puede incluir la clave Fernet necesaria para recuperar credenciales; en Windows las credenciales DPAPI permanecen ligadas al usuario/máquina que las cifró.

La restauración en caliente no está permitida. El procedimiento de restauración será offline/controlado para no reemplazar SQLite mientras el servicio tiene conexiones abiertas.
