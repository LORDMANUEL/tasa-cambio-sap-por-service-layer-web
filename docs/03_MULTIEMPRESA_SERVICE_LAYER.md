# Multiempresa y Service Layer

Existe una conexión predeterminada global y overrides opcionales por CompanyDB.

Campos por base:

- Nombre visible.
- Tipo BD: HANA / SQL Server.
- CompanyDB.
- Ambiente TEST/PROD.
- Usuario SAP.
- Credencial SAP cifrada.
- Service Layer root opcional.
- OData opcional.
- Fuentes asignadas y fuente oficial.
- Monedas.
- Hora diaria.
- Gates de escritura.

La función `_sap_url()` en `app/sync_engine.py` resuelve el endpoint efectivo por ejecución. Esto permite una sola empresa con varias bases o una torre multiempresa con servidores distintos.
