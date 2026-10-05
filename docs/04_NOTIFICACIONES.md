# Notificaciones salientes

Archivo: `app/notifications.py`.

El módulo usa SMTP y **solo realiza envíos**. No abre IMAP/POP3 ni recibe mensajes.

Configuración:

- enabled;
- SMTP host/port;
- STARTTLS / SSL / NONE;
- usuario;
- clave cifrada;
- remitente;
- lista de destinatarios;
- notificar éxito/error.

Los fallos de correo nunca revierten ni repiten una escritura SAP: se registran en log y el proceso contable conserva su resultado original.
