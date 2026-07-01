"""
Tools BEN - Consumo del SECTOR TRANSPORTE por fuente.

Dataset MIEM `ben-consumo-sector-transporte-por-fuente` (ktep, 1965-2024).
Es la desagregacion por fuente del renglon transporte (`T`) del dataset
`miem-consumo-final-energetico-por-sector`: el TOTAL de aqui coincide con esa
columna T anio a anio (cross-check 2024 = 1492.6 ktep en ambos).

El transporte es el sector mas fosil de la matriz: gasoil y gasolina
automotora explican casi todo el consumo. Las unicas fuentes renovables son
los biocombustibles (bioetanol y biodiesel, que entraron en 2010 mezclados en
naftas y gasoil) y, de forma incipiente, la electricidad (movilidad
electrica). Por eso es el sector mas dificil de descarbonizar.

Tools expuestas (todas con glosario de columnas incrustado para la IA):
  - consumo_transporte_por_fuente : mix por fuente + % renovable directo.
  - tendencia_consumo_transporte  : evolucion del consumo TOTAL del sector.
  - participacion_fuentes_transporte : participacion (%) de cada fuente y la
                                       entrada de los biocombustibles (2010).
  - fuente_transporte_detalle     : serie de UNA fuente (drill-down experto).
  - renovables_transporte         : % renovable del consumo segun el
                                     Indicador ODS 7.2.1 (cuenta la
                                     electricidad renovable; 2002-2024).
  - renovable_transporte_calculo  : el mismo % renovable para UN anio, con el
                                     calculo paso a paso desde los dos datasets.
"""

import pandas as pd

from mcp_server import DataToolOutput
from . import helpers as h


# ═══ Fuentes del consumo del transporte ════════════════════════════════════
# (columna CSV, etiqueta legible). Ordenadas por peso en el ultimo anio; las
# fuentes residuales / historicas quedan al final.
FUENTES_TRANSP = [
    ("Go",  "Gasoil"),
    ("Ga",  "Gasolina automotora"),
    ("Be",  "Bioetanol"),
    ("EE",  "Electricidad"),
    ("T",   "Turbocombustible"),
    ("GAv", "Gasolina aviación"),
    ("Bd",  "Biodiésel"),
    ("Fo",  "Fueloil"),
    ("Do",  "Diéseloil"),
    ("Q",   "Queroseno"),
]

# Renovables del transporte: solo los biocombustibles. No hay leña, biomasa
# ni solar en este sector. La electricidad NO se cuenta como renovable aqui
# (su mix varia ano a ano; para el criterio oficial que la cuenta ver
# `renovables_transporte`, que la reparte con el mix del SIN).
RENOVABLES_TRANSP = {"Bioetanol", "Biodiésel"}

# Glosario de columnas: se incrusta en TODAS las respuestas para que la IA
# nunca tenga que adivinar que significa cada codigo de fuente.
GLOSARIO_COLS = (
    "Significado de las columnas (todas en ktep, sector transporte; una "
    "celda vacía = la fuente no tuvo consumo registrado ese año):\n"
    "  - Go  = gasoil\n"
    "  - Ga  = gasolina automotora\n"
    "  - Be  = bioetanol (biocombustible que se mezcla en las gasolinas)\n"
    "  - Bd  = biodiésel (biocombustible que se mezcla en el gasoil)\n"
    "  - EE  = electricidad (movilidad eléctrica)\n"
    "  - T   = turbocombustible (combustible de aviación tipo queroseno)\n"
    "  - GAv = gasolina de aviación\n"
    "  - Fo  = fueloil (sobre todo transporte marítimo/fluvial)\n"
    "  - Do  = diéseloil\n"
    "  - Q   = queroseno\n"
    "  - TOTAL = consumo final energético total del sector transporte"
)

_TITULO = "Consumo de energía del sector transporte"


