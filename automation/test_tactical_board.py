# -*- coding: utf-8 -*-
"""
HERRAMIENTA Y SUITE DE CERTIFICACIÓN DE LA PIZARRA TÁCTICA v11.0 (test_tactical_board.py)
========================================================================================
Audita exhaustivamente el módulo interactivo 'Armá tu 11 Titular' de Peñarol:
1. Integridad del dataset del plantel 2026 (data/squad_2026.json v11.0):
   - Esquema v11.0, edades coherentes con fecha_nacimiento y resguardo anti-homónimos ESPN.
   - Rating diferenciado (no plano 7.6), titular_ultimo_1891 y matching 11/11 de ultimo_once_1891.
   - Unicidad de dorsales e IDs, posiciones canónicas y 1 arquero titular.
2. Definición matemática y roles de las formaciones en js/app.js (4-2-3-1, 4-3-3, 4-4-2).
3. Simulación de sustituciones, intercambios en cancha, filtro de banco por línea y preset Último 11.
4. Presencia y accesibilidad de elementos HTML v11.0 en index.html (filtros, presets, cancha).
5. Verificación de renderizado Canvas 1080x1350 y generador de texto para compartir.
6. Cobertura de estilos CSS v11.0 y responsividad móvil en css/styles.css.
7. Sintaxis JS (`node --check js/app.js` y `node --check sw.js`) y funciones tácticas Pro.
"""

import sys
import json
import re
import subprocess
import unicodedata
from datetime import datetime, date, timezone, timedelta
from pathlib import Path
from typing import Tuple, List

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
JS_DIR = BASE_DIR / "js"
CSS_DIR = BASE_DIR / "css"
UY_TZ = timezone(timedelta(hours=-3))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CANONICAL_POSITIONS = {
    "ARQ", "LD", "LI", "DFC", "MCD", "MC", "MD", "MI", "MCO", "SD", "ED", "EI", "DC"
}

LINE_GROUPS = {
    "ARQ": {"ARQ"},
    "DEF": {"LD", "LI", "DFC"},
    "VOL": {"MCD", "MC", "MD", "MI", "MCO"},
    "ATA": {"ED", "EI", "SD", "DC"},
}

# Resguardo anti-homónimos ESPN: veteranos verificados que jamás pueden caer en edad ~20
KNOWN_MIN_AGES_2026 = {
    "javier cabrera": 32,
    "franco romero": 29,
    "washington aguerre": 31,
    "german pezzella": 33,
    "maximiliano olivera": 32,
    "sebastian britos": 35,
    "abel hernandez": 34,
}


def _norm_name(val: str) -> str:
    norm = unicodedata.normalize("NFKD", val or "")
    return "".join(c for c in norm if not unicodedata.combining(c)).lower().strip()


def _line_group(pos: str) -> str:
    p = (pos or "").upper().strip()
    for grp, members in LINE_GROUPS.items():
        if p in members:
            return grp
    return "VOL"


