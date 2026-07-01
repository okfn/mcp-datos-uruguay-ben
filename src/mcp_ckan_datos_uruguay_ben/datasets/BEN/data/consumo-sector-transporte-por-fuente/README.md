# BEN - Consumo sector transporte por fuente

**Página del dataset:** https://catalogodatos.gub.uy/dataset/ministerio-de-industria-energia-y-mineria-ben-consumo-sector-transporte-por-fuente
**CSV directo:** https://catalogodatos.gub.uy/dataset/88219cac-31cb-4b62-a4b0-786d18072a9c/resource/1a4de650-9eb9-47e4-9339-df0da15adca0/download/consumo-sector-transporte-por-fuente.csv
**Archivo local:** `consumo-sector-transporte-por-fuente.csv` · **Metadata:** `metadatos_consumo-sector-transporte-por-fuente.json`
**Encoding:** UTF-8 · **Separador:** `,` · **Decimal:** `,` · **Cobertura:** 1965-2024 (anual, 60 años) · **Filas de datos:** 60

```python
import pandas as pd
URL = "https://catalogodatos.gub.uy/dataset/88219cac-31cb-4b62-a4b0-786d18072a9c/resource/1a4de650-9eb9-47e4-9339-df0da15adca0/download/consumo-sector-transporte-por-fuente.csv"
df = pd.read_csv(URL, decimal=",", encoding="utf-8")
```

## Descripción
Energía consumida por el **sector transporte** (terrestre, aéreo, marítimo/fluvial),
abierta por la fuente energética. Es una desagregación del renglón transporte
(`T`) de `miem-consumo-final-energetico-por-sector`, repartido entre los
combustibles que mueven al transporte. Es el sector más fósil de la matriz: el
gasoil y la gasolina automotora explican casi todo el consumo.

## Diccionario de columnas
| Columna | Unidad | Descripción |
|---|---|---|
| `AÑO` | año | Año del registro |
| `Ga` | ktep | Gasolina automotora |
| `GAv` | ktep | Gasolina de aviación |
| `Q` | ktep | Queroseno (histórico, hasta 1980) |
| `T` | ktep | Turbocombustible (jet fuel de aviación, desde 1981) |
| `Do` | ktep | Diéseloil |
| `Go` | ktep | Gasoil |
| `Fo` | ktep | Fueloil (sobre todo transporte marítimo/fluvial) |
| `Be` | ktep | Bioetanol (biocombustible, se mezcla en las gasolinas; desde 2010) |
| `Bd` | ktep | Biodiésel (biocombustible, se mezcla en el gasoil; desde 2010) |
| `EE` | ktep | Energía eléctrica (movilidad eléctrica) |
| `TOTAL` | ktep | Consumo final energético total del sector transporte |

Una celda vacía significa que no hay dato (la fuente no se consumía en el
transporte ese año). Los valores usan **coma decimal** (`260,5` = 260.5).

## Head (primeras 10 líneas)
```
AÑO,Ga,GAv,Q,T,Do,Go,Fo,Be,Bd,EE,TOTAL
1965,"260,5",,"3,4",,,"175,3","77,5",,,"2,1","518,8"
1966,"255,8",,"6,4",,,"174,7","75,4",,,"1,8","514,1"
1967,"256,4",,"7,6",,,"167,4","63,8",,,"2,2","497,4"
1968,"247,1",,"7,3",,,"179,2","51,1",,,"1,7","486,4"
1969,"266,4",,"7,7",,,"202,8","43,9",,,"1,5","522,3"
1970,"255,6",,"9,1",,,"234,5","51,1",,,"1,6","551,9"
1971,"264,2",,"7,8",,,246,"52,3",,,"2,1","572,4"
1972,"266,1",,"9,8",,,"286,6","49,8",,,"1,9","614,2"
1973,"241,9",,"7,8",,,"274,2","68,9",,,"1,9","594,7"
```
2024: TOTAL = 1492.6 ktep. Top fuentes: gasoil 791.9, gasolina automotora
648.1, bioetanol 45.5, electricidad 2.7, turbocombustible 2.4, gasolina de
aviación 2.0.

## Preguntas que ayuda a responder
- **Mix del transporte** - peso de cada combustible y su evolución (gasoil y
  gasolina dominan; el gasoil superó a la gasolina como principal fuente).
- **Entrada de biocombustibles** - el bioetanol y el biodiésel aparecen en
  2010; en 2024 suman ~3% del consumo del transporte.
- **Renovables directas del transporte** = `(Be + Bd) / TOTAL` = 45.5 / 1492.6
  ~ 3.0% en 2024 (solo biocombustibles). OJO: NO es el "% renovable del
  consumo" oficial; ese es el Indicador ODS 7.2.1, que cuenta ademas la parte
  renovable de la electricidad.
- **% renovable oficial del transporte (criterio Indicador ODS 7.2.1)** - el
  BEN cuenta tambien la electricidad renovable. Como este CSV reporta la
  electricidad como una sola columna (`EE`) sin desglosar que parte es
  renovable, el indicador NO se calcula con este CSV solo: hay que cruzarlo con
  la matriz de generacion del SIN
  (`miem-generacion-de-electricidad-por-fuente`, desde 2002). Con ese cruce:
  `(Be + Bd + EE * %renov_SIN) / TOTAL` ~ **3.2% en 2024** (la electricidad del
  transporte es minima). El transporte es el sector mas dificil de
  descarbonizar. Tools: `renovables_transporte_uy` (serie) y
  `renovable_transporte_calculo_uy` (calculo paso a paso de un anio).

## Notas
- El `TOTAL` coincide con la columna `T` (transporte) de
  `miem-consumo-final-energetico-por-sector` (cross-check: 2024 ambos =
  1492.6) - es la misma magnitud desagregada por fuente en vez de por sector.
- A diferencia de los demas datasets BEN (ISO-8859-1, separador `;`), este CSV
  viene en **UTF-8 con separador `,` y coma decimal**; usar `decimal=","` al
  leerlo.
- `Q` (queroseno) es historico de aviacion hasta 1979; a partir de 1980 se
  reemplaza por `T` (turbocombustible). `Do` (dieseloil) tambien es mayormente
  historico.
