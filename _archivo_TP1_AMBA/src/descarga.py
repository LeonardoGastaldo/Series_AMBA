"""
Funciones de descarga y parseo para las fuentes de datos del proyecto:

- SMN (Servicio Meteorológico Nacional): observaciones horarias por estación.
  Automatizable en su totalidad, con profundidad histórica confiable desde
  aproximadamente enero de 2018 hasta el día anterior a la fecha de ejecución.

- CAMMESA (demanda del SADI): la API pública sólo expone una ventana móvil
  reciente (aproximadamente los últimos 7 meses). Se documenta y automatiza
  esa ventana, pero NO reemplaza el histórico 2018-2024 requerido por el TP.

- CAMMESA (histórico horario de demanda y generación, "Síntesis Mensual"):
  no tiene un endpoint ni un enlace de descarga directa scrapeable (los
  botones de descarga del portal son JavaScript sin URL de archivo real).
  Por eso este módulo no "descarga" estos datos: sólo inventaría lo que el
  usuario haya guardado manualmente en data/raw/cammesa/sintesis_mensual_manual/,
  para validar que el pipeline tenga con qué seguir.

Ver notebooks/01_descarga_datos.ipynb para el detalle de por qué se llegó a
este diseño (resultado de una verificación real de los endpoints, no de una
suposición).
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# SMN — observaciones horarias
# ---------------------------------------------------------------------------

SMN_BASE_URL = "https://ssl.smn.gob.ar/dpd/descarga_opendata.php"
SMN_PRIMER_DIA_CONFIABLE = date(2018, 1, 1)
ESTACION_SMN_DEFAULT = "AEROPARQUE AERO"

# Formato verificado de las líneas de datos del archivo horario del SMN:
# "15012024     0  25.2   41  1010.9  240    6     AEROPARQUE AERO"
#   FECHA(ddmmyyyy)  HORA  TEMP(°C)  HUM(%)  PNM(hPa)  DD(°)  FF(km/h)  NOMBRE
_PATRON_LINEA_SMN = re.compile(
    r"^(?P<fecha>\d{8})\s+(?P<hora>\d{1,2})\s+(?P<temp>-?[\d.]+)\s+"
    r"(?P<hum>\d+)\s+(?P<pnm>[\d.]+)\s+(?P<dd>\d+)\s+(?P<ff>\d+)\s+(?P<nombre>.+?)\s*$"
)


@dataclass
class ResumenDescargaSMN:
    dias_solicitados: int = 0
    dias_ok: int = 0
    dias_ya_existentes: int = 0
    dias_sin_datos: int = 0
    dias_con_error: int = 0
    errores: list = field(default_factory=list)


def descargar_dia_smn(
    fecha: date,
    destino_dir: str | Path,
    timeout: int = 20,
    reintentos: int = 3,
    espera_reintento_seg: float = 5.0,
) -> tuple[Path | None, str]:
    """Descarga el archivo de observaciones horarias del SMN para un día puntual.

    Devuelve (ruta_archivo, estado), donde estado es uno de:
    "ok" | "ya_existente" | "sin_datos" | "error"

    El SMN publica un archivo de texto por día con TODAS las estaciones del
    país; se guarda tal cual (sin filtrar por estación) en data/raw para
    respetar el principio de no transformar los datos crudos. El filtro por
    estación se aplica recién al parsear (ver `parsear_archivo_smn`).

    Ante un error de red (timeout, conexión rechazada, etc.) reintenta hasta
    `reintentos` veces, esperando `espera_reintento_seg` entre intentos, antes
    de devolver "error". No reintenta cuando el SMN responde que el archivo
    no existe ("sin_datos"): eso no es un problema transitorio de red, es
    una respuesta válida del servidor.
    """
    destino_dir = Path(destino_dir)
    nombre_archivo = f"datohorario{fecha.strftime('%Y%m%d')}.txt"
    destino = destino_dir / nombre_archivo

    if destino.exists():
        return destino, "ya_existente"

    for intento in range(1, reintentos + 1):
        try:
            resp = requests.get(
                SMN_BASE_URL,
                params={"file": f"observaciones/{nombre_archivo}"},
                timeout=timeout,
            )
            resp.raise_for_status()
        except requests.RequestException:
            if intento < reintentos:
                time.sleep(espera_reintento_seg)
            continue

        contenido = resp.content
        # El SMN responde 200 OK con un cuerpo corto ("El archivo no existe.")
        # cuando no hay datos para esa fecha, en vez de devolver un 404.
        if len(contenido) < 200 or b"no existe" in contenido.lower():
            return None, "sin_datos"

        destino_dir.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(contenido)
        return destino, "ok"

    return None, "error"


def descargar_smn_rango(
    fecha_inicio: date,
    fecha_fin: date,
    destino_dir: str | Path,
    logger=None,
    pausa_seg: float = 0.3,
    reintentos: int = 3,
    espera_reintento_seg: float = 5.0,
) -> ResumenDescargaSMN:
    """Descarga (de forma resumible) un archivo por día del SMN entre
    fecha_inicio y fecha_fin, ambas inclusive.

    Es resumible: si el notebook se interrumpe y se vuelve a ejecutar, los
    días ya guardados en destino_dir se detectan y no se vuelven a pedir.
    `pausa_seg` evita golpear el servidor del SMN con cientos de pedidos
    consecutivos sin espera. Cada día que falle por un error de red se
    reintenta internamente hasta `reintentos` veces (ver `descargar_dia_smn`)
    antes de contarlo como error definitivo en el resumen.
    """
    resumen = ResumenDescargaSMN()
    dia = fecha_inicio
    while dia <= fecha_fin:
        resumen.dias_solicitados += 1
        _, estado = descargar_dia_smn(
            dia, destino_dir, reintentos=reintentos, espera_reintento_seg=espera_reintento_seg
        )

        if estado == "ok":
            resumen.dias_ok += 1
            if logger:
                logger.info(f"SMN {dia.isoformat()}: descargado")
            time.sleep(pausa_seg)
        elif estado == "ya_existente":
            resumen.dias_ya_existentes += 1
        elif estado == "sin_datos":
            resumen.dias_sin_datos += 1
            if logger:
                logger.warning(f"SMN {dia.isoformat()}: sin datos en el servidor")
        else:
            resumen.dias_con_error += 1
            resumen.errores.append(dia.isoformat())
            if logger:
                logger.error(f"SMN {dia.isoformat()}: error de descarga tras {reintentos} intentos")

        dia += timedelta(days=1)

    return resumen


def parsear_archivo_smn(path: str | Path, estacion: str = ESTACION_SMN_DEFAULT):
    """Parsea un archivo diario crudo del SMN y filtra por estación.

    Devuelve una lista de dicts con: fecha (date), hora (int), temperatura_C,
    humedad_pct, presion_hpa, direccion_viento_gr, velocidad_viento_kmh.
    Se usa una lista de dicts (no un DataFrame) para no forzar una dependencia
    de pandas dentro de este módulo de bajo nivel; el notebook arma el
    DataFrame consolidado a partir de estas filas.
    """
    registros = []
    texto = Path(path).read_text(encoding="latin-1", errors="ignore")

    for linea in texto.splitlines():
        m = _PATRON_LINEA_SMN.match(linea)
        if not m:
            continue  # líneas de encabezado / unidades
        if estacion not in m.group("nombre").strip():
            continue

        fecha_str = m.group("fecha")  # ddmmyyyy
        registros.append(
            {
                "fecha": date(int(fecha_str[4:8]), int(fecha_str[2:4]), int(fecha_str[0:2])),
                "hora": int(m.group("hora")),
                "temperatura_C": float(m.group("temp")),
                "humedad_pct": int(m.group("hum")),
                "presion_hpa": float(m.group("pnm")),
                "direccion_viento_gr": int(m.group("dd")),
                "velocidad_viento_kmh": int(m.group("ff")),
            }
        )

    return registros


# ---------------------------------------------------------------------------
# CAMMESA — demanda reciente vía API pública (ventana móvil, NO histórico)
# ---------------------------------------------------------------------------

CAMMESA_DEMANDA_URL = "https://api.cammesa.com/demanda-svc/demanda/ObtieneDemandaYTemperaturaRegionByFecha"
CAMMESA_REGIONES = {
    "SADI": 1002,  # sistema completo
    "GBA": 426,  # Edenor + Edesur + Edelap -> mejor proxy disponible del AMBA
}


def descargar_cammesa_demanda_dia(fecha: date, id_region: int, destino_dir: str | Path, timeout: int = 20):
    """Descarga la demanda (y temperatura) de 5 minutos que CAMMESA expone
    para un día puntual, dentro de su ventana móvil reciente.

    Importante: si `fecha` cae fuera de esa ventana (verificado empíricamente
    en ~7 meses hacia atrás desde hoy), la API responde una lista vacía `[]`,
    NO un error. Por eso esta función devuelve explícitamente el estado
    "fuera_de_ventana" para que quien la use no lo confunda con "sin viento".
    """
    destino_dir = Path(destino_dir)
    nombre_archivo = f"demanda_{id_region}_{fecha.strftime('%Y%m%d')}.json"
    destino = destino_dir / nombre_archivo

    if destino.exists():
        return destino, "ya_existente"

    try:
        resp = requests.get(
            CAMMESA_DEMANDA_URL,
            params={"fecha": fecha.isoformat(), "id_region": id_region},
            timeout=timeout,
        )
        resp.raise_for_status()
    except requests.RequestException:
        return None, "error"

    datos = resp.json()
    if not datos:
        return None, "fuera_de_ventana"

    destino_dir.mkdir(parents=True, exist_ok=True)
    destino.write_text(resp.text, encoding="utf-8")
    return destino, "ok"


def descargar_cammesa_demanda_reciente(
    fecha_inicio: date,
    fecha_fin: date,
    destino_dir: str | Path,
    id_region: int = CAMMESA_REGIONES["GBA"],
    logger=None,
    pausa_seg: float = 0.3,
) -> ResumenDescargaSMN:
    """Igual que descargar_smn_rango pero para la ventana reciente de CAMMESA.

    Se reutiliza la misma dataclass de resumen (ResumenDescargaSMN) porque la
    forma de contabilizar es idéntica; el nombre genérico se mantiene por
    simplicidad ya que ambos representan "resumen de una descarga por rango
    de fechas, día a día".
    """
    resumen = ResumenDescargaSMN()
    dia = fecha_inicio
    while dia <= fecha_fin:
        resumen.dias_solicitados += 1
        _, estado = descargar_cammesa_demanda_dia(dia, id_region, destino_dir)

        if estado == "ok":
            resumen.dias_ok += 1
            if logger:
                logger.info(f"CAMMESA demanda {dia.isoformat()}: descargado")
            time.sleep(pausa_seg)
        elif estado == "ya_existente":
            resumen.dias_ya_existentes += 1
        elif estado == "fuera_de_ventana":
            resumen.dias_sin_datos += 1
        else:
            resumen.dias_con_error += 1
            resumen.errores.append(dia.isoformat())
            if logger:
                logger.error(f"CAMMESA demanda {dia.isoformat()}: error de descarga")

        dia += timedelta(days=1)

    return resumen


# ---------------------------------------------------------------------------
# CAMMESA — histórico horario de demanda y generación (adquisición MANUAL)
# ---------------------------------------------------------------------------

# Se comprobó que:
#   - "Demanda Horaria por Tipo" (cammesaweb.cammesa.com/download/demanda-horaria/)
#   - "Síntesis Mensual" (cammesaweb.cammesa.com/informe-sintesis-mensual/),
#     que según su propia descripción incluye datos en paso horario de
#     demanda y generación,
# exponen sus descargas mediante un botón de JavaScript sin URL de archivo
# real detrás (href="#"), por lo que no son automatizables con requests/
# BeautifulSoup sin simular un navegador completo (Selenium/Playwright),
# lo cual excede el alcance de este notebook. La vía elegida es documentar
# el paso manual y automatizar sólo la VALIDACIÓN de lo descargado.

CAMMESA_URL_SINTESIS_MENSUAL = "https://cammesaweb.cammesa.com/informe-sintesis-mensual/"


def inventariar_cammesa_manual(directorio: str | Path) -> list[dict]:
    """Recorre el directorio donde el usuario guarda manualmente los archivos
    de "Síntesis Mensual" descargados desde el portal de CAMMESA, y arma un
    inventario simple para saber qué meses ya están disponibles y cuáles
    faltan antes de pasar a 02_limpieza.ipynb.
    """
    directorio = Path(directorio)
    directorio.mkdir(parents=True, exist_ok=True)

    inventario = []
    for archivo in sorted(directorio.glob("*")):
        if archivo.is_file() and not archivo.name.startswith("."):
            inventario.append(
                {
                    "archivo": archivo.name,
                    "tamano_kb": round(archivo.stat().st_size / 1024, 1),
                }
            )
    return inventario
