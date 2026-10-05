# Asistente inicial

El setup aparece mientras `app_settings.setup_complete=false` y no requiere login porque todavía no existe administrador.

Al finalizar:

1. Guarda branding (nombre + logo).
2. Crea el administrador web.
3. Cifra SMTP password si se habilitó.
4. Guarda endpoint global Service Layer/OData.
5. Crea las CompanyDB indicadas.
6. Cifra credenciales SAP por CompanyDB.
7. Crea al menos tres fuentes de mercado.
8. Guarda horario, zona horaria, monedas y fuente oficial.
9. Marca `setup_complete=true`.
10. Abre sesión y redirige al dashboard con recorrido guiado.