def _pct_renov_row(row):
    """% renovable DIRECTO de una fila: solo biocombustibles (bioetanol +
    biodiésel), SIN contar la electricidad (no es el % oficial 7.2.1; para ese,
    que cuenta la electricidad renovable, ver `renovables_transporte`)."""
    p = h.pct_renovable(row, FUENTES_TRANSP, RENOVABLES_TRANSP)
    return f"{p:.1f}%" if p is not None else "-"


# ═══ 1. Mix del transporte por fuente ══════════════════════════════════════

def consumo_transporte_por_fuente(anio_desde=None, anio_hasta=None) -> DataToolOutput:
    """Consumo del sector transporte abierto por fuente, en ktep."""
    df = h.load_dataset("consumo_transporte")
    df = h.filter_years(df, anio_desde, anio_hasta)
    src = [h.DATASET_PAGES["consumo_transporte"]]
    if df.empty:
        return h.empty_result("de consumo del transporte por fuente en ese rango", src)

    ult = df.iloc[-1]
    anio_ult = int(ult["anio"])
    rango = h.rango(df)
    pct_dir = h.pct_renovable(ult, FUENTES_TRANSP, RENOVABLES_TRANSP)

    lines = [
        f"{_TITULO} por fuente, {rango} (ktep).",
        "",
        f"Mix del transporte {anio_ult}: TOTAL = {h.fmt_num(ult['TOTAL'], 1)} ktep; "
        f"renovables directas (biocombustibles) = {pct_dir:.1f}% "
        "(el valor de cada fuente, año por año, está en la tabla de abajo).",
        "",
        "La columna '% Renov. directa' suma sólo los biocombustibles (bioetanol "
        "y biodiésel); NO incluye la electricidad. No es el % renovable oficial "
        "del consumo: el BEN (Indicador ODS 7.2.1) cuenta además la parte "
        "renovable de la electricidad. Para esa cifra usar `renovables_transporte_uy`.",
        "",
        GLOSARIO_COLS,
        "",
        h.ALREADY_TABLE,
        h.ALREADY_CHART,
        "El TOTAL coincide con la columna 'Transporte' de "
        "`consumo_energetico_por_sector_uy` (misma magnitud, otra apertura).",
        h.definiciones_relevantes(
            "ktep", "energia_final", "sector_de_consumo",
        ),
        "",
        h.SOURCE_FOOTER,
    ]

    table = h.build_table(
        df, FUENTES_TRANSP, extra_cols=[("% Renov. directa", _pct_renov_row)],
    )
    chart = h.chart_for_mix(
        df, FUENTES_TRANSP,
        f"Consumo del transporte por fuente ({rango}), ktep",
        palette=h.COLORES_BEN,
    )
    return h.text_result("\n".join(lines), src, table=table, charts=[chart])


# ═══ 2. Tendencia del consumo total del transporte ═════════════════════════

