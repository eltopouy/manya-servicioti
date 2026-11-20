# -*- coding: utf-8 -*-
"""
SUITE INTEGRAL DE PRUEBAS AUTOMATIZADAS — MANYA SERVICIOTI v11.0 (Zero-Hardcode)
================================================================================
Audita 14 invariantes universales y reales del ecosistema (sin puntos ni rivales hardcodeados):
  1. Zona Horaria UY_TZ (UTC-3).
  2. Coherencia Temporal 'es_hoy' (cero falsos positivos).
  3. Integridad Matemática de Tablas (Anual, Clausura y Libertadores ordenadas por PTS/DG).
  4. Consistencia Cruzada del Rival Activo, DT, Escenario e Historial 1891 BD.
  5. Integridad y Esquema v11.0 de los 11 Datasets JSON en `data/`.
  6. Salud de Locks y Anti-Colisión (`scratch/.locks` y `~/.manya_locks`).
  7. Accesibilidad HTTP 200 de Endpoints Oficiales (Portal + Blogger).
  8. Armonía de Versiones PWA v11.0 (sw.js Network-First, manifest.json real, index.html, styles.css, app.js).
  9. Seguridad XSS, UX Pro v11.0 y Accesibilidad (escapeHtml/safeUrl, Lightbox, Prensa filtrable, Scroll-Spy, Toasts, PWA CTA).
 10. Higiene de Logging (cero duplicación / propagate=False) y Cero Hardcodes Obsoletos en Backend + CI/SPEC v11.0.
 11. Integridad de Escudos Oficiales AUF + Copa CONMEBOL Libertadores.
 12. Frescura Fotográfica, Galerías sin Duplicados y Feeds Sociales.
 13. Coherencia Editorial, Prensa Difusa (sin sufijos sucios) y SSR v11.0.
 14. Pizarra Táctica Pro v11.0 (Plantel verificado 2026, filtros banco, Último 11, Canvas 1080x1350, node --check).
"""

import ast
import importlib
import json
import logging
import py_compile
import re
import struct
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
AUTOMATION_DIR = BASE_DIR / "automation"
LOGS_DIR.mkdir(exist_ok=True)

if str(AUTOMATION_DIR) not in sys.path:
    sys.path.insert(0, str(AUTOMATION_DIR))

from manya_logging import get_manya_logger

UY_TZ = timezone(timedelta(hours=-3))
logger = get_manya_logger("ManyaTestEcosystem")


def _read_png_dimensions(path: Path) -> tuple[int, int] | None:
    """Lee ancho y alto reales desde el header IHDR de un PNG usando solo stdlib."""
    try:
        header = path.read_bytes()[:24]
        if len(header) >= 24 and header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR":
            return struct.unpack(">II", header[16:24])
    except Exception:
        pass
    return None


