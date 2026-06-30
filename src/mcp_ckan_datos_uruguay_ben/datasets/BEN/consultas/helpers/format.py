"""
Formateo de números, builders de `CallToolResult`, tablas y mensajes fijos.

`fmt_num`, `text_result`/`empty_result` (arman el `CallToolResult` con su
`structuredContent` y, además, embeben la tabla como texto para que la IA vea
los datos crudos), `pct_renovable` y `build_table` para el texto y la tabla de
cada respuesta, más las notas fijas `ALREADY_TABLE`/`ALREADY_CHART` y el
`SOURCE_FOOTER`.
"""

import pandas as pd
from mcp.types import CallToolResult, TextContent


# Notas para la IA: el gráfico y la tabla renderizada ya se mostraron al
# usuario en pantalla vía structuredContent (la IA NO los recibe por ahí). Los
# datos crudos de la tabla sí se le adjuntan a la IA como texto (ver
# `text_result`), para que base su análisis en los números reales.
ALREADY_TABLE = (
    "Al usuario ya se le mostró una tabla renderizada en pantalla con estos "
    "datos. Más abajo te adjuntamos los mismos datos en texto para que analices "
    "los números; no copies la tabla de vuelta en tu respuesta, interpretala."
)
ALREADY_CHART = (
    "Acabamos de generar y mostrarle un gráfico al usuario. No es necesario "
    "que intentes generar otro."
)

SOURCE_FOOTER = (
    "Fuente: MIEM - Balance Energético Nacional, Uruguay "
    "(catalogodatos.gub.uy)."
)

# Guardrails para la IA: se appendea automáticamente a toda respuesta de BEN
# desde `text_result`. Evita que el modelo invente nombres de empresas y que
# atribuya las variaciones a causas (clima, lluvias) que no están en los datos.
SIN_ESPECULAR = (
    "Responde únicamente con los datos presentes en esta respuesta y en los "
    "datasets del BEN (producción y consumo energético). NO menciones nombres "
    "de empresas, compañías ni operadores que no aparezcan explícitamente en "
    "los datos. NO atribuyas las variaciones (por ejemplo, suba o baja de la "
    "generación hidráulica) a causas como clima, lluvias, sequía o nivel de "
    "embalses: el BEN de Uruguay no contiene datos meteorológicos ni "
    "hidrológicos. Limítate a describir qué muestran los números."
)


def fmt_num(v, dec=0):
    """Formato '1,234' (locale C) o '-' si NaN/None."""
    if v is None:
        return "-"
    try:
        if pd.isna(v):
            return "-"
    except (TypeError, ValueError):
        pass
    return f"{float(v):,.{dec}f}"


def _table_to_text(table):
    """Renderiza la tabla (lista de filas) como bloque delimitado por ' | '.

    La tabla de `structuredContent` la renderiza la UI para el USUARIO; la IA
    NO la recibe por ese canal. Este texto es la copia que sí ve la IA, para
    que sus conclusiones se apoyen en TODOS los números, no sólo en el resumen.
    """
    if not table:
        return ""
    return "\n".join(" | ".join(str(c) for c in row) for row in table)


def text_result(text, sources, table=None, charts=None):
    sc = {"sources": sources}
    if table:
        sc["table"] = table
    if charts:
        sc["charts"] = charts
    body = text
    if table:
        body += (
            "\n\n=== Datos completos (para tu análisis) ===\n"
            + _table_to_text(table)
        )
    body = f"{body}\n\n{SIN_ESPECULAR}"
    return CallToolResult(
        content=[TextContent(type="text", text=body)],
        structuredContent=sc,
    )


def empty_result(label, sources):
    return CallToolResult(
        content=[TextContent(
            type="text",
            text=f"No hay datos disponibles {label}.",
        )],
        structuredContent={"sources": sources},
    )


def rango(df, col="anio"):
    """'1965-2024', o '2024' si hay un solo año en el df (asume df no vacío)."""
    a0, a1 = int(df[col].min()), int(df[col].max())
    return f"{a1}" if a0 == a1 else f"{a0}-{a1}"


def cagr(v0, v1, n):
    """Tasa de crecimiento anual compuesta (%) entre v0 y v1 en n años.

    Devuelve None si no es calculable (n<=0, valores nulos o v0<=0)."""
    if n <= 0 or v0 is None or v1 is None:
        return None
    if pd.isna(v0) or pd.isna(v1) or float(v0) <= 0:
        return None
    return ((float(v1) / float(v0)) ** (1 / n) - 1) * 100


def pct_renovable(row, fuentes, renovables, total_col="TOTAL"):
    """% renovable de una fila: suma de las `fuentes` cuya etiqueta está en
    `renovables`, sobre el total. Devuelve None si el total es 0/NaN.

    Se expone como helper para que las tools den el % renovable como dato de
    análisis (no está en la tabla cruda) sin reimprimir el desglose por fuente,
    que ya va completo en la tabla embebida por `text_result`."""
    total = float(row[total_col]) if pd.notna(row[total_col]) else 0.0
    if not total:
        return None
    renov = sum(
        float(row[col]) for col, et in fuentes
        if et in renovables and pd.notna(row[col])
    )
    return renov / total * 100


def build_table(df, fuentes, total_col="TOTAL", extra_cols=None):
    """Tabla genérica: Año + 1 col por fuente + Total + cols extra.

    `extra_cols`: list[(header, fn(row) -> str)] para columnas calculadas
    como '% Renov.' o tasas. Si None, sólo se muestra Total.
    """
    headers = ["Año"] + [et for _, et in fuentes] + [total_col.title()]
    if extra_cols:
        headers += [h for h, _ in extra_cols]
    rows = [headers]
    for _, row in df.iterrows():
        line = [str(int(row["anio"]))]
        for col, _et in fuentes:
            line.append(fmt_num(row[col]))
        line.append(fmt_num(row[total_col]))
        if extra_cols:
            for _h, fn in extra_cols:
                line.append(fn(row))
        rows.append(line)
    return rows