def tendencia_consumo_transporte(anio_desde=None, anio_hasta=None) -> DataToolOutput:
    """Evolución del consumo energético TOTAL del sector transporte, ktep/año."""
    df = h.load_dataset("consumo_transporte")
    df = h.filter_years(df, anio_desde, anio_hasta)
    src = [h.DATASET_PAGES["consumo_transporte"]]
    if df.empty:
        return h.empty_result("de consumo del transporte total en ese rango", src)

    rango = h.rango(df)
    ult = df.iloc[-1]
    prim = df.iloc[0]
    n = int(ult["anio"]) - int(prim["anio"])

    lines = [
        f"{_TITULO} - TOTAL del país, {rango} (ktep/año).",
        "",
        f"  - {int(ult['anio'])}: {h.fmt_num(ult['TOTAL'], 1)} ktep "
        f"(~ {float(ult['TOTAL']) * 11.63 / 1000:.1f} TWh equivalentes).",
    ]
    g = h.cagr(prim["TOTAL"], ult["TOTAL"], n)
    if g is not None:
        delta_pct = (float(ult["TOTAL"]) / float(prim["TOTAL"]) - 1) * 100
        lines.append(f"  - {int(prim['anio'])}: {h.fmt_num(prim['TOTAL'], 1)} ktep.")
        lines.append(
            f"  - Variación {int(prim['anio'])}->{int(ult['anio'])}: "
            f"{delta_pct:+.1f}% total ({g:+.2f}% / año compuesto)."
        )
        ult_n = df.tail(min(6, len(df)))
        if len(ult_n) >= 2:
            x0 = float(ult_n.iloc[0]["TOTAL"])
            x1 = float(ult_n.iloc[-1]["TOTAL"])
            tendencia = (
                "creciendo" if x1 > x0
                else "contrayéndose" if x1 < x0 else "estable"
            )
            lines.append(
                f"  - Últimos {len(ult_n)} años: {tendencia} "
                f"({(x1 / x0 - 1) * 100:+.1f}% en el período)."
            )

    lines.append("")
    lines.append(GLOSARIO_COLS)
    lines.append("")
    lines.append(h.ALREADY_TABLE)
    lines.append(h.ALREADY_CHART)
    lines.append(
        "Recordar: BEN no incluye parque automotor ni población. Para "
        "'consumo por vehículo' o per cápita hay que cruzar con otras fuentes."
    )
    lines.append(h.definiciones_relevantes("ktep", "energia_final", "sector_de_consumo"))
    lines.append("")
    lines.append(h.SOURCE_FOOTER)

    table = [["Año", "Consumo transporte (ktep)"]]
    for _, row in df.iterrows():
        table.append([str(int(row["anio"])), h.fmt_num(row["TOTAL"], 1)])

    chart = h.line_chart(
        f"Consumo energético del sector transporte ({rango}), ktep",
        df["anio"].tolist(),
        [("Consumo transporte", df["TOTAL"].tolist())],
        palette=h.COLORES_BEN,
    )
    return h.text_result("\n".join(lines), src, table=table, charts=[chart])


# ═══ 3. Participación (%) de cada fuente en el tiempo ══════════════════════

# Fuentes cuya participacion seguimos en el tiempo (las relevantes del sector).
_FUENTES_SHARE = [
    ("Go",  "Gasoil"),
    ("Ga",  "Gasolina automotora"),
    ("Be",  "Bioetanol"),
    ("Bd",  "Biodiésel"),
    ("T",   "Turbocombustible"),
    ("GAv", "Gasolina aviación"),
]


