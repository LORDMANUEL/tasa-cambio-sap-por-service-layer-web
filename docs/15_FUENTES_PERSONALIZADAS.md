# Fuentes bancarias personalizadas

Atas no está limitado a los bancos incorporados. Una empresa puede agregar fuentes nuevas desde **Bancos y fuentes** sin modificar Python.

## Tipos soportados

### PRESET

Conector desarrollado dentro de Atas para una fuente conocida.

Ejemplo:

```json
{"preset":"BANPAIS"}
```

### WEB_HTML — AUTO

Atas descarga la página, elimina el marcado visual y busca la moneda junto con términos de compra/venta.

```json
{
  "mode": "AUTO",
  "currencies": ["USD"]
}
```

Es el modo más rápido para una página sencilla. Si el banco cambia el orden visual, use CSS o REGEX.

### WEB_HTML — CSS

Permite indicar selectores exactos:

```json
{
  "mode": "CSS",
  "currencies": ["USD"],
  "mapping": {
    "USD": {
      "buy": "#usd-buy",
      "sell": "#usd-sell"
    }
  }
}
```

Atas usa el atributo `content` cuando existe; de lo contrario usa el texto del nodo.

### WEB_HTML — REGEX

Útil cuando la página contiene datos en texto pero no dispone de selectores estables:

```json
{
  "mode": "REGEX",
  "currencies": ["USD"],
  "mapping": {
    "USD": {
      "regex": "USD.*?Compra:\\s*(?P<buy>[0-9.]+).*?Venta:\\s*(?P<sell>[0-9.]+)"
    }
  }
}
```

Puede usar grupos nombrados `buy` y `sell` o dos grupos posicionales.

### API_JSON — AUTO

Atas recorre el JSON y busca rutas asociadas a la moneda y palabras comunes como `buy`, `compra`, `sell`, `venta`, `bid` o `ask`.

```json
{
  "mode": "AUTO",
  "currencies": ["USD"]
}
```

### API_JSON — MAPPING

Para APIs estables es preferible mapear rutas explícitas:

```json
{
  "mode": "MAPPING",
  "currencies": ["USD"],
  "mapping": {
    "USD": {
      "buy": "fx.rates[0].purchase",
      "sell": "fx.rates[0].sale"
    }
  }
}
```

Las rutas admiten objetos y posiciones de listas.

## Headers y API keys

`headers_json` almacena headers no sensibles.

Los headers secretos se introducen en **Headers secretos / API key JSON** y se cifran con el mismo sistema de credenciales de Atas.

Ejemplo conceptual:

```json
{
  "Authorization": "Bearer <token>"
}
```

El valor real no debe escribirse en documentación, repositorio ni logs.

## TLS

Cada fuente puede validar TLS de forma independiente. Deshabilitar TLS debe reservarse para servicios internos/autofirmados que la organización haya validado previamente.

## Flujo recomendado al agregar un banco

1. crear la fuente;
2. seleccionar WEB_HTML o API_JSON;
3. colocar URL;
4. comenzar con AUTO;
5. usar **Escanear sin guardar**;
6. si AUTO no es estable, usar CSS/REGEX/MAPPING;
7. guardar;
8. confirmar que publica las monedas requeridas;
9. incluirla en una CompanyDB;
10. si será la tasa usada por SAP, marcarla como **Fuente oficial** en esa empresa.

La fuente oficial sigue pasando por consenso. Ser oficial no permite saltarse controles de rango, estructura, cantidad mínima de fuentes u outliers.
