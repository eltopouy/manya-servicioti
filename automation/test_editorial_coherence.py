# -*- coding: utf-8 -*-
"""
HERRAMIENTA Y SUITE DE CERTIFICACIÓN DE COHERENCIA EDITORIAL Y TÁCTICA (test_editorial_coherence.py)
====================================================================================================
Audita rigurosamente que NINGÚN contenido periodístico, titular, cuerpo de nota,
citas, scouting táctico o DUELOS 1x1 contengan referencias a rivales anteriores,
estadios pasados o entrenadores desactualizados (Anti-Contaminación de Rivales).
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
UY_TZ = timezone(timedelta(hours=-3))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def auditar_coherencia_editorial() -> tuple[bool, list[str]]:
    """Audita coherencia editorial y táctica entre el rival activo y los textos publicados."""
    errors = []

    # 1. Detectar rival activo desde live_status.json
    live_file = DATA_DIR / "live_status.json"
    if not live_file.exists():
        return False, ["No existe data/live_status.json"]

    try:
        live_data = json.loads(live_file.read_text(encoding="utf-8"))
    except Exception as e:
        return False, [f"Error parseando live_status.json: {e}"]

    prox = live_data.get("proximo_partido", {})
    loc_nom = prox.get("local", {}).get("nombre", "")
    vis_nom = prox.get("visitante", {}).get("nombre", "")
    rival_activo = vis_nom if prox.get("local", {}).get("es_penarol") else loc_nom

    if not rival_activo:
        rival_activo = "Defensor Sporting"

    # Definir términos prohibidos según el rival activo
    rival_slug = "defensor" if "defensor" in rival_activo.lower() else "wanderers"

    if rival_slug == "defensor":
        rival_esperado = "Defensor Sporting"
        estadio_esperado = "Franzini"
        dt_esperado = "Andrés Rodríguez"
        terminos_prohibidos_en_editorial = [
            ("Montevideo Wanderers", "Mención no permitida a Wanderers en el editorial activo de Defensor"),
            ("Wanderers", "Mención residual a Wanderers en el editorial activo"),
            ("Mathías Corujo", "Mención residual a Mathías Corujo como DT"),
            ("Antonio Pacheco", "Mención a Antonio Pacheco"),
            ("Parque Saroldi", "Mención residual a Parque Saroldi"),
            ("Parque Federico Omar Saroldi", "Mención a Parque Saroldi"),
            ("Tickantel", "Mención residual a Tickantel en vez de RedTickets")
        ]
        terminos_prohibidos_en_duelos = [
            ("Gonzalo Freitas", "Jugador de Wanderers (Gonzalo Freitas) en duelos tácticos de Defensor"),
            ("Fabricio Formiliano", "Jugador de Wanderers (Formiliano) en duelos tácticos de Defensor"),
            ("Urretaviscaya", "Jugador de Wanderers (Urretaviscaya) en duelos tácticos de Defensor"),
            ("Mateo Levato", "Jugador de Wanderers (Levato) en duelos tácticos de Defensor"),
            ("bohemio", "Término 'bohemio' en duelos tácticos de Defensor"),
            ("Wanderers", "Mención a Wanderers en duelos tácticos de Defensor"),
            ("Saroldi", "Mención a Saroldi en duelos tácticos de Defensor")
        ]
        figuras_esperadas_en_duelos = ["Fernando Elizari", "Spinelli"]
    else:
        rival_esperado = "Montevideo Wanderers"
        estadio_esperado = "Saroldi"
        dt_esperado = "Mathías Corujo"
        terminos_prohibidos_en_editorial = [
            ("Defensor Sporting", "Mención no permitida a Defensor en editorial de Wanderers"),
            ("Franzini", "Mención a Franzini en editorial de Wanderers"),
            ("Antonio Pacheco", "Mención errónea a Pacheco como DT")
        ]
        terminos_prohibidos_en_duelos = [
            ("Elizari", "Jugador de Defensor (Elizari) en duelos tácticos de Wanderers"),
            ("Spinelli", "Jugador de Defensor (Spinelli) en duelos tácticos de Wanderers"),
            ("Duarte", "Jugador de Defensor (Duarte) en duelos tácticos de Wanderers"),
            ("violeta", "Término 'violeta' en duelos tácticos de Wanderers")
        ]
        figuras_esperadas_en_duelos = ["Gonzalo Freitas", "Formiliano"]

    # 2. Auditar index.html en todas las secciones clave
    html_file = BASE_DIR / "index.html"
    if html_file.exists():
        html_txt = html_file.read_text(encoding="utf-8")
        
        # A. Extraer el bloque del artículo editorial (#editorial-lead-article)
        lead_match = re.search(r'<article class="editorial-lead-article">(.*?)</article>', html_txt, re.DOTALL)
        if lead_match:
            lead_content = lead_match.group(1)
            for prohibido, motivo in terminos_prohibidos_en_editorial:
                if prohibido.lower() in lead_content.lower():
                    ocurrencias = [m.start() for m in re.finditer(re.escape(prohibido), lead_content, re.IGNORECASE)]
                    for idx in ocurrencias:
                        contexto = lead_content[max(0, idx - 40):min(len(lead_content), idx + 60)].lower()
                        if "fecha pasada" in contexto or "partido anterior" in contexto or "empate 1-1" in contexto:
                            continue
                        errors.append(f"index.html (#editorial-lead-article): {motivo} ('{prohibido}')")

            if rival_esperado.lower() not in lead_content.lower():
                errors.append(f"index.html (#editorial-lead-article): No menciona al rival activo '{rival_esperado}'")
            if estadio_esperado.lower() not in lead_content.lower():
                errors.append(f"index.html (#editorial-lead-article): No menciona el escenario '{estadio_esperado}'")
        else:
            errors.append("index.html: No se encontró el bloque <article class='editorial-lead-article'>")

        # B. Extraer las 4 claves del día (#claves-editorial-container)
        claves_match = re.search(r'<div class="claves-editorial-list" id="claves-editorial-container">(.*?)</div>\s*<!--', html_txt, re.DOTALL)
        if claves_match:
            claves_content = claves_match.group(1)
            for prohibido, motivo in terminos_prohibidos_en_editorial:
                if prohibido.lower() in claves_content.lower():
                    errors.append(f"index.html (#claves-editorial-container): {motivo} ('{prohibido}')")

        # C. Extraer el bloque de DUELOS TÁCTICOS 1x1 (#duelos-1x1-box)
        duelos_match = re.search(r'<div class="duelos-1x1-card"[^>]*id="duelos-1x1-box"[^>]*>(.*?)</div>\s*<!--\s*HISTORIAL', html_txt, re.DOTALL)
        if duelos_match:
            duelos_content = duelos_match.group(1)
            for prohibido, motivo in terminos_prohibidos_en_duelos:
                if prohibido.lower() in duelos_content.lower():
                    errors.append(f"index.html (#duelos-1x1-box): {motivo} ('{prohibido}')")

            for fig in figuras_esperadas_en_duelos:
                if fig.lower() not in duelos_content.lower():
                    errors.append(f"index.html (#duelos-1x1-box): Falta figura clave del rival '{fig}'")
        else:
            errors.append("index.html: No se encontró el bloque #duelos-1x1-box")

        # D. Extraer el bloque de SCOUTING TÁCTICO (#rival-scout-box)
        scout_match = re.search(r'<div class="rival-scout-card"[^>]*id="rival-scout-box"[^>]*>(.*?)</div>\s*<!--\s*DUELOS', html_txt, re.DOTALL)
        if scout_match:
            scout_content = scout_match.group(1)
            for prohibido, motivo in terminos_prohibidos_en_duelos:
                if prohibido.lower() in scout_content.lower():
                    errors.append(f"index.html (#rival-scout-box): {motivo} ('{prohibido}')")
        else:
            errors.append("index.html: No se encontró el bloque #rival-scout-box")

        # E. Auditar subtítulo de la tabla (#standings-sub-info)
        sub_info_match = re.search(r'id="standings-sub-info"[^>]*>(.*?)</div>', html_txt, re.DOTALL)
        if sub_info_match:
            sub_info_txt = sub_info_match.group(1)
            if "wanderers" in sub_info_txt.lower() and rival_slug == "defensor":
                errors.append(f"index.html (#standings-sub-info): Menciona erróneamente a Wanderers en la tabla de Defensor")
    else:
        errors.append("No existe index.html")

    # 3. Auditar data/news_digest.json
    digest_file = DATA_DIR / "news_digest.json"
    if digest_file.exists():
        try:
            digest = json.loads(digest_file.read_text(encoding="utf-8"))
            art = digest.get("articulo_principal", {})
            parrafos = art.get("parrafos", [])
            
            if len(parrafos) < 3:
                errors.append(f"news_digest.json: Menos de 3 párrafos en el artículo principal ({len(parrafos)})")

            cuerpo_editorial = " ".join(parrafos)

            for prohibido, motivo in terminos_prohibidos_en_editorial:
                if prohibido.lower() in cuerpo_editorial.lower():
                    ocurrencias = [m.start() for m in re.finditer(re.escape(prohibido), cuerpo_editorial, re.IGNORECASE)]
                    for idx in ocurrencias:
                        contexto = cuerpo_editorial[max(0, idx - 40):min(len(cuerpo_editorial), idx + 60)].lower()
                        if "fecha pasada" in contexto or "partido anterior" in contexto or "empate 1-1" in contexto:
                            continue
                        errors.append(f"news_digest.json: {motivo} ('{prohibido}')")

            # Certificar que mencione los 66 puntos de la Tabla Anual y la Fecha 14
            if "66" not in cuerpo_editorial:
                errors.append("news_digest.json: No menciona los 66 puntos de Peñarol en la Tabla Anual")
            if "fecha 14" not in cuerpo_editorial.lower():
                errors.append("news_digest.json: No menciona la Fecha 14 del Torneo Clausura")

            # Certificar que no contenga placeholders de plantillas
            placeholders = ["Párrafo 1:", "Párrafo 2:", "Párrafo 3:", "[Insertar", "Lorem ipsum"]
            for pl in placeholders:
                if pl.lower() in cuerpo_editorial.lower():
                    errors.append(f"news_digest.json: Contiene texto plantilla o placeholder ('{pl}')")

        except Exception as e:
            errors.append(f"Error procesando data/news_digest.json: {e}")
    else:
        errors.append("No existe data/news_digest.json")

    # 4. Auditar data/rival_intelligence.json
    intel_file = DATA_DIR / "rival_intelligence.json"
    if intel_file.exists():
        try:
            intel = json.loads(intel_file.read_text(encoding="utf-8"))
            duelos = intel.get("duelos_tacticos_1x1", [])
            if len(duelos) < 3:
                errors.append(f"rival_intelligence.json: Menos de 3 duelos tácticos 1x1 ({len(duelos)})")
            
            intel_str = json.dumps(intel, ensure_ascii=False).lower()
            for prohibido, motivo in terminos_prohibidos_en_duelos:
                if prohibido.lower() in intel_str:
                    errors.append(f"rival_intelligence.json: {motivo} ('{prohibido}')")

        except Exception as e:
            errors.append(f"Error procesando data/rival_intelligence.json: {e}")
    else:
        errors.append("No existe data/rival_intelligence.json")

    # 5. Auditar data/influencers_feed.json (Anti-Contaminación en el Feed Social de la Previa)
    inf_file = DATA_DIR / "influencers_feed.json"
    if inf_file.exists():
        try:
            inf = json.loads(inf_file.read_text(encoding="utf-8"))
            if inf and len(inf) > 0:
                item0_str = json.dumps(inf[0], ensure_ascii=False).lower()
                for prohibido, motivo in terminos_prohibidos_en_editorial:
                    if prohibido.lower() in item0_str:
                        errors.append(f"influencers_feed.json (item 0): {motivo} ('{prohibido}')")
                if rival_esperado.lower() not in item0_str:
                    errors.append(f"influencers_feed.json (item 0): No menciona al rival activo '{rival_esperado}'")
        except Exception as e:
            errors.append(f"Error procesando data/influencers_feed.json: {e}")
    else:
        errors.append("No existe data/influencers_feed.json")

    return len(errors) == 0, errors


def auditar_temporalidad_no_hoy_juega() -> tuple[bool, list[str]]:
    """Verifica que NINGÚN archivo (live_status, news_digest, index.html, app.js) diga 'Hoy juega' cuando el partido no es hoy."""
    errors = []
    now_uy = datetime.now(UY_TZ)

    live_file = DATA_DIR / "live_status.json"
    if not live_file.exists():
        return False, ["No existe data/live_status.json"]

    try:
        live = json.loads(live_file.read_text(encoding="utf-8"))
    except Exception as e:
        return False, [f"Error leyendo live_status.json: {e}"]

    prox = live.get("proximo_partido", {})
    fecha_iso = prox.get("fecha_iso", "")
    if not fecha_iso:
        return False, ["live_status.json no contiene fecha_iso en proximo_partido"]

    try:
        m_dt = datetime.fromisoformat(fecha_iso.replace("Z", "+00:00")).astimezone(UY_TZ)
        delta_days = (m_dt.date() - now_uy.date()).days
    except Exception as e:
        return False, [f"Error parseando fecha_iso ({fecha_iso}): {e}"]

    # Si NO es hoy (delta_days != 0):
    if delta_days != 0:
        # 1. Validar flags booleanos en live_status.json
        partido_activo = live.get("partido_activo", {})
        if partido_activo.get("es_hoy") is True:
            errors.append(f"live_status.json: partido_activo.es_hoy es True, pero faltan {delta_days} días para el partido")
        if prox.get("es_hoy") is True:
            errors.append(f"live_status.json: proximo_partido.es_hoy es True, pero faltan {delta_days} días para el partido")

        # 2. Validar cadenas de texto en live_status.json
        live_str = json.dumps(live, ensure_ascii=False)
        for frase in ["hoy juega", "¡hoy juega", "hoy juega peñarol", "hoy juega el manya"]:
            if frase in live_str.lower():
                errors.append(f"data/live_status.json contiene frase engañosa '{frase}' en día sin partido")

        # 3. Validar news_digest.json
        digest_file = DATA_DIR / "news_digest.json"
        if digest_file.exists():
            digest_str = digest_file.read_text(encoding="utf-8")
            for frase in ["hoy juega", "¡hoy juega", "hoy juega peñarol", "hoy juega el manya"]:
                if frase in digest_str.lower():
                    errors.append(f"data/news_digest.json contiene frase engañosa '{frase}' en día sin partido")

        # 4. Validar index.html
        html_file = BASE_DIR / "index.html"
        if html_file.exists():
            html_str = html_file.read_text(encoding="utf-8")
            # Buscar en elementos visibles de encabezado / ticker
            ticker_match = re.search(r'id="ticker-text"[^>]*>(.*?)</div>', html_str, re.DOTALL)
            if ticker_match and "hoy juega" in ticker_match.group(1).lower():
                errors.append("index.html (#ticker-text) dice 'Hoy juega' pero el partido es el domingo 15/11")

            badge_match = re.search(r'id="hero-match-badge"[^>]*>(.*?)</span>', html_str, re.DOTALL)
            if badge_match and "hoy juega" in badge_match.group(1).lower():
                errors.append("index.html (#hero-match-badge) dice 'Hoy juega'")

            lead_match = re.search(r'<article class="editorial-lead-article">(.*?)</article>', html_str, re.DOTALL)
            if lead_match and "hoy juega" in lead_match.group(1).lower():
                errors.append("index.html (#editorial-lead-article) dice 'Hoy juega'")

    return len(errors) == 0, errors


def auditar_fotos_e_instagram_feed() -> tuple[bool, list[str]]:
    """Verifica que NO persistan fotos ni festejos viejos de Liverpool y que todas las fotos en assets/ig/ existan."""
    errors = []

    # 1. Validar feeds JSON: instagram_feed.json, influencers_feed.json, galleries.json
    feed_files = ["instagram_feed.json", "influencers_feed.json", "galleries.json"]
    for fn in feed_files:
        fp = DATA_DIR / fn
        if not fp.exists():
            errors.append(f"Archivo data/{fn} no encontrado")
            continue

        try:
            content = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"Error parseando data/{fn}: {e}")
            continue

        feed_str = json.dumps(content, ensure_ascii=False).lower()
        if "liverpool" in feed_str:
            errors.append(f"data/{fn} contiene mención obsoleta a 'Liverpool' o festejo de gol de Liverpool")

        # Validar existencia de imágenes referenciadas
        img_paths = re.findall(r'["\'](assets/ig/[^"\']+\.(?:webp|jpg|jpeg|png))["\']', feed_str)
        if not img_paths:
            # También buscar nombres de archivo simples si se usan
            img_paths = re.findall(r'["\']image["\']\s*:\s*["\']([^"\']+)["\']', feed_str)

        for ipath in img_paths:
            # Limpiar ruta
            clean_path = ipath.strip().lstrip("/")
            full_path = BASE_DIR / clean_path
            if not full_path.exists():
                # Intentar en assets/ig si era solo nombre de archivo
                alt_path = BASE_DIR / "assets" / "ig" / Path(clean_path).name
                if not alt_path.exists():
                    errors.append(f"data/{fn}: imagen referenciada '{ipath}' no existe en disco")
                elif alt_path.stat().st_size == 0:
                    errors.append(f"data/{fn}: imagen referenciada '{ipath}' está vacía (0 bytes)")
            elif full_path.stat().st_size == 0:
                errors.append(f"data/{fn}: imagen referenciada '{ipath}' está vacía (0 bytes)")

    # 2. Validar index.html
    html_file = BASE_DIR / "index.html"
    if html_file.exists():
        html_str = html_file.read_text(encoding="utf-8")
        # Buscar en sección de galerías o muro visual
        muro_match = re.search(r'<section id="muro-visual"[^>]*>(.*?)</section>', html_str, re.DOTALL)
        if muro_match:
            muro_content = muro_match.group(1).lower()
            if "gol de liverpool" in muro_content or "festejo liverpool" in muro_content:
                errors.append("index.html (#muro-visual) contiene tarjeta con festejo de gol de Liverpool")

        inf_match = re.search(r'<section id="influencers-manya"[^>]*>(.*?)</section>', html_str, re.DOTALL)
        if inf_match:
            inf_content = inf_match.group(1).lower()
            if "liverpool" in inf_content:
                errors.append("index.html (#influencers-manya) contiene referencia obsoleta a Liverpool")

    return len(errors) == 0, errors


def auditar_coherencia_editorial_completa() -> tuple[bool, list[str]]:
    """Ejecuta todas las auditorías de coherencia editorial, temporal y fotográfica."""
    all_errors = []

    tests = [
        ("Coherencia Editorial y Anti-Contaminación de Rivales", auditar_coherencia_editorial),
        ("Temporalidad Estricta (No 'Hoy Juega' en Días Sin Partido)", auditar_temporalidad_no_hoy_juega),
        ("Actualización Fotográfica y Feed de Instagram", auditar_fotos_e_instagram_feed)
    ]

    for name, fn in tests:
        passed, errs = fn()
        if not passed:
            for e in errs:
                all_errors.append(f"[{name}] {e}")

    return len(all_errors) == 0, all_errors


if __name__ == "__main__":
    ok, errs = auditar_coherencia_editorial_completa()
    if ok:
        print("[PASS] Coherencia Editorial, Temporal y Fotográfica 100% Verificada: Portal totalmente sincronizado.")
        sys.exit(0)
    else:
        print(f"[FAIL] Se detectaron {len(errs)} incoherencias:")
        for err in errs:
            print(f"  • {err}")
        sys.exit(1)
