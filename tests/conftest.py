"""
Fixtures de test para las tools BEN.

`seed_cache` precarga el cache de `helpers/data.py` con DataFrames sintéticos
(sin red) para cada dataset que consumen las tools, de modo que los tests
corran offline y de forma determinista. `load_dataset` devuelve el cache si la
key existe, así que basta con poblar `data._caches`.
"""

import pandas as pd
import pytest

from mcp_ckan_datos_uruguay_ben.datasets.BEN.consultas.helpers import data as data_mod


# Años usados en todos los fixtures (>= 2002 para que el criterio 7.2.1, que
# necesita el mix del SIN, sea aplicable en renovables_residencial).
YEARS = [2020, 2021, 2022]

# Columnas por dataset (ademas de 'anio'), tomadas de lo que leen las tools.
FIXTURE_COLUMNS = {
    "consumo_residencial": [
        "EE", "L", "GLP", "GN", "RB", "S", "Go", "CV", "Q",
        "Ga", "Fo", "Be", "Do", "GM", "Bd", "TOTAL",
    ],
    "generacion": ["EE_H", "EE_Eo", "EE_S", "EE_B", "EE_F", "TOTAL"],
    "potencia": [
        "TOTAL_H", "TOTAL_Eo", "TOTAL_S", "TOTAL_B", "TOTAL_F",
        "TCR_F", "TCB_F", "M_F", "TCR_B", "M_B", "TOTAL",
    ],
    "factor_emision_sin": ["FE_SIN", "Em_CE_SP", "EE_CE_SP"],
    "consumo_fuente": [
        "CM", "GN", "S", "L_CV", "RB", "RI", "DP", "Bc", "DC", "EE", "TOTAL",
    ],
    "consumo_sector": ["I", "T", "R", "C_S_SP", "AP", "NI", "TOTAL"],
    "abastecimiento": [
        "P_D", "B", "EE_H", "EE_Eo", "S", "GN", "C_C", "EE_i", "RI", "TOTAL",
    ],
    "emisiones_sector": ["T", "I", "CE_SP", "R", "AP", "C_S_SP", "CP", "NI", "TOTAL"],
    "petroleo": ["impo_petroleo", "carga_refineria"],
    "gas_natural": ["impo_gas_natural"],
    "impo_expo_electricidad": ["impo_electricidad", "expo_electricidad"],
}


def _fake_df(columns):
    """DataFrame con 'anio' + `columns`, valores deterministas no nulos."""
    data = {"anio": list(YEARS)}
    for i, col in enumerate(columns):
        # Valores distintos por columna y por año (no nulos, > 0).
        data[col] = [round(100 + i * 7 + y * 3, 1) for y in range(len(YEARS))]
    return pd.DataFrame(data)


@pytest.fixture
def seed_cache():
    """Precarga el cache de datasets y lo limpia al terminar."""
    data_mod._caches.clear()
    for key, cols in FIXTURE_COLUMNS.items():
        data_mod._caches[key] = _fake_df(cols)
    yield
    data_mod._caches.clear()
