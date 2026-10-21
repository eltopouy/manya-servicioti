# -*- coding: utf-8 -*-
import sys
import ssl
import re
import urllib.request
import json
from pathlib import Path
from bs4 import BeautifulSoup

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def parse_auf_liga():
    url = "https://www.auf.org.uy/liga-auf-uruguaya/"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Extraer escudos y nombres del carrusel oficial
    clubs_found = {}
    club_items = soup.find_all(class_=re.compile(r'club2', re.I))
    for c in club_items:
        txt = c.get_text(strip=True)
        img = c.find("img")
        img_src = img["src"] if img else ""
        if img_src and not img_src.startswith("http"):
            img_src = f"https://www.auf.org.uy{img_src}"
        
        # Filtrar abreviatura de 3 letras al final si existe
        m = re.match(r'^(.*?)([A-Z]{3})$', txt)
        if m:
            nombre = m.group(1).strip()
            abrev = m.group(2).strip()
        else:
            nombre = txt
            abrev = ""
        
        if nombre and nombre not in clubs_found:
            clubs_found[nombre] = {
                "nombre": nombre,
                "abreviatura": abrev,
                "escudo_auf": img_src
            }

    # 2. Extraer bloques de tablas de posiciones
    # AUF tiene divs con class "cont-tabla_posiciones"
    tablas_bloques = soup.find_all(class_=re.compile(r'cont-tabla_posiciones', re.I))
    tablas_parsed = []
    
    for tb in tablas_bloques:
        # Título de la tabla
        title_el = tb.find_previous(["h2", "h3", "h4", "div", "span"], class_=re.compile(r'titulo|name|header', re.I))
        title_text = tb.get_text(strip=True)[:40]
        rows = tb.find_all(class_=re.compile(r'item-tabla_posiciones', re.I))
        
        tabla_filas = []
        for r in rows:
            if "titular" in r.get("class", []):
                continue
            cols = [div.get_text(strip=True) for div in r.find_all(["div", "span"]) if div.get_text(strip=True)]
            # O texto plano si no hay divs
            if not cols:
                txt_row = r.get_text(strip=True)
                cols = [txt_row]
            tabla_filas.append(cols)
        
        if tabla_filas:
            tablas_parsed.append({
                "header_sample": title_text,
                "total_filas": len(tabla_filas),
                "primeras_filas": tabla_filas[:5]
            })

    result = {
        "fuente": "AUF - Asociación Uruguaya de Fútbol (https://www.auf.org.uy/liga-auf-uruguaya/)",
        "total_clubes_registrados": len(clubs_found),
        "clubes": clubs_found,
        "tablas": tablas_parsed[:4]
    }
    
    out_path = DATA_DIR / "auf_liga_datos.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ AUF Liga Datos extraídos: {len(clubs_found)} clubes detectados.")
    for k, v in list(clubs_found.items())[:8]:
        print(f"   - {k} ({v['abreviatura']}) -> {v['escudo_auf']}")
    return result

if __name__ == "__main__":
    parse_auf_liga()