def participacion_fuentes_transporte(anio_desde=None, anio_hasta=None) -> DataToolOutput:
    """Participación (%) de cada fuente en el consumo del transporte a lo largo
    del tiempo, con foco en la entrada de los biocombustibles (2010)."""
    df = h.load_dataset("consumo_transporte")
    df = h.filter_years(df, anio_desde, anio_hasta)
    src = [h.DATASET_PAGES["consumo_transporte"]]
    if df.empty:
        return h.empty_result("de consumo del transporte en ese rango", src)

    rango = h.rango(df)

    shares = {}
    for col, label in _FUENTES_SHARE:
        serie = []
        for _, row in df.iterrows():
            total = float(row["TOTAL"]) if pd.notna(row["TOTAL"]) else 0.0
            v = float(row[col]) if pd.notna(row[col]) else 0.0
            serie.append(round(v / total * 100, 2) if total else 0.0)
        shares[label] = serie

    ult = df.iloc[-1]
    total_ult = float(ult["TOTAL"]) if pd.notna(ult["TOTAL"]) else 0.0

    lines = [
        f"{_TITULO}: participación (%) de cada fuente, {rango}.",
        "",
        f"Composición {int(ult['anio'])}: TOTAL = {h.fmt_num(total_ult, 1)} ktep "
        "(la participación de cada fuente, año por año, está en la tabla).",
    ]

    # Participacion de los biocombustibles (bioetanol + biodiesel) en el ultimo
    # ano del rango y primer ano en que aparecen dentro del rango.
    bio_share = [
        round(shares["Bioetanol"][i] + shares["Biodiésel"][i], 2)
        for i in range(len(df))
    ]
    primer_bio = next(
        (int(df.iloc[i]["anio"]) for i in range(len(df)) if bio_share[i] > 0),
        None,
    )
    lines.append("")
    if primer_bio is not None:
        lines.append(
            f"  -> Biocombustibles (bioetanol + biodiésel): "
            f"{bio_share[-1]:.1f}% del transporte en {int(ult['anio'])}; "
            f"primer año con presencia en el rango: {primer_bio} "
            "(entraron a nivel nacional en 2010)."
        )
    else:
        lines.append(
            "  -> Sin biocombustibles en el rango (entraron a nivel nacional en 2010)."
        )

    # Cruce gasoil <-> gasolina automotora.
    cruce = None
    for i in range(len(df)):
        if shares["Gasoil"][i] > shares["Gasolina automotora"][i]:
            cruce = int(df.iloc[i]["anio"])
            break
    if cruce is not None and int(df.iloc[0]["anio"]) < cruce:
        lines.append(
            f"  -> El gasoil superó a la gasolina automotora como principal "
            f"fuente del transporte en {cruce}."
        )

    lines.append("")
    lines.append(GLOSARIO_COLS)
    lines.append("")
    lines.append(h.ALREADY_TABLE)
    lines.append(h.ALREADY_CHART)
    lines.append(
        "Los valores del gráfico y la tabla son participaciones (% del total "
        "del año), no ktep. Para los valores absolutos usar "
        "`consumo_transporte_por_fuente`."
    )
    lines.append(h.definiciones_relevantes("energia_final", "sector_de_consumo"))
    lines.append("")
    lines.append(h.SOURCE_FOOTER)

    headers = ["Año"] + [label for _, label in _FUENTES_SHARE]
    table = [headers]
    for i, (_, row) in enumerate(df.iterrows()):
        line = [str(int(row["anio"]))]
        for _, label in _FUENTES_SHARE:
            line.append(f"{shares[label][i]:.1f}%")
        table.append(line)

    chart = h.line_chart(
        f"Participación de cada fuente en el transporte ({rango}), %",
        df["anio"].tolist(),
        [(label, shares[label]) for _, label in _FUENTES_SHARE],
        palette=h.COLORES_BEN,
    )
    return h.text_result("\n".join(lines), src, table=table, charts=[chart])


# ═══ 4. Drill-down: una sola fuente ═══════════════════════════════════════

# Tokens aceptados -> (columna, etiqueta). Acepta el codigo (Go, Ga, Be...) y
# algunos sinonimos frecuentes, sin distincion de mayusculas/acentos.
_FUENTE_LOOKUP = {}
for _col, _label in FUENTES_TRANSP:
    _FUENTE_LOOKUP[_col.lower()] = (_col, _label)
    _FUENTE_LOOKUP[_label.lower()] = (_col, _label)
_FUENTE_LOOKUP.update({
    "gasolina": ("Ga", "Gasolina automotora"),
    "nafta": ("Ga", "Gasolina automotora"),
    "diesel": ("Do", "Diéseloil"),
    "dieseloil": ("Do", "Diéseloil"),
    "biodiesel": ("Bd", "Biodiésel"),
    "turbo": ("T", "Turbocombustible"),
    "jet": ("T", "Turbocombustible"),
    "electricidad": ("EE", "Electricidad"),
})
_FUENTES_VALIDAS = ", ".join(col for col, _ in FUENTES_TRANSP)


