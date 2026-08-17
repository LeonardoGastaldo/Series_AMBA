"""Parsers de los datos crudos (data/raw) a series horarias limpias, en UTC.

Cada función toma un archivo anual crudo y devuelve un DataFrame con índice
datetime horario en UTC y una sola columna de valor. Nunca modifican los
archivos de data/raw: leen y transforman en memoria.
"""

import io
import zipfile
from pathlib import Path

import pandas as pd


def _concatenar_anios(directorio: Path, patron: str, parser, anio_inicio: int, anio_fin: int) -> pd.Series:
    partes = []
    for anio in range(anio_inicio, anio_fin + 1):
        archivo = directorio / patron.format(anio=anio)
        if archivo.exists():
            partes.append(parser(archivo))
    serie = pd.concat(partes).sort_index()
    return serie[~serie.index.duplicated(keep="first")]

# --- EPA AQS (ozono) ---------------------------------------------------

EPA_SITE_STATE = "06"
EPA_SITE_COUNTY = "037"
EPA_SITE_NUM = "1103"  # Los Angeles-North Main Street
EPA_PARAMETRO = "44201"  # Ozono


def parsear_epa_aqs_anio(path: str | Path) -> pd.Series:
    """Lee un hourly_44201_YYYY.zip de AirData y devuelve la serie horaria de
    ozono (ppm) del sitio fijado arriba, indexada en UTC.

    Los .zip de AirData traen el país entero (varios GB sin comprimir) para
    filtrar un solo sitio; parsear todo con pandas para después descartar el
    99% de las filas es lentísimo. En cambio, se filtran las líneas de texto
    que empiezan con el prefijo del sitio (rápido, no requiere cargar el CSV
    completo en memoria) y sólo esas pocas líneas se parsean con pandas.
    """
    # POC=1 fijo: es el monitor principal del sitio (evita duplicar horas si
    # en algún año hubiera más de un instrumento midiendo el mismo parámetro).
    prefijo = f'"{EPA_SITE_STATE}","{EPA_SITE_COUNTY}","{EPA_SITE_NUM}","{EPA_PARAMETRO}",1,'
    columnas = [
        "State Code", "County Code", "Site Num", "Parameter Code", "POC",
        "Latitude", "Longitude", "Datum", "Parameter Name", "Date Local",
        "Time Local", "Date GMT", "Time GMT", "Sample Measurement",
        "Units of Measure", "MDL", "Uncertainty", "Qualifier", "Method Type",
        "Method Code", "Method Name", "State Name", "County Name", "Date of Last Change",
    ]

    prefijo_bytes = prefijo.encode("utf-8")
    with zipfile.ZipFile(path) as zf:
        (nombre_csv,) = zf.namelist()
        contenido = zf.read(nombre_csv)

    fin_encabezado = contenido.index(b"\n") + 1
    encabezado = contenido[:fin_encabezado]
    lineas = [
        linea for linea in contenido[fin_encabezado:].split(b"\n")
        if linea.startswith(prefijo_bytes)
    ]

    buffer = io.BytesIO(encabezado + b"\n".join(lineas))
    df = pd.read_csv(buffer, usecols=["Date GMT", "Time GMT", "Sample Measurement"])
    dt = pd.to_datetime(df["Date GMT"] + " " + df["Time GMT"], utc=True)
    serie = pd.Series(df["Sample Measurement"].values, index=dt, name="ozono_ppm")
    return serie[~serie.index.duplicated(keep="first")].sort_index()


# --- NOAA ISD (temperatura) --------------------------------------------


def _parsear_campo_tmp(valor: str) -> float | None:
    """Campo TMP del formato ISD: '+0222,1' -> 22.2 °C. '+9999' = faltante."""
    if not isinstance(valor, str) or "," not in valor:
        return None
    bruto, _calidad = valor.split(",", 1)
    if bruto in ("+9999", "-9999"):
        return None
    return int(bruto) / 10.0


def parsear_noaa_isd_anio(path: str | Path) -> pd.Series:
    """Lee un CSV anual de NOAA Global Hourly (una estación) y devuelve la
    serie horaria de temperatura (°C), indexada en UTC."""
    df = pd.read_csv(path, usecols=["DATE", "TMP"], dtype={"TMP": str})
    dt = pd.to_datetime(df["DATE"], utc=True)
    temp = df["TMP"].map(_parsear_campo_tmp)
    serie = pd.Series(temp.values, index=dt, name="temperatura_c")
    serie = serie[~serie.index.duplicated(keep="first")].sort_index()
    # El ISD trae observaciones a intervalos irregulares (a veces submuestreadas
    # o repetidas dentro de la misma hora); se agrupa a la hora en punto con la
    # media de lo que haya caído en esa hora.
    return serie.resample("h").mean()


# --- NSRDB (radiación solar) --------------------------------------------

NSRDB_OFFSET_HORAS_A_UTC = 8  # Local Time Zone = -8 (fijo, sin DST) -> UTC


def parsear_nsrdb_anio(path: str | Path) -> pd.Series:
    """Lee un CSV anual de NSRDB (intervalos de 30 min, hora local fija
    UTC-8) y devuelve la serie horaria de GHI (W/m2), indexada en UTC."""
    df = pd.read_csv(path, skiprows=2, usecols=["Year", "Month", "Day", "Hour", "Minute", "GHI"])
    dt_local = pd.to_datetime(df[["Year", "Month", "Day", "Hour", "Minute"]])
    dt_utc = (dt_local + pd.Timedelta(hours=NSRDB_OFFSET_HORAS_A_UTC)).dt.tz_localize("UTC")
    serie = pd.Series(df["GHI"].values, index=dt_utc, name="radiacion_ghi_wm2")
    serie = serie[~serie.index.duplicated(keep="first")].sort_index()
    return serie.resample("h").mean()


# --- Rango completo (todos los años) y combinación ----------------------


def parsear_epa_aqs_rango(directorio: Path, anio_inicio: int, anio_fin: int) -> pd.Series:
    return _concatenar_anios(
        Path(directorio), "hourly_44201_{anio}.zip", parsear_epa_aqs_anio, anio_inicio, anio_fin
    )


def parsear_noaa_isd_rango(directorio: Path, anio_inicio: int, anio_fin: int, estacion: str = "72295023174") -> pd.Series:
    return _concatenar_anios(
        Path(directorio), estacion + "_{anio}.csv", parsear_noaa_isd_anio, anio_inicio, anio_fin
    )


def parsear_nsrdb_rango(directorio: Path, anio_inicio: int, anio_fin: int) -> pd.Series:
    return _concatenar_anios(
        Path(directorio), "nsrdb_{anio}.csv", parsear_nsrdb_anio, anio_inicio, anio_fin
    )


def combinar_series(ozono: pd.Series, temperatura: pd.Series, radiacion: pd.Series) -> pd.DataFrame:
    """Combina las tres series horarias en una sola tabla, alineadas por
    índice UTC. Usa join externo (outer) para no perder horas donde falte
    sólo una de las tres variables; los faltantes quedan como NaN, a
    resolver explícitamente después (no se interpola acá en silencio)."""
    df = pd.concat(
        {"ozono_ppm": ozono, "temperatura_c": temperatura, "radiacion_ghi_wm2": radiacion},
        axis=1,
    )
    return df.sort_index()
