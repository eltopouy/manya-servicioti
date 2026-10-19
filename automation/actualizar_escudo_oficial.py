# -*- coding: utf-8 -*-
"""
ACTUALIZADOR DEL ESCUDO OFICIAL DE PEÑAROL (assets/img/)
========================================================
1. Lee el SVG oficial original de Constante Facello (3 cúspides, 11 estrellas, 9 franjas).
2. Normaliza el color amarillo al oro oficial del club: #FFC20E.
3. Exporta con Playwright y Pillow las versiones de alta fidelidad:
   - assets/img/escudo_penarol_oficial.svg
   - assets/img/escudo_penarol_oficial.png
   - assets/img/escudo_penarol_oficial.webp
   - assets/img/escudo_penarol_oficial_alpha.webp
   - assets/img/escudos/escudo_penarol.svg
   - assets/img/escudos/escudo_penarol.png
   - assets/img/escudos/escudo_penarol.webp
"""

import os
import re
import sys
import shutil
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


BASE_DIR = Path(__file__).resolve().parent.parent
COMMONS_SVG = Path(r"C:\Users\Andrés\.gemini\antigravity\brain\cd7f821d-a75f-472b-9279-c95f5b809106\scratch\escudo_commons.svg")

if not COMMONS_SVG.exists():
    raise FileNotFoundError(f"No se encontró el SVG de referencia en {COMMONS_SVG}")

raw_svg = COMMONS_SVG.read_text(encoding="utf-8")

# Limpieza profunda de namespaces y tags de Inkscape
clean = re.sub(r'xmlns:sodipodi=["\'][^"\']+["\']', '', raw_svg)
clean = re.sub(r'xmlns:inkscape=["\'][^"\']+["\']', '', clean)
clean = re.sub(r'<sodipodi:namedview[\s\S]*?</sodipodi:namedview>', '', clean)
clean = re.sub(r'<metadata[\s\S]*?</metadata>', '', clean)
clean = re.sub(r'sodipodi:[a-zA-Z0-9_\-]+="[^"]*"', '', clean)
clean = re.sub(r'inkscape:[a-zA-Z0-9_\-]+="[^"]*"', '', clean)

# Estandarización al color oro oficial de Peñarol (#FFC20E)
clean = clean.replace('#ffe600', '#FFC20E').replace('#FFE600', '#FFC20E')

# Asegurar viewBox y dimensiones limpias
clean = re.sub(r'width="[^"]+"', 'width="100%"', clean, count=1)
clean = re.sub(r'height="[^"]+"', 'height="100%"', clean, count=1)

# Guardar SVG oficial principal
dest_svg = BASE_DIR / "assets" / "img" / "escudo_penarol_oficial.svg"
dest_svg.write_text(clean.strip(), encoding="utf-8")
print(f"[✓] SVG guardado en {dest_svg}")

# Guardar réplica en assets/img/escudos/
dest_escudos_svg = BASE_DIR / "assets" / "img" / "escudos" / "escudo_penarol.svg"
dest_escudos_svg.write_text(clean.strip(), encoding="utf-8")
print(f"[✓] SVG réplica guardado en {dest_escudos_svg}")

# Renderizar PNG transparente en alta definición usando Playwright (716x962)
html_temp = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; }}
  svg {{ width: 716px; height: 962px; display: block; }}
</style>
</head>
<body>
{clean}
</body>
</html>
"""
temp_html_path = BASE_DIR / "automation" / "_temp_crest.html"
temp_html_path.write_text(html_temp, encoding="utf-8")

temp_png = BASE_DIR / "automation" / "_temp_crest.png"
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 716, "height": 962}, device_scale_factor=2)
    page.goto(temp_html_path.as_uri())
    page.screenshot(path=str(temp_png), omit_background=True)
    browser.close()

if temp_html_path.exists():
    temp_html_path.unlink()

print("[✓] Renderizado de PNG transparente completado")

# Optimizar PNG y WebP con Pillow en varios tamaños
img = Image.open(temp_png).convert("RGBA")

# 1. Versión oficial grande (716 x 962)
dest_png = BASE_DIR / "assets" / "img" / "escudo_penarol_oficial.png"
img.save(dest_png, format="PNG", optimize=True)

dest_webp = BASE_DIR / "assets" / "img" / "escudo_penarol_oficial.webp"
img.save(dest_webp, format="WEBP", quality=95, method=6)

dest_alpha = BASE_DIR / "assets" / "img" / "escudo_penarol_oficial_alpha.webp"
img.save(dest_alpha, format="WEBP", quality=95, method=6)

# 2. Versión Match Center / Escudos (256 x 344)
img_escudo = img.resize((256, 344), Image.Resampling.LANCZOS)
dest_escudo_png = BASE_DIR / "assets" / "img" / "escudos" / "escudo_penarol.png"
img_escudo.save(dest_escudo_png, format="PNG", optimize=True)

dest_escudo_webp = BASE_DIR / "assets" / "img" / "escudos" / "escudo_penarol.webp"
img_escudo.save(dest_escudo_webp, format="WEBP", quality=90, method=6)

if temp_png.exists():
    temp_png.unlink()

print("[✓] Todos los formatos PNG y WebP del Escudo Oficial de Peñarol fueron actualizados con éxito.")