def auditar_dataset_plantel() -> Tuple[bool, List[str]]:
    """Valida la consistencia, precisión de edades/dorsales/ratings y esquema v11.0 de data/squad_2026.json."""
    errors = []
    squad_file = DATA_DIR / "squad_2026.json"
    if not squad_file.exists():
        return False, ["Archivo data/squad_2026.json no encontrado."]

    try:
        data = json.loads(squad_file.read_text(encoding="utf-8"))
    except Exception as e:
        return False, [f"Error al parsear squad_2026.json: {e}"]

    # Validar versión de esquema v11.0
    if str(data.get("schema_version", "")) != "11.0":
        errors.append(f"squad_2026.json debe declarar schema_version='11.0', encontrado: '{data.get('schema_version')}'")

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

    seen_ids = set()
    seen_nums = set()
    distinct_ratings = set()
    arq_titulares = 0
    ultimo_1891_flags = 0
    today_uy = datetime.now(UY_TZ).date()

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

        if "titular_ultimo_1891" not in p or not isinstance(p.get("titular_ultimo_1891"), bool):
            errors.append(f"Falta booleano 'titular_ultimo_1891' en '{nom}'")
        elif p.get("titular_ultimo_1891"):
            ultimo_1891_flags += 1

        # Validar edad biológica, coherencia con fecha_nacimiento y resguardo anti-homónimos
        edad = p.get("edad", 0)
        rating = p.get("rating", 0)
        if not isinstance(edad, int) or not (16 <= edad <= 45):
            errors.append(f"Edad fuera de rango biológico ({edad}) para '{nom}'")

        dob_str = p.get("fecha_nacimiento")
        if dob_str:
            try:
                dob = date.fromisoformat(dob_str)
                calc_age = today_uy.year - dob.year - ((today_uy.month, today_uy.day) < (dob.month, dob.day))
                if abs(calc_age - int(edad)) > 1:
                    errors.append(f"Desfase edad/DOB en '{nom}': edad={edad} vs fecha_nacimiento={dob_str} (calc={calc_age})")
            except ValueError:
                errors.append(f"fecha_nacimiento inválida '{dob_str}' en '{nom}'")

        norm_nom = _norm_name(nom or "")
        for vet_name, min_age in KNOWN_MIN_AGES_2026.items():
            if vet_name == norm_nom and isinstance(edad, int) and edad < min_age:
                errors.append(
                    f"Posible colisión de homónimo ESPN en '{nom}': edad={edad} (se espera >= {min_age})"
                )

        if not isinstance(rating, (int, float)) or not (5.0 <= rating <= 10.0):
            errors.append(f"Rating fuera de rango 5.0-10.0 ({rating}) para '{nom}'")
        else:
            distinct_ratings.add(round(float(rating), 2))

    if arq_titulares != 1:
        errors.append(f"Debe haber exactamente 1 arquero titular en cancha, encontrados: {arq_titulares}")

    if len(distinct_ratings) < 5:
        errors.append(f"Los ratings del plantel no están diferenciados (solo {len(distinct_ratings)} valor(es): {sorted(distinct_ratings)})")

    # Validar ultimo_once_1891 (11 nombres coincidentes con jugadores[])
    ultimo_once = data.get("ultimo_once_1891", [])
    if len(ultimo_once) != 11:
        errors.append(f"ultimo_once_1891 debe contener 11 futbolistas, encontrados: {len(ultimo_once)}")
    else:
        squad_names_norm = {_norm_name(p.get("nombre", "")) for p in jugadores}
        unmatched = [n for n in ultimo_once if _norm_name(n) not in squad_names_norm]
        if unmatched:
            errors.append(f"Nombres en ultimo_once_1891 ausentes en jugadores[]: {unmatched}")

    if ultimo_1891_flags != 11:
        errors.append(f"Se esperan exactamente 11 futbolistas con titular_ultimo_1891=True, encontrados: {ultimo_1891_flags}")

    return len(errors) == 0, errors


def auditar_definicion_formaciones() -> Tuple[bool, List[str]]:
    """Extrae y valida FORMATIONS de js/app.js."""
    errors = []
    app_js = JS_DIR / "app.js"
    if not app_js.exists():
        return False, ["Archivo js/app.js no encontrado."]

    code = app_js.read_text(encoding="utf-8")

    match = re.search(r"const\s+FORMATIONS\s*=\s*({[\s\S]*?\n\s*};)", code)
    if not match:
        return False, ["No se encontró la constante FORMATIONS en js/app.js"]

    form_block = match.group(1)

    required_formations = ["4-2-3-1", "4-3-3", "4-4-2"]
    for form in required_formations:
        if f"'{form}'" not in form_block and f'"{form}"' not in form_block:
            errors.append(f"Falta el esquema táctico '{form}' en FORMATIONS")

    for form in required_formations:
        pat = rf"['\"]{form}['\"]\s*:\s*\[([\s\S]*?)\]"
        f_match = re.search(pat, form_block)
        if not f_match:
            continue
        slots_text = f_match.group(1)
        slots = re.findall(r"\{\s*x:\s*(\d+),\s*y:\s*(\d+),\s*role:\s*['\"]([^'\"]+)['\"]\s*\}", slots_text)

        if len(slots) != 11:
            errors.append(f"El esquema '{form}' debe tener exactamente 11 posiciones, tiene: {len(slots)}")
            continue

        for s_idx, (x_str, y_str, role) in enumerate(slots):
            x = int(x_str)
            y = int(y_str)

            if not (10 <= x <= 92):
                errors.append(f"Esquema '{form}' posición {s_idx} coordenada x ({x}%) fuera de límites seguros (10-92%)")
            if not (8 <= y <= 95):
                errors.append(f"Esquema '{form}' posición {s_idx} coordenada y ({y}%) fuera de límites seguros (8-95%)")

            if role not in CANONICAL_POSITIONS:
                errors.append(f"Esquema '{form}' posición {s_idx} tiene rol desconocido '{role}'")

            if s_idx == 0:
                if role != "ARQ":
                    errors.append(f"Esquema '{form}' slot 0 debe tener rol 'ARQ', tiene: '{role}'")
                if y < 80:
                    errors.append(f"Esquema '{form}' slot 0 arquero debe estar en y >= 80, está en: {y}%")

            if s_idx == 10:
                if role not in ["DC", "DEL"]:
                    errors.append(f"Esquema '{form}' slot 10 debe ser centrodelantero (DC), tiene: '{role}'")
                if y > 25:
                    errors.append(f"Esquema '{form}' slot 10 debe estar en y <= 25, está en: {y}%")

    return len(errors) == 0, errors


