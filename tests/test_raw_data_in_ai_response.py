"""
Garantiza que la respuesta que recibe la IA (el texto de `content`) incluye los
DATOS CRUDOS, no sólo un resumen.

Contexto: el gateway manda a la IA únicamente `content[0].text`; la tabla y los
gráficos de `structuredContent` se renderizan sólo para el usuario. Por eso
`text_result` embebe la tabla como texto en `content`. Si esto se rompe, la IA
analiza a ciegas y sus conclusiones son malas.
"""

import pytest

from mcp_ckan_datos_uruguay_ben.datasets.BEN.consultas import helpers as h
from mcp_ckan_datos_uruguay_ben.datasets.BEN.consultas.helpers.format import (
    _table_to_text,
)
from mcp_ckan_datos_uruguay_ben.datasets.BEN import consultas as ben


# ─── Unit: el builder text_result embebe la tabla cruda ───────────────────

def _text(res):
    return res.content[0].text


def test_text_result_embeds_full_table_verbatim():
    table = [
        ["Año", "A", "Total"],
        ["2020", "1.0", "11.0"],
        ["2021", "2.0", "12.0"],
    ]
    res = h.text_result("resumen", ["http://src"], table=table)

    txt = _text(res)
    # El bloque de datos para la IA está presente...
    assert "=== Datos completos" in txt
    # ...y contiene la tabla COMPLETA verbatim (no sólo la última fila).
    assert _table_to_text(table) in txt
    for row in table:
        for cell in row:
            assert cell in txt
    # structuredContent (lo que ve el usuario) queda intacto.
    assert res.structuredContent["table"] == table
    assert res.structuredContent["sources"] == ["http://src"]


def test_text_result_sin_tabla_no_agrega_bloque():
    res = h.text_result("solo texto", ["http://src"])
    txt = _text(res)
    assert "=== Datos completos" not in txt
    assert "table" not in res.structuredContent


def test_table_to_text_formato_pipe():
    table = [["a", "b"], ["1", "2"]]
    assert _table_to_text(table) == "a | b\n1 | 2"
    assert _table_to_text([]) == ""


# ─── Contrato: TODA tool de datos manda la serie cruda a la IA ────────────

# (nombre, callable, kwargs) para cada tool de datos del repo.
DATA_TOOLS = [
    ("consumo_residencial_por_fuente", ben.consumo_residencial_por_fuente, {}),
    ("tendencia_consumo_residencial", ben.tendencia_consumo_residencial, {}),
    ("electrificacion_hogares", ben.electrificacion_hogares, {}),
    ("fuente_residencial_detalle", ben.fuente_residencial_detalle, {"fuente": "L"}),
    ("renovables_residencial", ben.renovables_residencial, {}),
    ("renovable_residencial_calculo", ben.renovable_residencial_calculo, {}),
    ("consumo_transporte_por_fuente", ben.consumo_transporte_por_fuente, {}),
    ("tendencia_consumo_transporte", ben.tendencia_consumo_transporte, {}),
    ("participacion_fuentes_transporte", ben.participacion_fuentes_transporte, {}),
    ("fuente_transporte_detalle", ben.fuente_transporte_detalle, {"fuente": "Go"}),
    ("renovables_transporte", ben.renovables_transporte, {}),
    ("renovable_transporte_calculo", ben.renovable_transporte_calculo, {}),
    ("matriz_generacion_electrica", ben.matriz_generacion_electrica, {}),
    ("potencia_instalada_por_fuente", ben.potencia_instalada_por_fuente, {}),
    ("factor_emision_electrico", ben.factor_emision_electrico, {}),
    ("consumo_final_por_sector", ben.consumo_final_por_sector, {}),
    ("consumo_final_por_fuente", ben.consumo_final_por_fuente, {}),
    ("tendencia_demanda_total", ben.tendencia_demanda_total, {}),
    ("matriz_abastecimiento_primario", ben.matriz_abastecimiento_primario, {}),
    ("dependencia_energetica_externa", ben.dependencia_energetica_externa, {}),
    ("perdidas_transformacion", ben.perdidas_transformacion, {}),
    ("importacion_petroleo", ben.importacion_petroleo, {}),
    ("importacion_gas_natural", ben.importacion_gas_natural, {}),
    ("intercambio_electricidad", ben.intercambio_electricidad, {}),
    ("emisiones_co2_por_sector", ben.emisiones_co2_por_sector, {}),
]


@pytest.mark.parametrize("name,fn,kwargs", DATA_TOOLS, ids=[t[0] for t in DATA_TOOLS])
def test_tool_embeds_full_table_in_ai_text(seed_cache, name, fn, kwargs):
    res = fn(**kwargs)
    txt = _text(res)
    sc = res.structuredContent

    # 1. La tool produjo una tabla (datos para el usuario).
    assert "table" in sc, f"{name}: no devolvió tabla"
    assert len(sc["table"]) >= 2, f"{name}: tabla sin filas de datos"

    # 2. Esa MISMA tabla completa está embebida en el texto que recibe la IA.
    assert "=== Datos completos" in txt, f"{name}: falta el bloque de datos"
    assert _table_to_text(sc["table"]) in txt, (
        f"{name}: la tabla del usuario no está verbatim en el texto de la IA"
    )


# ─── Regresión: las tools multi-año mandan TODOS los años, no sólo el último ─

@pytest.mark.parametrize(
    "fn",
    [ben.consumo_residencial_por_fuente, ben.matriz_generacion_electrica,
     ben.consumo_final_por_fuente, ben.emisiones_co2_por_sector,
     ben.consumo_transporte_por_fuente, ben.participacion_fuentes_transporte],
)
def test_multianio_incluye_todos_los_anios_en_texto(seed_cache, fn):
    res = fn()
    bloque = _text(res).split("=== Datos completos")[1]
    # Años = primera columna de cada fila de datos de la tabla.
    years = [row[0] for row in res.structuredContent["table"][1:]]
    assert len(years) >= 2, f"{fn.__name__}: el fixture no es multi-año"
    for year in years:
        assert year in bloque, (
            f"{fn.__name__}: falta el año {year} en los datos para la IA "
            "(regresión: antes sólo se mandaba el último año)"
        )
