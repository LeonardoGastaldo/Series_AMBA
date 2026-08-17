"""Utilidades comunes del proyecto: estructura de carpetas, logging, info de entorno."""

import logging
import platform
import sys
from pathlib import Path

import psutil


ESTRUCTURA_PROYECTO = [
    "data/raw/epa_aqs",
    "data/raw/noaa_isd",
    "data/raw/nsrdb",
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


def crear_estructura_proyecto(project_root: Path):
    creadas, existentes = [], []
    for carpeta in ESTRUCTURA_PROYECTO:
        destino = project_root / carpeta
        if destino.exists():
            existentes.append(destino)
        else:
            destino.mkdir(parents=True, exist_ok=True)
            creadas.append(destino)
    return creadas, existentes


def info_entorno():
    mem = psutil.virtual_memory()
    return {
        "sistema_operativo": platform.system() + " " + platform.release(),
        "version_so_detallada": platform.version(),
        "version_python": platform.python_version(),
        "arquitectura": platform.machine(),
        "memoria_total_gb": round(mem.total / (1024**3), 2),
        "memoria_disponible_gb": round(mem.available / (1024**3), 2),
    }


def configurar_logging(log_path: Path, nombre_logger: str = "descarga_datos"):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(nombre_logger)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formato = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formato)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formato)
    logger.addHandler(stream_handler)

    return logger
