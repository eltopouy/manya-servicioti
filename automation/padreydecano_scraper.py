# -*- coding: utf-8 -*-
"""
EXTRAE NOTICIAS E IMÁGENES REALES DE PADRE Y DECANO
===================================================
Descarga los artículos más recientes del RSS de padreydecano.com,
extrae la fotografía principal de cada uno y devuelve una lista estructurada.
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

def obtener_noticias_e_imagenes_padreydecano(max_items: int = 8) -> List[Dict[str, Any]]:
    rss_url = "https://www.padreydecano.com/cms/feed/"
    req = urllib.request.Request(rss_url, headers=HEADERS)
    noticias = []
    
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        items = root.findall(".//item")
        
        for item in items[:max_items]:
            t_el = item.find("title")
            l_el = item.find("link")
            d_el = item.find("description")
            c_el = item.find("category")
            
            titulo = (t_el.text or "").strip() if t_el is not None else ""
            link = (l_el.text or "").strip() if l_el is not None else ""
            desc = (d_el.text or "").strip() if d_el is not None else ""
            cat = (c_el.text or "Actualidad").strip() if c_el is not None else "Actualidad"
            
            # Limpiar HTML del resumen
            desc_clean = re.sub(r"<[^>]+>", " ", desc).strip()
            desc_clean = re.sub(r"\s+", " ", desc_clean)[:240]
            
            # Si el artículo tiene link, intentar extraer la imagen de cabecera
            img_url = ""
            if link:
                try:
                    art_req = urllib.request.Request(link, headers=HEADERS)
                    with urllib.request.urlopen(art_req, timeout=8) as a_resp:
                        a_html = a_resp.read().decode("utf-8", errors="ignore")
                    
                    # Buscar imágenes de contenido de uploads
                    matches = re.findall(r'https?://www\.padreydecano\.com/cms/wp-content/uploads/\d{4}/\d{2}/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)', a_html)
                    # Descartar thumbnails diminutos si hay versión grande
                    buenas_imgs = [m for m in matches if not any(x in m for x in ["-102x", "-26x", "-240x", "-150x"])]
                    if buenas_imgs:
                        img_url = buenas_imgs[0]
                    elif matches:
                        img_url = matches[0]
                except Exception as e_art:
                    pass
            
            noticias.append({
                "titulo": titulo,
                "url": link,
                "categoria": cat,
                "resumen": desc_clean,
                "img_url": img_url,
                "fuente": "Padre y Decano"
            })
    except Exception as e:
        print("[Padre y Decano] Error obteniendo feed:", e)
        
    return noticias

if __name__ == "__main__":
    res = obtener_noticias_e_imagenes_padreydecano(5)
    for r in res:
        print(f"[{r['categoria']}] {r['titulo']}")
        print(f" URL: {r['url']}")
        print(f" IMG: {r['img_url']}\n")
