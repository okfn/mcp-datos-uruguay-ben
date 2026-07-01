"""
Tools BEN - Consumo del SECTOR RESIDENCIAL (hogares) por fuente.

Dataset MIEM `ben-consumo-sector-residencial-por-fuente` (ktep, 1965-2024).
Es la desagregación por fuente del renglón residencial (`R`) del dataset
`miem-consumo-final-energetico-por-sector`: el TOTAL de aquí coincide con esa
columna R año a año.

A diferencia de `consumo_final_por_fuente` (que agrupa las fuentes en grandes
familias para todo el país), acá las fuentes vienen **abiertas una por una**
(leña, supergás, queroseno, gasoil, solar térmica, etc.), lo que permite
contar la historia energética del hogar uruguayo: el paso de la leña y el
queroseno a la electricidad y el supergás, y la entrada de la solar térmica.

Tools expuestas (todas con glosario de columnas incrustado para la IA):
  - consumo_residencial_por_fuente : mix por fuente del hogar + % renovable.
  - tendencia_consumo_residencial  : evolución del consumo TOTAL del hogar.
  - electrificacion_hogares        : participación (%) de cada fuente y el
                                     cruce histórico leña <-> electricidad.
  - fuente_residencial_detalle     : serie de UNA fuente (drill-down experto).
  - renovables_residencial         : % renovable del consumo del hogar según
                                     el Indicador ODS 7.2.1 (cuenta la
                                     electricidad renovable; 2002-2024).
  - renovable_residencial_calculo  : el mismo % renovable para UN año, con el
                                     cálculo paso a paso desde los dos datasets.
"""

import pandas as pd

from mcp_server import DataToolOutput
from . import helpers as h


# ═══ Fuentes del consumo residencial ══════════════════════════════════════
# (columna CSV, etiqueta legible). Ordenadas por peso en el último año para
# que el mix y los gráficos muestren primero lo relevante; las fuentes casi
# residuales / históricas quedan al final.
FUENTES_RESID = [
    ("EE",  "Electricidad"),
    ("L",   "Leña"),
    ("GLP", "Supergás (GLP)"),
    ("GN",  "Gas natural"),
    ("RB",  "Residuos de biomasa"),
    ("S",   "Solar térmica"),
    ("Go",  "Gasoil"),
    ("CV",  "Carbón vegetal"),
    ("Q",   "Queroseno"),
    ("Ga",  "Gasolina automotora"),
    ("Fo",  "Fueloil"),
    ("Be",  "Bioetanol"),
    ("Do",  "Diéseloil"),
    ("GM",  "Gas manufacturado"),
    ("Bd",  "Biodiésel"),
]

# Renovables del lado del hogar (criterio idéntico a `consumo.py`): leña,
# carbón vegetal, residuos de biomasa, solar térmica y biocombustibles.
# La electricidad NO se cuenta como renovable aquí (su mix es variable año a
# año; para su composición renovable usar `matriz_generacion_electrica_uy`).
RENOVABLES_RESID = {
    "Leña", "Carbón vegetal", "Residuos de biomasa",
    "Solar térmica", "Bioetanol", "Biodiésel",
}

# Glosario de columnas: se incrusta en TODAS las respuestas para que la IA
# nunca tenga que adivinar qué significa cada código de fuente.
GLOSARIO_COLS = (
    "Significado de las columnas (todas en ktep, sector residencial; una "
    "celda vacía = la fuente no tuvo consumo registrado ese año):\n"
    "  - EE  = electricidad\n"
    "  - L   = leña\n"
    "  - GLP = supergás y propano (gas licuado de petróleo)\n"
    "  - GN  = gas natural (por red)\n"
    "  - RB  = residuos de biomasa (en el hogar: pellets, briquetas y aserrín)\n"
    "  - S   = energía solar térmica (calentadores solares de agua)\n"
    "  - CV  = carbón vegetal\n"
    "  - Q   = queroseno\n"
    "  - Go  = gasoil\n"
    "  - Do  = diéseloil\n"
    "  - Fo  = fueloil\n"
    "  - Ga  = gasolina automotora\n"
    "  - GM  = gas manufacturado (histórico)\n"
    "  - Be  = bioetanol\n"
    "  - Bd = biodiésel\n"
    "  - TOTAL = consumo final energético total del sector residencial"
)

_TITULO = "Consumo de energía del sector residencial (hogares)"