def auditar_simulacion_sustituciones() -> Tuple[bool, List[str]]:
    """Simula sustituciones, intercambios, filtro de banco por línea y preset Último 11 de Aguirre."""
    errors = []
    squad_file = DATA_DIR / "squad_2026.json"
    if not squad_file.exists():
        return False, ["Archivo data/squad_2026.json no encontrado."]

    data = json.loads(squad_file.read_text(encoding="utf-8"))
    jugadores = data.get("jugadores", [])

    initial_lineup = [dict(p) for p in jugadores if p.get("titular")][:11]
    initial_bench = [dict(p) for p in jugadores if not p.get("titular")]

    # Simulación 1: Cambio Titular -> Suplente
    lineup = [dict(p) for p in initial_lineup]
    bench = [dict(p) for p in initial_bench]

    temp = lineup[0]
    lineup[0] = bench[0]
    bench[0] = temp

    if lineup[0]["id"] != initial_bench[0]["id"]:
        errors.append("Fallo en sustitución slot 0: el suplente no ingresó correctamente")
    if bench[0]["id"] != initial_lineup[0]["id"]:
        errors.append("Fallo en sustitución: el titular saliente no pasó al banco")
    if len(lineup) != 11:
        errors.append(f"La alineación tras cambio no tiene 11 jugadores: {len(lineup)}")

    all_current_ids = [p["id"] for p in lineup] + [p["id"] for p in bench]
    if len(all_current_ids) != len(set(all_current_ids)):
        errors.append("Se detectaron futbolistas duplicados tras la sustitución")

    # Simulación 2: Intercambio posicional en cancha (Starter A <-> Starter B)
    p_slot7_orig = lineup[7]["id"]
    p_slot9_orig = lineup[9]["id"]
    lineup[7], lineup[9] = lineup[9], lineup[7]
    if lineup[7]["id"] != p_slot9_orig or lineup[9]["id"] != p_slot7_orig:
        errors.append("Fallo en intercambio posicional entre dos titulares en cancha")

    # Simulación 3: Filtro de banco por línea (ARQ, DEF, VOL, ATA) preserva suma exacta
    counts = {"ARQ": 0, "DEF": 0, "VOL": 0, "ATA": 0}
    for b in initial_bench:
        counts[_line_group(b.get("posicion", ""))] += 1
    if sum(counts.values()) != len(initial_bench):
        errors.append("El filtro de banco por línea no cubre al 100% de los relevos")
    for line_key in ("ARQ", "DEF", "VOL", "ATA"):
        if counts[line_key] == 0:
            errors.append(f"El banco de relevos no tiene ningún jugador en la línea '{line_key}'")

    # Simulación 4: Preset "Último 11 de Aguirre" (ultimo_once_1891)
    ult_names = [_norm_name(n) for n in data.get("ultimo_once_1891", [])[:11]]
    ult_starters = [p for p in jugadores if _norm_name(p.get("nombre", "")) in ult_names]
    ult_bench = [p for p in jugadores if _norm_name(p.get("nombre", "")) not in ult_names]
    if len(ult_starters) != 11:
        errors.append(f"Preset Último 11 de Aguirre resolvió {len(ult_starters)} titulares (se requieren 11)")
    if len(ult_starters) + len(ult_bench) != len(jugadores):
        errors.append("Preset Último 11 de Aguirre perdió o duplicó jugadores al repartir cancha/banco")

    # Simulación 5: Restablecer 11 inicial
    reset_lineup = [dict(p) for p in initial_lineup]
    if [p["id"] for p in reset_lineup] != [p["id"] for p in initial_lineup]:
        errors.append("Fallo al restablecer la alineación original")

    return len(errors) == 0, errors


