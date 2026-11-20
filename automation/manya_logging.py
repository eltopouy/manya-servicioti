# -*- coding: utf-8 -*-
"""
Utilidad Centralizada de Logging Sin Duplicación — Manya ServicioTI v11.0
=========================================================================
Garantiza que cada módulo del ecosistema emita cada línea de log exactamente 1 vez:
  - Jamás llama a `logging.basicConfig()` a nivel de módulo (evita contaminar el root logger).
  - Fija `logger.propagate = False` en todos los loggers del proyecto.
  - Evita adjuntar handlers duplicados ante re-importaciones o ejecuciones repetidas.
  - Protege la codificación UTF-8 en consolas Windows (caracter 'é' en rutas y tildes).
"""

import sys
import logging
from pathlib import Path
from typing import Optional

LOG_FORMAT = "%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"


def configure_utf8_stdout() -> None:
    """Configura stdout/stderr en UTF-8 de forma segura para Windows."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass


def get_manya_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """
    Retorna un logger aislado (`propagate = False`) con un único StreamHandler
    en stdout y, opcionalmente, un único FileHandler deduplicado por ruta.
    """
    configure_utf8_stdout()
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(LOG_FORMAT)

    has_stream = any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        for h in logger.handlers
    )
    if not has_stream:
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    if log_file is not None:
        log_path = Path(log_file).resolve()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        has_file = any(
            isinstance(h, logging.FileHandler)
            and Path(getattr(h, "baseFilename", "")).resolve() == log_path
            for h in logger.handlers
        )
        if not has_file:
            fh = logging.FileHandler(log_path, encoding="utf-8")
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger
