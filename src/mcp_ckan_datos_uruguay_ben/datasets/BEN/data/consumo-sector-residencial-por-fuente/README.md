# BEN - Consumo sector residencial por fuente

**Página del dataset:** https://catalogodatos.gub.uy/dataset/ministerio-industra-energia-mineria-ben-consumo-sector-residencial-por-fuente
**CSV directo:** https://catalogodatos.gub.uy/dataset/f36babe7-c21e-4ad5-b94e-f525ed393fbe/resource/a7318ff7-16da-498b-a475-a810e7ace162/download/consumo-sector-residencial-por-fuente.csv
**Archivo local:** `consumo-sector-residencial-por-fuente.csv` · **Metadata:** `metadatos_consumo-sector-residencial-por-fuente.json`
**Encoding:** UTF-8 · **Separador:** `,` · **Decimal:** `,` · **Cobertura:** 1965-2024 (anual, 60 años) · **Filas de datos:** 60

```python
import pandas as pd
URL = "https://catalogodatos.gub.uy/dataset/f36babe7-c21e-4ad5-b94e-f525ed393fbe/resource/a7318ff7-16da-498b-a475-a810e7ace162/download/consumo-sector-residencial-por-fuente.csv"
df = pd.read_csv(URL, decimal=",", encoding="utf-8")
```

## Descripción
Energía consumida por el **sector residencial** (hogares), abierta por la
fuente energética. Es una desagregación del renglón residencial (`R`) de
`miem-consumo-final-energetico-por-sector`, repartido entre las fuentes que
abastecen al hogar (leña, electricidad, supergás, etc.).

## Diccionario de columnas
| Columna | Unidad | Descripción |
|---|---|---|
| `AÑO` | año | Año del registro |
| `GN` | ktep | Gas natural |
| `S` | ktep | Solar térmica |
| `L` | ktep | Leña |
| `RB` | ktep | Residuos de biomasa (en residencial: pellets, briquetas de madera, aserrín, etc.) |
| `GLP` | ktep | Gas licuado de petróleo (supergás y propano) |
| `Ga` | ktep | Gasolina automotora |
| `Q` | ktep | Queroseno |
| `Do` | ktep | Diéseloil |
| `Go` | ktep | Gasoil |
| `Fo` | ktep | Fueloil |
| `GM` | ktep | Gas manufacturado |
| `Be` | ktep | Bioetanol |
| `Bd` | ktep | Biodiésel |
| `CV` | ktep | Carbón vegetal |
| `EE` | ktep | Energía eléctrica |
| `TOTAL` | ktep | Consumo final energético total del sector residencial |

Una celda vacía significa que no hay dato (la fuente no se consumía en el
residencial ese año). Los valores usan **coma decimal** (`296,5` = 296.5).

## Head (primeras 10 líneas)
```
AÑO,GN,S,L,RB,GLP,Ga,Q,Do,Go,Fo,GM,Be,Bd,CV,EE,TOTAL
1965,,,"296,5",,"20,1",,"150,2",,"13,5","8,9","9,5",,,,"53,1","551,8"
1966,,,"297,9",,"22,1",,"151,8",,"6,6","9,3",9,,,,"57,2","553,9"
1967,,,"299,4",,"23,5",,"145,1",,"7,8","10,4","8,8",,,,"62,7","557,7"
1968,,,"300,9",,"24,3",,"144,8",,"6,7","12,1","8,2",,,,62,559
1969,,,"302,4",,"29,9",,"159,3",,"7,4","10,4","8,2",,,,"67,1","584,7"
1970,,,"303,8",,"34,6",,"166,9",,"6,1","9,2","8,1",,,,"71,7","600,4"
1971,,,"305,3",,"39,7",,"187,7",,"9,2","9,2","8,2",,,,"77,9","637,2"
1972,,,"306,7",,"41,4",,192,,"8,4",5,"8,1",,,,"73,2","634,8"
1973,,,"308,2",,"37,7",,"185,1",,"10,9","10,8",8,,,,"74,9","635,6"
```
2024: TOTAL = 864.1 ktep. Top fuentes: electricidad 428.5, leña 283.5,
supergás (GLP) 106.0, gas natural 19.4, residuos de biomasa 7.6, solar 6.6.

## Preguntas que ayuda a responder
- **Matriz energética del hogar** - peso de cada fuente en el consumo
  residencial y su evolución (la leña pasó de dominante a ser superada por
  la electricidad).
- **Electrificación** - participación de `EE`: `EE / TOTAL` = 49.6% en 2024.
- **Renovables directas del hogar** = `(S + L + RB + CV + Be + Bd) / TOTAL`
  = 302.6 / 864.1 ≈ 35% en 2024 (leña es el grueso). OJO: esto NO es el
  "% renovable del consumo" oficial, es sólo el componente que se ve en este
  dataset (no incluye la electricidad).
- **% renovable oficial del hogar (criterio Indicador ODS 7.2.1)** - el BEN
  define la "Proporción de la energía renovable en el consumo final total de
  energía" contando **además la parte renovable de la electricidad**. Este
  dataset reporta la electricidad como una sola columna (`EE`) sin desglosar
  qué fracción es renovable, así que el indicador NO se calcula con este CSV
  solo: hay que cruzarlo con la matriz de generación del SIN
  (`miem-generacion-de-electricidad-por-fuente`, desde 2002) para repartir
  `EE` en renovable/fósil. Con ese cruce:
  `(S + L + RB + CV + Be + Bd + EE * %renov_SIN) / TOTAL` ≈ **84% en 2024**
  (SIN 98.9% renovable). El 64% que publica el BEN es el indicador **nacional**
  (todos los sectores), no el residencial; ese 64% también se reproduce
  cruzando `consumo-final-energetico-por-fuente` con el SIN (da 63.7% en 2024,
  >50% en 2013, ~60% promedio de la última década, igual que el libro).
  Tools: `renovables_residencial_uy` (serie) y
  `renovable_residencial_calculo_uy` (cálculo paso a paso de un año).
- **Sustitución de fuentes fósiles** - caída del queroseno (`Q`) y avance
  del supergás (`GLP`) y la electricidad a lo largo de las décadas.

## Notas
- El `TOTAL` coincide con la columna `R` (residencial) de
  `miem-consumo-final-energetico-por-sector` (cross-check: 2024 ambos =
  864.1) - es la misma magnitud desagregada por fuente en vez de por sector.
- A diferencia de los demás datasets BEN (ISO-8859-1, separador `;`), este
  CSV viene en **UTF-8 con separador `,` y coma decimal**; usar
  `decimal=","` al leerlo.
