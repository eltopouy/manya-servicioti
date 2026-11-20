# -*- coding: utf-8 -*-
"""
DAEMON Y ORQUESTADOR DE PARTIDOS Y PRENSA — MANYA SERVICIOTI v11.0
==================================================================
Delega toda la lógica central en el Orquestador Maestro Idempotente (`sync_manya_hub.py`)
respetando:
  - Anti-colisión con tareas matutinas de ServicioTI (05:25 - 07:15 UY).
  - Idempotencia estricta por (event_id, fase) en Blogger y redacción IA (cero duplicados).
  - Git Sync Semántico Anti-Spam (jamás hace commits repetidos cuando nada cambió).
  - Polling adaptativo en modo `--daemon` (3 min EN_VIVO, 15 min PREVIA, 60 min reposo).

Modos de uso:
  python automation/manya_partidos_daemon.py --once
  python automation/manya_partidos_daemon.py --daemon
  python automation/manya_partidos_daemon.py --hoy-juega
"""

import sys
import time
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
AUTOMATION_DIR = BASE_DIR / "automation"
if str(AUTOMATION_DIR) not in sys.path:
    sys.path.insert(0, str(AUTOMATION_DIR))
UY_TZ = timezone(timedelta(hours=-3))

from manya_logging import get_manya_logger
from manya_anti_collision import CentralAutomationLock
from sync_manya_hub import ejecutar_sincronizacion_hub

logger = get_manya_logger("ManyaDaemon")


def ejecutar_orquestador(modo: str = "once", hoy_juega: bool = False):
    logger.info("=" * 70)
    logger.info(f"=== VIGILANTE DE PARTIDOS Y PRENSA MANYA v11.0 (MODO: {'HOY-JUEGA' if hoy_juega else modo.upper()}) ===")
    logger.info("=" * 70)

    while True:
        fase = "PREVIA"
        try:
            with CentralAutomationLock.acquire("manya_sync_hub", timeout_sec=60):
                res = ejecutar_sincronizacion_hub(
                    mode="hoy-juega" if hoy_juega else "full",
                    auto_commit=True,
                    force_editorial=hoy_juega
                )
                fase = (res.get("live") or {}).get("fase_partido", "PREVIA")
        except Exception as e:
            logger.error(f"[ManyaDaemon] Error en ciclo: {e}", exc_info=True)

        if modo == "once" or hoy_juega:
            logger.info("[ManyaDaemon] ✓ Ciclo único completado.")
            break

        if fase == "EN_VIVO":
            time.sleep(180)
        elif fase == "PREVIA":
            time.sleep(900)
        else:
            time.sleep(3600)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daemon de partidos y prensa Manya ServicioTI v11.0")
    parser.add_argument("--daemon", action="store_true", help="Ejecutar en modo continuo")
    parser.add_argument("--once", action="store_true", help="Ejecutar un solo ciclo y salir")
    parser.add_argument("--hoy-juega", action="store_true", help="Ejecutar revisión de madrugada 00:05 hs")
    args = parser.parse_args()

    ejecutar_orquestador(modo="daemon" if args.daemon else "once", hoy_juega=args.hoy_juega)
