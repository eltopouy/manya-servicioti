# -*- coding: utf-8 -*-
"""
PIPELINE DINÁMICO POST-PARTIDO — v4.0 (Manya v11.0 Zero-Hardcode)
=================================================================
Ejecutor 100% dinámico de cierre post-partido conectado al Orquestador Maestro
`sync_manya_hub.py` (MatchEngine v5.0 + 1891 BD + Narrativa + Prensa + SSR).
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
AUTOMATION_DIR = BASE_DIR / "automation"
if str(AUTOMATION_DIR) not in sys.path:
    sys.path.insert(0, str(AUTOMATION_DIR))

from manya_logging import get_manya_logger

logger = get_manya_logger("PostMatchPipeline")


class ManyaPostMatchPipeline:
    """Orquestador post-partido dinámico (delega a MatchEngine + 1891 BD + Narrativa + Hub)."""

    def ejecutar_pipeline_completo(self, publicar_blogger: bool = False, hacer_push: bool = False) -> dict:
        logger.info("=== EJECUTANDO PIPELINE POST-PARTIDO DINÁMICO v4.0 (MANYA v11.0) ===")
        from sync_manya_hub import ejecutar_sincronizacion_hub
        modo = "full" if publicar_blogger else "fast"
        return ejecutar_sincronizacion_hub(mode=modo, auto_commit=hacer_push)


if __name__ == "__main__":
    ManyaPostMatchPipeline().ejecutar_pipeline_completo(publicar_blogger=False, hacer_push=False)
