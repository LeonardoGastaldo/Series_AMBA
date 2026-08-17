"""Descarga de las 3 series del proyecto (cuenca de Los Ángeles, California):

- EPA AQS/AirData: ozono horario (calidad del aire).
- NOAA ISD (Global Hourly): temperatura y clima horario.
- NSRDB (NLR, ex-NREL): radiación solar horaria/30-min.

Cada fuente se descarga en archivos crudos por año, sin transformar, respetando
el principio de no modificar los datos originales. La limpieza/parseo real
(unir años, pasar a un único índice horario, etc.) queda para 02_limpieza.ipynb.
"""

import time
from dataclasses import dataclass, field
from pathlib import Path

import requests


@dataclass
class ResumenDescarga:
    anios_solicitados: int = 0
    anios_ok: int = 0
    anios_ya_existentes: int = 0
    anios_sin_datos: int = 0
    anios_con_error: int = 0
    errores: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# EPA AQS / AirData — ozono horario (calidad del aire)
# ---------------------------------------------------------------------------

EPA_AQS_BASE_URL = "https://aqs.epa.gov/aqsweb/airdata"
EPA_AQS_PARAMETROS = {
    "OZONO": "44201",
    "PM2.5": "88101",
}


def descargar_epa_aqs_anio(
    anio: int,
    destino_dir: str | Path,
    parametro_codigo: str = EPA_AQS_PARAMETROS["OZONO"],
    timeout: int = 60,
    reintentos: int = 3,
    espera_reintento_seg: float = 5.0,
) -> tuple[Path | None, str]:
    """Descarga el archivo anual de EPA AirData con TODAS las estaciones del
    país para un parámetro y año dados (ej. ozono 2023 = hourly_44201_2023.zip).

    El filtro por el sitio de Los Ángeles elegido para el proyecto se aplica
    recién al parsear (02_limpieza.ipynb), no acá: se guarda el .zip nacional
    tal cual, sin recortar, para no transformar el dato crudo.
    """
    destino_dir = Path(destino_dir)
    nombre_archivo = f"hourly_{parametro_codigo}_{anio}.zip"
    destino = destino_dir / nombre_archivo

    if destino.exists():
        return destino, "ya_existente"

    url = f"{EPA_AQS_BASE_URL}/{nombre_archivo}"
    for intento in range(1, reintentos + 1):
        try:
            resp = requests.get(url, timeout=timeout)
        except requests.RequestException:
            if intento < reintentos:
                time.sleep(espera_reintento_seg)
            continue

        if resp.status_code == 404:
            return None, "sin_datos"
        try:
            resp.raise_for_status()
        except requests.RequestException:
            if intento < reintentos:
                time.sleep(espera_reintento_seg)
            continue

        destino_dir.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(resp.content)
        return destino, "ok"

    return None, "error"


def descargar_epa_aqs_rango(
    anio_inicio: int,
    anio_fin: int,
    destino_dir: str | Path,
    parametro_codigo: str = EPA_AQS_PARAMETROS["OZONO"],
    logger=None,
    pausa_seg: float = 1.0,
    reintentos: int = 3,
    espera_reintento_seg: float = 5.0,
) -> ResumenDescarga:
    resumen = ResumenDescarga()
    for anio in range(anio_inicio, anio_fin + 1):
        resumen.anios_solicitados += 1
        _, estado = descargar_epa_aqs_anio(
            anio, destino_dir, parametro_codigo, reintentos=reintentos, espera_reintento_seg=espera_reintento_seg
        )

        if estado == "ok":
            resumen.anios_ok += 1
            if logger:
                logger.info(f"EPA AQS {anio}: descargado")
            time.sleep(pausa_seg)
        elif estado == "ya_existente":
            resumen.anios_ya_existentes += 1
        elif estado == "sin_datos":
            resumen.anios_sin_datos += 1
            if logger:
                logger.warning(f"EPA AQS {anio}: sin archivo publicado para ese año")
        else:
            resumen.anios_con_error += 1
            resumen.errores.append(anio)
            if logger:
                logger.error(f"EPA AQS {anio}: error de descarga tras {reintentos} intentos")

    return resumen


# ---------------------------------------------------------------------------
# NOAA ISD (Global Hourly) — clima/temperatura horaria
# ---------------------------------------------------------------------------

NOAA_ISD_BASE_URL = "https://www.ncei.noaa.gov/data/global-hourly/access"
NOAA_ISD_ESTACION_LAX = "72295023174"  # USAF 722950 + WBAN 23174 = LAX


def descargar_noaa_isd_anio(
    anio: int,
    destino_dir: str | Path,
    estacion_id: str = NOAA_ISD_ESTACION_LAX,
    timeout: int = 60,
    reintentos: int = 3,
    espera_reintento_seg: float = 5.0,
) -> tuple[Path | None, str]:
    """Descarga el archivo anual de observaciones horarias de una estación del
    ISD (formato "Global Hourly" de NCEI). Un archivo por año y por estación.
    """
    destino_dir = Path(destino_dir)
    nombre_archivo = f"{estacion_id}_{anio}.csv"
    destino = destino_dir / nombre_archivo

    if destino.exists():
        return destino, "ya_existente"

    url = f"{NOAA_ISD_BASE_URL}/{anio}/{estacion_id}.csv"
    for intento in range(1, reintentos + 1):
        try:
            resp = requests.get(url, timeout=timeout)
        except requests.RequestException:
            if intento < reintentos:
                time.sleep(espera_reintento_seg)
            continue

        if resp.status_code == 404:
            return None, "sin_datos"
        try:
            resp.raise_for_status()
        except requests.RequestException:
            if intento < reintentos:
                time.sleep(espera_reintento_seg)
            continue

        destino_dir.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(resp.content)
        return destino, "ok"

    return None, "error"


