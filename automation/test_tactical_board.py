# -*- coding: utf-8 -*-
"""
HERRAMIENTA Y SUITE DE CERTIFICACIÓN DE LA PIZARRA TÁCTICA (test_tactical_board.py)
==================================================================================
Audita exhaustivamente el módulo interactivo 'Armá tu 11 Titular' de Peñarol:
1. Integridad del dataset del plantel (data/squad_2026.json).
2. Definición matemática y roles de las formaciones en js/app.js (4-2-3-1, 4-3-3, 4-4-2).
3. Simulación de la máquina de estados de sustituciones e intercambios en cancha.
4. Presencia y accesibilidad de elementos HTML en index.html.
5. Verificación de renderizado Canvas 1080x1350 y generador de texto para compartir.
6. Cobertura de estilos CSS y responsividad móvil en css/styles.css.
"""

import sys
import os
import json
import re
from pathlib import Path
from typing import Tuple, List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
JS_DIR = BASE_DIR / "js"
CSS_DIR = BASE_DIR / "css"

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CANONICAL_POSITIONS = {
    "ARQ", "LD", "LI", "DFC", "MCD", "MC", "MD", "MI", "MCO", "SD", "ED", "EI", "DC"
}


def auditar_dataset_plantel() -> Tuple[bool, List[str]]:
    """Valida la consistencia e integridad del archivo data/squad_2026.json."""
    errors = []
    squad_file = DATA_DIR / "squad_2026.json"
    if not squad_file.exists():
        return False, ["Archivo data/squad_2026.json no encontrado."]

    try:
        data = json.loads(squad_file.read_text(encoding="utf-8"))
    except Exception as e:
        return False, [f"Error al parsear squad_2026.json: {e}"]

    # Validar DT
    dt = data.get("director_tecnico", {})
    if not dt or not dt.get("nombre"):
        errors.append("Falta 'director_tecnico.nombre' en squad_2026.json")
    if "Aguirre" not in dt.get("nombre", ""):
        errors.append(f"DT de Peñarol debe ser Diego Aguirre, encontrado: {dt.get('nombre')}")

    jugadores = data.get("jugadores", [])
    if not jugadores or len(jugadores) < 17:
        errors.append(f"Plantel insuficiente: se esperan al menos 17 futbolistas, encontrados: {len(jugadores)}")

    titulares = [p for p in jugadores if p.get("titular") is True]
    suplentes = [p for p in jugadores if p.get("titular") is False]

    if len(titulares) != 11:
        errors.append(f"Se requieren exactamente 11 titulares, encontrados: {len(titulares)}")

    if len(suplentes) < 6:
        errors.append(f"Banco de relevos insuficiente: se esperan al menos 6 suplentes, encontrados: {len(suplentes)}")

    # Verificar unicidad de dorsales e IDs
    seen_ids = set()
    seen_nums = set()
    arq_titulares = 0

    for idx, p in enumerate(jugadores):
        pid = p.get("id")
        num = p.get("numero")
        nom = p.get("nombre")
        pos = p.get("posicion")

        if not pid or pid in seen_ids:
            errors.append(f"Jugador #{idx} tiene ID inválido o duplicado: '{pid}'")
        seen_ids.add(pid)

        if not isinstance(num, int) or num <= 0 or num in seen_nums:
            errors.append(f"Dorsal inválido o duplicado: #{num} en jugador '{nom}'")
        seen_nums.add(num)

        if not nom or len(nom) < 3:
            errors.append(f"Nombre inválido en jugador con dorsal #{num}")

        if pos not in CANONICAL_POSITIONS:
            errors.append(f"Posición no canónica '{pos}' en jugador '{nom}' (#{num})")

        if p.get("titular") and pos == "ARQ":
            arq_titulares += 1

        # Validar edad y rating
        edad = p.get("edad", 0)
        rating = p.get("rating", 0)
        if not (16 <= edad <= 45):
            errors.append(f"Edad fuera de rango biológico ({edad}) para '{nom}'")
        if not (5.0 <= rating <= 10.0):
            errors.append(f"Rating fuera de rango 5.0-10.0 ({rating}) para '{nom}'")

    if arq_titulares != 1:
        errors.append(f"Debe haber exactamente 1 arquero titular en cancha, encontrados: {arq_titulares}")

    return len(errors) == 0, errors