def fuente_transporte_detalle(fuente, anio_desde=None, anio_hasta=None) -> DataToolOutput:
    """Serie histórica de UNA fuente en el consumo del transporte, en ktep."""
    src = [h.DATASET_PAGES["consumo_transporte"]]
    if not fuente:
        return h.empty_result(
            f"(falta el argumento 'fuente'; opciones: {_FUENTES_VALIDAS})", src
        )
    clave = _FUENTE_LOOKUP.get(str(fuente).strip().lower())
    if clave is None:
        return h.empty_result(
            f"para la fuente '{fuente}' (opciones válidas: {_FUENTES_VALIDAS})",
            src,
        )
    col, label = clave

    df = h.load_dataset("consumo_transporte")
    df = h.filter_years(df, anio_desde, anio_hasta)
    if df.empty:
        return h.empty_result(f"de {label} en el transporte en ese rango", src)

    rango = h.rango(df)
    con_dato = df[df[col].notna()]

    lines = [f"{_TITULO}: {label} ({col}), {rango} (ktep)."]
    if con_dato.empty:
        lines.append("")
        lines.append(f"No hay datos de {label} en el rango pedido.")
    else:
        prim = con_dato.iloc[0]
        ult = con_dato.iloc[-1]
        total_ult = float(ult["TOTAL"]) if pd.notna(ult["TOTAL"]) else 0.0
        share_ult = (float(ult[col]) / total_ult * 100) if total_ult else 0.0
        idx_max = con_dato[col].astype(float).idxmax()
        fila_max = con_dato.loc[idx_max]
        n = int(ult["anio"]) - int(prim["anio"])
        g = h.cagr(prim[col], ult[col], n)

        lines += [
            "",
            f"  - {int(ult['anio'])}: {h.fmt_num(ult[col], 1)} ktep "
            f"({share_ult:.1f}% del consumo del transporte ese año).",
            f"  - {int(prim['anio'])} (primer año con dato): "
            f"{h.fmt_num(prim[col], 1)} ktep.",
            f"  - Máximo histórico: {h.fmt_num(fila_max[col], 1)} ktep "
            f"en {int(fila_max['anio'])}.",
        ]
        if g is not None:
            lines.append(
                f"  - Crecimiento {int(prim['anio'])}->{int(ult['anio'])}: "
                f"{g:+.2f}% / año compuesto."
            )

    lines.append("")
    lines.append(GLOSARIO_COLS)
    lines.append("")
    lines.append(h.ALREADY_TABLE)
    lines.append(h.ALREADY_CHART)
    lines.append(h.definiciones_relevantes("ktep", "energia_final", "sector_de_consumo"))
    lines.append("")
    lines.append(h.SOURCE_FOOTER)

    table = [["Año", f"{label} (ktep)", "% del transporte"]]
    for _, row in df.iterrows():
        total = float(row["TOTAL"]) if pd.notna(row["TOTAL"]) else 0.0
        v = row[col]
        pct = (float(v) / total * 100) if (total and pd.notna(v)) else None
        table.append([
            str(int(row["anio"])),
            h.fmt_num(v, 1),
            f"{pct:.1f}%" if pct is not None else "-",
        ])

    chart = h.line_chart(
        f"{label} en el consumo del transporte ({rango}), ktep",
        df["anio"].tolist(),
        [(label, df[col].tolist())],
        palette=h.COLORES_BEN,
    )
    return h.text_result("\n".join(lines), src, table=table, charts=[chart])


# ═══ 5. Renovables del transporte (Indicador ODS 7.2.1) ════════════════════
# El BEN define el % renovable del consumo final (Indicador ODS 7.2.1)
# contando la fraccion renovable de la electricidad. En el transporte las
# renovables directas son los biocombustibles (Be + Bd); a eso se le suma la
# electricidad renovable, repartiendo la electricidad del sector segun el mix
# de generacion del SIN de cada ano. Ese mix solo existe desde 2002, asi que
# el indicador se reporta a partir de ese ano (los biocombustibles, ademas,
# entraron en 2010).

