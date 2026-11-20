# -*- coding: utf-8 -*-
"""
PIPELINE DINÁMICO POST-PARTIDO — v3.0 (Zero-Hardcode)
=====================================================
Reemplaza el antiguo pipeline estático de Wanderers 1-1 (Oct 2026) por un ejecutor
100% dinámico conectado al Orquestador Maestro `sync_manya_hub.py`.
"""

import sys
import logging
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger = logging.getLogger("PostMatchPipeline")
if not logger.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "automation"))


class ManyaPostMatchPipeline:
    """Orquestador post-partido dinámico (delega a MatchEngine + 1891 BD + Narrativa + Hub)."""

    def ejecutar_pipeline_completo(self, publicar_blogger: bool = False, hacer_push: bool = False) -> dict:
        logger.info("=== EJECUTANDO PIPELINE POST-PARTIDO DINÁMICO v3.0 ===")
        from sync_manya_hub import ejecutar_sincronizacion_hub
        modo = "full" if publicar_blogger else "fast"
        return ejecutar_sincronizacion_hub(mode=modo, auto_commit=hacer_push)


if __name__ == "__main__":
    ManyaPostMatchPipeline().ejecutar_pipeline_completo(publicar_blogger=False, hacer_push=False)