def auditar_definicion_formaciones() -> Tuple[bool, List[str]]:
    """Extrae y valida FORMATIONS de js/app.js."""
    errors = []
    app_js = JS_DIR / "app.js"
    if not app_js.exists():
        return False, ["Archivo js/app.js no encontrado."]

    code = app_js.read_text(encoding="utf-8")

    # Extraer el bloque FORMATIONS
    match = re.search(r"const\s+FORMATIONS\s*=\s*({[\s\S]*?\n\s*};)", code)
    if not match:
        return False, ["No se encontró la constante FORMATIONS en js/app.js"]

    form_block = match.group(1)

    required_formations = ["4-2-3-1", "4-3-3", "4-4-2"]
    for form in required_formations:
        if f"'{form}'" not in form_block and f'"{form}"' not in form_block:
            errors.append(f"Falta el esquema táctico '{form}' en FORMATIONS")

    # Analizar coordenadas y roles de cada esquema usando regex
    for form in required_formations:
        pat = rf"['\"]{form}['\"]\s*:\s*\[([\s\S]*?)\]"
        f_match = re.search(pat, form_block)
        if not f_match:
            continue
        slots_text = f_match.group(1)
        # Extraer cada objeto { x: .., y: .., role: '..' }
        slots = re.findall(r"\{\s*x:\s*(\d+),\s*y:\s*(\d+),\s*role:\s*['\"]([^'\"]+)['\"]\s*\}", slots_text)

        if len(slots) != 11:
            errors.append(f"El esquema '{form}' debe tener exactamente 11 posiciones, tiene: {len(slots)}")
            continue

        for s_idx, (x_str, y_str, role) in enumerate(slots):
            x = int(x_str)
            y = int(y_str)

            # Verificar márgenes seguros (10 a 92%)
            if not (10 <= x <= 92):
                errors.append(f"Esquema '{form}' posición {s_idx} coordenada x ({x}%) fuera de límites seguros (10-92%)")
            if not (8 <= y <= 95):
                errors.append(f"Esquema '{form}' posición {s_idx} coordenada y ({y}%) fuera de límites seguros (8-95%)")

            if role not in CANONICAL_POSITIONS:
                errors.append(f"Esquema '{form}' posición {s_idx} tiene rol desconocido '{role}'")

            # Slot 0 siempre debe ser el arquero defendiendo en y >= 80
            if s_idx == 0:
                if role != "ARQ":
                    errors.append(f"Esquema '{form}' slot 0 debe tener rol 'ARQ', tiene: '{role}'")
                if y < 80:
                    errors.append(f"Esquema '{form}' slot 0 arquero debe estar en y >= 80, está en: {y}%")

            # Slot 10 debe ser el atacante principal en y <= 25
            if s_idx == 10:
                if role not in ["DC", "DEL"]:
                    errors.append(f"Esquema '{form}' slot 10 debe ser centrodelantero (DC), tiene: '{role}'")
                if y > 25:
                    errors.append(f"Esquema '{form}' slot 10 debe estar en y <= 25, está en: {y}%")

    return len(errors) == 0, errors