def renovables_transporte(anio_desde=None, anio_hasta=None) -> DataToolOutput:
    """% renovable del consumo del transporte según el criterio del Indicador
    ODS 7.2.1 del BEN (cuenta la electricidad renovable). Cobertura 2002-2024."""
    src = [h.DATASET_PAGES["consumo_transporte"], h.DATASET_PAGES["generacion"]]

    desde = (
        max(int(anio_desde), h.PRIMER_ANIO_MIX_SIN)
        if anio_desde is not None else h.PRIMER_ANIO_MIX_SIN
    )
    df = h.load_dataset("consumo_transporte")
    df = h.filter_years(df, desde, anio_hasta)
    if df.empty:
        return h.empty_result(
            "de renovables en el consumo del transporte en ese rango (el "
            "Indicador 7.2.1 requiere el mix del SIN, disponible desde 2002)",
            src,
        )

    share_sin = h.share_renovable_sin()
    renov_cols = [col for col, et in FUENTES_TRANSP if et in RENOVABLES_TRANSP]
    rango = h.rango(df)

    anios, s_dir, s_ee_ren, s_norenov, s_pct = [], [], [], [], []
    for _, row in df.iterrows():
        y = int(row["anio"])
        sh = share_sin.get(y)
        if sh is None:
            continue
        total = float(row["TOTAL"]) if pd.notna(row["TOTAL"]) else 0.0
        directas = sum(float(row[c]) for c in renov_cols if pd.notna(row[c]))
        ee = float(row["EE"]) if pd.notna(row["EE"]) else 0.0
        ee_ren = ee * sh
        renov_total = directas + ee_ren
        no_renov = max(total - renov_total, 0.0)
        anios.append(y)
        s_dir.append(round(directas, 1))
        s_ee_ren.append(round(ee_ren, 1))
        s_norenov.append(round(no_renov, 1))
        s_pct.append(round(renov_total / total * 100, 1) if total else 0.0)

    if not anios:
        return h.empty_result(
            "de renovables en el consumo del transporte en ese rango (sin "
            "datos de mix del SIN para esos años)",
            src,
        )

    i = -1
    total_u = s_dir[i] + s_ee_ren[i] + s_norenov[i]
    sh_u = share_sin.get(anios[i])

    lines = [
        f"{_TITULO}: % renovable (criterio Indicador ODS 7.2.1), "
        f"{rango} (ktep).",
        "",
        f"Año {anios[i]}: % renovable = **{s_pct[i]:.1f}%** del consumo del "
        f"transporte (TOTAL {h.fmt_num(total_u, 1)} ktep; los biocombustibles "
        f"aportan {h.fmt_num(s_dir[i], 1)} ktep y la electricidad renovable "
        f"{h.fmt_num(s_ee_ren[i], 1)} ktep, calculada con el {sh_u * 100:.1f}% "
        "renovable del SIN ese año). El desglose anual está en la tabla.",
        "",
        "El transporte es el sector más fósil: aun contando biocombustibles y "
        "electricidad renovable, el % renovable es bajo (es el gran desafío de "
        "descarbonización). La electricidad renovable se estima repartiendo la "
        "electricidad del sector según el mix de generación del SIN de cada año "
        "(`matriz_generacion_electrica_uy`), disponible desde 2002. El 64% que "
        "publica el BEN para 2024 es el indicador NACIONAL (todos los "
        "sectores), no el del transporte.",
        "",
        GLOSARIO_COLS,
        "",
        h.ALREADY_TABLE,
        h.ALREADY_CHART,
        h.definiciones_relevantes(
            "renovable_consumo_final", "ktep", "energia_final",
            "sector_de_consumo",
        ),
        "",
        h.SOURCE_FOOTER,
    ]

    table = [["Año", "Biocombustibles (ktep)", "Electricidad renovable (ktep)",
              "No renovable (ktep)", "Total (ktep)", "% Renovable (7.2.1)"]]
    for j, y in enumerate(anios):
        total = s_dir[j] + s_ee_ren[j] + s_norenov[j]
        table.append([
            str(y),
            h.fmt_num(s_dir[j], 1),
            h.fmt_num(s_ee_ren[j], 1),
            h.fmt_num(s_norenov[j], 1),
            h.fmt_num(total, 1),
            f"{s_pct[j]:.1f}%",
        ])

    chart = h.stacked_bar_chart(
        f"Transporte renovable vs no renovable - criterio 7.2.1 ({rango}), ktep",
        anios,
        [
            ("Renovable", [round(s_dir[j] + s_ee_ren[j], 1) for j in range(len(anios))]),
            ("No renovable", s_norenov),
        ],
        palette=h.COLORES_BEN,
    )
    return h.text_result("\n".join(lines), src, table=table, charts=[chart])


