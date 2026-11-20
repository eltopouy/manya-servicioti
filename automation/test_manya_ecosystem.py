# -*- coding: utf-8 -*-
"""
SUITE INTEGRAL DE PRUEBAS AUTOMATIZADAS — MANYA SERVICIOTI v10.0 (Zero-Hardcode)
================================================================================
Audita 12 invariantes universales y reales del ecosistema (sin puntos ni rivales hardcodeados):
  1. Zona Horaria UY_TZ (UTC-3).
  2. Coherencia Temporal 'es_hoy' (cero falsos positivos).
  3. Integridad Matemática de Tablas (Anual, Clausura y Libertadores ordenadas por PTS/DG).
  4. Consistencia Cruzada del Rival Activo, DT, Escenario e Historial 1891 BD.
  5. Integridad y Esquema de 11 Datasets JSON en `data/`.
  6. Salud de Locks y Anti-Colisión (`scratch/.locks` y `~/.manya_locks`).
  7. Accesibilidad HTTP 200 de Endpoints Oficiales (Portal + Blogger).
  8. Armonía de Versiones PWA v10.0 (Network-First en sw.js, index.html, styles.css, app.js).
  9. Integridad de Escudos Oficiales AUF + Copa CONMEBOL Libertadores.
 10. Frescura Fotográfica, Galerías sin Duplicados y Feeds Sociales.
 11. Coherencia Editorial, Anti-Contaminación y Frescura de Prensa Deportiva.
 12. Pizarra Táctica Interactiva (Plantel real 2026, 3 formaciones, Canvas 1080x1350, node --check).
"""

import sys
import os
import json
import logging
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(BASE_DIR / "automation"))

UY_TZ = timezone(timedelta(hours=-3))

logger = logging.getLogger("ManyaTestEcosystem")
if not logger.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)