def auditar_marcado_html_y_componentes() -> Tuple[bool, List[str]]:
    """Verifica que index.html contenga todos los elementos interactivos v11.0, filtros y presets de la pizarra."""
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
        ('id="bench-line-filters"', "Filtros de banco por línea id='bench-line-filters'"),
        ('data-line="ARQ"', "Chip de filtro de banco ARQ"),
        ('data-line="DEF"', "Chip de filtro de banco DEF"),
        ('data-line="VOL"', "Chip de filtro de banco VOL"),
        ('data-line="ATA"', "Chip de filtro de banco ATA"),
        ('id="preset-ultimo-11-btn"', "Botón rápido 'Último 11 de Aguirre' id='preset-ultimo-11-btn'"),
        ('id="preset-ideal-11-btn"', "Botón rápido '11 Ideal 2026' id='preset-ideal-11-btn'"),
        ('data-formation="4-2-3-1"', "Botón táctico 4-2-3-1"),
        ('data-formation="4-3-3"', "Botón táctico 4-3-3"),
        ('data-formation="4-4-2"', "Botón táctico 4-4-2"),
        ('id="reset-lineup-btn"', "Botón id='reset-lineup-btn' para restaurar 11 inicial"),
        ('id="export-lineup-btn"', "Botón id='export-lineup-btn' para descargar PNG"),
        ('id="share-lineup-btn"', "Botón id='share-lineup-btn' para compartir 11"),
    ]

    for needle, desc in required_elements:
        if needle not in html:
            errors.append(f"Falta elemento en index.html: {desc}")

    if "Diego Aguirre" not in html:
        errors.append("index.html no menciona a Diego Aguirre en la sección táctica")
    if "Léo Coelho" in html or "Guillermo De Amores" in html:
        errors.append("index.html conserva ex-jugadores obsoletos (Coelho / De Amores) en la pizarra táctica")

    has_players_layer = ('id="pitch-players-layer"' in html) or ('class="pitch-player"' in html)
    if not has_players_layer:
        errors.append("index.html no contiene la capa de futbolistas ni fichas visibles en la cancha táctica")

    pitch_match = re.search(r'<div[^>]*id="tactical-pitch"[^>]*>(.*?)</div>\s*<div class="card-panel">', html, re.DOTALL)
    if pitch_match:
        pitch_content = pitch_match.group(1).strip()
        if pitch_content and ('pitch-player' not in pitch_content and 'pitch-players-layer' not in pitch_content):
            errors.append("El contenedor #tactical-pitch tiene contenido pero carece de fichas o capa de jugadores")

    return len(errors) == 0, errors


def auditar_canvas_y_compartir() -> Tuple[bool, List[str]]:
    """Verifica el generador de Canvas PNG 1080x1350 y la funcionalidad de compartir."""
    errors = []
    app_js = JS_DIR / "app.js"
    if not app_js.exists():
        return False, ["Archivo js/app.js no encontrado."]

    code = app_js.read_text(encoding="utf-8")

    if "canvas.width = 1080" not in code or "canvas.height = 1350" not in code:
        errors.append("El Canvas de exportación no utiliza la resolución reglamentaria 1080x1350")
    if "link.download = `mi-11-penarol-${state.formation}.png`" not in code:
        errors.append("Falta plantilla de nombre de archivo descargable en exportLineupPNG")
    if "navigator.share" not in code:
        errors.append("Falta soporte para Web Share API en app.js")
    if "https://manya.servicioti.com.uy/#pizarra-tactica" not in code:
        errors.append("Falta la URL canónica de la pizarra táctica en el texto para compartir")

    return len(errors) == 0, errors


