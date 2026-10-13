# PRD — Atas V5.0.4

## 1. Producto

**Atas** automatiza y audita la tasa de cambio diaria utilizada por SAP Business One mediante Service Layer.

El producto es local-first, multiempresa y configurable. No reemplaza un ERP ni un módulo financiero; resuelve la obtención, validación, comparación, escritura y auditoría de tasas.

## 2. Usuarios

- Contabilidad: supervisa la tasa, estado y auditoría.
- Administrador de Atas: configura empresas, SAP, fuentes, horarios y seguridad.
- TI: instala, respalda, restaura y diagnostica.
- Auditoría: consulta transacciones, errores y evidencia de fuente.

## 3. Objetivos

1. Obtener una tasa desde una **fuente oficial configurable por empresa**.
2. Validarla contra al menos dos fuentes adicionales.
3. No escribir en SAP cuando el consenso no sea seguro.
4. Evitar escrituras duplicadas.
5. Verificar por GET toda escritura efectuada.
6. Mantener trazabilidad local.
7. Operar automáticamente con política de revalidación ante tasa repetida.
8. Permitir incorporar bancos/fuentes nuevas sin modificar Python mediante HTML o API JSON.

## 4. Alcance funcional

### 4.1 Moneda

USD es la moneda principal y predeterminada.

Otras monedas son opcionales. Una moneda sólo puede automatizarse cuando dispone de al menos tres fuentes válidas para esa moneda.

### 4.2 Política de fuente oficial

Cada CompanyDB selecciona una fuente oficial (`primary_bank`).

- La mediana/consenso es un control.
- La tasa aplicada es el valor `sell` de la fuente oficial.
- La fuente oficial debe superar controles de estructura, rango, spread, cantidad mínima de fuentes y outliers.
- Una empresa distinta puede elegir un banco distinto.

### 4.3 Tasa repetida

Para una ejecución configurada a las 06:00:

- 06:00: consulta fresca.
- si la fuente oficial conserva la tasa del día anterior: `WAITING_BANK_UPDATE`;
- 06:20: nueva consulta;
- 06:40: nueva consulta;
- 07:00: nueva consulta;
- si antes cambia y pasa consenso: procesar inmediatamente;
- si a las 07:00 sigue igual pero continúa válida y coherente: confirmar la tasa sin cambio y procesar SAP.

Los intervalos se parametrizan con:

- `same_rate_retry_minutes=20`;
- `same_rate_validation_window_minutes=60`.

La ventana es relativa al horario configurado de cada empresa.

### 4.4 SAP

Atas debe:

- soportar Service Layer OData v1/v2;
- soportar HANA y SQL Server a nivel de configuración de CompanyDB;
- leer tasa con `SBOBobService_GetCurrencyRate`;
- tratar SAP `-4006` como tasa ausente;
- decidir CREATE / UPDATE / MATCH;
- escribir con `SBOBobService_SetCurrencyRate` sólo cuando está autorizado;
- ejecutar GET posterior y exigir igualdad exacta;
- permitir TLS verificado cuando la infraestructura lo requiera;
- permitir TLS deshabilitado para redes internas/autofirmadas administradas por la organización.

### 4.5 Fuentes

Tipos:

- PRESET;
- WEB_HTML AUTO/CSS/REGEX;
- API_JSON AUTO/MAPPING.

Las fuentes pueden usar headers públicos y headers secretos cifrados.

### 4.6 Multiempresa

Cada CompanyDB puede definir:

- TEST/PROD;
- endpoint Service Layer propio o global;
- versión OData;
- usuario/credencial SAP;
- fuente oficial;
- fuentes de consenso;
- moneda(s);
- horario;
- autorización de escritura;
- TLS.

### 4.7 Auditoría y recuperación

Atas debe mantener:

- transacciones;
- errores;
- evidencia diaria de fuentes;
- logs;
- CSV;
- backup verificado;
- restauración offline con rollback;
- reporte de recuperabilidad de credenciales.

## 5. Requisitos no funcionales

- ejecución local por defecto en `127.0.0.1`;
- secretos cifrados: DPAPI Windows / Fernet Linux;
- SQLite WAL;
- no registrar passwords/tokens;
- CI Windows y Ubuntu;
- instalador EXE, Portable ZIP y DEB;
- seguridad fail-closed para consenso o escritura;
- responsive claro/oscuro;
- documentación y trazabilidad de release.

## 6. Fuera de alcance

- reemplazar SAP;
- definir la política contable de una empresa;
- garantizar disponibilidad de sitios bancarios externos;
- migrar automáticamente credenciales DPAPI entre usuarios/equipos Windows;
- ejecutar pruebas reales contra infraestructura privada desde GitHub Actions.

## 7. Criterio de aceptación del producto

La entrega de software se acepta cuando:

- suite automática verde en Windows y Ubuntu;
- secret scan de árbol + historial verde;
- EXE/Portable/DEB construidos y smoke-tested;
- documentación PRD/TRD/UI/UX/Appflow/Backend Schema/Plan/Trazabilidad actualizada;
- release estable creada desde un commit verde;
- Pages actualizada.

La activación productiva de una instalación requiere además probar su Service Layer real y autorizar PROD.