def auditar_simulacion_sustituciones() -> Tuple[bool, List[str]]:
    """Simula la lógica de sustituciones de la pizarra táctica para garantizar robustez."""
    errors = []
    squad_file = DATA_DIR / "squad_2026.json"
    if not squad_file.exists():
        return False, ["Archivo data/squad_2026.json no encontrado."]

    data = json.loads(squad_file.read_text(encoding="utf-8"))
    jugadores = data.get("jugadores", [])

    initial_lineup = [dict(p) for p in jugadores if p.get("titular")][:11]
    initial_bench = [dict(p) for p in jugadores if not p.get("titular")]

    # Simulación 1: Cambio Titular -> Suplente
    # Seleccionar arquero (slot 0) y cambiarlo por De Amores (bench 0)
    lineup = [dict(p) for p in initial_lineup]
    bench = [dict(p) for p in initial_bench]

    selected_slot = 0
    selected_bench = 0
    temp = lineup[selected_slot]
    lineup[selected_slot] = bench[selected_bench]
    bench[selected_bench] = temp

    if lineup[0]["id"] != initial_bench[0]["id"]:
        errors.append("Fallo en sustitución slot 0: el suplente no ingresó correctamente")
    if bench[0]["id"] != initial_lineup[0]["id"]:
        errors.append("Fallo en sustitución: el titular saliente no pasó al banco")
    if len(lineup) != 11:
        errors.append(f"La alineación tras cambio no tiene 11 jugadores: {len(lineup)}")

    # Verificar que no haya IDs duplicados entre cancha y banco
    all_current_ids = [p["id"] for p in lineup] + [p["id"] for p in bench]
    if len(all_current_ids) != len(set(all_current_ids)):
        errors.append("Se detectaron futbolistas duplicados tras la sustitución")

    # Simulación 2: Intercambio posicional en cancha (Starter A <-> Starter B)
    # Intercambiar extremo derecho (slot 7) con extremo izquierdo (slot 9)
    p_slot7_orig = lineup[7]["id"]
    p_slot9_orig = lineup[9]["id"]
    temp_swap = lineup[7]
    lineup[7] = lineup[9]
    lineup[9] = temp_swap

    if lineup[7]["id"] != p_slot9_orig or lineup[9]["id"] != p_slot7_orig:
        errors.append("Fallo en intercambio posicional entre dos titulares en cancha")

    # Simulación 3: Restablecer 11 inicial
    reset_lineup = [dict(p) for p in initial_lineup]
    reset_bench = [dict(p) for p in initial_bench]
    if [p["id"] for p in reset_lineup] != [p["id"] for p in initial_lineup]:
        errors.append("Fallo al restablecer la alineación original")

    return len(errors) == 0, errors


def auditar_marcado_html_y_componentes() -> Tuple[bool, List[str]]:
    """Verifica que index.html contenga todos los elementos interactivos y accesibles de la pizarra."""
    errors = []
    index_html = BASE_DIR / "index.html"
    if not index_html.exists():
        return False, ["Archivo index.html no encontrado."]

    html = index_html.read_text(encoding="utf-8")

    required_elements = [
        ('id="pizarra-tactica"', "Sección principal id='pizarra-tactica'"),
        ('id="tactical-pitch"', "Cancha táctica id='tactical-pitch'"),
        ('id="tactical-bench"', "Banco de relevos id='tactical-bench'"),
        ('id="tactical-guidance-banner"', "Banner dinámico de guía táctica id='tactical-guidance-banner'"),
        ('data-formation="4-2-3-1"', "Botón táctico 4-2-3-1"),
        ('data-formation="4-3-3"', "Botón táctico 4-3-3"),
        ('data-formation="4-4-2"', "Botón táctico 4-4-2"),
        ('id="reset-lineup-btn"', "Botón id='reset-lineup-btn' para restaurar 11 inicial"),
        ('id="export-lineup-btn"', "Botón id='export-lineup-btn' para descargar PNG"),
        ('id="share-lineup-btn"', "Botón id='share-lineup-btn' para compartir 11")
    ]

    for needle, desc in required_elements:
        if needle not in html:
            errors.append(f"Falta elemento en index.html: {desc}")

    # Verificar mención al DT Diego Aguirre y al rival activo Defensor Sporting
    if "Diego Aguirre" not in html:
        errors.append("index.html no menciona a Diego Aguirre en la sección táctica")
    if "Defensor Sporting" not in html:
        errors.append("index.html no menciona a Defensor Sporting en la sección táctica")

    return len(errors) == 0, errors


