# -*- coding: utf-8 -*-
"""
COMPATIBILIDAD / SHIM DE ORQUESTACIÓN — actualizar_manya_completo.py (v11.0 Zero-Hardcode)
==========================================================================================
NOTA DE ARQUITECTURA:
  La antigua implementación monolítica de este archivo (con datos estáticos de fechas pasadas
  y ex-jugadores) fue reemplazada por el Orquestador Maestro Idempotente `sync_manya_hub.py`.

  Este script se conserva como capa de compatibilidad segura para lanzadores heredados
  (como `ejecutar_manya_diario.bat`), delegando el 100% del trabajo a `sync_manya_hub.py`.
"""

import sys
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
AUTOMATION_DIR = BASE_DIR / "automation"
if str(AUTOMATION_DIR) not in sys.path:
    sys.path.insert(0, str(AUTOMATION_DIR))

from manya_logging import get_manya_logger
from sync_manya_hub import ejecutar_sincronizacion_hub

logger = get_manya_logger("ActualizarManyaCompat")


def main(mode: str = "full", auto_commit: bool = False) -> dict:
    logger.warning(
        "[Compat] `actualizar_manya_completo.py` fue reemplazado por `sync_manya_hub.py` v11.0. "
        "Delegando ejecución segura al Orquestador Maestro Zero-Hardcode..."
    )
    return ejecutar_sincronizacion_hub(mode=mode, auto_commit=auto_commit)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compatibilidad hacia Manya Sync Hub v11.0")
    parser.add_argument("--mode", choices=["fast", "ci", "full"], default="full")
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()
    main(mode=args.mode, auto_commit=args.commit)
