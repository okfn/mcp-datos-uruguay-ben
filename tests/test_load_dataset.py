"""
Regresión del parseo de CSVs en `load_dataset` (helpers/data.py).

Contexto: en 2026-02 el MIEM migró los datasets `consumo_residencial` y
`consumo_transporte` del formato UTF-8 / separador ',' / coma decimal al
formato estándar del resto de los CSVs (ISO-8859-1 / ';' / punto decimal), y
el transporte ganó además una columna `GM` aún vacía. Con las opciones de
parseo viejas, pandas leía cada renglón como UNA sola columna y todas las
tools de esos datasets fallaban con `KeyError: 'anio'`.

Estos tests mockean `requests.get` (sin red) para verificar que
`load_dataset` parsea correctamente el formato actual del catálogo.
"""

import types

import pytest

from mcp_ckan_datos_uruguay_ben.datasets.BEN.consultas.helpers import data as data_mod


def _mock_response(csv_bytes):
    """Response falso: `content` crudo (bytes) + `text` decodificado."""
    resp = types.SimpleNamespace()
    resp.status_code = 200
    resp.content = csv_bytes
    resp.text = csv_bytes.decode("latin-1")
    resp.raise_for_status = lambda: None
    return resp


# Snapshot del header REAL del catálogo (2026-02): ISO-8859-1 ('AÑO' =
# b'A\xd1O'), separador ';', punto decimal, columna GM vacía, dato hasta 2025.
_TRANSPORTE_CSV = (
    b"A\xd1O;Ga;GAv;Q;T;Do;Go;Fo;GM;Be;Bd;EE;TOTAL\n"
    b"1965;260.5;;3.4;;;175.3;77.5;;;;2.1;518.8\n"
    b"2024;648.1;2.0;;2.4;;791.9;0.0;;45.5;;2.7;1492.6\n"
    b"2025;670.2;1.7;;2.6;;797.3;0.0;;47.2;;6.7;1525.7\n"
)

_RESIDENCIAL_CSV = (
    b"A\xd1O;GN;S;L;RB;GLP;Ga;Q;Do;Go;Fo;GM;Be;Bd;CV;EE;TOTAL\n"
    b"1965;;;296.5;;20.1;;150.2;;13.5;8.9;9.5;;;;53.1;551.8\n"
    b"2024;19.4;6.6;345.6;7.6;106.0;0.4;1.0;;5.7;0.3\n"
)


@pytest.fixture
def no_cache():
    data_mod._caches.clear()
    yield
    data_mod._caches.clear()


@pytest.mark.parametrize("key,csv_bytes", [
    ("consumo_transporte", _TRANSPORTE_CSV),
    ("consumo_residencial", _RESIDENCIAL_CSV),
])
def test_load_dataset_parsea_formato_actual_del_catalogo(monkeypatch, no_cache, key, csv_bytes):
    """El formato migrado (';' + punto decimal + latin-1) debe parsear y
    exponer la columna `anio` como int (regresión del KeyError 'anio')."""
    monkeypatch.setattr(
        data_mod.requests, "get", lambda *a, **k: _mock_response(csv_bytes)
    )
    df = data_mod.load_dataset(key)
    assert "anio" in df.columns
    assert df["anio"].tolist() == [1965, 2024, 2025] if key == "consumo_transporte" else df["anio"].tolist()[0] == 1965
    assert "TOTAL" in df.columns
    # Valores numéricos con punto decimal (no strings) y NaN donde no hay dato.
    assert float(df.loc[df["anio"] == 1965, "Ga"].iloc[0]) == 260.5 if key == "consumo_transporte" else True


def test_load_dataset_rechaza_csv_sin_columna_de_anio(monkeypatch, no_cache):
    """Si el catálogo vuelve a cambiar el formato, el error debe ser claro
    (menciona las columnas recibidas), no un KeyError críptico."""
    html = b"<html><body>503 Service Unavailable</body></html>"
    monkeypatch.setattr(
        data_mod.requests, "get", lambda *a, **k: _mock_response(html)
    )
    with pytest.raises(ValueError, match="columna de año"):
        data_mod.load_dataset("consumo_transporte")


def test_load_dataset_reintenta_ante_503(monkeypatch, no_cache):
    """Los 503 transitorios del catálogo se reintentan antes de fallar."""
    calls = {"n": 0}

    def flaky_get(*a, **k):
        calls["n"] += 1
        resp = types.SimpleNamespace()
        resp.status_code = 503 if calls["n"] == 1 else 200
        resp.content = _TRANSPORTE_CSV
        resp.text = _TRANSPORTE_CSV.decode("latin-1")

        def raise_for_status():
            if resp.status_code != 200:
                import requests as _r
                raise _r.exceptions.HTTPError(f"{resp.status_code} Server Error")

        resp.raise_for_status = raise_for_status
        return resp

    monkeypatch.setattr(data_mod.requests, "get", flaky_get)
    monkeypatch.setattr(data_mod.time, "sleep", lambda s: None)  # sin backoff real
    df = data_mod.load_dataset("consumo_transporte")
    assert calls["n"] == 2
    assert "anio" in df.columns
