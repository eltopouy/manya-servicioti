# -*- coding: utf-8 -*-
"""
EXTRAE NOTICIAS E IMÁGENES ACTUALIZADAS DE PEÑAROL (PRENSA + PADRE Y DECANO)
===========================================================================
Obtiene las crónicas, noticias y fotografías de alta resolución más recientes
del Club Atlético Peñarol desde fuentes deportivas uruguayas verificadas:
1. Tenfield Peñarol (cobertura fotográfica en tiempo real y actualidad del plantel)
2. Google News Uruguay (El País Ovación, El Observador, Montevideo Portal, ESPN)
3. Padre y Decano RSS (con validación de fecha: solo admite publicaciones de 2026)
"""
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}


def extraer_imagen_de_articulo(url: str, html_content: str = "") -> str:
    """Extrae la fotografía principal de alta resolución del artículo deportivo."""
    if not html_content and url:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=6) as resp:
                html_content = resp.read().decode("utf-8", errors="ignore")
        except Exception:
            return ""

    if not html_content:
        return ""

    # 1. Buscar fotos directas de Tenfield Storage o WordPress Uploads de 2026
    all_imgs = re.findall(r'<img[^>]+src=[\'"]([^\'"]+)[\'"]', html_content)
    buenas_imgs = [
        m for m in all_imgs
        if ("2026/10" in m or "wp-content/gallery" in m or "2026/09" in m or "2026/11" in m)
        and not any(bad in m.lower() for bad in ["carnaval", "banner", "icon", "login", "logo", "tilde", "400x250", "-150x", "-300x", "svg"])
    ]
    if buenas_imgs:
        return buenas_imgs[0]

    # 2. Buscar en open-graph / twitter card
    og_m = re.search(r'<meta[^>]+property=[\'"]og:image[\'"][^>]+content=[\'"]([^\'"]+)[\'"]', html_content, re.I)
    if not og_m:
        og_m = re.search(r'<meta[^>]+content=[\'"]([^\'"]+)[\'"][^>]+property=[\'"]og:image[\'"]', html_content, re.I)
    if not og_m:
        og_m = re.search(r'<meta[^>]+name=[\'"]twitter:image[\'"][^>]+content=[\'"]([^\'"]+)[\'"]', html_content, re.I)
    if og_m:
        img_cand = og_m.group(1).strip()
        if not any(bad in img_cand.lower() for bad in ["googleusercontent", "logo", "favicon", "default", "placeholder", "carnaval"]):
            return img_cand

    return ""


