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

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

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

    return len(errors) == 0, errors


if __name__ == "__main__":
    ok, errs = auditar_coherencia_editorial()
    if ok:
        print("[PASS] Coherencia Editorial y Táctica 100% Verificada: Ninguna contaminación entre rivales detectada en todo el DOM.")
        sys.exit(0)
    else:
        print(f"[FAIL] Se detectaron {len(errs)} incoherencias:")
        for err in errs:
            print(f"  • {err}")
        sys.exit(1)
