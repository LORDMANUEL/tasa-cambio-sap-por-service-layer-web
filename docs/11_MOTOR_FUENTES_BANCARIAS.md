# Motor de fuentes bancarias V5

## Objetivo

Permitir que una instalación en cualquier país configure sus propios bancos o proveedores de tasa sin modificar Python.

## Tipos de fuente

### PRESET
Conector Python incluido y probado. Banpaís y Ficohsa se conservan como ejemplos/presets históricos.

### WEB_HTML
Descarga HTML público y extrae tasas mediante:

- `AUTO`: heurística moneda + compra/venta.
- `CSS`: selectores configurados.
- `REGEX`: patrón configurado.

### API_JSON
Descarga JSON y extrae mediante:

- `AUTO`: detección por nombres de paths.
- `MAPPING`: rutas exactas.

## Flujo de escaneo

1. Usuario ingresa tipo, URL y configuración.
2. `Escanear sin guardar` realiza GET.
3. Se valida HTTP, tamaño y formato.
4. Se extraen tasas.
5. Se normalizan a `Decimal`.
6. Se presenta compra/venta por moneda.
7. Sólo después se guarda/usa la fuente.

## Consenso

Para cada CompanyDB:

1. deben existir 3 o más fuentes configuradas;
2. la fuente oficial debe responder;
3. cada moneda necesita 3 o más valores `sell`;
4. se calcula la mediana;
5. se mide la desviación de la fuente oficial;
6. se detectan outliers;
7. si existe warning, se bloquea escritura SAP.

La mediana es control, no la tasa aplicada. SAP recibe el `sell` de la fuente oficial si el consenso es seguro.

## Secretos API

Headers secretos como `Authorization` o `X-API-Key` se guardan cifrados. Los headers no sensibles pueden permanecer en JSON normal.
