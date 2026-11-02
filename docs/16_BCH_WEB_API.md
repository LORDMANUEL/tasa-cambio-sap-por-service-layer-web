# BCH Web-API oficial — integración Atas

Atas soporta dos rutas BCH:

1. `BCH`: XLSX oficial, sin credenciales, útil como fallback/referencia.
2. `BCH_API`: Web-API oficial del Banco Central de Honduras, con API key.

## Indicador

El portal de desarrolladores del BCH identifica:

- indicador: `97`;
- nombre: `EC-TCR-01`;
- descripción: Tipo de Cambio de Referencia;
- periodicidad: diaria;
- endpoint documentado: `GET /api/v1/indicadores/97/cifras`.

## Configuración en Atas

Tipo:

```text
BCH Web-API oficial
```

URL:

```text
https://bchapi-am.azure-api.net/api/v1/indicadores/97/cifras
```

Headers secretos API:

```json
{"clave":"SU_CLAVE_BCH"}
```

Atas cifra el JSON de headers secretos antes de persistirlo.

## Política

- BCH API se usa como referencia USD: `buy=sell=TCR` internamente para consenso.
- No reemplaza por defecto la cotización comercial de venta del banco oficial de la empresa.
- Se selecciona la observación más reciente no futura.
- Se rechazan datos con antigüedad superior al límite.
- Se valida el rango USD configurado.
- Se mantiene el XLSX BCH como alternativa sin API key.

## Alta de clave

La clave se obtiene registrándose y suscribiéndose en el portal Web-API del BCH.


## Regla de escritura

Las fuentes de respaldo pueden consultarse para diagnóstico y comparación. Si la fuente oficial configurada para la CompanyDB no responde, el consenso queda no seguro y Atas bloquea la escritura SAP. Esto evita sustituir silenciosamente la política financiera de la empresa.


## Autenticación

La clave se guarda cifrada dentro de los headers secretos de Atas usando:

```json
{"clave":"SU_CLAVE_BCH"}
```

Atas no envía `clave` como header: la extrae en memoria y la agrega únicamente como parámetro de la solicitud al gateway BCH. También admite `Ocp-Apim-Subscription-Key` cuando una suscripción del BCH utilice ese mecanismo.
