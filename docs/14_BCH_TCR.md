# BCH como fuente de referencia

Atas soporta el **Banco Central de Honduras (BCH)** como preset automático para USD.

## Fuente

Se consume el XLSX oficial anual **Resultados Diarios del Tipo de Cambio de Referencia (TCR)** publicado por BCH.

La estructura validada es:

- hoja: `Datos`;
- columna A: `Fecha`;
- columna B: `TCR`.

El proveedor selecciona la observación más reciente cuya fecha no sea posterior a la fecha local de Atas.

## Semántica

BCH publica un **TCR**, no una cotización comercial separada de compra y venta. Por eso Atas representa internamente esa referencia como:

```
USD.buy  = TCR
USD.sell = TCR
```

Esto se hace exclusivamente para que BCH participe en la mediana y detección de outliers.

**BCH no debe configurarse como fuente oficial comercial para decidir la tasa que se escribe en SAP** salvo una decisión contable explícita de la empresa.

## Monedas

El preset BCH aporta solamente USD. No inventa EUR.

Si una CompanyDB procesa EUR, debe disponer de al menos tres fuentes reales que publiquen EUR para que el consenso de EUR sea seguro.

## Frescura

Se permite una antigüedad máxima de 10 días para soportar fines de semana y periodos de vigencia/feriados. Si la última observación supera ese umbral, la fuente falla cerrada como desactualizada.
