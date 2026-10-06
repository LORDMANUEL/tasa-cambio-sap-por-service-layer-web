# Atas V5.0.4-dev — Production Readiness

Fecha de revisión: 2026-10-06  
Head revisado: `6cc69576`  
Build de referencia: **Build Atas installers #192 — SUCCESS**

## Estado ejecutivo

Atas está **funcional a nivel de código, empaquetado y smoke tests**, pero todavía no debe calificarse como “100% producción” hasta cerrar los controles externos que CI no puede demostrar.

### Ya validado

- 77 pruebas automáticas en Windows.
- 77 pruebas automáticas en Debian/Ubuntu.
- compilación Python y validación JavaScript;
- Windows EXE x64;
- Windows Portable x64;
- Debian/Ubuntu DEB;
- instalación limpia y `/health`;
- wizard de primera ejecución;
- assets estáticos;
- single-instance en Windows;
- scheduler diario;
- claim atómico;
- Service Layer v1/v2 a nivel de cliente y mocks;
- CREATE / UPDATE / MATCH;
- GET posterior a escritura;
- mínimo de fuentes y detección de outliers;
- memoria diaria de tasas;
- `WAITING_BANK_UPDATE` y reintento cada hora;
- límite de reintentos;
- migraciones SQLite;
- GitHub Pages publicada en `gh-pages`;
- licencia propietaria, avisos legales y seguridad básica.

## Bloqueadores P0 — necesarios antes de PRODUCCIÓN

### P0.1 — Aceptación real contra SAP Business One TEST

**Problema:** CI utiliza mocks y smoke tests locales. No existe una prueba automatizada contra un Service Layer real del cliente.

**Cerrar con:**

1. configurar una CompanyDB TEST;
2. probar Login/Logout;
3. GET de moneda local;
4. GET de tasa inexistente y existente;
5. validar `-4006`;
6. CREATE de una tasa controlada;
7. GET posterior;
8. UPDATE controlado;
9. GET posterior;
10. comprobar auditoría;
11. repetir en OData realmente usado por el cliente;
12. validar certificado TLS y timeout.

**Criterio de cierre:** evidencia firmada/capturada de una ejecución TEST completa sin error.

### P0.2 — Definir la tasa contable exacta que debe escribir SAP

**Problema:** técnicamente se usa la tasa de venta de la fuente oficial, pero la empresa debe confirmar formalmente si corresponde **venta**, **compra** u otra referencia contable para USD→HNL.

**Cerrar con:** aprobación de Contabilidad/Finanzas documentada por moneda y banco.

### P0.3 — Fuente oficial bancaria lista

**Problema:** los presets automáticos actualmente validados son **Banpaís** y **Ficohsa**. Banco Atlántida sigue marcado `PENDIENTE` en el catálogo porque no hay un endpoint estable validado.

**Cerrar con una de estas opciones:**

- validar un endpoint/API estable de Atlántida;
- configurar Atlántida como WEB_HTML/API_JSON probado desde Atas;
- o designar formalmente otro banco como fuente oficial.

### P0.4 — Tercera fuente real de consenso

**Problema:** Atas exige mínimo 3 fuentes, pero sólo hay 2 presets automáticos incorporados. La tercera fuente debe configurarse y probarse en el despliegue.

**Criterio de cierre:** 3 fuentes activas reales, con prueba diaria y consenso aprobado.

### P0.5 — Backup y recuperación

**Problema:** no se detecta un mecanismo propio de backup/restore ni `PRAGMA integrity_check` automatizado para la SQLite de Atas.

**Cerrar con:**

- backup consistente de SQLite;
- rotación;
- restauración probada;
- verificación de integridad;
- respaldo de la clave de credenciales según plataforma;
- procedimiento documentado.

## Riesgos P1 — alta prioridad

### P1.1 — `app/main.py` demasiado grande

La capa HTTP/UI sigue concentrada en un archivo de aproximadamente 70 KB.

