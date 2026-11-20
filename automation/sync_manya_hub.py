# -*- coding: utf-8 -*-
"""
ORQUESTADOR MAESTRO UNIFICADO DE ACTUALIZACIÓN — MANYA SERVICIOTI v10.0
=======================================================================
Punto de entrada único, determinista e idempotente para actualizar TODO el ecosistema:
  1. Match Engine v4.0 (ESPN Schedule + AUF Tabla Anual reconciliada + Libertadores + Plantel 2026 + 1891 BD).
  2. 1891 BD (Efemérides diarias UY_TZ + Fotografías reales de los últimos partidos).
  3. Rival Intelligence v3.0 (Scouting + 4 Duelos Tácticos 1x1 + Historial 1891 BD).
  4. Prensa Deportiva v3.0 (Filtro estricto Peñarol <= 10 días, ordenado por fecha real).
  5. Redacción Editorial Idempotente (solo invoca IA al cambiar de partido/fase; refresca noticias siempre).
  6. Sincronización Segura SSR de `index.html` mediante BeautifulSoup (cero HTML roto).
  7. Publicación en Blogger API v3 idempotente (1 Previa / 1 Hoy Juega / 1 Crónica por event_id).
  8. Git Sync Semántico Anti-Spam (solo hace commit/push cuando hay cambios reales de contenido).

Modos de ejecución:
  python automation/sync_manya_hub.py --mode fast      # Datos en vivo + prensa + SSR (rápido, sin Blogger/Chrome)
  python automation/sync_manya_hub.py --mode ci        # GitHub Actions (datos + fotos 1891 + prensa + SSR + tests)
  python automation/sync_manya_hub.py --mode full      # Local completo (+ Gemini + Blogger + git push semántico)
  python automation/sync_manya_hub.py --mode hoy-juega # Edición 00:05 hs de día de partido
"""

import os
import sys
import json
import hashlib
import logging
import argparse
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
AUTOMATION_DIR = BASE_DIR / "automation"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(AUTOMATION_DIR))

UY_TZ = timezone(timedelta(hours=-3))

logger = logging.getLogger("ManyaSyncHub")
if not logger.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

SYNC_STATE_FILE = DATA_DIR / ".sync_state.json"


def _strip_volatile_keys(obj: Any) -> Any:
    """Elimina timestamps puramente volátiles para detectar cambios reales de contenido."""
    volatile = {"actualizado", "generado_el", "timestamp", "antiguedad_horas", "horas_desde_ultimo_partido", "fecha_auditoria"}
    if isinstance(obj, dict):
        return {k: _strip_volatile_keys(v) for k, v in sorted(obj.items()) if k not in volatile}
    if isinstance(obj, list):
        return [_strip_volatile_keys(v) for v in obj]
    return obj


def compute_semantic_content_hash() -> str:
    """Calcula un hash SHA-256 determinista del estado publicado (ignorando timestamps de reloj)."""
    h = hashlib.sha256()
    watched_json = [
        "live_status.json",
        "news_digest.json",
        "rival_intelligence.json",
        "historial_activo.json",
        "squad_2026.json",
        "efemerides_hoy.json",
        "galleries.json",
        "instagram_feed.json",
        "influencers_feed.json",
    ]
    for fn in watched_json:
        p = DATA_DIR / fn
        if p.exists():
            try:
                parsed = json.loads(p.read_text(encoding="utf-8"))
                canonical = json.dumps(_strip_volatile_keys(parsed), sort_keys=True, ensure_ascii=False)
                h.update(fn.encode("utf-8"))
                h.update(canonical.encode("utf-8"))
            except Exception:
                h.update(p.read_bytes())
    return h.hexdigest()


