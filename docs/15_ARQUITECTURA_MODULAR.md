# Arquitectura modular de rutas

Atas separa gradualmente la capa HTTP/UI del motor contable para reducir el
radio de impacto de cada cambio.

## Regla

Cada router debe:

- conservar las mismas URLs públicas;
- recibir dependencias explícitas cuando dependan del estado de la aplicación;
- no contener lógica SAP ni reglas de consenso bancario;
- delegar trabajo de dominio a servicios/módulos existentes;
- disponer de pruebas de regresión antes de extraer otro bloque.

## Routers extraídos

- `app/routes/auth.py`: login/logout.
- `app/routes/backup.py`: creación de backups verificados desde Configuración.

La extracción es incremental. No se moverán múltiples áreas grandes en un solo
commit.
