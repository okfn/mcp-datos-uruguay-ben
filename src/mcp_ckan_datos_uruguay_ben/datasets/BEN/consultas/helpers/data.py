"""
Carga y filtrado de los datasets BEN (catalogodatos.gub.uy).

URLs de los 10 datasets (página del portal CKAN + CSV directo), loader
cacheado (`load_dataset`) que normaliza la columna AÑO → anio, y `filter_years`.
"""
import io
import requests

import pandas as pd


PORTAL = "https://catalogodatos.gub.uy/dataset/"

# Página del dataset (slug) → URL al portal CKAN
DATASET_PAGES = {
    "gas_natural":            PORTAL + "ben-importacion-de-gas-natural",
    "petroleo":               PORTAL + "ben-importacion-de-petroleo-y-carga-de-refineria",
    "impo_expo_electricidad": PORTAL + "ben-importacion-y-exportacion-de-electricidad",
    "abastecimiento":         PORTAL + "miem-abastecimiento-de-energia-por-fuente",
    "factor_emision_sin":     PORTAL + "miem-ben-factor-de-emision-de-co2-del-sin",
    "consumo_fuente":         PORTAL + "miem-consumo-final-energetico-por-fuente",
    "consumo_sector":         PORTAL + "miem-consumo-final-energetico-por-sector",
    "emisiones_sector":       PORTAL + "miem-emisiones-de-co2-por-sector",
    "generacion":             PORTAL + "miem-generacion-de-electricidad-por-fuente",
    "potencia":               PORTAL + "miem-potencia-instalada-por-fuente",
    "consumo_residencial":    PORTAL + "ministerio-industra-energia-mineria-ben-consumo-sector-residencial-por-fuente",
    "consumo_transporte":     PORTAL + "ministerio-de-industria-energia-y-mineria-ben-consumo-sector-transporte-por-fuente",
}

# Cada entrada es (dataset_uuid, resource_uuid, filename) - verificada
# contra los snapshots `_meta_*.json` de `package_show`. El CSV directo
# se compone debajo en `DATASET_URLS`.
_DATASET_PARTS = {
    "gas_natural": (
        "61631f9e-03ac-4080-a225-a4ddad8da40f",
        "9690c070-d697-40ff-a848-7f9dc98454ab",
        "impo_gas_natural.csv",
    ),
    "petroleo": (
        "db244448-da5e-4dff-8bca-8163ed9c8d6d",
        "7efe24ee-b7ee-45fb-8b97-5518b02930fe",
        "impo_y_carga_refineria_petroleo.csv",
    ),
    "impo_expo_electricidad": (
        "b0ab3d1f-4d00-490b-86fc-727238a405cc",
        "dbec6e8f-0202-46dc-8bf5-64ef4018cab9",
        "impo_y_expo_electricidad.csv",
    ),
    "abastecimiento": (
        "fc5e7e9c-73cc-4c10-a3b7-6c27848bc095",
        "eb3fadb3-a0b5-4324-8742-5355632f9b24",
        "abastecimiento-de-energia-por-fuente.csv",
    ),
    "factor_emision_sin": (
        "10967adb-2b87-4d25-b8e3-7accbcc917f5",
        "79af11a5-a11d-49e8-8e56-b54b5539af0c",
        "factor_emision-co2-sin.csv",
    ),
    "consumo_fuente": (
        "1737fc66-58b7-4286-a246-f1864533975d",
        "6e6af1ef-15ee-434a-ba11-b091641b292d",
        "consumo-final-energetico-por-fuente.csv",
    ),
    "consumo_sector": (
        "9beed8c2-b881-4e9b-a3d8-9412e48b9554",
        "11142183-96cb-4309-8f90-2b368f8eb99c",
        "consumo-final-energetico-por-sector.csv",
    ),
    "emisiones_sector": (
        "fded3eeb-2904-43a5-a348-0b31434ef085",
        "0276c0ec-a444-4221-8354-b4909b5bd2d6",
        "emisiones-de-co2-por-sector.csv",
    ),
    "generacion": (
        "91118d5f-11be-4c84-82f0-79370ab7b089",
        "101c92a0-2906-4232-ad8d-34234a5eca17",
        "generacion-electricidad-por-fuente.csv",
    ),
    "potencia": (
        "a3254965-7f67-4c91-b52d-7c50d2192f40",
        "1306f14e-fdf8-4e26-82c6-7e12319ee0ec",
        "potencia-instalada-por-fuente.csv",
    ),
    "consumo_residencial": (
        "f36babe7-c21e-4ad5-b94e-f525ed393fbe",
        "a7318ff7-16da-498b-a475-a810e7ace162",
        "consumo-sector-residencial-por-fuente.csv",
    ),
    "consumo_transporte": (
        "88219cac-31cb-4b62-a4b0-786d18072a9c",
        "1a4de650-9eb9-47e4-9339-df0da15adca0",
        "consumo-sector-transporte-por-fuente.csv",
    ),
}