def _load_sync_state() -> Dict[str, Any]:
    if SYNC_STATE_FILE.exists():
        try:
            return json.loads(SYNC_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_sync_state(state: Dict[str, Any]):
    try:
        SYNC_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def sync_influencers_lead_card(live: Dict[str, Any], digest: Dict[str, Any]):
    """Mantiene sincronizada la primera tarjeta de @oficialcap en data/influencers_feed.json con el partido activo."""
    inf_file = DATA_DIR / "influencers_feed.json"
    if not inf_file.exists():
        return
    try:
        items = json.loads(inf_file.read_text(encoding="utf-8"))
        if not items or not isinstance(items, list):
            return
        act = live.get("partido_activo", {}) or {}
        pv = digest.get("portada_visual", {}) or {}
        res_temp = live.get("resumen_temporada", {}) or {}
        pts = res_temp.get("penarol_anual_pts", 69)

        lead = items[0]
        if digest.get("titular_dia"):
            lead["titulo"] = digest["titular_dia"]
        if digest.get("bajada_seo"):
            lead["descripcion"] = digest["bajada_seo"]
        if pv.get("imagen_webp") and (BASE_DIR / pv["imagen_webp"]).exists():
            lead["imagen_webp"] = pv["imagen_webp"]
            lead["imagen_jpg"] = pv.get("imagen_jpg", pv["imagen_webp"])
        lead["partido"] = f"{act.get('nombre', 'Peñarol')} • Tabla Anual {pts} pts"
        items[0] = lead
        inf_file.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        logger.debug(f"[SyncHub] Aviso actualizando influencers lead card: {e}")


def sync_index_ssr_snapshot(live: Dict[str, Any], digest: Dict[str, Any], rival: Dict[str, Any], h2h: Dict[str, Any], efem: Dict[str, Any]):
    """
    Actualiza de forma segura (vía BeautifulSoup, sin regex frágiles) los textos SSR/fallback
    de `index.html` para que SEO, bots y carga inicial sin JS coincidan 100% con los JSON en vivo.
    """
    index_file = BASE_DIR / "index.html"
    if not index_file.exists():
        return
    try:
        from bs4 import BeautifulSoup
        raw_html = index_file.read_text(encoding="utf-8")
        soup = BeautifulSoup(raw_html, "html.parser")

        fase = live.get("fase_partido", "PREVIA")
        act = live.get("partido_activo", {}) or {}
        prox = live.get("proximo_partido", {}) or {}
        res_temp = live.get("resumen_temporada", {}) or {}
        pts = res_temp.get("penarol_anual_pts", 69)
        dg = res_temp.get("penarol_anual_dg", "+27")
        pj = res_temp.get("penarol_anual_pj", 37)

        def set_text(el_id: str, txt: str):
            el = soup.find(id=el_id)
            if el and txt is not None:
                el.string = str(txt)

        # Ticker & Hero
        set_text("ticker-text", live.get("alerta_banner", ""))
        display_match = act if fase in ("EN_VIVO", "POST_PARTIDO") else prox
        loc = display_match.get("local", {}) or {}
        vis = display_match.get("visitante", {}) or {}

        if fase == "POST_PARTIDO":
            set_text("hero-match-badge", f"🏁 RESULTADO FINAL • {display_match.get('torneo', 'CAMPEONATO URUGUAYO').upper()}")
            set_text("hero-live-score-home", str(loc.get("goles", "-")))
            set_text("hero-live-score-away", str(vis.get("goles", "-")))
            set_text("hero-match-date", f"🏁 FINALIZADO • {display_match.get('fecha_legible', '')} • {display_match.get('torneo', '')}")
        elif fase == "EN_VIVO":
            set_text("hero-match-badge", f"🔴 EN VIVO ({display_match.get('minuto_reloj', '1T')}) • {display_match.get('torneo', '').upper()}")
            set_text("hero-live-score-home", str(loc.get("goles", "0")))
            set_text("hero-live-score-away", str(vis.get("goles", "0")))
            set_text("hero-match-date", f"🔴 EN DIRECTO • {display_match.get('minuto_reloj', '1T')} • {display_match.get('torneo', '')}")
        else:
            prefix = "🟡⚫ ¡HOY JUEGA PEÑAROL!" if display_match.get("es_hoy") else "★ PRÓXIMO HORIZONTE"
            set_text("hero-match-badge", f"{prefix} • {display_match.get('torneo', 'CAMPEONATO URUGUAYO').upper()}")
            set_text("hero-match-date", f"{prefix} • {display_match.get('fecha_legible', '')}")

        set_text("hero-home-name", loc.get("nombre", "Peñarol"))
        set_text("hero-away-name", vis.get("nombre", "Rival"))
        set_text("hero-match-venue", display_match.get("estadio", "Estadio Campeón del Siglo"))
        set_text("hero-last-result", f"Peñarol {pts} pts ({'Campeón Tabla Anual' if res_temp.get('campeon_anual') else 'Tabla Anual'} • {dg} DG • {pj} PJ)")

        home_img = soup.find(id="hero-home-crest")
        if home_img and loc.get("escudo"):
            home_img["src"] = loc["escudo"]
            home_img["alt"] = f"Escudo Oficial de {loc.get('nombre', 'Local')}"
        away_img = soup.find(id="hero-away-crest")
        if away_img and vis.get("escudo"):
            away_img["src"] = vis["escudo"]
            away_img["alt"] = f"Escudo Oficial de {vis.get('nombre', 'Visitante')}"

        # Clima
        w = live.get("clima_campeon_del_siglo", {}) or {}
        if w.get("temperatura_c") is not None:
            set_text("hero-weather", f"🌡️ Campeón del Siglo: {w['temperatura_c']}°C • {w.get('condicion', '')} (Viento {w.get('viento_kmh', 12)} km/h)")

        # Rival Scout & Duelos
        if rival:
            sc = rival.get("scouting_tactico", {}) or {}
            inst = rival.get("datos_institucionales_auf", {}) or {}
            r_nom = rival.get("rival_nombre", "Rival")
            r_dt = sc.get("entrenador", "")
            prefix_sc = "Radiografía Táctica del Último Rival" if fase == "POST_PARTIDO" else "Radiografía Táctica del Próximo Rival"
            set_text("scout-rival-title", f"🧭 {prefix_sc}: {r_nom}" + (f" (DT {r_dt})" if r_dt else ""))
            set_text("scout-dt", r_dt)
            set_text("scout-esquema", sc.get("esquema_base", ""))
            set_text("scout-estadio", inst.get("estadio_propio", ""))
            set_text("scout-fundacion", inst.get("fundacion", ""))
            set_text("scout-propuesta", sc.get("propuesta_juego", ""))
            set_text("duelos-1x1-title", f"⚔️ Duelos Tácticos 1x1: Claves de Peñarol vs {rival.get('rival_corto', r_nom)}")

        # H2H
        if h2h and h2h.get("resumen"):
            r_h2h = h2h["resumen"]
            set_text("h2h-title", f"📜 Historial Oficial Verificado: Peñarol vs {h2h.get('rival_oficial') or h2h.get('rival', '')}")
            set_text("h2h-pj", str(r_h2h.get("partidos_jugados", 0)))
            set_text("h2h-pg", str(r_h2h.get("ganados_penarol", 0)))
            set_text("h2h-pe", str(r_h2h.get("empatados", 0)))
            set_text("h2h-pp", str(r_h2h.get("perdidos_penarol", 0)))
            set_text("h2h-gf", f"{r_h2h.get('goles_penarol', 0)} - {r_h2h.get('goles_rival', 0)}")
            set_text("h2h-gf-lbl", f"Goles (Dif: {r_h2h.get('diferencia_goles', '0')})")
            set_text("h2h-eff", str(r_h2h.get("efectividad_pct", "0%")))
            set_text("h2h-pill", f"★ {r_h2h.get('ventaja_victorias', '')}")
            set_text(
                "h2h-summary-text",
                f"Peñarol lidera el historial oficial 1891 BD frente a {h2h.get('rival', '')} con {r_h2h.get('ganados_penarol', 0)} victorias, "
                f"{r_h2h.get('empatados', 0)} empates y {r_h2h.get('perdidos_penarol', 0)} derrotas ({r_h2h.get('diferencia_goles', '0')} goles de diferencia)."
            )

        # Portada & Editorial
        if digest:
            pv = digest.get("portada_visual", {}) or {}
            art = digest.get("articulo_principal", {}) or {}
            set_text("hero-post-headline", pv.get("titular_portada") or digest.get("titular_dia", ""))
            set_text("hero-post-text", pv.get("bajada_portada") or digest.get("bajada_seo", ""))
            set_text("hero-post-location", pv.get("ubicacion", "📍 Estadio Campeón del Siglo • Montevideo"))
            hp_img = soup.find(id="hero-post-img")
            if hp_img and pv.get("imagen_webp"):
                hp_img["src"] = pv["imagen_webp"]
                hp_img["alt"] = (pv.get("titular_portada") or digest.get("titular_dia") or "Peñarol")[:120]

            set_text("editorial-headline", art.get("titulo") or digest.get("titular_dia", ""))
            pars = art.get("parrafos", [])
            if len(pars) >= 1:
                set_text("editorial-p1", pars[0])
            if len(pars) >= 2:
                set_text("editorial-p2", pars[1])
            if len(pars) >= 3:
                set_text("editorial-p3", pars[2])

        # Efemérides fecha
        if efem and efem.get("dia_mes"):
            set_text("efemerides-date-tag", efem["dia_mes"])

        # Footer timestamp
        set_text("footer-last-sync", f"Última sincronización automática: {live.get('actualizado', '')} (UY)")

        # Guardar solo si el HTML efectivamente cambió
        new_html = str(soup)
        if new_html != raw_html:
            index_file.write_text(new_html, encoding="utf-8")
            logger.info("[SyncHub] ✓ index.html SSR snapshot sincronizado de forma segura (BeautifulSoup).")
    except Exception as e:
        logger.warning(f"[SyncHub] Aviso en sync_index_ssr_snapshot: {e}")


def semantic_git_sync(mensaje: str, force: bool = False) -> bool:
    """
    Sincroniza cambios con GitHub Pages SOLO si el contenido semántico cambió
    (elimina por completo el spam de 96 commits repetidos y conflictos con logs).
    """
    current_hash = compute_semantic_content_hash()
    state = _load_sync_state()
    if not force and state.get("last_pushed_hash") == current_hash:
        logger.info("[GitSync] Sin cambios semánticos nuevos respecto al último push. Commit omitido (anti-spam).")
        return False

    git_env = os.environ.copy()
    git_env["GIT_TERMINAL_PROMPT"] = "0"

    # Archivos publicables estrictos (nunca logs/, *.db, ni health_status.json)
    add_targets = [
        "data/live_status.json",
        "data/news_digest.json",
        "data/rival_intelligence.json",
        "data/historial_activo.json",
        "data/squad_2026.json",
        "data/efemerides_hoy.json",
        "data/galleries.json",
        "data/instagram_feed.json",
        "data/influencers_feed.json",
        "data/blogger_pagina_historica.json",
        "assets/gallery/",
        "assets/ig/",
        "index.html",
    ]
    existing_targets = [t for t in add_targets if (BASE_DIR / t).exists()]
    subprocess.run(["git", "add"] + existing_targets, cwd=str(BASE_DIR), env=git_env, check=False)

    diff_check = subprocess.run(["git", "diff", "--staged", "--quiet"], cwd=str(BASE_DIR), env=git_env)
    if diff_check.returncode == 0:
        logger.info("[GitSync] Índice git sin diferencias tras stage. Sin commit.")
        state["last_pushed_hash"] = current_hash
        _save_sync_state(state)
        return False

    c_res = subprocess.run(["git", "commit", "-m", mensaje], cwd=str(BASE_DIR), env=git_env, capture_output=True, text=True)
    if c_res.returncode != 0:
        logger.warning(f"[GitSync] Aviso al hacer commit: {c_res.stderr.strip()}")
        return False

    # Traer cambios remotos con rebase limpio (si falla rebase, abortar y usar ort -X ours)
    subprocess.run(["git", "fetch", "origin", "main"], cwd=str(BASE_DIR), env=git_env, check=False, timeout=30)
    rb = subprocess.run(["git", "rebase", "origin/main"], cwd=str(BASE_DIR), env=git_env, capture_output=True, text=True, timeout=30)
    if rb.returncode != 0:
        subprocess.run(["git", "rebase", "--abort"], cwd=str(BASE_DIR), env=git_env, check=False)
        subprocess.run(
            ["git", "merge", "-s", "ort", "-X", "ours", "origin/main", "-m", f"merge: sincronización remota '{mensaje}'"],
            cwd=str(BASE_DIR), env=git_env, check=False, timeout=30
        )

    p_res = subprocess.run(["git", "push", "origin", "main"], cwd=str(BASE_DIR), env=git_env, capture_output=True, text=True, timeout=45)
    if p_res.returncode == 0:
        logger.info(f"[GitSync] ✓ Push exitoso a origin/main: '{mensaje}'")
        state["last_pushed_hash"] = current_hash
        state["last_pushed_at"] = datetime.now(UY_TZ).isoformat()
        _save_sync_state(state)
        return True

    logger.warning(f"[GitSync] Aviso al hacer push: {p_res.stderr.strip()}")
    return False


def ejecutar_sincronizacion_hub(mode: str = "fast", auto_commit: bool = False, force_editorial: bool = False) -> Dict[str, Any]:
    """Ejecuta el pipeline completo unificado según el modo solicitado."""
    logger.info("=" * 70)
    logger.info(f"=== MANYA SYNC HUB v10.0 • MODO: {mode.upper()} • {datetime.now(UY_TZ).strftime('%d/%m/%Y %H:%M UY')} ===")
    logger.info("=" * 70)

    # 1. Match Engine v4.0 (ESPN + AUF + 1891 BD + Squad 2026)
    from manya_match_engine import ManyaMatchEngine
    live = ManyaMatchEngine.generate_updated_live_status()

    # 2. Efemérides y Fotografías 1891 BD
    from extraer_datos_1891 import extraer_efemerides_hoy, procesar_fotografias_partidos_1891
    efem = extraer_efemerides_hoy()
    state = _load_sync_state()
    last_id_1891 = str((live.get("ultimo_partido") or {}).get("id_1891", ""))
    if mode in ("ci", "full") or (last_id_1891 and state.get("last_photos_id_1891") != last_id_1891):
        procesar_fotografias_partidos_1891()
        state["last_photos_id_1891"] = last_id_1891
        _save_sync_state(state)

    # 3. Inteligencia de Rival + Historial 1891 BD
    from manya_rival_intelligence import generar_informe_rival
    rival_slug = live.get("rival_activo_slug") or live.get("rival_activo_nombre") or "cerro_largo"
    dt_override = (live.get("partido_activo") or {}).get("dt_rival", "")
    rival = generar_informe_rival(rival_slug, dt_override=dt_override)
    h2h_file = DATA_DIR / "historial_activo.json"
    h2h = json.loads(h2h_file.read_text(encoding="utf-8")) if h2h_file.exists() else {}

    # 4. Prensa Deportiva Fresca (strict Peñarol <= 10 días)
    from manya_sports_press import ManyaSportsPressService
    noticias = ManyaSportsPressService.recolectar_todas(max_por_fuente=10)

    # 5. Editorial Idempotente (news_digest.json)
    from generar_cronica_gemini_narrativa import generar_cronica_con_gemini, actualizar_digest_json
    digest_file = DATA_DIR / "news_digest.json"
    existing_digest = {}
    if digest_file.exists():
        try:
            existing_digest = json.loads(digest_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    fase = live.get("fase_partido", "PREVIA")
    act = live.get("partido_activo", {}) or {}
    expected_pub_phase = "CRONICA_POST_PARTIDO" if fase == "POST_PARTIDO" else ("HOY_JUEGA" if act.get("es_hoy") else "PREVIA")
    expected_event_id = str(act.get("event_id", ""))

    need_new_editorial = (
        force_editorial
        or existing_digest.get("schema_version") != "10.0"
        or str(existing_digest.get("partido_id", "")) != expected_event_id
        or existing_digest.get("fase_publicacion") != expected_pub_phase
        or not existing_digest.get("articulo_principal", {}).get("parrafos")
    )

    if need_new_editorial:
        logger.info(f"[SyncHub] Generando nueva edición editorial ({expected_pub_phase} • event_id={expected_event_id})...")
        cronica = generar_cronica_con_gemini(usar_ia=(mode == "full"), noticias=noticias)
        actualizar_digest_json(cronica, noticias_fuentes=noticias)
    else:
        # Solo refrescar titulares frescos de prensa y timestamp sin reescribir la crónica aprobada
        existing_digest["noticias_fuentes"] = noticias[:10]
        existing_digest["actualizado"] = datetime.now(UY_TZ).strftime("%d/%m/%Y %H:%M")
        digest_file.write_text(json.dumps(existing_digest, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"[SyncHub] ✓ Crónica vigente preservada ({expected_pub_phase}); actualizados {len(noticias[:10])} titulares de prensa.")

    digest = json.loads(digest_file.read_text(encoding="utf-8"))
    sync_influencers_lead_card(live, digest)

    # 6. Sincronización segura SSR de index.html
    sync_index_ssr_snapshot(live, digest, rival, h2h, efem)

    # 7. Blogger Sync (solo en modo full local con credenciales OAuth y control anti-duplicados)
    if mode == "full":
        try:
            from manya_anti_collision import ManyaBloggerCatalog, ScheduleSafety
            safe, safe_msg = ScheduleSafety.is_safe_to_publish()
            if safe:
                post_type = "CRONICA" if fase == "POST_PARTIDO" else ("HOY_JUEGA" if act.get("es_hoy") else "PREVIA")
                can_pub, motivo = ManyaBloggerCatalog.can_publish(post_type=post_type, match_id=expected_event_id)
                if can_pub:
                    from blogger_manya_publisher import publish_manya_article_to_blogger
                    publish_manya_article_to_blogger(post_type=post_type, match_id=expected_event_id)
                else:
                    logger.info(f"[Blogger] Idempotencia activa: {motivo}")
                try:
                    from sincronizar_pagina_blogger_historico import sincronizar_pagina_blogger
                    sincronizar_pagina_blogger()
                except Exception as ex_h:
                    logger.debug(f"[Blogger Histórico] {ex_h}")
            else:
                logger.info(f"[Blogger] {safe_msg}")
        except Exception as ex_bl:
            logger.warning(f"[Blogger] Aviso en sincronización remota: {ex_bl}")

    # 8. Git Sync Semántico Anti-Spam (solo si se pidió auto_commit=True)
    pushed = False
    if auto_commit:
        commit_msg = f"chore(sync): actualizar portal Manya ({fase} • {act.get('nombre', 'Peñarol')}) [skip ci]"
        pushed = semantic_git_sync(commit_msg)

    logger.info("=== MANYA SYNC HUB COMPLETADO CON ÉXITO ===")
    return {"live": live, "digest": digest, "rival": rival, "pushed": pushed}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestador Maestro Unificado Manya ServicioTI v10.0")
    parser.add_argument("--mode", choices=["fast", "ci", "full", "hoy-juega"], default="fast")
    parser.add_argument("--commit", action="store_true", help="Ejecutar git sync semántico anti-spam al finalizar")
    parser.add_argument("--force-editorial", action="store_true", help="Forzar regeneración de la nota editorial")
    args = parser.parse_args()

    effective_mode = "full" if args.mode == "hoy-juega" else args.mode
    ejecutar_sincronizacion_hub(mode=effective_mode, auto_commit=args.commit, force_editorial=args.force_editorial)