def _pct_renov_row(row):
    """% renovable DIRECTA de una fila: leña, CV, biomasa, solar y
    biocombustibles, SIN contar la electricidad (no es el % oficial 7.2.1;
    para ese, que cuenta la electricidad renovable, ver `renovables_residencial`)."""
    total = float(row["TOTAL"]) if pd.notna(row["TOTAL"]) else 0.0
    if not total:
        return "-"
    renov = sum(
        float(row[col]) for col, et in FUENTES_RESID
        if et in RENOVABLES_RESID and pd.notna(row[col])
    )
    return f"{(renov / total * 100):.1f}%"


# ═══ 1. Mix del hogar por fuente ══════════════════════════════════════════

def consumo_residencial_por_fuente(anio_desde=None, anio_hasta=None) -> DataToolOutput:
    """Consumo del sector residencial abierto por fuente, en ktep."""
    df = h.load_dataset("consumo_residencial")
    df = h.filter_years(df, anio_desde, anio_hasta)
    src = [h.DATASET_PAGES["consumo_residencial"]]
    if df.empty:
        return h.empty_result("de consumo residencial por fuente en ese rango", src)

    ult = df.iloc[-1]
    anio_ult = int(ult["anio"])
    rango = h.rango(df)

    pct_dir = h.pct_renovable(ult, FUENTES_RESID, RENOVABLES_RESID)

    lines = [
        f"{_TITULO} por fuente, {rango} (ktep).",
        "",
        f"Mix del hogar {anio_ult}: TOTAL = {h.fmt_num(ult['TOTAL'], 1)} ktep; "
        f"renovables directas = {pct_dir:.1f}% "
        "(el valor de cada fuente, año por año, está en la tabla de abajo).",
    ]
    lines.append("")
    lines.append(
        "La columna '% Renov. directa' suma sólo las renovables consumidas "
        "directamente (leña, carbón vegetal, residuos de biomasa, solar "
        "térmica, biocombustibles); NO incluye la electricidad. No es el % "
        "renovable oficial del consumo: el BEN (Indicador ODS 7.2.1) cuenta "
        "además la parte renovable de la electricidad. Para esa cifra usar "
        "`renovables_residencial_uy`."
    )
    lines.append("")
    lines.append(GLOSARIO_COLS)
    lines.append("")
    lines.append(h.ALREADY_TABLE)
    lines.append(h.ALREADY_CHART)
    lines.append(
        "El TOTAL coincide con la columna 'Residencial' de "
        "`consumo_energetico_por_sector_uy` (misma magnitud, otra apertura)."
    )
    lines.append(h.definiciones_relevantes(
        "ktep", "energia_final", "sector_de_consumo", "residuos_de_biomasa",
    ))
    lines.append("")
    lines.append(h.SOURCE_FOOTER)

    table = h.build_table(
        df, FUENTES_RESID, extra_cols=[("% Renov. directa", _pct_renov_row)],
    )
    chart = h.chart_for_mix(
        df, FUENTES_RESID,
        f"Consumo residencial por fuente ({rango}), ktep",
        palette=h.COLORES_BEN,
    )
    return h.text_result("\n".join(lines), src, table=table, charts=[chart])


# ═══ 2. Tendencia del consumo total del hogar ═════════════════════════════