DATASET_URLS = {
    key: f"{PORTAL}{ds}/resource/{rs}/download/{fn}"
    for key, (ds, rs, fn) in _DATASET_PARTS.items()
}

# Opciones de parseo por dataset. Casi todos los CSV del MIEM vienen en
# ISO-8859-1 con separador ';' y punto decimal (`_DEFAULT_READ_OPTS`). El
# dataset residencial, publicado más tarde, viene en UTF-8 con separador ','
# y **coma decimal** ("296,5" = 296.5), así que necesita su propia entrada.
_DEFAULT_READ_OPTS = {"sep": ";", "encoding": "latin-1"}
_DATASET_READ_OPTS = {
    "consumo_residencial": {"sep": ",", "encoding": "utf-8", "decimal": ","},
    "consumo_transporte": {"sep": ",", "encoding": "utf-8", "decimal": ","},
}

_caches = {}


def load_dataset(key):
    """Lee el CSV remoto del MIEM y lo cachea por key.

    El formato de parseo (separador, encoding, decimal) sale de
    `_DATASET_READ_OPTS` (default: latin-1 / ';' / punto decimal).

    Renombra `AÑO` → `anio` y la castea a int para que las tools puedan
    filtrar con confianza.
    """
    if key in _caches:
        return _caches[key]
    url = DATASET_URLS[key]
    opts = _DATASET_READ_OPTS.get(key, _DEFAULT_READ_OPTS)

    # El 09 de Junio, el catálogo se desplegó con un Self-Signed certificate y
    # las llamadas programáticas ya no funcionan. Como controlamos las URLs que
    # se llaman y confiamos en el servidor, esquivamos la validación SSL.
    # TODO: Hablar con el equipo de infraestructura y revisar este fix que ponemos
    # para poder desplegar en el entorno de pruebas.
    response = requests.get(url, verify=False)
    # Forzamos el encoding: sin charset en la cabecera, requests asume
    # ISO-8859-1 y rompería los acentos del dataset residencial (UTF-8).
    response.encoding = opts["encoding"]
    df = pd.read_csv(io.StringIO(response.text), **opts)
    if "AÑO" in df.columns:
        df = df.rename(columns={"AÑO": "anio"})
    df["anio"] = df["anio"].astype(int)
    _caches[key] = df
    return df


def filter_years(df, anio_desde=None, anio_hasta=None):
    """Filtra por rango cerrado [anio_desde, anio_hasta] y ordena."""
    if anio_desde is not None:
        df = df[df["anio"] >= int(anio_desde)]
    if anio_hasta is not None:
        df = df[df["anio"] <= int(anio_hasta)]
    return df.sort_values("anio").reset_index(drop=True)


# ── Fracción renovable del SIN (para el criterio ODS 7.2.1 del consumo) ────
# El % renovable del consumo final cuenta la parte renovable de la
# electricidad; esa fracción sale del mix de generación del SIN (dataset
# `generacion`), disponible desde 2002. Lo usan las tools de renovables de
# cada sector de consumo (residencial, transporte, ...), por eso vive acá y
# no duplicado en cada módulo.
PRIMER_ANIO_MIX_SIN = 2002
_GEN_RENOV_COLS = ["EE_H", "EE_Eo", "EE_S", "EE_B"]  # hidro, eólica, solar, biomasa


def share_renovable_sin():
    """{año: fracción renovable de la generación del SIN} (0-1), desde 2002."""
    gen = load_dataset("generacion")
    share = {}
    for _, gr in gen.iterrows():
        tot = float(gr["TOTAL"]) if pd.notna(gr["TOTAL"]) else 0.0
        if tot:
            renov = sum(float(gr[c]) for c in _GEN_RENOV_COLS if pd.notna(gr[c]))
            share[int(gr["anio"])] = renov / tot
    return share


def sin_detalle(anio):
    """(fracción renovable, GWh renovables, GWh totales) del SIN para `anio`,
    o None si no hay datos de generación ese año (serie desde 2002)."""
    gen = load_dataset("generacion")
    fila = gen[gen["anio"] == int(anio)]
    if fila.empty:
        return None
    gr = fila.iloc[0]
    tot = float(gr["TOTAL"]) if pd.notna(gr["TOTAL"]) else 0.0
    if not tot:
        return None
    renov = sum(float(gr[c]) for c in _GEN_RENOV_COLS if pd.notna(gr[c]))
    return renov / tot, renov, tot
