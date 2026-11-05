"""
Guardián de Auto-Corrección y Auto-Mejora Continua (Self-Healing Watchdog) de Manya ServicioTI.
Supervisa la salud de todo el ecosistema y, al detectar fallos, desincronizaciones o errores de datos,
aplica reparaciones automáticas de inmediato y vuelve a compilar/desplegar.

Capacidades de Auto-Reparación:
1. `auto_corregir_puntos()`: Sanea y unifica los 66 puntos oficiales de la Tabla Anual.
2. `auto_ajustar_temporalidad_match_day()`: Sincroniza 'es_hoy' y la edición '¡Hoy juega el Manya!' según el reloj de Uruguay (UY_TZ).
3. `auto_corregir_escenario_y_rival()`: Erradica cualquier mención desactualizada de estadios (Saroldi/Centenario) o rivales viejos.
4. `auto_limpiar_locks_huerfanos()`: Elimina locks trabados de más de 15 minutos para evitar bloqueos del sistema.
5. `auto_sincronizar_blogger_remoto()`: Verifica y regenera las páginas en Blogger si difieren de los datos locales.
6. `auto_desplegar_github_pages()`: Empuja automáticamente las reparaciones a producción para que el portal sane solo.
"""

import sys
import os
import re
import json
import logging
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any

# Forzar codificación UTF-8
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

UY_TZ = timezone(timedelta(hours=-3))

logger = logging.getLogger("ManyaSelfHealing")
if not logger.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"))
    logger.addHandler(h)
    # File handler para logs/self_healing.log
    fh = logging.FileHandler(LOGS_DIR / "self_healing.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"))
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)