# ═══ 6. Cálculo auditable del % renovable de UN año ═══════════════════════

def renovable_transporte_calculo(anio=None) -> DataToolOutput:
    """% renovable del consumo del transporte para UN año, mostrando el cálculo
    paso a paso a partir de los dos datasets que lo alimentan."""
    src = [h.DATASET_PAGES["consumo_transporte"], h.DATASET_PAGES["generacion"]]
    df = h.load_dataset("consumo_transporte")

    if anio is None:
        anio = int(df["anio"].max())
    else:
        anio = int(anio)
    fila = df[df["anio"] == anio]
    if fila.empty:
        return h.empty_result(
            f"para el año {anio} en el consumo del transporte "
            f"(rango disponible: {int(df['anio'].min())}-{int(df['anio'].max())})",
            src,
        )
    row = fila.iloc[0]

    total = float(row["TOTAL"]) if pd.notna(row["TOTAL"]) else 0.0
    ee = float(row["EE"]) if pd.notna(row["EE"]) else 0.0
    directas_det = [
        (et, float(row[col]))
        for col, et in FUENTES_TRANSP
        if et in RENOVABLES_TRANSP and pd.notna(row[col]) and float(row[col]) > 0
    ]
    directas = sum(v for _, v in directas_det)
    sin = h.sin_detalle(anio)

    enc = (
        f"{_TITULO}: cálculo del % renovable del transporte - año {anio}.\n\n"
        "Fórmula (criterio Indicador ODS 7.2.1 del BEN):\n"
        "  % renovable = (biocombustibles + electricidad renovable) / consumo total\n"
        "  electricidad renovable = electricidad del transporte x fracción renovable del SIN\n"
    )

    p1 = [
        "",
        "Paso 1 - Biocombustibles del transporte "
        "(dataset: consumo transporte por fuente):",
    ]
    if directas_det:
        for et, v in directas_det:
            p1.append(f"    {et:<22}: {h.fmt_num(v, 1):>8} ktep")
    else:
        p1.append("    (sin biocombustibles ese año; entraron a nivel nacional en 2010)")
    p1.append(f"    {'SUMA biocombustibles':<22}: {h.fmt_num(directas, 1):>8} ktep")

    if sin is None:
        pct_dir = directas / total * 100 if total else 0.0
        lines = [
            enc,
            *p1,
            "",
            f"Paso 2 - Electricidad renovable: NO disponible para {anio}.",
            "    La matriz de generación del SIN (que da la fracción renovable "
            "de la electricidad) sólo existe desde 2002, así que el criterio "
            "oficial 7.2.1 no puede aplicarse a este año.",
            "",
            f"Sólo se puede informar el renovable DIRECTO (biocombustibles): "
            f"{h.fmt_num(directas, 1)} / {h.fmt_num(total, 1)} = "
            f"**{pct_dir:.1f}%** del consumo del transporte en {anio}.",
            "",
            GLOSARIO_COLS,
            "",
            h.ALREADY_TABLE,
            h.definiciones_relevantes(
                "renovable_consumo_final", "ktep", "energia_final",
                "sector_de_consumo",
            ),
            "",
            h.SOURCE_FOOTER,
        ]
        table = [["Componente", "ktep", "% del total"]]
        for et, v in directas_det:
            table.append([et, h.fmt_num(v, 1), f"{v / total * 100:.1f}%" if total else "-"])
        table.append(["Renovable directo (subtotal)", h.fmt_num(directas, 1),
                      f"{pct_dir:.1f}%"])
        table.append(["TOTAL consumo del transporte", h.fmt_num(total, 1), "100.0%"])
        return h.text_result("\n".join(lines), src, table=table)

    share, gwh_ren, gwh_tot = sin
    ee_ren = ee * share
    renov_total = directas + ee_ren
    no_renov = max(total - renov_total, 0.0)
    pct = renov_total / total * 100 if total else 0.0
    pct_dir = directas / total * 100 if total else 0.0

    lines = [
        enc,
        *p1,
        "",
        "Paso 2 - Fracción renovable de la electricidad del SIN "
        "(dataset: generación de electricidad por fuente):",
        f"    generación renovable (hidro+eólica+solar+biomasa): "
        f"{h.fmt_num(gwh_ren, 1)} GWh",
        f"    generación total: {h.fmt_num(gwh_tot, 1)} GWh",
        f"    fracción renovable del SIN = {h.fmt_num(gwh_ren, 1)} / "
        f"{h.fmt_num(gwh_tot, 1)} = {share * 100:.1f}%",
        "",
        "Paso 3 - Electricidad renovable consumida por el transporte:",
        f"    electricidad del transporte = {h.fmt_num(ee, 1)} ktep",
        f"    electricidad renovable = {h.fmt_num(ee, 1)} x {share * 100:.1f}% "
        f"= {h.fmt_num(ee_ren, 1)} ktep",
        "",
        "Paso 4 - Total renovable y porcentaje:",
        f"    renovable total = {h.fmt_num(directas, 1)} (biocombustibles) + "
        f"{h.fmt_num(ee_ren, 1)} (electricidad) = {h.fmt_num(renov_total, 1)} ktep",
        f"    consumo total del transporte = {h.fmt_num(total, 1)} ktep",
        f"    % renovable = {h.fmt_num(renov_total, 1)} / {h.fmt_num(total, 1)} "
        f"= **{pct:.1f}%**",
        "",
        f"Para comparar: contando SÓLO los biocombustibles (sin la "
        f"electricidad) el {anio} daría {pct_dir:.1f}%. La diferencia "
        f"({pct - pct_dir:+.1f} pp) es el aporte de la electricidad renovable "
        "(muy chico: la movilidad eléctrica es todavía marginal).",
        "",
        "Nota: el transporte es el sector más fósil de la matriz; este % "
        "renovable es bajo aun con el criterio oficial. Es el mismo criterio "
        "del indicador NACIONAL del BEN (64% en 2024, todos los sectores).",
        "",
        GLOSARIO_COLS,
        "",
        h.ALREADY_TABLE,
        h.ALREADY_CHART,
        h.definiciones_relevantes(
            "renovable_consumo_final", "ktep", "energia_final",
            "sector_de_consumo",
        ),
        "",
        h.SOURCE_FOOTER,
    ]

    table = [["Componente", "ktep", "% del total"]]
    for et, v in directas_det:
        table.append([et, h.fmt_num(v, 1), f"{v / total * 100:.1f}%"])
    table.append(["Biocombustibles (subtotal)", h.fmt_num(directas, 1),
                  f"{pct_dir:.1f}%"])
    table.append([f"Electricidad renovable (EE x {share * 100:.1f}%)",
                  h.fmt_num(ee_ren, 1), f"{ee_ren / total * 100:.1f}%"])
    table.append(["RENOVABLE TOTAL", h.fmt_num(renov_total, 1), f"{pct:.1f}%"])
    table.append(["No renovable", h.fmt_num(no_renov, 1),
                  f"{no_renov / total * 100:.1f}%"])
    table.append(["TOTAL consumo del transporte", h.fmt_num(total, 1), "100.0%"])

    chart = h.pie_chart(
        f"Transporte {anio}: renovable vs no renovable (criterio 7.2.1)",
        [
            ("Biocombustibles", round(directas, 1)),
            ("Electricidad renovable", round(ee_ren, 1)),
            ("No renovable", round(no_renov, 1)),
        ],
        palette=h.COLORES_BEN,
    )
    return h.text_result("\n".join(lines), src, table=table, charts=[chart])
