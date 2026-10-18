# -*- coding: utf-8 -*-
"""
DESCARGADOR Y OPTIMIZADOR AUTOMÁTICO DE ESCUDOS DEL FÚTBOL URUGUAYO
==================================================================
Descarga los escudos oficiales de los rivales desde fuentes de alta calidad
(ESPN CDN oficial y Wikimedia Commons), los normaliza con canal Alpha transparente,
los redimensiona con remuestreo Lanczos (máximo 240x240 px) y los exporta en
WebP ultraligero (< 25 KB) y PNG optimizado.

Genera además el catálogo `data/escudos_uruguay.json` para resolución instantánea
por nombre, sigla o alias en el frontend y en los motores de publicación.
"""

import os
import sys
import json
import io
import shutil
import urllib.request
import unicodedata
from pathlib import Path
from PIL import Image

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ESCUDOS_DIR = BASE_DIR / "assets" / "img" / "escudos"

DATA_DIR.mkdir(parents=True, exist_ok=True)
ESCUDOS_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 ManyaServicioTI/2.0"
}

# Definición maestra de los clubes de Primera y Segunda División uruguaya
CLUBES = [
    {
        "slug": "penarol",
        "nombre": "Club Atlético Peñarol",
        "nombre_corto": "Peñarol",
        "abreviatura": "CAP",
        "es_penarol": True,
        "aliases": ["peñarol", "penarol", "cap", "carbonero", "manya", "aurinegro", "club atlético peñarol", "club atletico penarol"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/2683.png",
        "local_source": str(BASE_DIR / "assets" / "img" / "escudo_penarol_oficial.png")
    },
    {
        "slug": "liverpool",
        "nombre": "Liverpool Fútbol Club",
        "nombre_corto": "Liverpool",
        "abreviatura": "LIV",
        "es_penarol": False,
        "aliases": ["liverpool", "liv", "liverpool fc", "liverpool fútbol club", "liverpool futbol club", "negriazul"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/5492.png"
    },
    {
        "slug": "nacional",
        "nombre": "Club Nacional de Football",
        "nombre_corto": "Nacional",
        "abreviatura": "NAC",
        "es_penarol": False,
        "aliases": ["nacional", "nac", "cndf", "club nacional de football", "tricolor", "bolso"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/2684.png"
    },
    {
        "slug": "defensor_sporting",
        "nombre": "Defensor Sporting Club",
        "nombre_corto": "Defensor Sporting",
        "abreviatura": "DEF",
        "es_penarol": False,
        "aliases": ["defensor sporting", "defensor", "dsc", "def", "tuerto", "violeta", "defensor sporting club"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/1007.png"
    },
    {
        "slug": "danubio",
        "nombre": "Danubio Fútbol Club",
        "nombre_corto": "Danubio",
        "abreviatura": "DAN",
        "es_penarol": False,
        "aliases": ["danubio", "dan", "dfc", "danubio fútbol club", "danubio futbol club", "la franja"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/4817.png"
    },
    {
        "slug": "boston_river",
        "nombre": "Club Atlético Boston River",
        "nombre_corto": "Boston River",
        "abreviatura": "BOS",
        "es_penarol": False,
        "aliases": ["boston river", "boston", "bos", "sastre", "club atlético boston river", "club atletico boston river"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/9999.png"
    },
    {
        "slug": "montevideo_wanderers",
        "nombre": "Montevideo Wanderers Fútbol Club",
        "nombre_corto": "Wanderers",
        "abreviatura": "WAN",
        "es_penarol": False,
        "aliases": ["wanderers", "montevideo wanderers", "wan", "mwfc", "bohemio", "montevideo wanderers fútbol club"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/5501.png"
    },
    {
        "slug": "cerro",
        "nombre": "Club Atlético Cerro",
        "nombre_corto": "Cerro",
        "abreviatura": "CER",
        "es_penarol": False,
        "aliases": ["cerro", "cer", "cac", "club atlético cerro", "club atletico cerro", "villero"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/5490.png"
    },
    {
        "slug": "cerro_largo",
        "nombre": "Cerro Largo Fútbol Club",
        "nombre_corto": "Cerro Largo",
        "abreviatura": "CLG",
        "es_penarol": False,
        "aliases": ["cerro largo", "clg", "cerr", "clfc", "cerro largo fútbol club", "cerro largo futbol club", "arachán", "arachan"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/9902.png"
    },
    {
        "slug": "racing",
        "nombre": "Racing Club de Montevideo",
        "nombre_corto": "Racing",
        "abreviatura": "RAC",
        "es_penarol": False,
        "aliases": ["racing", "racing (montevideo)", "rac", "rcm", "racing club de montevideo", "la escuelita", "cervecero"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/9903.png"
    },
    {
        "slug": "progreso",
        "nombre": "Club Atlético Progreso",
        "nombre_corto": "Progreso",
        "abreviatura": "PSO",
        "es_penarol": False,
        "aliases": ["progreso", "pso", "pro", "caprogreso", "club atlético progreso", "club atletico progreso", "gaucho del pantanoso"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/6866.png"
    },
    {
        "slug": "deportivo_maldonado",
        "nombre": "Club Deportivo Maldonado",
        "nombre_corto": "Deportivo Maldonado",
        "abreviatura": "MAL",
        "es_penarol": False,
        "aliases": ["deportivo maldonado", "maldonado", "mal", "dep maldonado", "club deportivo maldonado", "rojiverde"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/10000.png"
    },
    {
        "slug": "montevideo_city_torque",
        "nombre": "Montevideo City Torque",
        "nombre_corto": "Torque",
        "abreviatura": "MCT",
        "es_penarol": False,
        "aliases": ["montevideo city torque", "torque", "mct", "city torque", "ciudadanos"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/19002.png"
    },
    {
        "slug": "albion",
        "nombre": "Albion Football Club",
        "nombre_corto": "Albion",
        "abreviatura": "ALB",
        "es_penarol": False,
        "aliases": ["albion", "alb", "albion fc", "albion football club", "pionero"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/21403.png"
    },
    {
        "slug": "juventud",
        "nombre": "Club Atlético Juventud de Las Piedras",
        "nombre_corto": "Juventud",
        "abreviatura": "JUV",
        "es_penarol": False,
        "aliases": ["juventud", "juv", "juventud de las piedras", "club atlético juventud", "pedrense"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/8416.png"
    },
    {
        "slug": "central_espanol",
        "nombre": "Central Español Fútbol Club",
        "nombre_corto": "Central Español",
        "abreviatura": "CEFC",
        "es_penarol": False,
        "aliases": ["central español", "central espanol", "cefc", "palermitano", "central español fútbol club"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/131688.png"
    },
    {
        "slug": "miramar_misiones",
        "nombre": "Club Sportivo Miramar Misiones",
        "nombre_corto": "Miramar Misiones",
        "abreviatura": "MIR",
        "es_penarol": False,
        "aliases": ["miramar misiones", "miramar", "mir", "cebrita", "club sportivo miramar misiones"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/5493.png"
    },
    {
        "slug": "rampla_juniors",
        "nombre": "Rampla Juniors Fútbol Club",
        "nombre_corto": "Rampla Juniors",
        "abreviatura": "RAM",
        "es_penarol": False,
        "aliases": ["rampla juniors", "rampla", "ram", "rjfc", "rampla juniors fútbol club", "picapiedra"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/5496.png"
    },
    {
        "slug": "river_plate",
        "nombre": "Club Atlético River Plate (Uruguay)",
        "nombre_corto": "River Plate",
        "abreviatura": "RIV",
        "es_penarol": False,
        "aliases": ["river plate", "river", "riv", "darsenero", "river plate uruguay", "club atlético river plate"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/5498.png"
    },
    {
        "slug": "plaza_colonia",
        "nombre": "Club Atlético Plaza Colonia",
        "nombre_corto": "Plaza Colonia",
        "abreviatura": "PLA",
        "es_penarol": False,
        "aliases": ["plaza colonia", "plaza", "pla", "patablanca", "club atlético plaza colonia"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/5495.png"
    },
    {
        "slug": "rentistas",
        "nombre": "Club Atlético Rentistas",
        "nombre_corto": "Rentistas",
        "abreviatura": "REN",
        "es_penarol": False,
        "aliases": ["rentistas", "ren", "bicho colorado", "club atlético rentistas"],
        "url": "https://a.espncdn.com/i/teamlogos/soccer/500/5497.png"
    },
    {
        "slug": "fenix",
        "nombre": "Centro Atlético Fénix",
        "nombre_corto": "Fénix",
        "abreviatura": "FEN",
        "es_penarol": False,
        "aliases": ["fenix", "fénix", "fen", "caf", "albivioleta", "centro atlético fénix", "centro atletico fenix"],
        "url": "https://upload.wikimedia.org/wikipedia/en/thumb/0/00/Centro_Atl%C3%A9tico_F%C3%A9nix_logo.svg/500px-Centro_Atl%C3%A9tico_F%C3%A9nix_logo.svg.png"
    }
]


def normalizar_texto(txt: str) -> str:
    """Remueve acentos, signos y normaliza a minúsculas para matching de alias."""
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return "".join(c for c in txt.lower() if c.isalnum() or c.isspace()).strip()


def optimizar_imagen(img_bytes: bytes, out_webp: Path, out_png: Path, max_size: int = 240) -> tuple:
    """
    Carga la imagen, conserva canal alfa, redimensiona y guarda en WebP y PNG.
    Retorna (tam_webp_kb, tam_png_kb).
    """
    im = Image.open(io.BytesIO(img_bytes))
    if im.mode != "RGBA":
        im = im.convert("RGBA")

    # Escalar proporcionalmente hasta max_size
    im.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    # Guardar WebP ultraligero
    im.save(out_webp, format="WEBP", quality=90, method=6)
    # Guardar PNG optimizado
    im.save(out_png, format="PNG", optimize=True)

    kb_webp = round(out_webp.stat().st_size / 1024.0, 1)
    kb_png = round(out_png.stat().st_size / 1024.0, 1)
    return kb_webp, kb_png


def procesar_todos():
    print(f"=== INICIANDO DESCARGA Y OPTIMIZACIÓN DE ESCUDOS ({len(CLUBES)} CLUBES) ===")
    catalogo = {}
    alias_index = {}

    for c in CLUBES:
        slug = c["slug"]
        webp_path = ESCUDOS_DIR / f"escudo_{slug}.webp"
        png_path = ESCUDOS_DIR / f"escudo_{slug}.png"

        print(f"\nProcesando: {c['nombre']} ({c['abreviatura']})...")

        img_bytes = None
        # Si es Peñarol y ya existe localmente, leerlo
        if c.get("local_source") and Path(c["local_source"]).exists():
            try:
                img_bytes = Path(c["local_source"]).read_bytes()
                print(f"  -> Usando archivo local de alta fidelidad: {c['local_source']}")
            except Exception as e:
                print(f"  -> Aviso leyendo local: {e}")

        if not img_bytes and c.get("url"):
            try:
                req = urllib.request.Request(c["url"], headers=HEADERS)
                with urllib.request.urlopen(req, timeout=12) as resp:
                    img_bytes = resp.read()
                print(f"  -> Descargado exitosamente desde: {c['url'][:60]}...")
            except Exception as e_net:
                print(f"  -> Error descargando {c['url']}: {e_net}")

        if img_bytes:
            kb_webp, kb_png = optimizar_imagen(img_bytes, webp_path, png_path, max_size=240)
            print(f"  -> Optimizado con éxito: WebP={kb_webp} KB, PNG={kb_png} KB")
        else:
            print(f"  -> ADVERTENCIA: No se obtuvieron bytes para {c['nombre']}")

        # Registrar en catálogo
        info = {
            "slug": slug,
            "nombre": c["nombre"],
            "nombre_corto": c["nombre_corto"],
            "abreviatura": c["abreviatura"],
            "es_penarol": c["es_penarol"],
            "ruta_webp": f"assets/img/escudos/escudo_{slug}.webp",
            "ruta_png": f"assets/img/escudos/escudo_{slug}.png",
            "kb_webp": round(webp_path.stat().st_size / 1024.0, 1) if webp_path.exists() else 0,
            "aliases": c["aliases"]
        }
        catalogo[slug] = info

        # Registrar aliases
        for a in c["aliases"]:
            alias_index[normalizar_texto(a)] = slug
        alias_index[normalizar_texto(c["nombre"])] = slug
        alias_index[normalizar_texto(c["nombre_corto"])] = slug
        alias_index[normalizar_texto(c["abreviatura"])] = slug

    # Si Peñarol tiene SVG oficial, copiarlo también a la carpeta de escudos
    penarol_svg = BASE_DIR / "assets" / "img" / "escudo_penarol_oficial.svg"
    if penarol_svg.exists():
        shutil.copy2(penarol_svg, ESCUDOS_DIR / "escudo_penarol.svg")

    output_payload = {
        "actualizado": "2026-10-18T20:30:00-03:00",
        "total_clubes": len(catalogo),
        "clubes": catalogo,
        "alias_index": alias_index
    }

    out_json = DATA_DIR / "escudos_uruguay.json"
    out_json.write_text(json.dumps(output_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✓ Catálogo guardado en {out_json} con {len(catalogo)} clubes y {len(alias_index)} alias.")


if __name__ == "__main__":
    procesar_todos()
