# -*- coding: utf-8 -*-
"""
PUBLICADOR Y SINCRONIZADOR EN VIVO BLOGGER & MANYA SERVICIOTI — v11.0 (Zero-Hardcode)
=====================================================================================
NOTA DE ARQUITECTURA:
  Reemplaza la antigua versión fija de un único partido de octubre 2026 por un ejecutor
  100% dinámico que delega en `sync_manya_hub.py` + `blogger_manya_publisher.py`
  respetando idempotencia SQLite (`ManyaBloggerCatalog`) y ventanas `ScheduleSafety`.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
AUTOMATION_DIR = BASE_DIR / "automation"
if str(AUTOMATION_DIR) not in sys.path:
    sys.path.insert(0, str(AUTOMATION_DIR))

from manya_logging import get_manya_logger
from sync_manya_hub import ejecutar_sincronizacion_hub

logger = get_manya_logger("PublicarEnVivoBlogger")


def publicar_cobertura_en_vivo(auto_commit: bool = False) -> dict:
    """Sincroniza el partido activo en vivo y publica/actualiza Blogger de forma idempotente."""
    logger.info("=== PUBLICACIÓN EN VIVO ZERO-HARDCODE (DELEGANDO A MANYA SYNC HUB v11.0) ===")
    return ejecutar_sincronizacion_hub(mode="full", auto_commit=auto_commit)


if __name__ == "__main__":
    publicar_cobertura_en_vivo(auto_commit=False)