def tendencia_consumo_residencial(anio_desde=None, anio_hasta=None) -> DataToolOutput:
    """Evolución del consumo energético TOTAL del sector residencial, ktep/año."""
    df = h.load_dataset("consumo_residencial")
    df = h.filter_years(df, anio_desde, anio_hasta)
    src = [h.DATASET_PAGES["consumo_residencial"]]
    if df.empty:
        return h.empty_result("de consumo residencial total en ese rango", src)

    rango = h.rango(df)
    ult = df.iloc[-1]
    prim = df.iloc[0]
    n = int(ult["anio"]) - int(prim["anio"])

    lines = [
        f"{_TITULO} - TOTAL del país, {rango} (ktep/año).",
        "",
        f"  - {int(ult['anio'])}: {h.fmt_num(ult['TOTAL'], 1)} ktep "
        f"(≈ {float(ult['TOTAL']) * 11.63 / 1000:.1f} TWh equivalentes).",
    ]
    cagr = h.cagr(prim["TOTAL"], ult["TOTAL"], n)
    if cagr is not None:
        delta_pct = (float(ult["TOTAL"]) / float(prim["TOTAL"]) - 1) * 100
        lines.append(f"  - {int(prim['anio'])}: {h.fmt_num(prim['TOTAL'], 1)} ktep.")
        lines.append(
            f"  - Variación {int(prim['anio'])}→{int(ult['anio'])}: "
            f"{delta_pct:+.1f}% total ({cagr:+.2f}% / año compuesto)."
        )
        ult_n = df.tail(min(6, len(df)))
        if len(ult_n) >= 2:
            x0 = float(ult_n.iloc[0]["TOTAL"])
            x1 = float(ult_n.iloc[-1]["TOTAL"])
            tendencia = (
                "↑ creciendo" if x1 > x0
                else "↓ contrayéndose" if x1 < x0 else "<-> estable"
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
        "Recordar: BEN no incluye población ni cantidad de hogares. Para "
        "'consumo por hogar' o 'per cápita' hay que cruzar con datos del INE."
    )
    lines.append(h.definiciones_relevantes("ktep", "energia_final", "sector_de_consumo"))
    lines.append("")
    lines.append(h.SOURCE_FOOTER)

    table = [["Año", "Consumo residencial (ktep)"]]
    for _, row in df.iterrows():
        table.append([str(int(row["anio"])), h.fmt_num(row["TOTAL"], 1)])

    chart = h.line_chart(
        f"Consumo energético del sector residencial ({rango}), ktep",
        df["anio"].tolist(),
        [("Consumo residencial", df["TOTAL"].tolist())],
        palette=h.COLORES_BEN,
    )
    return h.text_result("\n".join(lines), src, table=table, charts=[chart])


# ═══ 3. Electrificación: participación (%) de cada fuente ═════════════════

# Fuentes cuya participación (%) seguimos en el tiempo para contar la
# transición del hogar. El resto son marginales y quedarían como ruido.
_FUENTES_SHARE = [
    ("EE",  "Electricidad"),
    ("L",   "Leña"),
    ("GLP", "Supergás (GLP)"),
    ("GN",  "Gas natural"),
    ("RB",  "Residuos de biomasa"),
    ("S",   "Solar térmica"),
    ("Q",   "Queroseno"),
]


def electrificacion_hogares(anio_desde=None, anio_hasta=None) -> DataToolOutput:
    """Participación (%) de cada fuente en el consumo del hogar a lo largo del
    tiempo, con foco en el cruce histórico leña <-> electricidad."""
    df = h.load_dataset("consumo_residencial")
    df = h.filter_years(df, anio_desde, anio_hasta)
    src = [h.DATASET_PAGES["consumo_residencial"]]
    if df.empty:
        return h.empty_result("de consumo residencial en ese rango", src)

    rango = h.rango(df)

    # Series de participación (%) por fuente.
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

    # Cruce leña <-> electricidad: primer año (dentro del rango) en que la
    # electricidad supera a la leña.
    cruce = None
    for i in range(len(df)):
        if shares["Electricidad"][i] > shares["Leña"][i]:
            cruce = int(df.iloc[i]["anio"])
            break
    lines.append("")
    if cruce is not None and int(df.iloc[0]["anio"]) < cruce:
        lines.append(
            f"  → La electricidad superó a la leña como principal fuente del "
            f"hogar en {cruce}."
        )
    elif shares["Electricidad"][0] > shares["Leña"][0]:
        lines.append(
            "  → En todo el rango la electricidad ya supera a la leña."
        )
    else:
        lines.append(
            "  → En todo el rango la leña sigue por encima de la electricidad."
        )

    lines.append("")
    lines.append(GLOSARIO_COLS)
    lines.append("")
    lines.append(h.ALREADY_TABLE)
    lines.append(h.ALREADY_CHART)
    lines.append(
        "Los valores del gráfico y la tabla son participaciones (% del total "
        "del año), no ktep. Para los valores absolutos usar "
        "`consumo_residencial_por_fuente`."
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
        f"Participación de cada fuente en el consumo del hogar ({rango}), %",
        df["anio"].tolist(),
        [(label, shares[label]) for _, label in _FUENTES_SHARE],
        palette=h.COLORES_BEN,
    )
    return h.text_result("\n".join(lines), src, table=table, charts=[chart])


# ═══ 4. Drill-down: una sola fuente ═══════════════════════════════════════

# Tokens aceptados → (columna, etiqueta). Acepta el código (EE, L, GLP...) y
# algunos sinónimos frecuentes, sin distinción de mayúsculas/acentos.
_FUENTE_LOOKUP = {}
for _col, _label in FUENTES_RESID:
    _FUENTE_LOOKUP[_col.lower()] = (_col, _label)
    _FUENTE_LOOKUP[_label.lower()] = (_col, _label)
_FUENTE_LOOKUP.update({
    "supergas": ("GLP", "Supergás (GLP)"),
    "supergás": ("GLP", "Supergás (GLP)"),
    "lena": ("L", "Leña"),
    "solar": ("S", "Solar térmica"),
    "keroseno": ("Q", "Queroseno"),
    "carbon vegetal": ("CV", "Carbón vegetal"),
    "biomasa": ("RB", "Residuos de biomasa"),
})
_FUENTES_VALIDAS = ", ".join(col for col, _ in FUENTES_RESID)


def fuente_residencial_detalle(fuente, anio_desde=None, anio_hasta=None) -> DataToolOutput:
    """Serie histórica de UNA fuente en el consumo residencial, en ktep."""
    src = [h.DATASET_PAGES["consumo_residencial"]]
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

    df = h.load_dataset("consumo_residencial")
    df = h.filter_years(df, anio_desde, anio_hasta)
    if df.empty:
        return h.empty_result(f"de {label} en el hogar en ese rango", src)

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
        cagr = h.cagr(prim[col], ult[col], n)

        lines += [
            "",
            f"  - {int(ult['anio'])}: {h.fmt_num(ult[col], 1)} ktep "
            f"({share_ult:.1f}% del consumo del hogar ese año).",
            f"  - {int(prim['anio'])} (primer año con dato): "
            f"{h.fmt_num(prim[col], 1)} ktep.",
            f"  - Máximo histórico: {h.fmt_num(fila_max[col], 1)} ktep "
            f"en {int(fila_max['anio'])}.",
        ]
        if cagr is not None:
            lines.append(
                f"  - Crecimiento {int(prim['anio'])}→{int(ult['anio'])}: "
                f"{cagr:+.2f}% / año compuesto."
            )

    lines.append("")
    lines.append(GLOSARIO_COLS)
    lines.append("")
    lines.append(h.ALREADY_TABLE)
    lines.append(h.ALREADY_CHART)
    defs = ["ktep", "energia_final", "sector_de_consumo"]
    if col == "RB":
        defs.append("residuos_de_biomasa")
    lines.append(h.definiciones_relevantes(*defs))
    lines.append("")
    lines.append(h.SOURCE_FOOTER)

    table = [["Año", f"{label} (ktep)", "% del hogar"]]
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
        f"{label} en el consumo residencial ({rango}), ktep",
        df["anio"].tolist(),
        [(label, df[col].tolist())],
        palette=h.COLORES_BEN,
    )
    return h.text_result("\n".join(lines), src, table=table, charts=[chart])


# ═══ 5. Renovables del hogar (Indicador ODS 7.2.1) ════════════════════════
# El BEN define el % renovable del consumo final (Indicador ODS 7.2.1)
# **contando la fracción renovable de la electricidad**: como la matriz
# eléctrica del SIN es casi totalmente renovable, electrificar usos finales
# sube el indicador. Por eso esta tool NO trata la electricidad como un bloque
# aparte: la reparte en su parte renovable y su parte fósil según el mix de
# generación del SIN de cada año (dataset de generación). Ese mix sólo existe
# desde 2002, así que el indicador se reporta a partir de ese año.


