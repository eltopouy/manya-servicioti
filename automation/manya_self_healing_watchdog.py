# -*- coding: utf-8 -*-
"""
GUARDIÁN DE AUTO-CURACIÓN Y SALUD CONTINUA — MANYA SERVICIOTI v11.0
===================================================================
Zero-Hardcode Self-Healing Watchdog:
  1. Limpia locks huérfanos (> 15 min) en `scratch/.locks` y `~/.manya_locks`.
  2. Ejecuta la suite de salud dinámica `test_manya_ecosystem.py`.
  3. Si detecta cualquier fallo o desfase (tablas, rival, fotos, prensa, SSR, 48h post-partido),
     ejecuta `sync_manya_hub.py --mode fast` para auto-reparar todo el ecosistema y vuelve a auditar.
  4. Solo sincroniza Git si hubo una reparación real verificada al 100%.
  5. Mantiene `logs/` y `data/health_status.json` fuera del árbol versionado (cero conflictos git).
"""

import sys
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
AUTOMATION_DIR = BASE_DIR / "automation"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
if str(AUTOMATION_DIR) not in sys.path:
    sys.path.insert(0, str(AUTOMATION_DIR))

from manya_logging import get_manya_logger

UY_TZ = timezone(timedelta(hours=-3))
logger = get_manya_logger("ManyaSelfHealing", log_file=LOGS_DIR / "self_healing.log")


class ManyaSelfHealingWatchdog:
    """Motor de auto-diagnóstico y auto-reparación continua sin hardcodes."""

    def __init__(self):
        self.reparaciones_realizadas: List[str] = []

    def auto_limpiar_locks_huerfanos(self) -> int:
        eliminados = 0
        now_ts = datetime.now().timestamp()
        for lock_dir in [Path.home() / ".manya_locks", BASE_DIR.parent / ".locks"]:
            if not lock_dir.exists():
                continue
            for lf in lock_dir.glob("*.lock"):
                try:
                    age = now_ts - lf.stat().st_mtime
                    if age > 900:
                        lf.unlink(missing_ok=True)
                        eliminados += 1
                        msg = f"Lock huérfano eliminado: {lf.name} ({round(age/60, 1)} min)"
                        self.reparaciones_realizadas.append(msg)
                        logger.info(f"[Auto-Healing] ✓ {msg}")
                except Exception:
                    pass
        return eliminados

    def ejecutar_ciclo_guardian(self, auto_push: bool = True) -> Dict[str, Any]:
        logger.info("=== INICIANDO GUARDIÁN DE AUTO-CURACIÓN MANYA v11.0 ===")
        self.auto_limpiar_locks_huerfanos()

        from test_manya_ecosystem import ManyaEcosystemTester
        tester = ManyaEcosystemTester()
        report = tester.run_all_tests()

        if report.get("pruebas_fallidas", 0) > 0:
            logger.warning(f"[Auto-Healing] Detectados {report['pruebas_fallidas']} fallo(s) (Score {report['score_salud']}%). Ejecutando auto-reparación integral...")
            try:
                from sync_manya_hub import ejecutar_sincronizacion_hub, semantic_git_sync
                ejecutar_sincronizacion_hub(mode="fast", auto_commit=False)
                self.reparaciones_realizadas.append("Re-sincronización integral ejecutada vía ManyaSyncHub (--mode fast)")

                # Re-evaluar salud tras reparación
                tester2 = ManyaEcosystemTester()
                report = tester2.run_all_tests()
                if report.get("pruebas_fallidas", 0) == 0 and auto_push:
                    semantic_git_sync("fix(auto-healing): sincronización y auto-reparación certificada 100% [skip ci]")
            except Exception as ex:
                logger.error(f"[Auto-Healing] Error durante auto-reparación: {ex}")
        else:
            logger.info(f"[Auto-Healing] ✓ Ecosistema íntegro al {report['score_salud']}% ({report['pruebas_exitosas']}/{report['total_pruebas']} PASS).")

        report["reparaciones_aplicadas"] = self.reparaciones_realizadas
        try:
            (DATA_DIR / "health_status.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

        logger.info(f"=== AUTO-CURACIÓN FINALIZADA. SCORE FINAL: {report.get('score_salud', 0)}% ===")
        return report


if __name__ == "__main__":
    watchdog = ManyaSelfHealingWatchdog()
    rep = watchdog.ejecutar_ciclo_guardian(auto_push=True)
    sys.exit(0 if rep.get("pruebas_fallidas", 0) == 0 else 1)
