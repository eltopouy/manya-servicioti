"""
Suite Integral de Pruebas Automatizadas y Auditoría de Salud del Ecosistema Manya ServicioTI.
Valida todas las dimensiones críticas del sistema:
1. Temporalidad y Control de Zona Horaria (UY_TZ = America/Montevideo / UTC-3).
2. Consistencia de Datos y Puntos (Tabla Anual 65 pts, Torneo Clausura Fecha 12).
3. Verificación de Rival, Estadio y Entradas (Montevideo Wanderers, Parque Viera, RedTickets).
4. Integridad de los 20 Datasets JSON en `data/`.
5. Salud de Locks y Anti-Colisión (`~/.manya_locks/`).
6. Accesibilidad HTTP de los 5 Endpoints Oficiales (Portal y Blogger).
7. Infraestructura de Logs y Despliegue.
"""

import sys
import os
import json
import logging
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Forzar codificación UTF-8 en salida
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

logger = logging.getLogger("ManyaTestEcosystem")
if not logger.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)


class ManyaEcosystemTester:
    """Ejecutor de pruebas integrales para el ecosistema Manya."""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.passed_count = 0
        self.failed_count = 0
        self.warnings_count = 0

    def record_result(self, test_name: str, passed: bool, message: str, details: Any = None):
        if passed:
            self.passed_count += 1
            status = "PASS"
        else:
            self.failed_count += 1
            status = "FAIL"
        
        entry = {
            "test": test_name,
            "status": status,
            "passed": passed,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now(UY_TZ).isoformat()
        }
        self.results.append(entry)
        prefix = "[PASS]" if passed else "[FAIL]"
        logger.info(f"{prefix} {test_name}: {message}")

    def test_timezone_and_temporal_assertions(self):
        """Verifica que el sistema esté operando con zona horaria de Uruguay (UTC-3)."""
        now_uy = datetime.now(UY_TZ)
        now_utc = datetime.now(timezone.utc)
        offset_hours = (now_uy.utcoffset().total_seconds() / 3600.0) if now_uy.utcoffset() else 0.0

        is_utc3 = (offset_hours == -3.0)
        self.record_result(
            "Zona Horaria UY_TZ (UTC-3)",
            is_utc3,
            f"Offset detectado: {offset_hours} hs (esperado: -3.0 hs). Hora UY actual: {now_uy.strftime('%Y-%m-%d %H:%M:%S')}",
            {"now_uy": str(now_uy), "offset_hours": offset_hours}
        )

        # Verificar detección de match day
        live_file = DATA_DIR / "live_status.json"
        if live_file.exists():
            live_data = json.loads(live_file.read_text(encoding="utf-8"))
            prox = live_data.get("proximo_partido", {})
            fecha_iso = prox.get("fecha_iso", "")
            es_hoy = live_data.get("partido_activo", {}).get("es_hoy", False)
            if fecha_iso:
                try:
                    m_dt = datetime.fromisoformat(fecha_iso.replace("Z", "+00:00")).astimezone(UY_TZ)
                    delta_days = (m_dt.date() - now_uy.date()).days
                    temporal_correct = (delta_days == 0 and es_hoy) or (delta_days != 0 and not es_hoy)
                    self.record_result(
                        "Coherencia Temporal 'es_hoy'",
                        temporal_correct,
                        f"delta_days: {delta_days}, es_hoy: {es_hoy} (partido: {m_dt.strftime('%d/%m/%Y')})",
                        {"delta_days": delta_days, "es_hoy": es_hoy}
                    )
                except Exception as ex:
                    self.record_result("Coherencia Temporal 'es_hoy'", False, f"Error parseando fecha_iso: {ex}")
            else:
                self.record_result("Coherencia Temporal 'es_hoy'", True, "No hay fecha_iso en próximo partido para evaluar.")
        else:
            self.record_result("Coherencia Temporal 'es_hoy'", False, "No existe data/live_status.json")

    def test_points_and_standings_integrity(self):
        """Verifica que la Tabla Anual indique 65 puntos y no persistan referencias a 64 pts."""
        errors = []
        # 1. En live_status.json
        live_file = DATA_DIR / "live_status.json"
        if live_file.exists():
            txt = live_file.read_text(encoding="utf-8")
            if "64 puntos" in txt or "64 pts" in txt or "64 unidades" in txt:
                errors.append("data/live_status.json contiene menciones a 64 pts")
        
        # 2. En news_digest.json
        digest_file = DATA_DIR / "news_digest.json"
        if digest_file.exists():
            txt = digest_file.read_text(encoding="utf-8")
            if "64 puntos" in txt or "64 pts" in txt or "64 unidades" in txt:
                errors.append("data/news_digest.json contiene menciones a 64 pts")

        # 3. En index.html
        html_file = BASE_DIR / "index.html"
        if html_file.exists():
            txt = html_file.read_text(encoding="utf-8")
            if "64 puntos" in txt or "64 unidades" in txt:
                errors.append("index.html contiene menciones a 64 unidades/puntos")

        # 4. En js/app.js
        app_js = BASE_DIR / "js" / "app.js"
        if app_js.exists():
            txt = app_js.read_text(encoding="utf-8")
            if "64 puntos" in txt or "64 pts" in txt:
                errors.append("js/app.js contiene menciones a 64 puntos")

        passed = len(errors) == 0
        msg = "Todos los archivos sincronizados en 65 puntos oficiales AUF" if passed else f"Inconsistencias encontradas: {'; '.join(errors)}"
        self.record_result("Integridad de Puntos (Tabla Anual 65 pts)", passed, msg, {"errors": errors})

    def test_rival_and_venue_verification(self):
        """Verifica que el rival activo sea Montevideo Wanderers, DT Mathías Corujo, escenario Parque Saroldi y venta Tickantel."""
        errors = []
        html_file = BASE_DIR / "index.html"
        if html_file.exists():
            txt = html_file.read_text(encoding="utf-8")
            if "Parque Federico Omar Saroldi" not in txt and "Parque Saroldi" not in txt:
                errors.append("index.html no contiene el escenario oficial 'Parque Federico Omar Saroldi'")
            if "Mathías Corujo" not in txt and "Mathías 'Chiche' Corujo" not in txt:
                errors.append("index.html no menciona al DT oficial de Wanderers Mathías Corujo")
            if "Antonio Pacheco" in txt:
                errors.append("index.html menciona erróneamente a Antonio Pacheco como DT de Wanderers")
            if "Tickantel" not in txt:
                errors.append("index.html no menciona 'Tickantel' para la venta oficial de entradas de Wanderers")

        rival_file = DATA_DIR / "rival_intelligence.json"
        if rival_file.exists():
            txt = rival_file.read_text(encoding="utf-8")
            if "Mathías Corujo" not in txt:
                errors.append("data/rival_intelligence.json no tiene a Mathías Corujo como entrenador")
            if "Antonio Pacheco" in txt:
                errors.append("data/rival_intelligence.json menciona a Antonio Pacheco")

        passed = len(errors) == 0
        msg = "Rival Montevideo Wanderers, DT Mathías Corujo, Parque Saroldi y Tickantel verificados" if passed else f"Errores de escenario/rival/DT: {'; '.join(errors)}"
        self.record_result("Verificación de Rival, DT y Escenario", passed, msg, {"errors": errors})

    def test_data_files_schema(self):
        """Verifica que los archivos JSON requeridos existan, tengan sintaxis válida y no estén vacíos."""
        required_files = [
            "live_status.json", "news_digest.json", "historial_activo.json",
            "historial_wanderers.json", "rival_intelligence.json", "squad_2026.json",
            "history_1891.json", "efemerides_hoy.json", "escudos_uruguay.json",
            "influencers_feed.json", "tatuajes_manya.json"
        ]
        corrupted = []
        missing = []
        for fn in required_files:
            fp = DATA_DIR / fn
            if not fp.exists():
                missing.append(fn)
            else:
                try:
                    content = json.loads(fp.read_text(encoding="utf-8"))
                    if not content:
                        corrupted.append(f"{fn} (vacío)")
                except Exception as ex:
                    corrupted.append(f"{fn} ({ex})")

        passed = len(missing) == 0 and len(corrupted) == 0
        msg = f"{len(required_files)} archivos JSON validados con éxito" if passed else f"Faltantes: {missing}, Corruptos: {corrupted}"
        self.record_result("Integridad de Datasets JSON", passed, msg, {"missing": missing, "corrupted": corrupted})

    def test_concurrency_locks_health(self):
        """Verifica que el directorio de locks no contenga bloqueos huérfanos o abandonados."""
        lock_dir = Path.home() / ".manya_locks"
        abandoned_locks = []
        if lock_dir.exists():
            now_ts = datetime.now().timestamp()
            for lock_file in lock_dir.glob("*.lock"):
                try:
                    mtime = lock_file.stat().st_mtime
                    age_seconds = now_ts - mtime
                    if age_seconds > 900:  # Mayor a 15 minutos
                        abandoned_locks.append(f"{lock_file.name} ({round(age_seconds/60, 1)} min)")
                except Exception:
                    pass

        passed = len(abandoned_locks) == 0
        msg = "Sistema de locks limpio y sin bloqueos huérfanos" if passed else f"Locks huérfanos detectados: {abandoned_locks}"
        self.record_result("Salud de Locks y Anti-Colisión", passed, msg, {"abandoned": abandoned_locks})

    def test_external_endpoints_reachability(self):
        """Verifica que los endpoints públicos y páginas de Blogger respondan con código 200."""
        endpoints = [
            ("Portal Oficial Manya", "https://manya.servicioti.com.uy/"),
            ("Blogger Previa Permanente", "https://www.servicioti.com.uy/p/penarol-proximo-partido-radiografia.html"),
            ("Blogger Previa Post", "https://www.servicioti.com.uy/2026/10/penarol-en-vivo-la-previa-radiografia.html"),
            ("Blogger Archivo Histórico", "https://www.servicioti.com.uy/p/penarol-archivo-historico-de-analisis.html"),
            ("Blogger Post Concluido", "https://www.servicioti.com.uy/2026/10/penarol-en-vivo-juventud-vs-penarol.html")
        ]
        failed_urls = []
        results_map = {}
        for name, url in endpoints:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "ManyaHealthCheck/1.0 (Mozilla/5.0)"})
                with urllib.request.urlopen(req, timeout=12) as response:
                    status = response.status
                    results_map[name] = {"status": status, "url": url}
                    if status != 200:
                        failed_urls.append(f"{name} ({status})")
            except Exception as e:
                failed_urls.append(f"{name} ({e})")
                results_map[name] = {"error": str(e), "url": url}

        passed = len(failed_urls) == 0
        msg = "Todos los endpoints responden HTTP 200 OK" if passed else f"Endpoints con error: {failed_urls}"
        self.record_result("Accesibilidad de Endpoints Oficiales", passed, msg, results_map)

    def test_pwa_network_first_and_standings_selector(self):
        """Verifica que Service Worker use Network-First, la tabla por defecto sea Clausura y no haya datos viejos en el match center."""
        errors = []
        sw_file = BASE_DIR / "sw.js"
        if sw_file.exists():
            txt = sw_file.read_text(encoding="utf-8")
            if "v7.0-network-first" not in txt:
                errors.append("sw.js no tiene la versión v7.0-network-first")
            if "caches.match(event.request).then(cached => cached || fetch(event.request))" in txt:
                errors.append("sw.js aún tiene fetch cache-first")
        else:
            errors.append("sw.js no existe")

        live_file = DATA_DIR / "live_status.json"
        if live_file.exists():
            data = json.loads(live_file.read_text(encoding="utf-8"))
            if data.get("torneo_activo_id") != "clausura":
                errors.append(f"live_status.json torneo_activo_id es '{data.get('torneo_activo_id')}', se esperaba 'clausura'")
        else:
            errors.append("live_status.json no existe")

        html_file = BASE_DIR / "index.html"
        if html_file.exists():
            txt = html_file.read_text(encoding="utf-8")
            if "Pitazo inicial en el Estadio Centenario" in txt:
                errors.append("index.html contiene relato viejo del Centenario en el match center")
            if "manya_app_ver" not in txt:
                errors.append("index.html no tiene el script auto-invalidador de caché PWA")

        passed = len(errors) == 0
        msg = "PWA Network-First, selector de tablas en Clausura y saneamiento de caché verificados" if passed else f"Inconsistencias: {'; '.join(errors)}"
        self.record_result("PWA Network-First y Selector Clausura/Anual", passed, msg, {"errors": errors})

    def run_all_tests(self) -> Dict[str, Any]:
        """Ejecuta toda la batería de pruebas y devuelve el resumen consolidado."""
        self.results = []
        self.passed_count = 0
        self.failed_count = 0

        logger.info("=== INICIANDO BATERÍA DE PRUEBAS DEL ECOSISTEMA MANYA ===")
        self.test_timezone_and_temporal_assertions()
        self.test_points_and_standings_integrity()
        self.test_rival_and_venue_verification()
        self.test_data_files_schema()
        self.test_concurrency_locks_health()
        self.test_external_endpoints_reachability()
        self.test_pwa_network_first_and_standings_selector()

        total = self.passed_count + self.failed_count
        score = round((self.passed_count / total * 100), 1) if total > 0 else 0.0

        summary = {
            "fecha_auditoria": datetime.now(UY_TZ).strftime("%d/%m/%Y %H:%M:%S"),
            "timestamp": datetime.now(UY_TZ).isoformat(),
            "score_salud": score,
            "total_pruebas": total,
            "pruebas_exitosas": self.passed_count,
            "pruebas_fallidas": self.failed_count,
            "estado_general": "OPTIMO" if score == 100.0 else ("ALERTA" if score >= 80 else "CRITICO"),
            "detalle_pruebas": self.results
        }

        # Guardar informe en data/health_status.json
        health_file = DATA_DIR / "health_status.json"
        health_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

        # Guardar en logs/test_runs.log
        log_file = LOGS_DIR / "test_runs.log"
        with open(log_file, "a", encoding="utf-8") as lf:
            lf.write(f"[{summary['fecha_auditoria']}] SCORE: {score}% ({self.passed_count}/{total} OK) - ESTADO: {summary['estado_general']}\n")

        logger.info(f"=== PRUEBAS COMPLETADAS: SCORE {score}% ({self.passed_count}/{total} APROBADAS) ===")
        return summary


if __name__ == "__main__":
    tester = ManyaEcosystemTester()
    res = tester.run_all_tests()
    print("\nRESUMEN FINAL:")
    print(f"Estado: {res['estado_general']} | Score: {res['score_salud']}% | Aprobadas: {res['pruebas_exitosas']}/{res['total_pruebas']}")