def renovables_residencial(anio_desde=None, anio_hasta=None) -> DataToolOutput:
    """% renovable del consumo del hogar según el criterio del Indicador ODS
    7.2.1 del BEN (cuenta la electricidad renovable). Cobertura 2002-2024."""
    src = [h.DATASET_PAGES["consumo_residencial"], h.DATASET_PAGES["generacion"]]

    # El criterio oficial necesita el mix renovable del SIN, disponible desde
    # 2002; recortamos el rango a esa cobertura.
    desde = (
        max(int(anio_desde), h.PRIMER_ANIO_MIX_SIN)
        if anio_desde is not None else h.PRIMER_ANIO_MIX_SIN
    )
    df = h.load_dataset("consumo_residencial")
    df = h.filter_years(df, desde, anio_hasta)
    if df.empty:
        return h.empty_result(
            "de renovables en el consumo residencial en ese rango (el "
            "Indicador 7.2.1 requiere el mix del SIN, disponible desde 2002)",
            src,
        )

    share_sin = h.share_renovable_sin()
    renov_cols = [col for col, et in FUENTES_RESID if et in RENOVABLES_RESID]
    rango = h.rango(df)

    anios, s_dir, s_ee_ren, s_norenov, s_pct = [], [], [], [], []
    for _, row in df.iterrows():
        y = int(row["anio"])
        sh = share_sin.get(y)
        if sh is None:
            continue  # sin mix del SIN no se puede aplicar el criterio
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
            "de renovables en el consumo residencial en ese rango (sin datos "
            "de mix del SIN para esos años)",
            src,
        )

    # Último año del resultado.
    i = -1
    total_u = s_dir[i] + s_ee_ren[i] + s_norenov[i]
    sh_u = share_sin.get(anios[i])

    lines = [
        f"{_TITULO}: % renovable (criterio Indicador ODS 7.2.1), "
        f"{rango} (ktep).",
        "",
        f"Año {anios[i]}: % renovable = **{s_pct[i]:.1f}%** del consumo del hogar "
        f"(TOTAL {h.fmt_num(total_u, 1)} ktep; la electricidad renovable se "
        f"calcula con el {sh_u * 100:.1f}% renovable del SIN ese año). El "
        "desglose renovable directa / electricidad renovable / no renovable, "
        "año por año, está en la tabla.",
        "",
        "Metodología: el BEN define el % renovable del consumo final "
        "(Indicador ODS 7.2.1) contando la parte renovable de la electricidad. "
        "Aquí esa parte se estima repartiendo la electricidad del hogar según "
        "el mix de generación del SIN de cada año (`matriz_generacion_electrica_uy`), "
        "disponible desde 2002. El 64% que publica el BEN para 2024 es el "
        "indicador NACIONAL (todos los sectores); este es el del sector "
        "residencial, que es más alto por el peso de la electricidad y la leña.",
        "",
        GLOSARIO_COLS,
        "",
        h.ALREADY_TABLE,
        h.ALREADY_CHART,
        h.definiciones_relevantes(
            "renovable_consumo_final", "ktep", "energia_final",
            "sector_de_consumo", "residuos_de_biomasa",
        ),
        "",
        h.SOURCE_FOOTER,
    ]

    table = [["Año", "Renov. directa (ktep)", "Electricidad renovable (ktep)",
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
        f"Consumo residencial renovable vs no renovable - criterio 7.2.1 "
        f"({rango}), ktep",
        anios,
        [
            ("Renovable", [round(s_dir[j] + s_ee_ren[j], 1) for j in range(len(anios))]),
            ("No renovable", s_norenov),
        ],
        palette=h.COLORES_BEN,
    )
    return h.text_result("\n".join(lines), src, table=table, charts=[chart])


# ═══ 6. Cálculo auditable del % renovable de UN año ═══════════════════════

def renovable_residencial_calculo(anio=None) -> DataToolOutput:
    """% renovable del consumo del hogar para UN año, mostrando el cálculo
    paso a paso a partir de los dos datasets que lo alimentan."""
    src = [h.DATASET_PAGES["consumo_residencial"], h.DATASET_PAGES["generacion"]]
    df = h.load_dataset("consumo_residencial")

    if anio is None:
        anio = int(df["anio"].max())
    else:
        anio = int(anio)
    fila = df[df["anio"] == anio]
    if fila.empty:
        return h.empty_result(
            f"para el año {anio} en el consumo residencial "
            f"(rango disponible: {int(df['anio'].min())}-{int(df['anio'].max())})",
            src,
        )
    row = fila.iloc[0]

    total = float(row["TOTAL"]) if pd.notna(row["TOTAL"]) else 0.0
    ee = float(row["EE"]) if pd.notna(row["EE"]) else 0.0
    # Desglose de las renovables directas, fuente por fuente.
    directas_det = [
        (et, float(row[col]))
        for col, et in FUENTES_RESID
        if et in RENOVABLES_RESID and pd.notna(row[col]) and float(row[col]) > 0
    ]
    directas = sum(v for _, v in directas_det)
    sin = h.sin_detalle(anio)

    enc = (
        f"{_TITULO}: cálculo del % renovable del hogar - año {anio}.\n\n"
        "Fórmula (criterio Indicador ODS 7.2.1 del BEN):\n"
        "  % renovable = (renovables directas + electricidad renovable) / consumo total\n"
        "  electricidad renovable = electricidad del hogar x fracción renovable del SIN\n"
    )

    # Paso 1 - renovables directas (dataset de consumo residencial).
    p1 = [
        "",
        "Paso 1 - Renovables directas del hogar "
        "(dataset: consumo residencial por fuente):",
    ]
    for et, v in directas_det:
        p1.append(f"    {et:<22}: {h.fmt_num(v, 1):>8} ktep")
    p1.append(f"    {'SUMA directas':<22}: {h.fmt_num(directas, 1):>8} ktep")

    if sin is None:
        # Año anterior a 2002: no hay mix del SIN, no se puede aplicar 7.2.1.
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
            f"Sólo se puede informar el renovable DIRECTO (sin electricidad): "
            f"{h.fmt_num(directas, 1)} / {h.fmt_num(total, 1)} = "
            f"**{pct_dir:.1f}%** del consumo del hogar en {anio}.",
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
        table.append(["TOTAL consumo del hogar", h.fmt_num(total, 1), "100.0%"])
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
        "Paso 3 - Electricidad renovable consumida por el hogar:",
        f"    electricidad del hogar = {h.fmt_num(ee, 1)} ktep",
        f"    electricidad renovable = {h.fmt_num(ee, 1)} x {share * 100:.1f}% "
        f"= {h.fmt_num(ee_ren, 1)} ktep",
        "",
        "Paso 4 - Total renovable y porcentaje:",
        f"    renovable total = {h.fmt_num(directas, 1)} (directas) + "
        f"{h.fmt_num(ee_ren, 1)} (electricidad) = {h.fmt_num(renov_total, 1)} ktep",
        f"    consumo total del hogar = {h.fmt_num(total, 1)} ktep",
        f"    % renovable = {h.fmt_num(renov_total, 1)} / {h.fmt_num(total, 1)} "
        f"= **{pct:.1f}%**",
        "",
        f"Para comparar: contando SÓLO las renovables directas (sin la "
        f"electricidad) el {anio} daría {pct_dir:.1f}%. La diferencia "
        f"({pct - pct_dir:+.1f} pp) es el aporte de la electricidad renovable.",
        "",
        "Notas metodológicas:",
        "  - Es el mismo criterio con el que el BEN calcula su indicador "
        "NACIONAL (64% en 2024, todos los sectores); este es el del sector "
        "residencial, más alto por el peso de la electricidad y la leña.",
        "  - La fracción renovable se toma del mix de GENERACIÓN del SIN. La "
        "metodología oficial podría usar el mix de abastecimiento eléctrico "
        "(que trata aparte la electricidad importada); la diferencia es menor.",
        "",
        GLOSARIO_COLS,
        "",
        h.ALREADY_TABLE,
        h.ALREADY_CHART,
        h.definiciones_relevantes(
            "renovable_consumo_final", "ktep", "energia_final",
            "sector_de_consumo", "residuos_de_biomasa",
        ),
        "",
        h.SOURCE_FOOTER,
    ]

    table = [["Componente", "ktep", "% del total"]]
    for et, v in directas_det:
        table.append([et, h.fmt_num(v, 1), f"{v / total * 100:.1f}%"])
    table.append(["Renovables directas (subtotal)", h.fmt_num(directas, 1),
                  f"{pct_dir:.1f}%"])
    table.append([f"Electricidad renovable (EE x {share * 100:.1f}%)",
                  h.fmt_num(ee_ren, 1), f"{ee_ren / total * 100:.1f}%"])
    table.append(["RENOVABLE TOTAL", h.fmt_num(renov_total, 1), f"{pct:.1f}%"])
    table.append(["No renovable", h.fmt_num(no_renov, 1),
                  f"{no_renov / total * 100:.1f}%"])
    table.append(["TOTAL consumo del hogar", h.fmt_num(total, 1), "100.0%"])

    chart = h.pie_chart(
        f"Consumo residencial {anio}: renovable vs no renovable (criterio 7.2.1)",
        [
            ("Renovables directas", round(directas, 1)),
            ("Electricidad renovable", round(ee_ren, 1)),
            ("No renovable", round(no_renov, 1)),
        ],
        palette=h.COLORES_BEN,
    )
    return h.text_result("\n".join(lines), src, table=table, charts=[chart])