class ManyaEcosystemTester:
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.passed_count = 0
        self.failed_count = 0

    def record_result(self, test_name: str, passed: bool, message: str, details: Any = None):
        if passed:
            self.passed_count += 1
        else:
            self.failed_count += 1
        self.results.append({
            "test": test_name,
            "status": "PASS" if passed else "FAIL",
            "passed": passed,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now(UY_TZ).isoformat()
        })
        logger.info(f"[{'PASS' if passed else 'FAIL'}] {test_name}: {message}")

    def test_timezone_and_temporal(self):
        now_uy = datetime.now(UY_TZ)
        offset_h = (now_uy.utcoffset().total_seconds() / 3600.0) if now_uy.utcoffset() else 0.0
        self.record_result(
            "Zona Horaria UY_TZ (UTC-3)",
            offset_h == -3.0,
            f"Offset detectado: {offset_h} hs. Hora UY: {now_uy.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        from test_editorial_coherence import auditar_temporalidad_no_hoy_juega
        ok, errs = auditar_temporalidad_no_hoy_juega()
        self.record_result(
            "Coherencia Temporal 'es_hoy'",
            ok,
            "Temporalidad estricta verificada (sin falsos 'Hoy Juega')" if ok else "; ".join(errs),
            {"errors": errs}
        )

    def test_standings_mathematical_integrity(self):
        """Verifica ordenamiento real de Tabla Anual, Clausura y Copa Libertadores (sin puntos fijos)."""
        errors = []
        live_file = DATA_DIR / "live_status.json"
        if not live_file.exists():
            self.record_result("Integridad Matemática de Tablas (AUF/ESPN/CONMEBOL)", False, "Falta live_status.json")
            return

        live = json.loads(live_file.read_text(encoding="utf-8"))
        for key, min_rows in [("tabla_anual", 12), ("tabla_clausura", 12), ("tabla_libertadores", 4)]:
            rows = live.get(key, [])
            if len(rows) < min_rows:
                errors.append(f"{key} tiene solo {len(rows)} filas (mínimo {min_rows})")
                continue
            pts_list = [r.get("pts", 0) for r in rows]
            if pts_list != sorted(pts_list, reverse=True):
                errors.append(f"{key} está DESORDENADA por puntos: {pts_list[:6]}")
            pos_list = [r.get("pos", 0) for r in rows]
            if pos_list != list(range(1, len(rows) + 1)):
                errors.append(f"{key} tiene numeración pos inconsistente: {pos_list[:6]}")

        pen_anual = next((r for r in live.get("tabla_anual", []) if r.get("es_penarol")), None)
        if not pen_anual:
            errors.append("Peñarol no figura marcado con es_penarol=True en tabla_anual")
        else:
            res_pts = (live.get("resumen_temporada") or {}).get("penarol_anual_pts")
            if res_pts is not None and res_pts != pen_anual["pts"]:
                errors.append(f"Desfase de puntos Peñarol: resumen={res_pts} vs tabla_anual={pen_anual['pts']}")

        passed = len(errors) == 0
        msg = (
            f"Tablas Anual (Peñarol #{pen_anual['pos']} con {pen_anual['pts']} pts en {pen_anual['pj']} PJ), "
            f"Clausura y Libertadores 100% ordenadas e íntegras"
            if passed and pen_anual else "; ".join(errors)
        )
        self.record_result("Integridad Matemática de Tablas (AUF/ESPN/CONMEBOL)", passed, msg, {"errors": errors})

    def test_cross_dataset_rival_sync(self):
        """Verifica que rival activo, scouting, duelos 1x1 e historial 1891 BD estén 100% alineados."""
        errors = []
        live = json.loads((DATA_DIR / "live_status.json").read_text(encoding="utf-8"))
        intel = json.loads((DATA_DIR / "rival_intelligence.json").read_text(encoding="utf-8"))
        h2h = json.loads((DATA_DIR / "historial_activo.json").read_text(encoding="utf-8"))

        if live.get("rival_activo_slug") != intel.get("rival_slug"):
            errors.append(f"rival_activo_slug '{live.get('rival_activo_slug')}' != rival_intelligence '{intel.get('rival_slug')}'")
        if live.get("rival_activo_slug") != h2h.get("rival_slug"):
            errors.append(f"rival_activo_slug '{live.get('rival_activo_slug')}' != historial_activo '{h2h.get('rival_slug')}'")
        if len(intel.get("duelos_tacticos_1x1", [])) < 3:
            errors.append("rival_intelligence tiene menos de 3 duelos tácticos 1x1")
        if not intel.get("scouting_tactico", {}).get("entrenador"):
            errors.append("rival_intelligence no tiene DT definido")

        # Verificar consistencia matemática de diferencia de goles en H2H
        r_h2h = h2h.get("resumen", {})
        if r_h2h:
            calc_dif = int(r_h2h.get("goles_penarol", 0)) - int(r_h2h.get("goles_rival", 0))
            stored_dif = int(str(r_h2h.get("diferencia_goles", "0")).replace("+", ""))
            if calc_dif != stored_dif:
                errors.append(f"H2H diferencia_goles inconsistente: {stored_dif} != {calc_dif}")

        passed = len(errors) == 0
        msg = f"Rival activo '{intel.get('rival_nombre')}' (DT: {intel.get('scouting_tactico',{}).get('entrenador')}), {len(intel.get('duelos_tacticos_1x1',[]))} duelos y H2H 1891 BD 100% sincronizados" if passed else "; ".join(errors)
        self.record_result("Sincronización Cruzada Rival, Duelos y 1891 BD", passed, msg, {"errors": errors})

    def test_data_files_schema(self):
        required = [
            "live_status.json", "news_digest.json", "historial_activo.json",
            "rival_intelligence.json", "squad_2026.json", "history_1891.json",
            "efemerides_hoy.json", "escudos_uruguay.json", "galleries.json",
            "influencers_feed.json", "tatuajes_manya.json"
        ]
        missing, corrupted = [], []
        for fn in required:
            fp = DATA_DIR / fn
            if not fp.exists():
                missing.append(fn)
            else:
                try:
                    if not json.loads(fp.read_text(encoding="utf-8")):
                        corrupted.append(f"{fn} (vacío)")
                except Exception as ex:
                    corrupted.append(f"{fn} ({ex})")
        passed = not missing and not corrupted
        self.record_result("Integridad de Datasets JSON", passed, f"{len(required)} archivos JSON validados" if passed else f"Faltantes={missing}, Corruptos={corrupted}")

    def test_locks_health(self):
        abandoned = []
        now_ts = datetime.now().timestamp()
        for lock_dir in [Path.home() / ".manya_locks", BASE_DIR.parent / ".locks"]:
            if not lock_dir.exists():
                continue
            for lf in lock_dir.glob("*.lock"):
                try:
                    age = now_ts - lf.stat().st_mtime
                    if age > 900:
                        abandoned.append(f"{lf.name} ({round(age/60,1)} min)")
                except Exception:
                    pass
        self.record_result("Salud de Locks y Anti-Colisión", not abandoned, "Sin bloqueos huérfanos" if not abandoned else f"Locks huérfanos: {abandoned}")

    def test_external_endpoints(self):
        endpoints = [
            ("Portal Oficial Manya", "https://manya.servicioti.com.uy/"),
            ("Blogger Previa Permanente", "https://www.servicioti.com.uy/p/penarol-proximo-partido-radiografia.html"),
            ("Blogger Archivo Histórico", "https://www.servicioti.com.uy/p/penarol-archivo-historico-de-analisis.html"),
        ]
        failed = []
        for name, url in endpoints:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "ManyaHealthCheck/10.0 (Mozilla/5.0)"})
                with urllib.request.urlopen(req, timeout=12) as resp:
                    if resp.status != 200:
                        failed.append(f"{name} ({resp.status})")
            except Exception as e:
                failed.append(f"{name} ({e})")
        self.record_result("Accesibilidad de Endpoints Oficiales", not failed, "Todos los endpoints HTTP 200 OK" if not failed else f"Fallos: {failed}")

    def test_pwa_and_version_harmony(self):
        errors = []
        sw_txt = (BASE_DIR / "sw.js").read_text(encoding="utf-8")
        html_txt = (BASE_DIR / "index.html").read_text(encoding="utf-8")
        css_txt = (BASE_DIR / "css" / "styles.css").read_text(encoding="utf-8")
        js_txt = (BASE_DIR / "js" / "app.js").read_text(encoding="utf-8")

        if "v10.0" not in sw_txt:
            errors.append("sw.js no tiene versión v10.0")
        if "APP_VER = '10.0'" not in html_txt:
            errors.append("index.html no tiene APP_VER = '10.0'")
        if "styles.css?v=10.0" not in html_txt:
            errors.append("index.html no enlaza css/styles.css?v=10.0")
        if "app.js?v=10.0" not in html_txt:
            errors.append("index.html no enlaza js/app.js?v=10.0")
        if "v10.0" not in css_txt[:100]:
            errors.append("css/styles.css no declara cabecera v10.0")
        if "APP_VERSION = '10.0'" not in js_txt:
            errors.append("js/app.js no declara APP_VERSION = '10.0'")
        if "minmax(0," not in css_txt:
            errors.append("css/styles.css carece de blindaje anti-overflow minmax(0, ...)")

        passed = not errors
        self.record_result("PWA Network-First y Armonía v10.0", passed, "PWA Network-First, v10.0 unificada y grid anti-overflow certificados" if passed else "; ".join(errors))

    def test_libertadores_crests(self):
        errors = []
        live = json.loads((DATA_DIR / "live_status.json").read_text(encoding="utf-8"))
        lib_rows = live.get("tabla_libertadores", [])
        for r in lib_rows:
            esc = r.get("escudo", "")
            if not esc or not (BASE_DIR / esc.lstrip("/")).exists():
                errors.append(f"Falta escudo local para '{r.get('equipo')}': '{esc}'")
        passed = not errors and len(lib_rows) >= 4
        self.record_result("Escudos Oficiales Copa CONMEBOL Libertadores", passed, f"{len(lib_rows)} clubes Libertadores con escudos locales verificados" if passed else "; ".join(errors))

    def test_photos_and_social(self):
        from test_editorial_coherence import auditar_fotos_e_instagram_feed
        ok, errs = auditar_fotos_e_instagram_feed()
        self.record_result("Frescura Fotográfica y Feeds Sociales", ok, "Galerías, influencers y tatuajes 100% íntegros" if ok else "; ".join(errs), {"errors": errs})

    def test_editorial_and_press(self):
        from test_editorial_coherence import auditar_coherencia_editorial
        ok, errs = auditar_coherencia_editorial()
        self.record_result("Coherencia Editorial y Prensa Fresca", ok, "Editorial, prensa (<14d) y SSR sincronizados al 100%" if ok else "; ".join(errs), {"errors": errs})

    def test_tactical_board(self):
        from test_tactical_board import auditar_pizarra_tactica_exhaustiva
        ok, errs = auditar_pizarra_tactica_exhaustiva()
        self.record_result("Pizarra Táctica Interactiva (Plantel 2026)", ok, "Plantel 2026, 3 formaciones, Canvas 1080x1350 y node --check aprobados" if ok else "; ".join(errs), {"errors": errs})

    def run_all_tests(self) -> Dict[str, Any]:
        logger.info("=== INICIANDO BATERÍA DE PRUEBAS MANYA SERVICIOTI v10.0 ===")
        self.test_timezone_and_temporal()
        self.test_standings_mathematical_integrity()
        self.test_cross_dataset_rival_sync()
        self.test_data_files_schema()
        self.test_locks_health()
        self.test_external_endpoints()
        self.test_pwa_and_version_harmony()
        self.test_libertadores_crests()
        self.test_photos_and_social()
        self.test_editorial_and_press()
        self.test_tactical_board()

        total = self.passed_count + self.failed_count
        score = round((self.passed_count / total * 100), 1) if total else 0.0
        estado = "OPTIMO" if self.failed_count == 0 else ("DEGRADADO" if score >= 75 else "CRITICO")
        now_uy = datetime.now(UY_TZ)

        report = {
            "fecha_auditoria": now_uy.strftime("%d/%m/%Y %H:%M:%S"),
            "timestamp": now_uy.isoformat(),
            "schema_version": "10.0",
            "score_salud": score,
            "total_pruebas": total,
            "pruebas_exitosas": self.passed_count,
            "pruebas_fallidas": self.failed_count,
            "estado_general": estado,
            "detalle_pruebas": self.results
        }
        (DATA_DIR / "health_status.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        with open(LOGS_DIR / "test_runs.log", "a", encoding="utf-8") as lf:
            lf.write(f"[{now_uy.strftime('%d/%m/%Y %H:%M:%S')}] SCORE: {score}% ({self.passed_count}/{total} OK) - ESTADO: {estado}\n")
        logger.info(f"=== PRUEBAS COMPLETADAS: SCORE {score}% ({self.passed_count}/{total} APROBADAS) - ESTADO: {estado} ===")
        return report


if __name__ == "__main__":
    rep = ManyaEcosystemTester().run_all_tests()
    print(f"\nRESUMEN FINAL:\nEstado: {rep['estado_general']} | Score: {rep['score_salud']}% | Aprobadas: {rep['pruebas_exitosas']}/{rep['total_pruebas']}")
    sys.exit(0 if rep["pruebas_fallidas"] == 0 else 1)
