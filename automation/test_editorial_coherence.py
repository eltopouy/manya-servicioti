# -*- coding: utf-8 -*-
"""
HERRAMIENTA Y SUITE DE CERTIFICACIÓN DE COHERENCIA EDITORIAL (test_editorial_coherence.py)
========================================================================================
Audita rigurosamente que NINGÚN contenido periodístico, titular, cuerpo de nota,
citas o claves del día contengan referencias a rivales anteriores, estadios pasados
o entrenadores desactualizados (Anti-Contaminación de Rivales).
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
    """Audita coherencia editorial entre el rival activo y los textos publicados."""
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
    else:
        rival_esperado = "Montevideo Wanderers"
        estadio_esperado = "Saroldi"
        dt_esperado = "Mathías Corujo"
        terminos_prohibidos_en_editorial = [
            ("Defensor Sporting", "Mención no permitida a Defensor en editorial de Wanderers"),
            ("Franzini", "Mención a Franzini en editorial de Wanderers"),
            ("Antonio Pacheco", "Mención errónea a Pacheco como DT")
        ]

    # 2. Auditar index.html en la sección El Diario de Peñarol (#resumen-ia)
    html_file = BASE_DIR / "index.html"
    if html_file.exists():
        html_txt = html_file.read_text(encoding="utf-8")
        
        # Extraer el bloque del artículo editorial (#editorial-lead-article)
        lead_match = re.search(r'<article class="editorial-lead-article">(.*?)</article>', html_txt, re.DOTALL)
        if lead_match:
            lead_content = lead_match.group(1)
            for prohibido, motivo in terminos_prohibidos_en_editorial:
                if prohibido.lower() in lead_content.lower():
                    # Verificar si es una mención legítima histórica como "fecha pasada ante Wanderers"
                    # Permitir únicamente menciones explicadas como fecha pasada
                    ocurrencias = [m.start() for m in re.finditer(re.escape(prohibido), lead_content, re.IGNORECASE)]
                    for idx in ocurrencias:
                        contexto = lead_content[max(0, idx - 40):min(len(lead_content), idx + 60)].lower()
                        if "fecha pasada" in contexto or "partido anterior" in contexto or "empate 1-1" in contexto:
                            continue
                        errors.append(f"index.html (#editorial-lead-article): {motivo} ('{prohibido}')")

            # Verificar que el rival y escenario esperado estén presentes
            if rival_esperado.lower() not in lead_content.lower():
                errors.append(f"index.html (#editorial-lead-article): No menciona al rival activo '{rival_esperado}'")
            if estadio_esperado.lower() not in lead_content.lower():
                errors.append(f"index.html (#editorial-lead-article): No menciona el escenario '{estadio_esperado}'")
        else:
            errors.append("index.html: No se encontró el bloque <article class='editorial-lead-article'>")

        # Extraer las 4 claves del día (#claves-editorial-container)
        claves_match = re.search(r'<div class="claves-editorial-list" id="claves-editorial-container">(.*?)</div>\s*<!--', html_txt, re.DOTALL)
        if claves_match:
            claves_content = claves_match.group(1)
            for prohibido, motivo in terminos_prohibidos_en_editorial:
                if prohibido.lower() in claves_content.lower():
                    errors.append(f"index.html (#claves-editorial-container): {motivo} ('{prohibido}')")
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
                errors.append(f"data/news_digest.json: artículo principal tiene solo {len(parrafos)} párrafos (se requieren al menos 3)")

            for i, p_txt in enumerate(parrafos):
                if p_txt.lower().startswith("párrafo"):
                    errors.append(f"data/news_digest.json (Párrafo {i+1}): contiene texto template sin rellenar ('{p_txt[:40]}...')")
                if len(p_txt.split()) < 25:
                    errors.append(f"data/news_digest.json (Párrafo {i+1}): párrafo demasiado corto ({len(p_txt.split())} palabras)")

            # Verificar términos prohibidos en el artículo de digest
            art_str = json.dumps(art, ensure_ascii=False)
            for prohibido, motivo in terminos_prohibidos_en_editorial:
                if prohibido.lower() in art_str.lower():
                    # Comprobar si es contexto histórico explícito
                    ocurrencias = [m.start() for m in re.finditer(re.escape(prohibido), art_str, re.IGNORECASE)]
                    for idx in ocurrencias:
                        contexto = art_str[max(0, idx - 40):min(len(art_str), idx + 60)].lower()
                        if "fecha pasada" in contexto or "partido anterior" in contexto or "empate 1-1" in contexto:
                            continue
                        errors.append(f"data/news_digest.json: {motivo} ('{prohibido}')")

        except Exception as ex:
            errors.append(f"Error analizando data/news_digest.json: {ex}")
    else:
        errors.append("No existe data/news_digest.json")

    passed = len(errors) == 0
    return passed, errors


if __name__ == "__main__":
    ok, errs = auditar_coherencia_editorial()
    if ok:
        print("[PASS] Coherencia Editorial 100% Verificada: Ninguna contaminación entre rivales detectada.")
        sys.exit(0)
    else:
        print("[FAIL] Inconsistencias editoriales detectadas:")
        for e in errs:
            print(f"  - {e}")
        sys.exit(1)
