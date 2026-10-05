# Atas V5 — diferencias verificadas respecto a V4.3.4

Esta comparación toma como base el paquete funcional **TASA_V4_3_4_ACCOUNTING_FUNCIONAL.zip** y la línea V5 que evolucionó desde él. La intención de V5 no fue reemplazar el motor contable ya funcional de V4, sino conservarlo y convertirlo en un producto instalable, multiempresa, multipaís, configurable y con una interfaz más completa.

## Métricas del paquete base

| Métrica | V4.3.4 funcional | V5 histórico completo | Atas V5 actual en GitHub |
|---|---:|---:|---:|
| Archivos del paquete fuente | 55 | 54 | 72+ |
| Código Python | 23 archivos / 1,886 líneas | 26 archivos / 2,456 líneas | superior por motor de fuentes + distribución |
| Tamaño fuente sin comprimir | 442,311 bytes | 2,085,884 bytes* | ~241,912 bytes sin artifacts binarios |
| ZIP fuente | 151,714 bytes | 1,911,519 bytes* | GitHub mantiene fuente; binarios se generan por Actions |
| Instalador Windows | no era EXE autocontenido | preparación inicial | ~20.7 MB artifact, Python 3.13 embebido |
| Paquete Debian/Ubuntu | no | preparación inicial | ~61 KB DEB, Python/dependencias se instalan con APT/pip |

* El V5 histórico incluía una referencia visual PNG de alta resolución, por eso su ZIP era mucho mayor que el código real.

## Lo que V4.3.4 ya hacía y se conserva

V4.3.4 ya era la base funcional y contable. Atas V5 conserva los principios que no debían romperse:

- cliente SAP Business One Service Layer;
- login/logout;
- lectura de moneda local;
- lectura correcta de tasa con `SBOBobService_GetCurrencyRate`;
- interpretación de SAP `-4006` como tasa ausente;
- escritura con `SBOBobService_SetCurrencyRate`;
- GET posterior de verificación;
- política Decimal `MATCH / CREATE / UPDATE`;
- separación TEST/PROD;
- auditoría SQLite;
- scheduler;
- panel web local;
- logs;
- lectura de bancos comerciales;
- protección de credenciales;
- exportación contable;
- escritura manual controlada en producción incorporada en la evolución V4.3.x.

## Cambios agregados en V5 / Atas

### 1. Producto genérico
V4 estaba orientado al despliegue que originó el proyecto. V5 elimina CompanyDB, empresa y credenciales pregrabadas. Una instalación nueva inicia vacía y se configura mediante wizard.

### 2. Asistente de primera ejecución
Se agregó un setup guiado que solicita:

1. nombre y logo;
2. administrador local;
3. SMTP opcional;
4. Service Layer global;
5. una o varias CompanyDB;
6. credenciales SAP compartidas o individuales;
7. tres o más fuentes de tasa;
8. horario, zona horaria, monedas y fuente oficial.

### 3. Multiempresa / múltiples Service Layers
Cada CompanyDB puede definir:

- HANA o SQL Server;
- TEST o PROD;
- usuario SAP;
- secreto SAP;
- Service Layer propio;
- OData v1/v2 propio;
- monedas;
- fuentes de comparación;
- hora de ejecución;
- permisos de escritura.

### 4. Motor genérico de fuentes
Se agregó `app/market_sources.py`.

Tipos admitidos:

- `PRESET`;
- `WEB_HTML`;
- `API_JSON`.

Métodos de extracción:

- AUTO;
- CSS selectors;
- REGEX;
- JSON AUTO;
- JSON mapping por path.

Esto permite utilizar Atas fuera de Honduras sin modificar el código del motor.

### 5. Regla de 3 fuentes
V4 usaba banco primario/secundario. V5 exige por defecto **tres fuentes válidas** para automatización.

La fuente oficial sigue siendo la tasa que se aplica, pero sólo después de:

- obtener 3+ valores;
- calcular mediana;
- medir desviación;
- detectar outliers;
- confirmar que la fuente oficial está dentro del límite.

### 6. Notificaciones salientes
Se agregó SMTP opcional con:

- STARTTLS;
- SSL;
- múltiples destinatarios;
- avisos de éxito/error;
- contraseña cifrada.

Atas no recibe correo.

### 7. Seguridad multiplataforma
Windows conserva DPAPI. Linux agrega Fernet con una clave local separada de SQLite.

Además se mantienen:

- PBKDF2 para administrador web;
- cookie HttpOnly/SameSite;
- CSP;
- `127.0.0.1` por defecto;
- redacción de secretos en logs;
- doble autorización para PROD.

### 8. UX/UI
V4 ya tenía panel y mejoras visuales. V5 amplía la experiencia con el concepto visual integrado:

- sidebar;
- topbar;
- tarjetas KPI;
- modo claro/oscuro;
- recorrido guiado;
- responsive;
- branding por empresa;
- overlay de ejecución;
- flujo Banco → Validación → SAP → Comparación → Escritura → Verificación → Registro;
- bitácora visual durante procesos.

### 9. Distribución real
V4 se ejecutaba principalmente desde BAT/Python.

Atas V5 agrega:

- instalador Windows EXE con Python 3.13 embebido;
- dependencias Python dentro del payload Windows;
- paquete Debian/Ubuntu DEB;
- servicio systemd;
- launcher Linux;
- GitHub Actions para CI y builds;
- artifacts con tamaño y SHA-256;
- GitHub Pages para presentación del producto.

### 10. Branding
El producto pasa a llamarse **Atas**.

Autor y proyecto:

- GitHub: https://github.com/LORDMANUEL
- Repositorio: https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web

## Conclusión

**V4.3.4 = núcleo funcional contable probado.**

**Atas V5 = ese núcleo conservado + producto genérico + multiempresa + multipaís + motor de 3 fuentes + UX/UI ampliada + SMTP + instaladores + CI/CD + Pages + branding/distribución.**

Por diseño, ninguna mejora visual debe cambiar la regla contable principal: si la tasa SAP no coincide con la tasa oficial segura, Atas propone o ejecuta la corrección según los permisos configurados, y siempre verifica con un GET posterior.