def descargar_noaa_isd_rango(
    anio_inicio: int,
    anio_fin: int,
    destino_dir: str | Path,
    estacion_id: str = NOAA_ISD_ESTACION_LAX,
    logger=None,
    pausa_seg: float = 1.0,
    reintentos: int = 3,
    espera_reintento_seg: float = 5.0,
) -> ResumenDescarga:
    resumen = ResumenDescarga()
    for anio in range(anio_inicio, anio_fin + 1):
        resumen.anios_solicitados += 1
        _, estado = descargar_noaa_isd_anio(
            anio, destino_dir, estacion_id, reintentos=reintentos, espera_reintento_seg=espera_reintento_seg
        )

        if estado == "ok":
            resumen.anios_ok += 1
            if logger:
                logger.info(f"NOAA ISD {anio}: descargado")
            time.sleep(pausa_seg)
        elif estado == "ya_existente":
            resumen.anios_ya_existentes += 1
        elif estado == "sin_datos":
            resumen.anios_sin_datos += 1
            if logger:
                logger.warning(f"NOAA ISD {anio}: sin archivo publicado para esa estación/año")
        else:
            resumen.anios_con_error += 1
            resumen.errores.append(anio)
            if logger:
                logger.error(f"NOAA ISD {anio}: error de descarga tras {reintentos} intentos")

    return resumen


# ---------------------------------------------------------------------------
# NSRDB (NLR, ex-NREL) — radiación solar horaria/30-min
# ---------------------------------------------------------------------------

NSRDB_BASE_URL = "https://developer.nlr.gov/api/nsrdb/v2/solar/nsrdb-GOES-aggregated-v4-0-0-download.csv"
NSRDB_PUNTO_LAX = {"lat": 33.9425, "lon": -118.4081}


def descargar_nsrdb_anio(
    anio: int,
    api_key: str,
    email: str,
    destino_dir: str | Path,
    lat: float = NSRDB_PUNTO_LAX["lat"],
    lon: float = NSRDB_PUNTO_LAX["lon"],
    intervalo_min: int = 30,
    timeout: int = 120,
    reintentos: int = 3,
    espera_reintento_seg: float = 5.0,
) -> tuple[Path | None, str]:
    """Descarga un año de radiación solar (GOES Aggregated) para un punto fijo
    (por defecto, LAX). Requiere una API key propia de developer.nlr.gov
    (gratis, autoservicio — ver sección de este notebook).

    La API devuelve JSON en vez de CSV cuando algo falla (api_key inválida,
    año fuera de rango, parámetros mal formados); se detecta por el
    Content-Type de la respuesta y se reporta como "error_api", no como un
    archivo válido.
    """
    if not api_key or not email:
        return None, "sin_api_key"

    destino_dir = Path(destino_dir)
    nombre_archivo = f"nsrdb_{anio}.csv"
    destino = destino_dir / nombre_archivo

    if destino.exists():
        return destino, "ya_existente"

    params = {
        "api_key": api_key,
        "wkt": f"POINT({lon} {lat})",
        "names": str(anio),
        "interval": str(intervalo_min),
        "utc": "false",
        "leap_day": "true",
        "email": email,
    }

    for intento in range(1, reintentos + 1):
        try:
            resp = requests.get(NSRDB_BASE_URL, params=params, timeout=timeout)
        except requests.RequestException:
            if intento < reintentos:
                time.sleep(espera_reintento_seg)
            continue

        content_type = resp.headers.get("Content-Type", "")
        if "json" in content_type.lower() or resp.text.lstrip()[:1] == "{":
            return None, f"error_api: {resp.text[:300]}"
        try:
            resp.raise_for_status()
        except requests.RequestException:
            if intento < reintentos:
                time.sleep(espera_reintento_seg)
            continue

        destino_dir.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(resp.content)
        return destino, "ok"

    return None, "error"


def descargar_nsrdb_rango(
    anio_inicio: int,
    anio_fin: int,
    api_key: str,
    email: str,
    destino_dir: str | Path,
    lat: float = NSRDB_PUNTO_LAX["lat"],
    lon: float = NSRDB_PUNTO_LAX["lon"],
    logger=None,
    pausa_seg: float = 2.0,
    reintentos: int = 3,
    espera_reintento_seg: float = 5.0,
) -> ResumenDescarga:
    resumen = ResumenDescarga()

    if not api_key or not email:
        if logger:
            logger.error("NSRDB: falta API_KEY_NSRDB o EMAIL_NSRDB — no se pidió nada al servidor.")
        return resumen

    for anio in range(anio_inicio, anio_fin + 1):
        resumen.anios_solicitados += 1
        _, estado = descargar_nsrdb_anio(
            anio, api_key, email, destino_dir, lat, lon, reintentos=reintentos, espera_reintento_seg=espera_reintento_seg
        )

        if estado == "ok":
            resumen.anios_ok += 1
            if logger:
                logger.info(f"NSRDB {anio}: descargado")
            time.sleep(pausa_seg)
        elif estado == "ya_existente":
            resumen.anios_ya_existentes += 1
        elif estado.startswith("error_api"):
            resumen.anios_con_error += 1
            resumen.errores.append(anio)
            if logger:
                logger.error(f"NSRDB {anio}: {estado}")
        else:
            resumen.anios_con_error += 1
            resumen.errores.append(anio)
            if logger:
                logger.error(f"NSRDB {anio}: error de descarga tras {reintentos} intentos")

    return resumen