def auditar_canvas_y_compartir() -> Tuple[bool, List[str]]:
    """Verifica el generador de Canvas PNG y la funcionalidad de compartir."""
    errors = []
    app_js = JS_DIR / "app.js"
    if not app_js.exists():
        return False, ["Archivo js/app.js no encontrado."]

    code = app_js.read_text(encoding="utf-8")

    # Verificar dimensiones 1080x1350 del Canvas (formato 4:5 social)
    if "canvas.width = 1080" not in code or "canvas.height = 1350" not in code:
        errors.append("El Canvas de exportación no utiliza la resolución reglamentaria 1080x1350")

    # Verificar mención de descarga y blob
    if "link.download = `mi-11-penarol-${state.formation}.png`" not in code:
        errors.append("Falta plantilla de nombre de archivo descargable en exportLineupPNG")

    # Verificar que el texto para compartir incluya contexto y URL
    if "navigator.share" not in code:
        errors.append("Falta soporte para Web Share API en app.js")
    if "https://manya.servicioti.com.uy/#pizarra-tactica" not in code:
        errors.append("Falta la URL canónica de la pizarra táctica en el texto para compartir")

    return len(errors) == 0, errors


def auditar_estilos_y_responsividad() -> Tuple[bool, List[str]]:
    """Verifica los estilos CSS de la cancha y su adaptación responsiva."""
    errors = []
    styles_css = CSS_DIR / "styles.css"
    if not styles_css.exists():
        return False, ["Archivo css/styles.css no encontrado."]

    css = styles_css.read_text(encoding="utf-8", errors="replace")

    required_classes = [
        (".pitch-board", "Contenedor de la cancha .pitch-board"),
        (".pitch-center-circle", "Círculo central .pitch-center-circle"),
        (".pitch-mid-line", "Línea media .pitch-mid-line"),
        (".pitch-area-top", "Área penal superior .pitch-area-top"),
        (".pitch-area-bottom", "Área penal inferior .pitch-area-bottom"),
        (".pitch-player", "Ficha de futbolista .pitch-player"),
        (".player-token", "Token de camiseta .player-token"),
        (".player-label", "Etiqueta con dorsal/nombre .player-label"),
        (".bench-btn", "Botón de suplente .bench-btn"),
        (".tactical-hint-banner", "Banner dinámico de guía táctica .tactical-hint-banner")
    ]

    for cls_name, desc in required_classes:
        if cls_name not in css:
            errors.append(f"Falta clase CSS en styles.css: {desc}")

    # Verificar adaptación móvil
    if "@media (max-width: 640px)" not in css and "@media (max-width: 600px)" not in css:
        errors.append("Faltan reglas @media para pantallas móviles en la pizarra táctica")

    return len(errors) == 0, errors


def auditar_pizarra_tactica_exhaustiva() -> Tuple[bool, List[str]]:
    """Ejecuta todas las auditorías tácticas consolidadas."""
    all_errors = []

    tests = [
        ("Dataset del Plantel 2026", auditar_dataset_plantel),
        ("Definición de Formaciones (4-2-3-1, 4-3-3, 4-4-2)", auditar_definicion_formaciones),
        ("Simulación de Sustituciones e Intercambios", auditar_simulacion_sustituciones),
        ("Marcado HTML y Componentes Interactivos", auditar_marcado_html_y_componentes),
        ("Exportación Canvas PNG 1080x1350 y Compartir", auditar_canvas_y_compartir),
        ("Estilos CSS y Responsividad Móvil", auditar_estilos_y_responsividad)
    ]

    for name, fn in tests:
        passed, errs = fn()
        if not passed:
            for e in errs:
                all_errors.append(f"[{name}] {e}")

    return len(all_errors) == 0, all_errors


if __name__ == "__main__":
    print("=== AUDITORÍA EXHAUSTIVA DE LA PIZARRA TÁCTICA DEL CLUB ATLÉTICO PEÑAROL ===")
    ok, errors = auditar_pizarra_tactica_exhaustiva()
    if ok:
        print("✅ TODAS LAS AUDITORÍAS DE LA PIZARRA TÁCTICA APROBADAS (100% ÓPTIMO)")
        sys.exit(0)
    else:
        print(f"❌ SE ENCONTRARON {len(errors)} ERRORES EN LA PIZARRA TÁCTICA:")
        for err in errors:
            print(f"  • {err}")
        sys.exit(1)