**Acción:** dividir gradualmente en routers: auth/setup, companies, banks, automation, audit, settings. No mover reglas SAP o bancarias al router.

### P1.2 — Rama `main` sin protección

GitHub reporta `main.protected = false`.

**Acción:** exigir PR + CI verde para merge y bloquear force-push/deletion.

### P1.3 — Repositorio público con licencia propietaria

El código puede verse y GitHub necesariamente concede ciertos derechos de plataforma. La licencia limita reutilización, pero un repositorio público no ofrece secreto industrial.

**Acción si se busca máxima protección:** repositorio privado + Pages/binarios públicos por separado.

### P1.4 — Secret scanning e historial Git

No hay evidencia en este audit de un escaneo integral del historial completo con una herramienta dedicada.

**Acción:** integrar un escáner de secretos en CI y ejecutar un barrido inicial del historial.

### P1.5 — Política de tasa repetida requiere aceptación de negocio

Después de 3 reintentos horarios, Atas entra en `ATTENTION` y no escribe automáticamente la misma tasa del día anterior.

**Acción:** Contabilidad debe decidir qué hacer si el banco confirma que la tasa realmente no cambió: ejecución manual, aceptar después de determinada hora, o mantener bloqueo.

## Riesgos P2 — importantes pero no bloqueantes

### P2.1 — GitHub Pages y release estable están en V5.0.3

Esto es correcto mientras `main` siga en `5.0.4-dev`, pero la página debe actualizar tamaños, enlaces, hashes y novedades cuando se publique V5.0.4.

### P2.2 — Documentación de pruebas estaba desactualizada

El repositorio aún indicaba 53 pruebas. Build #192 ejecuta 77. Se corrige en este cambio.

### P2.3 — Warnings de dependencias/Actions

Build #192 reporta:

- deprecación de `anyio.abc.BlockingPortal` desde Starlette TestClient;
- acciones de GitHub que aún generan advertencias de runtime Node 20 en runners nuevos.

No rompen el producto hoy, pero deben vigilarse/actualizarse.

### P2.4 — Proveedores HTML pueden cambiar sin aviso

Banpaís, Ficohsa y cualquier WEB_HTML pueden modificar su estructura.

**Acción:** mantener el bloqueo seguro actual y añadir alertas/health operacional para cambios de parser.

### P2.5 — Crecimiento de auditoría

`transactions` se conserva deliberadamente como evidencia y no se purga con `log_retention_days`.

**Acción:** agregar archivado/exportación y política de retención separada antes de grandes volúmenes.

## Criterio para declarar Atas 100% funcional

No usar “100%” sólo porque CI esté verde. Declarar producción lista cuando se cumplan todos:

- [ ] SAP TEST real aprobado.
- [ ] dirección/tipo de tasa aprobada por Contabilidad.
- [ ] fuente oficial definida y validada.
- [ ] mínimo 3 fuentes reales funcionando.
- [ ] prueba de tasa repetida y reintentos aceptada.
- [ ] backup y restore probados.
- [ ] TLS verificado en SAP.
- [ ] usuario SAP de mínimo privilegio.
- [ ] secreto/credenciales revisados.
- [ ] branch protection habilitada.
- [ ] release V5.0.4 generada desde commit aceptado.
- [ ] hashes de release registrados.
- [ ] GitHub Pages actualizada a V5.0.4.
- [ ] instalación real en Windows objetivo.
- [ ] ejecución programada observada al menos un día completo en TEST.
- [ ] autorización formal para habilitar PROD.

## Orden de trabajo recomendado

1. implementar backup/restore + integrity check;
2. cerrar una tercera fuente y la fuente oficial;
3. ejecutar aceptación SAP TEST;
4. separar `main.py` por routers;
5. secret scanning + branch protection;
6. observabilidad/health de fuentes;
7. congelar cambios;
8. cambiar `VERSION.txt` a `5.0.4`;
9. generar release final;
10. actualizar GitHub Pages y checklist de entrega.
