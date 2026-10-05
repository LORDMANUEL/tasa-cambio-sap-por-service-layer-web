# Aviso legal de Atas

## Titularidad

Atas es software propietario de **Luis Manuel Fajardo Rivera**. Copyright © 2026. Todos los derechos reservados.

El repositorio público permite lectura y las funcionalidades que GitHub necesariamente concede bajo sus propios Términos de Servicio; esa visibilidad no convierte Atas en software open source ni concede una licencia general para copiar, comercializar, redistribuir o crear derivados.

La licencia aplicable está en [LICENSE](LICENSE).

## Integración con SAP

Atas es un desarrollo independiente que utiliza interfaces de SAP Business One cuando el operador configura sus propios endpoints y credenciales.

**Atas no es un producto de SAP SE y no está afiliado, patrocinado, certificado, aprobado ni respaldado por SAP SE o sus afiliadas.**

SAP y SAP Business One son marcas o marcas registradas de SAP SE o sus afiliadas en Alemania y otros países.

## Riesgo operativo

Atas puede modificar tasas de cambio de SAP Business One únicamente cuando la escritura se habilita expresamente. Un build o prueba automatizada exitosa no sustituye una prueba de aceptación del usuario en su infraestructura.

Antes de producción se debe validar, como mínimo:

- CompanyDB correcta;
- ambiente TEST/PROD;
- moneda y fecha;
- tasa de compra/venta según la política contable aplicable;
- fuente bancaria seleccionada;
- consenso y detección de outliers;
- permisos del usuario SAP;
- TLS/certificado del Service Layer;
- backup y procedimiento de reversión;
- GET de verificación posterior a la escritura.

## No asesoría profesional

Atas es una herramienta técnica. No presta asesoría legal, contable, fiscal, bancaria, financiera ni de inversión. La empresa operadora conserva la responsabilidad sobre sus controles, autorizaciones y cumplimiento normativo.

## Terceros

Bancos, APIs, sitios web, SAP, Python, GitHub y demás proveedores o componentes de terceros son independientes. Su disponibilidad, precisión, licencias, términos y políticas pueden cambiar sin intervención del autor de Atas.

## Alcance de las exclusiones

Toda exclusión de garantía o limitación de responsabilidad se aplica únicamente hasta donde lo permita la ley aplicable. Ningún archivo del proyecto pretende excluir obligaciones o responsabilidades que legalmente no puedan excluirse.