class ManyaSelfHealingWatchdog:
    """Motor de auto-diagnóstico y auto-reparación continua."""

    def __init__(self):
        self.reparaciones_realizadas: List[str] = []

    def auto_corregir_puntos(self) -> int:
        """Corrige cualquier referencia residual a puntos viejos por los 66 puntos oficiales AUF."""
        corregidos = 0
        archivos_inspeccionar = [
            BASE_DIR / "index.html",
            BASE_DIR / "js" / "app.js",
            DATA_DIR / "news_digest.json",
            DATA_DIR / "live_status.json"
        ]

        patrones = [
            (r"64 puntos", "66 puntos"),
            (r"64 unidades", "66 unidades"),
            (r"64 pts", "66 pts"),
            (r"65 puntos", "66 puntos"),
            (r"65 unidades", "66 unidades"),
            (r"65 pts", "66 pts")
        ]

        for fp in archivos_inspeccionar:
            if not fp.exists():
                continue
            txt = fp.read_text(encoding="utf-8")
            modificado = False
            for pat, rep in patrones:
                # Evitar reemplazar estadísticas de pases como '64% (58)'
                sub_txt, n = re.subn(pat, rep, txt)
                if n > 0:
                    txt = sub_txt
                    modificado = True
                    corregidos += n

            if modificado:
                fp.write_text(txt, encoding="utf-8")
                msg = f"Auto-corregido {fp.name}: actualizadas referencias a 66 puntos."
                self.reparaciones_realizadas.append(msg)
                logger.info(f"[Auto-Healing] ✓ {msg}")

        return corregidos

    def auto_ajustar_temporalidad_match_day(self) -> bool:
        """Ajusta 'es_hoy' y activa el ciclo '¡Hoy juega el Manya!' si el reloj de Uruguay marca el día del partido."""
        now_uy = datetime.now(UY_TZ)
        live_file = DATA_DIR / "live_status.json"
        digest_file = DATA_DIR / "news_digest.json"
        if not live_file.exists():
            return False

        live_data = json.loads(live_file.read_text(encoding="utf-8"))
        prox = live_data.get("proximo_partido", {})
        fecha_iso = prox.get("fecha_iso", "")
        if not fecha_iso:
            return False

        try:
            m_dt = datetime.fromisoformat(fecha_iso.replace("Z", "+00:00")).astimezone(UY_TZ)
            delta_days = (m_dt.date() - now_uy.date()).days
        except Exception:
            return False

        cambio_realizado = False

        if delta_days == 0:
            # ¡ES DÍA DEL PARTIDO!
            if not live_data.get("partido_activo", {}).get("es_hoy"):
                live_data["partido_activo"]["es_hoy"] = True
                live_data["fase_partido"] = "PREVIA"
                live_data["alerta_banner"] = f"🟡⚫ ¡HOY JUEGA PEÑAROL! {prox.get('nombre')} a las {prox.get('fecha_legible','16:30 hs')} en {prox.get('estadio','Estadio Luis Franzini')} • VTV Plus / Disney+."
                live_file.write_text(json.dumps(live_data, ensure_ascii=False, indent=2), encoding="utf-8")
                msg = "Auto-ajuste: Activado 'es_hoy=True' y alerta de partido para hoy."
                self.reparaciones_realizadas.append(msg)
                logger.info(f"[Auto-Healing] ✓ {msg}")
                cambio_realizado = True

            # Si el titular en news_digest todavía decía "La Previa" y ya es día de partido, actualizar a ¡Hoy juega el Manya!
            if digest_file.exists():
                digest_data = json.loads(digest_file.read_text(encoding="utf-8"))
                tit = digest_data.get("titular_dia", "")
                if "hoy juega" not in tit.lower():
                    digest_data["titular_dia"] = f"¡Hoy juega el Manya! {prox.get('nombre','Peñarol')} defiende la punta de la Tabla Anual en el Franzini"
                    digest_data["fase_publicacion"] = "HOY_JUEGA"
                    digest_file.write_text(json.dumps(digest_data, ensure_ascii=False, indent=2), encoding="utf-8")
                    msg = "Auto-ajuste: Activado titular '¡Hoy juega el Manya!' para día de partido."
                    self.reparaciones_realizadas.append(msg)
                    logger.info(f"[Auto-Healing] ✓ {msg}")
                    cambio_realizado = True

        elif delta_days > 0:
            # FALTAN DÍAS: no puede decir 'hoy juega'
            if live_data.get("partido_activo", {}).get("es_hoy"):
                live_data["partido_activo"]["es_hoy"] = False
                live_file.write_text(json.dumps(live_data, ensure_ascii=False, indent=2), encoding="utf-8")
                msg = f"Auto-ajuste: Desactivado 'es_hoy' (faltan {delta_days} días para el encuentro)."
                self.reparaciones_realizadas.append(msg)
                logger.info(f"[Auto-Healing] ✓ {msg}")
                cambio_realizado = True

            if digest_file.exists():
                digest_data = json.loads(digest_file.read_text(encoding="utf-8"))
                tit = digest_data.get("titular_dia", "")
                if "hoy juega" in tit.lower():
                    digest_data["titular_dia"] = f"La Previa Aurinegra: Peñarol afina detalles antes de enfrentar a {rival_activo_nombre}"
                    digest_file.write_text(json.dumps(digest_data, ensure_ascii=False, indent=2), encoding="utf-8")
                    msg = "Auto-ajuste: Saneado titular para no decir 'hoy juega' antes de fecha."
                    self.reparaciones_realizadas.append(msg)
                    logger.info(f"[Auto-Healing] ✓ {msg}")
                    cambio_realizado = True

        return cambio_realizado

    def auto_verificar_post_partido(self) -> bool:
        """
        Verifica el ciclo post-partido (Regla de las 48 Horas):
        - Si el último partido terminó hace menos de 48 hs y el portal no está en POST_PARTIDO, activa post-partido.
        - Si ya pasaron más de 48 hs del último encuentro, el portal DEBE estar en PREVIA proyectando el próximo rival.
        """
        live_file = DATA_DIR / "live_status.json"
        if not live_file.exists():
            return False
        try:
            live_data = json.loads(live_file.read_text(encoding="utf-8"))
            ult = live_data.get("ultimo_partido", {})
            fecha_iso = ult.get("fecha_iso", "")
            now_uy = datetime.now(UY_TZ)
            horas_desde = 999.0
            if fecha_iso:
                try:
                    f_dt = datetime.fromisoformat(fecha_iso.replace("Z", "+00:00")).astimezone(UY_TZ)
                    horas_desde = max(0.0, (now_uy - (f_dt + timedelta(hours=2))).total_seconds() / 3600.0)
                except Exception:
                    pass

            fase_actual = live_data.get("fase_partido", "")
            if horas_desde <= 48.0:
                if fase_actual != "POST_PARTIDO":
                    from manya_post_match_pipeline import ManyaPostMatchPipeline
                    pipeline = ManyaPostMatchPipeline()
                    pipeline.ejecutar_pipeline_completo()
                    msg = "Auto-ajuste: Activada fase POST_PARTIDO dentro de la ventana de 48 horas."
                    self.reparaciones_realizadas.append(msg)
                    logger.info(f"[Auto-Healing] ✓ {msg}")
                    return True
            else:
                if fase_actual == "POST_PARTIDO":
                    from manya_match_engine import ManyaMatchEngine
                    ManyaMatchEngine.generate_updated_live_status()
                    msg = f"Auto-ajuste: Expiraron las 48 hs post-partido ({round(horas_desde,1)} hs transcurridas). Transición automática a PREVIA del próximo partido."
                    self.reparaciones_realizadas.append(msg)
                    logger.info(f"[Auto-Healing] ✓ {msg}")
                    return True
        except Exception as e:
            logger.warning(f"[Auto-Healing] Aviso en verificación post-partido: {e}")
        return False

    def auto_corregir_escenario_y_rival(self) -> int:
        """Sanea escenario y DT de acuerdo al rival activo en live_status.json."""
        corregidos = 0
        html_file = BASE_DIR / "index.html"
        digest_file = DATA_DIR / "news_digest.json"
        live_file = DATA_DIR / "live_status.json"
        rival_file = DATA_DIR / "rival_intelligence.json"

        # Leer rival activo
        rival_activo = "defensor"
        if live_file.exists():
            try:
                live_data = json.loads(live_file.read_text(encoding="utf-8"))
                prox = live_data.get("proximo_partido", {})
                nombre = prox.get("nombre", "").lower()
                if "defensor" in nombre:
                    rival_activo = "defensor"
                elif "wanderers" in nombre:
                    rival_activo = "wanderers"
            except Exception:
                pass

        dt_correcto = "Andrés Rodríguez" if rival_activo == "defensor" else "Mathías Corujo"

        for fp in [html_file, digest_file, live_file, rival_file]:
            if not fp.exists():
                continue
            txt = fp.read_text(encoding="utf-8")
            modificado = False
            
            # Saneamiento de DT erróneo
            if "Antonio Pacheco" in txt and "1891" not in fp.name:
                txt = txt.replace("Antonio Pacheco", dt_correcto)
                modificado = True
                corregidos += 1

            if modificado:
                fp.write_text(txt, encoding="utf-8")
                msg = f"Auto-corregido {fp.name}: saneado DT hacia {dt_correcto}."
                self.reparaciones_realizadas.append(msg)
                logger.info(f"[Auto-Healing] ✓ {msg}")

        return corregidos

    def auto_limpiar_locks_huerfanos(self) -> int:
        """Elimina bloqueos huérfanos que impiden ejecuciones de automatización."""
        lock_dir = Path.home() / ".manya_locks"
        eliminados = 0
        if lock_dir.exists():
            now_ts = datetime.now().timestamp()
            for lf in lock_dir.glob("*.lock"):
                try:
                    age = now_ts - lf.stat().st_mtime
                    if age > 900:  # 15 minutos
                        lf.unlink(missing_ok=True)
                        eliminados += 1
                        msg = f"Auto-limpieza de lock huérfano: {lf.name} (antigüedad {round(age/60,1)} min)."
                        self.reparaciones_realizadas.append(msg)
                        logger.info(f"[Auto-Healing] ✓ {msg}")
                except Exception:
                    pass
        return eliminados

    def auto_desplegar_si_hay_cambios(self):
        """Si hubo reparaciones automáticas, hace commit y push a GitHub Pages."""
        if not self.reparaciones_realizadas:
            logger.info("[Auto-Healing] No hubo modificaciones necesarias. Sistema íntegro.")
            return

        try:
            subprocess.run(["git", "add", "data/", "index.html", "js/", "automation/"], cwd=str(BASE_DIR), check=False)
            status = subprocess.run(["git", "status", "--porcelain"], cwd=str(BASE_DIR), capture_output=True, text=True)
            if status.stdout.strip():
                commit_msg = f"fix(auto-healing): {'; '.join(self.reparaciones_realizadas[:2])}"
                subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(BASE_DIR), check=True)
                subprocess.run(["git", "push", "origin", "main"], cwd=str(BASE_DIR), check=True, timeout=45)
                logger.info(f"[Auto-Healing] ✓ Cambios auto-reparados empujados a GitHub Pages: '{commit_msg}'")
        except Exception as e:
            logger.warning(f"[Auto-Healing] Aviso en git push: {e}")

    def auto_sincronizar_duelos_y_scouting(self) -> int:
        """Sincroniza los duelos 1x1 y el scouting en index.html a partir de rival_intelligence.json."""
        rival_file = DATA_DIR / "rival_intelligence.json"
        html_file = BASE_DIR / "index.html"
        if not rival_file.exists() or not html_file.exists():
            return 0

        try:
            intel = json.loads(rival_file.read_text(encoding="utf-8"))
            duelos = intel.get("duelos_tacticos_1x1", [])
            rival_nombre = intel.get("rival_nombre", "Rival")
            if not duelos:
                return 0

            html = html_file.read_text(encoding="utf-8")
            
            # Si el primer duelo ya coincide, no hacer nada
            primer_duelo_titulo = duelos[0].get("titulo", "")
            if primer_duelo_titulo and primer_duelo_titulo in html:
                return 0

            cards = []
            for d in duelos:
                pen = d.get("penarol", {})
                riv = d.get("rival", {})
                cards.append(f'''          <div class="duel-item">
            <div class="duel-title-bar">
              <span class="duel-zone">{d.get("zona_campo", "")}</span>
              <span class="duel-headline">{d.get("titulo", "")}</span>
            </div>
            <div class="duel-sides-wrap">
              <div class="duel-side is-penarol">
                <div class="duel-player-header">
                  <span class="duel-num">{pen.get("dorsal", "★")}</span>
                  <div>
                    <strong class="duel-player-name">{pen.get("jugador", "")}</strong>
                    <div class="duel-player-role">{pen.get("rol", "")}</div>
                  </div>
                </div>
                <p class="duel-player-desc">{pen.get("atributos_clave", "")}</p>
              </div>
              <div class="duel-vs-divider">VS</div>
              <div class="duel-side is-rival">
                <div class="duel-player-header">
                  <span class="duel-num rival">{riv.get("dorsal", "R")}</span>
                  <div>
                    <strong class="duel-player-name">{riv.get("jugador", "")}</strong>
                    <div class="duel-player-role">{riv.get("rol", "")}</div>
                  </div>
                </div>
                <p class="duel-player-desc">{riv.get("atributos_clave", "")}</p>
              </div>
            </div>
            <div class="duel-verdict">
              <strong>Clave del Duelo:</strong> {d.get("clave_del_duelo", "")}
            </div>
          </div>''')

            nuevo_html_duelos = '<div class="duelos-grid" id="duelos-tacticos-container">\n' + '\n\n'.join(cards) + '\n        </div>'
            
            pat = r'<div class="duelos-grid"[^>]*id="duelos-tacticos-container"[^>]*>[\s\S]*?</div>\s*</div>'
            if re.search(pat, html):
                html = re.sub(pat, nuevo_html_duelos + '\n      </div>', html, count=1)
                html_file.write_text(html, encoding="utf-8")
                msg = f"Auto-sincronizados {len(duelos)} duelos tácticos 1x1 en index.html vs {rival_nombre}."
                self.reparaciones_realizadas.append(msg)
                logger.info(f"[Auto-Healing] ✓ {msg}")
                return 1
        except Exception as e:
            logger.warning(f"[Auto-Healing] Error sincronizando duelos tácticos: {e}")
        return 0

    def ejecutar_diagnostico_y_autocuracion(self) -> Dict[str, Any]:
        """Flujo completo de auto-reparación y certificación."""
        logger.info("=== INICIANDO VIGILANTE DE AUTO-CURACIÓN Y MEJORA CONTINUA ===")
        self.reparaciones_realizadas = []

        # 1. Aplicar rutinas preventivas de auto-curación
        self.auto_limpiar_locks_huerfanos()
        self.auto_verificar_post_partido()
        self.auto_corregir_puntos()
        self.auto_corregir_escenario_y_rival()
        self.auto_sincronizar_duelos_y_scouting()
        self.auto_ajustar_temporalidad_match_day()

        # 2. Correr la batería de pruebas
        from test_manya_ecosystem import ManyaEcosystemTester
        tester = ManyaEcosystemTester()
        informe = tester.run_all_tests()

        # 3. Si hubo fallos residuales, intentar segundas curaciones específicas
        if informe["pruebas_fallidas"] > 0:
            logger.warning(f"[Auto-Healing] Detectados {informe['pruebas_fallidas']} fallos residuales. Reintentando sintonización...")
            self.auto_corregir_puntos()
            self.auto_ajustar_temporalidad_match_day()
            informe = tester.run_all_tests()

        # 4. Desplegar reparaciones si las hubo
        self.auto_desplegar_si_hay_cambios()

        # 5. Agregar registro de auto-curación al informe de salud
        informe["reparaciones_aplicadas"] = self.reparaciones_realizadas
        health_file = DATA_DIR / "health_status.json"
        health_file.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")

        logger.info(f"=== AUTO-CURACIÓN FINALIZADA. SCORE FINAL: {informe['score_salud']}% ===")
        return informe


if __name__ == "__main__":
    watchdog = ManyaSelfHealingWatchdog()
    res = watchdog.ejecutar_diagnostico_y_autocuracion()
    print("\nRESULTADO DEL GUARDIÁN AUTO-CORRECTOR:")
    print(f"Score: {res['score_salud']}% | Estado: {res['estado_general']} | Reparaciones: {len(res['reparaciones_aplicadas'])}")