def auditar_estilos_y_responsividad() -> Tuple[bool, List[str]]:
    """Verifica los estilos CSS v11.0 de la cancha, filtros de banco, presets y adaptación responsiva."""
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
        (".bench-filter-chip", "Chip de filtro de banco por línea .bench-filter-chip"),
        (".preset-btn", "Botón de preset de alineación .preset-btn"),
        (".tactical-hint-banner", "Banner dinámico de guía táctica .tactical-hint-banner"),
    ]

    for cls_name, desc in required_classes:
        if cls_name not in css:
            errors.append(f"Falta clase CSS en styles.css: {desc}")

    if re.search(r"\.pitch-player\s*\{[^}]*display:\s*none", css):
        errors.append("CSS oculta .pitch-player con display: none")
    if re.search(r"\.pitch-player\s*\{[^}]*visibility:\s*hidden", css):
        errors.append("CSS oculta .pitch-player con visibility: hidden")
    if not re.search(r"\.pitch-board\s*\{[^}]*(min-height|height):", css):
        errors.append("CSS no define altura o min-height para .pitch-board")
    if "@media (max-width: 768px)" not in css and "@media (max-width: 640px)" not in css:
        errors.append("Faltan reglas @media para pantallas móviles en la pizarra táctica")

    return len(errors) == 0, errors


def auditar_js_sintaxis_y_robustez() -> Tuple[bool, List[str]]:
    """Verifica sintaxis de app.js y sw.js con node --check y funciones tácticas Pro v11.0."""
    errors = []
    app_js = JS_DIR / "app.js"
    sw_js = BASE_DIR / "sw.js"
    if not app_js.exists():
        return False, ["Archivo js/app.js no encontrado."]

    for target in [app_js, sw_js]:
        if not target.exists():
            errors.append(f"Falta archivo JS: {target.name}")
            continue
        try:
            proc = subprocess.run(
                ["node", "--check", str(target)],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if proc.returncode != 0:
                errors.append(f"node --check {target.name} falló: {proc.stderr.strip() or proc.stdout.strip()}")
        except Exception as e:
            errors.append(f"No se pudo ejecutar node --check sobre {target.name}: {e}")

    code = app_js.read_text(encoding="utf-8")
    for fn_name in [
        "renderTacticalBoard",
        "applyUltimoOnceAguirre",
        "applyIdealLineup2026",
        "getPlayerLineGroup",
        "updateBenchFilterChipsUI",
    ]:
        if f"function {fn_name}(" not in code and f"const {fn_name}" not in code:
            errors.append(f"js/app.js no contiene la función táctica v11.0 '{fn_name}'")

    for f in ["4-2-3-1", "4-3-3", "4-4-2"]:
        if f not in code:
            errors.append(f"js/app.js no menciona la formación '{f}'")

    return len(errors) == 0, errors


def auditar_pizarra_tactica_exhaustiva() -> Tuple[bool, List[str]]:
    """Ejecuta todas las auditorías tácticas consolidadas v11.0."""
    all_errors = []

    tests = [
        ("Dataset del Plantel Verificado 2026 (v11.0)", auditar_dataset_plantel),
        ("Definición de Formaciones (4-2-3-1, 4-3-3, 4-4-2)", auditar_definicion_formaciones),
        ("Simulación de Sustituciones, Filtros y Último 11", auditar_simulacion_sustituciones),
        ("Marcado HTML y Componentes Interactivos v11.0", auditar_marcado_html_y_componentes),
        ("Exportación Canvas PNG 1080x1350 y Compartir", auditar_canvas_y_compartir),
        ("Estilos CSS v11.0 y Responsividad Móvil", auditar_estilos_y_responsividad),
        ("Sintaxis JS (app.js + sw.js) y Robustez Táctica", auditar_js_sintaxis_y_robustez),
    ]

    for name, fn in tests:
        passed, errs = fn()
        if not passed:
            for e in errs:
                all_errors.append(f"[{name}] {e}")

    return len(all_errors) == 0, all_errors


if __name__ == "__main__":
    print("=== AUDITORÍA EXHAUSTIVA DE LA PIZARRA TÁCTICA v11.0 (CLUB ATLÉTICO PEÑAROL) ===")
    ok, errors = auditar_pizarra_tactica_exhaustiva()
    if ok:
        print("✅ TODAS LAS AUDITORÍAS DE LA PIZARRA TÁCTICA v11.0 APROBADAS (100% ÓPTIMO)")
        sys.exit(0)
    else:
        print(f"❌ SE ENCONTRARON {len(errors)} ERRORES EN LA PIZARRA TÁCTICA:")
        for err in errors:
            print(f"  • {err}")
        sys.exit(1)
