# Rutas principales

- `GET/POST /setup` — asistente inicial.
- `GET/POST /login`, `GET /logout`.
- `GET /` — dashboard.
- `GET /companies`, `POST /companies/save`, `POST /companies/{id}/delete`.
- `GET /companies/{id}/test`, `POST /companies/{id}/write/{currency}`.
- `GET /automation`, `POST /automation/prod-toggle`, `POST /automation/run/{id}`, `POST /automation/run-all`.
- `GET /banks`, `POST /banks/save`, `POST /banks/preview`, pruebas y eliminación.
- `GET /transactions`.
- `GET /reports` y CSV.
- `GET /settings`, configuración general, SMTP y administrador.
- `GET /logs`, `GET /health`.