def _has_module_level_basic_config(py_path: Path) -> bool:
    """Detecta vía AST cualquier llamada a logging.basicConfig() en nivel de módulo."""
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8", errors="replace"), filename=str(py_path))
    except SyntaxError:
        return True
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            fn = node.value.func
            if isinstance(fn, ast.Attribute) and fn.attr == "basicConfig":
                return True
    return False


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
            "timestamp": datetime.now(UY_TZ).isoformat(),
        })
        logger.info(f"[{'PASS' if passed else 'FAIL'}] {test_name}: {message}")

    def test_timezone_and_temporal(self):
        now_uy = datetime.now(UY_TZ)
        offset_h = (now_uy.utcoffset().total_seconds() / 3600.0) if now_uy.utcoffset() else 0.0
        self.record_result(
            "Zona Horaria UY_TZ (UTC-3)",
            offset_h == -3.0,
            f"Offset detectado: {offset_h} hs. Hora UY: {now_uy.strftime('%Y-%m-%d %H:%M:%S')}",
        )

        from test_editorial_coherence import auditar_temporalidad_no_hoy_juega
        ok, errs = auditar_temporalidad_no_hoy_juega()
        self.record_result(
            "Coherencia Temporal 'es_hoy'",
            ok,
            "Temporalidad estricta verificada (sin falsos 'Hoy Juega')" if ok else "; ".join(errs),
            {"errors": errs},
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

        r_h2h = h2h.get("resumen", {})
        if r_h2h:
            calc_dif = int(r_h2h.get("goles_penarol", 0)) - int(r_h2h.get("goles_rival", 0))
            stored_dif = int(str(r_h2h.get("diferencia_goles", "0")).replace("+", ""))
            if calc_dif != stored_dif:
                errors.append(f"H2H diferencia_goles inconsistente: {stored_dif} != {calc_dif}")

        passed = len(errors) == 0
        msg = (
            f"Rival activo '{intel.get('rival_nombre')}' (DT: {intel.get('scouting_tactico', {}).get('entrenador')}), "
            f"{len(intel.get('duelos_tacticos_1x1', []))} duelos y H2H 1891 BD 100% sincronizados"
            if passed else "; ".join(errors)
        )
        self.record_result("Sincronización Cruzada Rival, Duelos y 1891 BD", passed, msg, {"errors": errors})

    def test_data_files_schema(self):
        required = [
            "live_status.json", "news_digest.json", "historial_activo.json",
            "rival_intelligence.json", "squad_2026.json", "history_1891.json",
            "efemerides_hoy.json", "escudos_uruguay.json", "galleries.json",
            "influencers_feed.json", "tatuajes_manya.json",
        ]
        missing, corrupted, wrong_ver = [], [], []
        versioned_core = {"live_status.json", "news_digest.json", "squad_2026.json"}
        for fn in required:
            fp = DATA_DIR / fn
            if not fp.exists():
                missing.append(fn)
            else:
                try:
                    parsed = json.loads(fp.read_text(encoding="utf-8"))
                    if not parsed:
                        corrupted.append(f"{fn} (vacío)")
                    elif fn in versioned_core and str(parsed.get("schema_version", "")) != "11.0":
                        wrong_ver.append(f"{fn}={parsed.get('schema_version')}")
                except Exception as ex:
                    corrupted.append(f"{fn} ({ex})")
        passed = not missing and not corrupted and not wrong_ver
        self.record_result(
            "Integridad de Datasets JSON (v11.0)",
            passed,
            f"{len(required)} archivos JSON validados (schema_version=11.0 en core)"
            if passed else f"Faltantes={missing}, Corruptos={corrupted}, Versión={wrong_ver}",
        )

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
                        abandoned.append(f"{lf.name} ({round(age / 60, 1)} min)")
                except Exception:
                    pass
        self.record_result(
            "Salud de Locks y Anti-Colisión",
            not abandoned,
            "Sin bloqueos huérfanos" if not abandoned else f"Locks huérfanos: {abandoned}",
        )

    def test_external_endpoints(self):
        endpoints = [
            ("Portal Oficial Manya", "https://manya.servicioti.com.uy/"),
            ("Blogger Previa Permanente", "https://www.servicioti.com.uy/p/penarol-proximo-partido-radiografia.html"),
            ("Blogger Archivo Histórico", "https://www.servicioti.com.uy/p/penarol-archivo-historico-de-analisis.html"),
        ]
        failed = []
        for name, url in endpoints:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "ManyaHealthCheck/11.0 (Mozilla/5.0)"})
                with urllib.request.urlopen(req, timeout=12) as resp:
                    if resp.status != 200:
                        failed.append(f"{name} ({resp.status})")
            except Exception as e:
                failed.append(f"{name} ({e})")
        self.record_result(
            "Accesibilidad de Endpoints Oficiales",
            not failed,
            "Todos los endpoints HTTP 200 OK" if not failed else f"Fallos: {failed}",
        )

    def test_pwa_and_version_harmony(self):
        """Certifica armonía v11.0 unificada en sw.js, manifest.json, index.html, css/styles.css y js/app.js."""
        errors = []
        sw_txt = (BASE_DIR / "sw.js").read_text(encoding="utf-8")
        html_txt = (BASE_DIR / "index.html").read_text(encoding="utf-8")
        css_txt = (BASE_DIR / "css" / "styles.css").read_text(encoding="utf-8")
        js_txt = (BASE_DIR / "js" / "app.js").read_text(encoding="utf-8")
        mf_path = BASE_DIR / "manifest.json"

        # 1. Version harmony v11.0
        if "manya-servicioti-v11.0-unified" not in sw_txt:
            errors.append("sw.js no declara CACHE_NAME='manya-servicioti-v11.0-unified'")
        if "styles.css?v=11.0" not in sw_txt or "app.js?v=11.0" not in sw_txt:
            errors.append("sw.js CORE_ASSETS no referencia styles.css?v=11.0 y app.js?v=11.0")
        if "mode === 'navigate'" not in sw_txt and 'mode === "navigate"' not in sw_txt:
            errors.append("sw.js no incluye fallback offline para navegación")
        if "APP_VER = '11.0'" not in html_txt:
            errors.append("index.html no tiene APP_VER = '11.0'")
        if "styles.css?v=11.0" not in html_txt or "app.js?v=11.0" not in html_txt:
            errors.append("index.html no enlaza styles.css?v=11.0 y app.js?v=11.0")
        if "v10.0" in html_txt or "v10.0" in sw_txt:
            errors.append("Restos obsoletos de 'v10.0' detectados en index.html o sw.js")
        if "v11.0" not in css_txt[:120]:
            errors.append("css/styles.css no declara cabecera v11.0")
        if "APP_VERSION = '11.0'" not in js_txt:
            errors.append("js/app.js no declara APP_VERSION = '11.0'")

        # 2. CSS v11.0 quality & a11y
        for needle, desc in [
            ("minmax(0,", "blindaje anti-overflow minmax(0, ...)"),
            (":focus-visible", "indicador accesible :focus-visible"),
            ("prefers-reduced-motion", "soporte prefers-reduced-motion"),
            ("scroll-margin-top", "compensación scroll-margin-top"),
        ]:
            if needle not in css_txt:
                errors.append(f"css/styles.css carece de {desc}")
        if "shimmer" not in css_txt.lower() and "skeleton" not in css_txt.lower():
            errors.append("css/styles.css carece de shimmer/skeleton para lazy images")

        top_selectors = re.findall(r"(?m)^([.#a-zA-Z][^{}\n/@]{1,80})\s*\{", css_txt)
        dup_selectors = {s: c for s, c in Counter(x.strip() for x in top_selectors).items() if c > 1}
        if dup_selectors:
            errors.append(f"css/styles.css tiene selectores top-level duplicados: {dup_selectors}")

        # 3. Manifest.json validity & icon dimensions accuracy
        if not mf_path.exists():
            errors.append("Falta manifest.json")
        else:
            try:
                mf = json.loads(mf_path.read_text(encoding="utf-8"))
                for req_k in ("id", "name", "short_name", "start_url", "scope", "display", "icons"):
                    if not mf.get(req_k):
                        errors.append(f"manifest.json carece de '{req_k}'")
                for ic in mf.get("icons", []):
                    src = ic.get("src", "").lstrip("/")
                    p_ic = BASE_DIR / src
                    if not p_ic.exists():
                        errors.append(f"manifest.json referencia ícono inexistente: '{src}'")
                        continue
                    if p_ic.suffix.lower() == ".png":
                        dims = _read_png_dimensions(p_ic)
                        if dims:
                            actual = f"{dims[0]}x{dims[1]}"
                            if ic.get("sizes") != actual:
                                errors.append(f"manifest.json ícono '{src}' declara sizes='{ic.get('sizes')}' pero mide {actual}")
                            if dims[0] != dims[1] and "maskable" in (ic.get("purpose") or ""):
                                errors.append(f"manifest.json usa purpose='{ic.get('purpose')}' en ícono no cuadrado ({actual})")
            except Exception as ex:
                errors.append(f"Error leyendo manifest.json: {ex}")

        passed = not errors
        self.record_result(
            "PWA Network-First, Manifest y Armonía v11.0",
            passed,
            "PWA Network-First v11.0, manifest.json verificado y CSS depurado certificados" if passed else "; ".join(errors),
            {"errors": errors},
        )

    def test_frontend_xss_ux_and_a11y(self):
        """Audita blindaje XSS, Lightbox Pro, Prensa filtrable, Scroll-Spy, Toasts, PWA CTA y A11y en Frontend."""
        errors = []
        html_txt = (BASE_DIR / "index.html").read_text(encoding="utf-8")
        js_txt = (BASE_DIR / "js" / "app.js").read_text(encoding="utf-8")

        # 1. XSS helpers y cero handlers inline
        for fn in ["function escapeHtml(", "function safeUrl(", "function safeImgSrc("]:
            if fn not in js_txt:
                errors.append(f"js/app.js no define {fn}")
        if re.search(r"onerror\s*=", js_txt):
            errors.append("js/app.js aún contiene manejadores inline onerror=")

        # Verificar que todos los links target="_blank" en index.html lleven rel="noopener noreferrer"
        for a_tag in re.findall(r"<a\b[^>]*>", html_txt):
            if 'target="_blank"' in a_tag and "noopener" not in a_tag:
                errors.append(f"Enlace target=_blank sin rel='noopener noreferrer': {a_tag[:90]}")
            if "peñarolenlapiel" in a_tag.lower():
                errors.append("Enlace a #PeñarolEnLaPiel sin URL-encoding (%C3%B1)")

        # 2. Semántica HTML y A11y
        h1_matches = re.findall(r"<h1\b[^>]*>.*?</h1>", html_txt, re.S | re.I)
        if len(h1_matches) != 1:
            errors.append(f"index.html debe tener exactamente 1 <h1>, encontrados: {len(h1_matches)}")
        if "skip-link" not in html_txt:
            errors.append("index.html carece de skip-link accesible al contenido principal")
        if 'aria-live="polite"' not in html_txt:
            errors.append("index.html carece de región aria-live='polite' para toasts/anuncios")
        if re.search(r'id="lightbox-title"[^>]*>\s*</h3>', html_txt):
            errors.append("index.html tiene encabezado #lightbox-title vacío")

        all_ids = re.findall(r'\bid="([^"]+)"', html_txt)
        dup_ids = {k: v for k, v in Counter(all_ids).items() if v > 1}
        if dup_ids:
            errors.append(f"index.html tiene IDs duplicados: {dup_ids}")

        # 3. Presencia y conexión de todos los módulos interactivos v11.0
        required_v11_ids = [
            "prensa-vivo", "prensa-source-chips", "prensa-search-input", "live-news-list",
            "manya-lightbox", "lightbox-prev", "lightbox-next", "lightbox-counter", "lightbox-credit", "lightbox-stage",
            "bench-line-filters", "preset-ultimo-11-btn", "preset-ideal-11-btn",
            "manya-toast-region", "pwa-install-btn",
        ]
        for dom_id in required_v11_ids:
            if f'id="{dom_id}"' not in html_txt:
                errors.append(f"Falta id='{dom_id}' en index.html")
            if dom_id not in js_txt:
                errors.append(f"js/app.js no conecta el elemento '#{dom_id}'")

        for js_feature, desc in [
            ("IntersectionObserver", "Scroll-Spy con IntersectionObserver"),
            ("beforeinstallprompt", "PWA Install CTA (beforeinstallprompt)"),
            ("showToast(", "Sistema de Toasts"),
            ("enhanceLazyImages(", "Lazy-load shimmer sin cajas negras"),
            ("stepLightbox(", "Navegación Anterior/Siguiente en Lightbox"),
            ("lbTattoos", "Lightbox integrado en Piel Carbonera (#piel-carbonera)"),
        ]:
            if js_feature not in js_txt:
                errors.append(f"js/app.js carece de {desc}")

        passed = not errors
        self.record_result(
            "Seguridad XSS, UX Pro v11.0 y Accesibilidad",
            passed,
            f"XSS sanitizado, {len(all_ids)} IDs únicos, Lightbox Pro, Prensa filtrable, Scroll-Spy, Toasts y PWA CTA certificados"
            if passed else "; ".join(errors),
            {"errors": errors},
        )

    def test_backend_logging_and_code_hygiene(self):
        """Certifica cero logging duplicado, py_compile 100%, cero hardcodes obsoletos en activos y CI/SPEC v11.0."""
        errors = []

        # 1. Módulo central de logging
        logging_mod = AUTOMATION_DIR / "manya_logging.py"
        if not logging_mod.exists():
            errors.append("Falta automation/manya_logging.py")

        # 2. py_compile + AST check de cero logging.basicConfig() a nivel de módulo en TODO automation/*.py
        py_files = sorted(AUTOMATION_DIR.glob("*.py"))
        for pyf in py_files:
            try:
                py_compile.compile(str(pyf), doraise=True)
            except Exception as ex:
                errors.append(f"Error de sintaxis en {pyf.name}: {ex}")
            if _has_module_level_basic_config(pyf):
                errors.append(f"{pyf.name} ejecuta logging.basicConfig() a nivel de módulo (provoca logs duplicados)")

        # 3. Verificación viva de propagate=False y handler único en módulos activos del pipeline
        active_loggers = [
            ("sync_manya_hub", "ManyaSyncHub"),
            ("manya_match_engine", "ManyaMatchEngine"),
            ("manya_sports_press", "ManyaSportsPress"),
            ("generar_cronica_gemini_narrativa", "GeminiNarrativa"),
            ("manya_rival_intelligence", "ManyaRivalIntelligence"),
            ("extraer_datos_1891", "Manya1891Extractor"),
        ]
        for mod_name, log_name in active_loggers:
            try:
                importlib.import_module(mod_name)
                lg = logging.getLogger(log_name)
                if lg.propagate is not False:
                    errors.append(f"Logger '{log_name}' ({mod_name}) tiene propagate=True (riesgo de logs duplicados)")
                stream_handlers = [
                    h for h in lg.handlers
                    if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
                ]
                if len(stream_handlers) > 1:
                    errors.append(f"Logger '{log_name}' ({mod_name}) tiene {len(stream_handlers)} StreamHandlers duplicados")
            except Exception as ex:
                errors.append(f"No se pudo importar módulo activo '{mod_name}': {ex}")

        # 4. Cero hardcodes obsoletos en scripts activos (fuera de tests y legacy archivados)
        legacy_archived = {
            "actualizar_frontend_cronica.py", "actualizar_scripts_blogger.py",
            "integrar_frontend_1891.py", "publicar_previa_juventud.py",
            "reestructurar_tripartita_frontend.py", "sincronizar_oficialcap_centenario.py",
            "actualizar_manya_completo.py", "publicar_en_vivo_blogger.py",
        }
        forbidden_active = ["66 puntos", "66 pts", "CRÓNICA COMPLETA DEL 1-1"]
        for pyf in py_files:
            if pyf.name.startswith("test_") or pyf.name in legacy_archived:
                continue
            txt = pyf.read_text(encoding="utf-8", errors="replace").lower()
            for bad in forbidden_active:
                if bad.lower() in txt:
                    errors.append(f"Script activo {pyf.name} conserva hardcode obsoleto: '{bad}'")

        # 5. CI Workflow & SPEC.md en v11.0
        wf_path = BASE_DIR / ".github" / "workflows" / "actualizar_partidos.yml"
        if not wf_path.exists():
            errors.append("Falta .github/workflows/actualizar_partidos.yml")
        else:
            wf_txt = wf_path.read_text(encoding="utf-8")
            if "v11.0" not in wf_txt or "v10.0" in wf_txt:
                errors.append(".github/workflows/actualizar_partidos.yml no está actualizado limpiamente a v11.0")

        spec_path = BASE_DIR / "SPEC.md"
        if not spec_path.exists() or "11.0" not in spec_path.read_text(encoding="utf-8"):
            errors.append("SPEC.md ausente o no documenta la arquitectura v11.0")

        passed = not errors
        self.record_result(
            "Higiene de Logging, Scripts Activos y CI/SPEC v11.0",
            passed,
            f"{len(py_files)} scripts compilados, 0 basicConfig a nivel de módulo, 6/6 loggers aislados (propagate=False) y CI/SPEC v11.0 OK"
            if passed else "; ".join(errors),
            {"errors": errors},
        )

    def test_libertadores_crests(self):
        errors = []
        live = json.loads((DATA_DIR / "live_status.json").read_text(encoding="utf-8"))
        lib_rows = live.get("tabla_libertadores", [])
        for r in lib_rows:
            esc = r.get("escudo", "")
            if not esc or not (BASE_DIR / esc.lstrip("/")).exists():
                errors.append(f"Falta escudo local para '{r.get('equipo')}': '{esc}'")
        passed = not errors and len(lib_rows) >= 4
        self.record_result(
            "Escudos Oficiales Copa CONMEBOL Libertadores",
            passed,
            f"{len(lib_rows)} clubes Libertadores con escudos locales verificados" if passed else "; ".join(errors),
        )

    def test_photos_and_social(self):
        from test_editorial_coherence import auditar_fotos_e_instagram_feed
        ok, errs = auditar_fotos_e_instagram_feed()
        self.record_result(
            "Frescura Fotográfica y Feeds Sociales",
            ok,
            "Galerías, influencers y tatuajes 100% íntegros" if ok else "; ".join(errs),
            {"errors": errs},
        )

    def test_editorial_and_press(self):
        from test_editorial_coherence import auditar_coherencia_editorial
        ok, errs = auditar_coherencia_editorial()
        self.record_result(
            "Coherencia Editorial, Prensa Difusa y SSR v11.0",
            ok,
            "Editorial, prensa fresca deduplicada (<14d, sin sufijos), clima horario y SSR v11.0 100% OK"
            if ok else "; ".join(errs),
            {"errors": errs},
        )

    def test_tactical_board(self):
        from test_tactical_board import auditar_pizarra_tactica_exhaustiva
        ok, errs = auditar_pizarra_tactica_exhaustiva()
        self.record_result(
            "Pizarra Táctica Pro y Plantel Verificado 2026",
            ok,
            "Plantel 2026 (edades/DOB/ratings), filtros banco, Último 11, Canvas 1080x1350 y node --check aprobados"
            if ok else "; ".join(errs),
            {"errors": errs},
        )

    def run_all_tests(self) -> Dict[str, Any]:
        logger.info("=== INICIANDO BATERÍA DE PRUEBAS MANYA SERVICIOTI v11.0 ===")
        self.test_timezone_and_temporal()
        self.test_standings_mathematical_integrity()
        self.test_cross_dataset_rival_sync()
        self.test_data_files_schema()
        self.test_locks_health()
        self.test_external_endpoints()
        self.test_pwa_and_version_harmony()
        self.test_frontend_xss_ux_and_a11y()
        self.test_backend_logging_and_code_hygiene()
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
            "schema_version": "11.0",
            "score_salud": score,
            "total_pruebas": total,
            "pruebas_exitosas": self.passed_count,
            "pruebas_fallidas": self.failed_count,
            "estado_general": estado,
            "detalle_pruebas": self.results,
        }
        (DATA_DIR / "health_status.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        with open(LOGS_DIR / "test_runs.log", "a", encoding="utf-8") as lf:
            lf.write(f"[{now_uy.strftime('%d/%m/%Y %H:%M:%S')}] v11.0 SCORE: {score}% ({self.passed_count}/{total} OK) - ESTADO: {estado}\n")
        logger.info(f"=== PRUEBAS COMPLETADAS: SCORE {score}% ({self.passed_count}/{total} APROBADAS) - ESTADO: {estado} ===")
        return report


if __name__ == "__main__":
    rep = ManyaEcosystemTester().run_all_tests()
    print(f"\nRESUMEN FINAL:\nEstado: {rep['estado_general']} | Score: {rep['score_salud']}% | Aprobadas: {rep['pruebas_exitosas']}/{rep['total_pruebas']}")
    sys.exit(0 if rep["pruebas_fallidas"] == 0 else 1)
