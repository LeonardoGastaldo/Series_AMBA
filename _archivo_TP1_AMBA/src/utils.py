"""
Utilidades generales del proyecto Series_AMBA.

Funciones de: creación de la estructura de carpetas, información del entorno
de ejecución y configuración de logging. Usadas principalmente por
01_descarga_datos.ipynb, pero reutilizables desde cualquier notebook.
"""

from __future__ import annotations

import logging
import os
import platform
import sys
from pathlib import Path

# Estructura completa del proyecto. Se declara acá (y no repetida en cada
# notebook) para que exista una única fuente de verdad sobre qué carpetas
# componen el proyecto.
ESTRUCTURA_PROYECTO = [
    "data/raw/smn",
    "data/raw/cammesa/demanda_reciente_api",
    "data/raw/cammesa/sintesis_mensual_manual",
    "data/interim",
    "data/processed",
    "notebooks",
    "src",
    "outputs/figuras",
    "outputs/tablas",
    "outputs/modelos",
    "outputs/reportes",
    "docs",
    "logs",
]


def crear_estructura_proyecto(root: str | Path = ".") -> tuple[list[str], list[str]]:
    """Crea (si no existen) todas las carpetas de ESTRUCTURA_PROYECTO bajo `root`.

    Devuelve una tupla (creadas, existentes) con las rutas como string,
    para poder informar al usuario qué se creó de nuevo y qué ya estaba.
    """
    root = Path(root)
    creadas, existentes = [], []
    for carpeta in ESTRUCTURA_PROYECTO:
        destino = root / carpeta
        if destino.exists():
            existentes.append(str(destino))
        else:
            destino.mkdir(parents=True, exist_ok=True)
            creadas.append(str(destino))
    return creadas, existentes


def info_sistema(root: str | Path = ".") -> dict:
    """Recolecta información del entorno de ejecución para dejar constancia
    en el notebook de bajo qué condiciones se generaron los datos."""
    info = {
        "sistema_operativo": f"{platform.system()} {platform.release()}",
        "version_so_detallada": platform.version(),
        "version_python": sys.version.split()[0],
        "arquitectura": platform.machine(),
        "directorio_trabajo": str(Path(root).resolve()),
    }

    try:
        import psutil  # type: ignore

        mem = psutil.virtual_memory()
        info["memoria_total_gb"] = round(mem.total / (1024**3), 2)
        info["memoria_disponible_gb"] = round(mem.available / (1024**3), 2)
    except ImportError:
        info["memoria_total_gb"] = "psutil no instalado"
        info["memoria_disponible_gb"] = "psutil no instalado"

    return info


def configurar_logging(log_dir: str | Path = "logs", nombre: str = "descarga_datos") -> tuple[logging.Logger, Path]:
    """Configura un logger que escribe simultáneamente a consola y a un
    archivo de log persistente en `log_dir/{nombre}.log`.

    Se usa un logger con nombre propio (no el root logger) para no
    interferir con el logging de otras librerías (requests, urllib3, etc).
    """
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{nombre}.log"

    logger = logging.getLogger(nombre)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()  # evita duplicar handlers si la celda se re-ejecuta

    formato = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler_archivo = logging.FileHandler(log_path, encoding="utf-8")
    handler_archivo.setFormatter(formato)
    logger.addHandler(handler_archivo)

    handler_consola = logging.StreamHandler()
    handler_consola.setFormatter(formato)
    logger.addHandler(handler_consola)

    logger.propagate = False
    return logger, log_path
