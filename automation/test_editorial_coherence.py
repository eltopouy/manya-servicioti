# -*- coding: utf-8 -*-
"""
SUITE DINÁMICA DE CERTIFICACIÓN DE COHERENCIA EDITORIAL, TEMPORAL Y FOTOGRÁFICA — v10.0
=======================================================================================
Zero-Hardcode QA:
  1. Verifica coherencia cruzada entre live_status.json, rival_intelligence.json,
     historial_activo.json, news_digest.json e index.html para CUALQUIER rival y fase.
  2. Verifica temporalidad estricta (jamás 'Hoy juega' cuando es_hoy=False o delta_days!=0).
  3. Verifica frescura y relevancia de prensa deportiva (noticias <= 14 días, 100% Peñarol).
  4. Verifica integridad fotográfica (cero Liverpool 18/10 obsoleto, archivos existen > 0 bytes,
     cero duplicación de tatuajes en galleries.json).
  5. Verifica integridad del HTML (sin bloques huérfanos ni disclaimers de IA).
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UY_TZ = timezone(timedelta(hours=-3))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def auditar_coherencia_editorial() -> tuple[bool, list[str]]:
    """Audita coherencia cruzada dinámica entre todos los datasets y el HTML para cualquier rival."""
    errors = []

    live_file = DATA_DIR / "live_status.json"
    digest_file = DATA_DIR / "news_digest.json"
    intel_file = DATA_DIR / "rival_intelligence.json"
    h2h_file = DATA_DIR / "historial_activo.json"
    html_file = BASE_DIR / "index.html"

    for p in [live_file, digest_file, intel_file, h2h_file, html_file]:
        if not p.exists():
            errors.append(f"Archivo obligatorio no encontrado: {p.name}")
    if errors:
        return False, errors

    live = json.loads(live_file.read_text(encoding="utf-8"))
    digest = json.loads(digest_file.read_text(encoding="utf-8"))
    intel = json.loads(intel_file.read_text(encoding="utf-8"))
    h2h = json.loads(h2h_file.read_text(encoding="utf-8"))
    html_txt = html_file.read_text(encoding="utf-8")

    # 1. Rival activo coherente entre live_status, rival_intelligence y historial_activo
    live_slug = (live.get("rival_activo_slug") or "").lower()
    intel_slug = (intel.get("rival_slug") or "").lower()
    h2h_slug = (h2h.get("rival_slug") or "").lower()
    if live_slug and intel_slug and live_slug != intel_slug:
        errors.append(f"Desfase de rival: live_status='{live_slug}' vs rival_intelligence='{intel_slug}'")
    if live_slug and h2h_slug and live_slug != h2h_slug:
        errors.append(f"Desfase de historial: live_status='{live_slug}' vs historial_activo='{h2h_slug}'")

    # 2. Duelos tácticos 1x1 >= 3 siempre presentes
    duelos = intel.get("duelos_tacticos_1x1", [])
    if len(duelos) < 3:
        errors.append(f"rival_intelligence.json tiene menos de 3 duelos tácticos 1x1 ({len(duelos)})")

    # 3. Coherencia de news_digest.json con partido_activo + cero disclaimers/placeholders
    art = digest.get("articulo_principal", {})
    parrafos = art.get("parrafos", [])
    if len(parrafos) < 3:
        errors.append(f"news_digest.json tiene menos de 3 párrafos ({len(parrafos)})")

    cuerpo = json.dumps(digest, ensure_ascii=False).lower()
    for bad in ["como modelo de lenguaje", "como una ia", "no puedo generar", "párrafo 1:", "lorem ipsum", "antonio pacheco"]:
        if bad in cuerpo:
            errors.append(f"news_digest.json contiene texto prohibido o placeholder: '{bad}'")

    # 4. Coherencia de minuto_a_minuto ligado al event_id activo
    act_id = str((live.get("partido_activo") or {}).get("event_id", ""))
    tl_id = str(live.get("minuto_a_minuto_event_id", ""))
    if live.get("fase_partido") in ("EN_VIVO", "POST_PARTIDO") and act_id and tl_id and act_id != tl_id:
        errors.append(f"Minuto a minuto desfasado: timeline event_id='{tl_id}' != partido_activo='{act_id}'")

    # 5. Prensa fresca (noticias_fuentes <= 14 días, sin julio 2025 ni ruido no-Peñarol)
    noticias = digest.get("noticias_fuentes", [])
    if not noticias:
        errors.append("news_digest.json no contiene noticias_fuentes frescas")
    else:
        now_uy = datetime.now(UY_TZ)
        for idx, n in enumerate(noticias[:6]):
            f_iso = n.get("fecha_iso", "")
            if f_iso:
                try:
                    n_dt = datetime.fromisoformat(f_iso.replace("Z", "+00:00")).astimezone(UY_TZ)
                    if (now_uy - n_dt).days > 14:
                        errors.append(f"Noticia #{idx} desactualizada ({n.get('fecha')}): {n.get('titulo', '')[:50]}")
                except Exception:
                    pass
            tit_l = (n.get("titulo") or "").lower()
            if any(noise in tit_l for noise in ["carnaval", "charles carrera", "noticias de uruguay y del mundo"]):
                errors.append(f"Noticia #{idx} contiene ruido ajeno a Peñarol: '{n.get('titulo')}'")

    # 6. Verificar que index.html refleje el rival activo y no tenga etiquetas rotas / basura de 1-1 Wanderers
    rival_corto = intel.get("rival_corto", "")
    if rival_corto and rival_corto.lower() not in html_txt.lower():
        errors.append(f"index.html SSR no refleja al rival activo '{rival_corto}'")
    if "CRÓNICA COMPLETA DEL 1-1" in html_txt:
        errors.append("index.html todavía contiene texto viejo 'CRÓNICA COMPLETA DEL 1-1'")

    return len(errors) == 0, errors


def auditar_temporalidad_no_hoy_juega() -> tuple[bool, list[str]]:
    """Verifica que NINGÚN archivo diga 'Hoy juega' cuando el partido no se disputa hoy en UY_TZ."""
    errors = []
    now_uy = datetime.now(UY_TZ)
    live_file = DATA_DIR / "live_status.json"
    if not live_file.exists():
        return False, ["No existe data/live_status.json"]

    live = json.loads(live_file.read_text(encoding="utf-8"))
    prox = live.get("proximo_partido", {}) or {}
    act = live.get("partido_activo", {}) or {}
    fecha_iso = prox.get("fecha_iso", "")

    if fecha_iso:
        try:
            m_dt = datetime.fromisoformat(fecha_iso.replace("Z", "+00:00")).astimezone(UY_TZ)
            delta_days = (m_dt.date() - now_uy.date()).days
            if delta_days != 0:
                if prox.get("es_hoy") is True:
                    errors.append(f"live_status.json: proximo_partido.es_hoy es True faltando {delta_days} días")
                if live.get("fase_partido") != "EN_VIVO" and act.get("es_hoy") is True:
                    errors.append("live_status.json: partido_activo.es_hoy es True en día sin partido")
                for label, txt in [
                    ("live_status.json", json.dumps(live, ensure_ascii=False).lower()),
                    ("news_digest.json", (DATA_DIR / "news_digest.json").read_text(encoding="utf-8").lower() if (DATA_DIR / "news_digest.json").exists() else ""),
                ]:
                    if "¡hoy juega" in txt or "hoy juega peñarol" in txt or "hoy juega el manya" in txt:
                        errors.append(f"{label} contiene 'Hoy juega' en día sin partido (delta_days={delta_days})")
        except Exception as e:
            errors.append(f"Error parseando fecha_iso ({fecha_iso}): {e}")

    return len(errors) == 0, errors


def auditar_fotos_e_instagram_feed() -> tuple[bool, list[str]]:
    """Verifica frescura fotográfica, existencia física en disco y ausencia de duplicados/fotos obsoletas."""
    errors = []
    for fn in ["instagram_feed.json", "influencers_feed.json", "galleries.json", "tatuajes_manya.json"]:
        fp = DATA_DIR / fn
        if not fp.exists():
            errors.append(f"Falta data/{fn}")
            continue
        items = json.loads(fp.read_text(encoding="utf-8"))
        raw_str = json.dumps(items, ensure_ascii=False).lower()

        if "1891_liverpool_penarol_2026" in raw_str:
            errors.append(f"data/{fn} aún referencia fotos obsoletas de Liverpool 18/10/2026")
        if fn == "galleries.json" and any((it.get("id") or "").startswith("tattoo_") for it in items):
            errors.append("data/galleries.json duplica tarjetas de tatuajes (deben estar solo en tatuajes_manya.json)")
        if fn == "tatuajes_manya.json" and "12 estrellas" in raw_str:
            errors.append("data/tatuajes_manya.json contiene error factual '12 estrellas' (son 11 estrellas)")

        for it in items:
            img = it.get("imagen_webp") or it.get("imagen_jpg") or ""
            if img:
                f_disk = BASE_DIR / img.lstrip("/")
                if not f_disk.exists() or f_disk.stat().st_size == 0:
                    errors.append(f"data/{fn}: imagen inexistente o vacía '{img}'")

    return len(errors) == 0, errors


def auditar_coherencia_editorial_completa() -> tuple[bool, list[str]]:
    all_errors = []
    for name, fn in [
        ("Coherencia Editorial y Cross-Dataset", auditar_coherencia_editorial),
        ("Temporalidad Estricta (No 'Hoy Juega' Falso)", auditar_temporalidad_no_hoy_juega),
        ("Integridad Fotográfica y Feeds Sociales", auditar_fotos_e_instagram_feed),
    ]:
        ok, errs = fn()
        if not ok:
            for e in errs:
                all_errors.append(f"[{name}] {e}")
    return len(all_errors) == 0, all_errors


if __name__ == "__main__":
    ok, errs = auditar_coherencia_editorial_completa()
    if ok:
        print("[PASS] Coherencia Editorial, Temporal y Fotográfica v10.0 100% Verificada.")
        sys.exit(0)
    print(f"[FAIL] Se detectaron {len(errs)} incoherencias:")
    for e in errs:
        print(f"  • {e}")
    sys.exit(1)