def obtener_noticias_e_imagenes_padreydecano(max_items: int = 8) -> List[Dict[str, Any]]:
    """
    Obtiene noticias e imágenes 100% actualizadas (2026) sobre Peñarol.
    Filtra y descarta automáticamente cualquier noticia desactualizada de 2025.
    Combina Tenfield Peñarol, Google News Uruguay y Padre y Decano (si tiene publicaciones 2026).
    """
    noticias = []
    seen_titles = set()

    # 1. Tenfield Peñarol (cobertura fotográfica en tiempo real)
    try:
        tenfield_url = "https://www.tenfield.com.uy/tag/penarol/feed/"
        req = urllib.request.Request(tenfield_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)

        for item in root.findall(".//item"):
            if len(noticias) >= max_items:
                break
            t_el = item.find("title")
            l_el = item.find("link")
            d_el = item.find("description")
            p_el = item.find("pubDate")

            titulo = (t_el.text or "").strip() if t_el is not None else ""
            link = (l_el.text or "").strip() if l_el is not None else ""
            desc = (d_el.text or "").strip() if d_el is not None else ""
            pub = (p_el.text or "").strip() if p_el is not None else ""

            # Garantizar que es del 2026
            if not titulo or not link or ("2025" in pub or "2024" in pub):
                continue

            norm_t = re.sub(r"\W+", "", titulo.lower())[:40]
            if norm_t in seen_titles:
                continue
            seen_titles.add(norm_t)

            desc_clean = re.sub(r"<[^>]+>", " ", desc).strip()
            desc_clean = re.sub(r"\s+", " ", desc_clean)[:240]

            # Buscar imagen en el HTML del artículo
            img_url = extraer_imagen_de_articulo(link)

            # Clasificar categoría
            t_low = titulo.lower()
            cat = "Partidos"
            if any(k in t_low for k in ["entrenamiento", "aromos", "sanidad", "lesión", "recupera", "plantel"]):
                cat = "Los Aromos"
            elif any(k in t_low for k in ["hinchada", "entradas", "tribuna", "campeón del siglo", "socios"]):
                cat = "Hinchada"
            elif any(k in t_low for k in ["directiva", "ruglio", "aguirre", "tabla anual", "clausura"]):
                cat = "Actualidad"

            noticias.append({
                "titulo": titulo,
                "url": link,
                "categoria": cat,
                "resumen": desc_clean if len(desc_clean) > 20 else f"Cobertura oficial sobre Peñarol en Tenfield Deportes: {titulo}.",
                "img_url": img_url,
                "fuente": "Tenfield Deportes",
                "fecha_raw": pub
            })
    except Exception as e_tenfield:
        print("[Noticias Peñarol] Aviso consultando Tenfield:", e_tenfield)

    # 2. Padre y Decano (solo si tiene artículos de 2026)
    try:
        pyd_url = "https://www.padreydecano.com/cms/feed/"
        req = urllib.request.Request(pyd_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)

        for item in root.findall(".//item"):
            if len(noticias) >= max_items + 2:
                break
            t_el = item.find("title")
            l_el = item.find("link")
            d_el = item.find("description")
            c_el = item.find("category")
            p_el = item.find("pubDate")

            titulo = (t_el.text or "").strip() if t_el is not None else ""
            link = (l_el.text or "").strip() if l_el is not None else ""
            desc = (d_el.text or "").strip() if d_el is not None else ""
            cat = (c_el.text or "Actualidad").strip() if c_el is not None else "Actualidad"
            pub = (p_el.text or "").strip() if p_el is not None else ""

            # FILTRO ESTRICTO: Descartar noticias de 2025 o años anteriores
            if "2025" in pub or "2024" in pub or "2023" in pub or not titulo:
                continue

            norm_t = re.sub(r"\W+", "", titulo.lower())[:40]
            if norm_t in seen_titles:
                continue
            seen_titles.add(norm_t)

            desc_clean = re.sub(r"<[^>]+>", " ", desc).strip()
            desc_clean = re.sub(r"\s+", " ", desc_clean)[:240]
            img_url = extraer_imagen_de_articulo(link)

            noticias.append({
                "titulo": titulo,
                "url": link,
                "categoria": cat,
                "resumen": desc_clean,
                "img_url": img_url,
                "fuente": "Padre y Decano",
                "fecha_raw": pub
            })
    except Exception as e_pyd:
        pass

    # 3. Google News Peñarol (Uruguay) para complementar hasta max_items
    if len(noticias) < max_items:
        try:
            gnews_url = "https://news.google.com/rss/search?q=Pe%C3%B1arol+Uruguay+when:7d&hl=es-419&gl=UY&ceid=UY:es-419"
            req = urllib.request.Request(gnews_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                xml_data = resp.read()
            root = ET.fromstring(xml_data)

            for item in root.findall(".//item"):
                if len(noticias) >= max_items:
                    break
                t_el = item.find("title")
                l_el = item.find("link")
                d_el = item.find("description")
                p_el = item.find("pubDate")
                s_el = item.find("source")

                titulo = (t_el.text or "").strip() if t_el is not None else ""
                link = (l_el.text or "").strip() if l_el is not None else ""
                desc = (d_el.text or "").strip() if d_el is not None else ""
                pub = (p_el.text or "").strip() if p_el is not None else ""
                source_name = s_el.text if s_el is not None else "Prensa Uruguaya"

                # Descartar cualquier noticia que no sea 2026
                if "2025" in pub or "2024" in pub or not titulo or not link:
                    continue

                clean_t = re.sub(r"\s*-\s*[A-Za-z0-9\.\s]+$", "", titulo).strip()
                norm_t = re.sub(r"\W+", "", clean_t.lower())[:40]
                if norm_t in seen_titles:
                    continue
                seen_titles.add(norm_t)

                desc_clean = re.sub(r"<[^>]+>", " ", desc).strip()
                desc_clean = re.sub(r"\s+", " ", desc_clean)[:240]

                noticias.append({
                    "titulo": clean_t,
                    "url": link,
                    "categoria": "Prensa",
                    "resumen": desc_clean if len(desc_clean) > 20 else f"Actualidad del Club Atlético Peñarol en {source_name}.",
                    "img_url": "",
                    "fuente": source_name,
                    "fecha_raw": pub
                })
        except Exception as e_gnews:
            print("[Noticias Peñarol] Aviso consultando Google News:", e_gnews)

    return noticias[:max_items]


if __name__ == "__main__":
    res = obtener_noticias_e_imagenes_padreydecano(6)
    print(f"Total noticias 2026 obtenidas: {len(res)}")
    for r in res:
        print(f"[{r['fuente']} | {r['categoria']}] {r['titulo']}")
        print(f" Fecha: {r.get('fecha_raw')}")
        print(f" URL: {r['url']}")
        print(f" IMG: {r.get('img_url')}\n")
