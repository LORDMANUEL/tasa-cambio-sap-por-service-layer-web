# UI/UX Design Specification — Atas V5.0.4

## Principios

1. Mostrar estado antes que configuración.
2. Distinguir claramente TEST y PROD.
3. Hacer visible la fuente oficial y la tasa elegida.
4. No ocultar bloqueos, reintentos ni errores.
5. Las operaciones críticas deben mostrar progreso y resultado.
6. Responsive y usable desde escritorio/tablet/teléfono.
7. Branding configurable sin cambiar código.

## Sistema visual

- sidebar persistente;
- topbar;
- tarjetas KPI;
- badges semánticos;
- tablas contables;
- tema claro/oscuro;
- branding empresa;
- estados OK / WARNING / BLOCKED / ERROR / WAITING;
- proceso animado Banco → Validación → SAP → Comparación → Escritura → Verificación → Auditoría.

## Pantallas

### Setup

Ocho etapas:

1. empresa/branding;
2. administrador;
3. notificaciones;
4. Service Layer;
5. CompanyDB;
6. fuentes;
7. automatización;
8. finalización.

Debe impedir terminar con configuración inválida.

### Login

- identidad del producto;
- organización;
- usuario/password;
- sin revelar detalles técnicos sensibles.

### Dashboard

Debe responder en segundos:

- ¿qué empresas están activas?;
- ¿qué tasa/fuente se usó?;
- ¿qué pasó en SAP?;
- ¿hay bloqueo/error?;
- ¿cuándo se ejecuta/reintenta?.

### Empresas

CRUD CompanyDB y prueba de SAP.

### Bancos/fuentes

- alta;
- preview sin guardar;
- test individual/todos;
- configuración HTML/API;
- fuente oficial definida a nivel de empresa.

### Automatización

- horario;
- estado última ejecución;
- próximo reintento;
- ejecución manual;
- gate PROD.

### Transacciones/Reportes

- trazabilidad;
- filtros;
- CSV;
- errores.

### Configuración

- organización;
- Service Layer global;
- TLS;
- backup;
- SMTP;
- administrador.

## Criterios UX

- ninguna escritura SAP debe parecer exitosa sin verificación;
- `WAITING_BANK_UPDATE` se muestra como espera operacional, no éxito;
- errores deben ofrecer contexto y ruta de recuperación;
- valores sensibles nunca se reimprimen;
- botones de ejecución deben usar feedback de proceso;
- no depender sólo de color para significado.
