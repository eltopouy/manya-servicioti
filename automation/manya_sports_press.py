# -*- coding: utf-8 -*-
"""
Módulo de Recolección y Análisis Exhaustivo de Prensa Deportiva de Peñarol.
Fuentes integradas:
  - Ovación Digital (El País Uruguay)
  - Referí (El Observador)
  - Tenfield Deportes (VTV)
  - FútbolUy (Montevideo Portal)
  - Padre y Decano (Portal del Hincha Aurinegro)
  - Google News Peñarol
"""

import sys
import re
import html
import json
import logging
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

logger = logging.getLogger("ManyaSportsPress")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

UY_TZ = timezone(timedelta(hours=-3))

HEADERS_HTTP = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 "
        "(ServicioTI-ManyaSportsPress/2.0)"
    )
}

KEYWORDS_RELEVANTES = [
    "peñarol", "aurinegro", "carbonero", "manya", "campeón del siglo",
    "diego aguirre", "leonardo fernández", "silvera", "baez", "juventud",
    "liverpool", "clausura", "tabla anual"
]


class ManyaSportsPressService:
    """Recolector, normalizador y rankeador de prensa deportiva especializada."""

    FUENTES_CONFIG = [
        {
            "id": "ovacion_el_pais",
            "nombre": "Ovación Digital (El País)",
            "tipo": "google_news_site",
            "query": "site:elpais.com.uy+Peñarol",
            "peso": 1.2
        },
        {
            "id": "referi_el_observador",
            "nombre": "Referí (El Observador)",
            "tipo": "google_news_site",
            "query": "site:elobservador.com.uy+Peñarol",
            "peso": 1.2
        },
        {
            "id": "tenfield_deportes",
            "nombre": "Tenfield Deportes",
            "tipo": "google_news_site",
            "query": "site:tenfield.com.uy+Peñarol",
            "peso": 1.1
        },
        {
            "id": "futbol_uy",
            "nombre": "FútbolUy (Montevideo Portal)",
            "tipo": "rss_direct",
            "url": "https://www.montevideo.com.uy/anxml.aspx?60",
            "peso": 1.1
        },
        {
            "id": "padre_y_decano",
            "nombre": "Padre y Decano",
            "tipo": "rss_direct",
            "url": "https://www.padreydecano.com/cms/feed/",
            "peso": 1.3
        },
        {
            "id": "google_news_penarol",
            "nombre": "Google News Deportes Peñarol",
            "tipo": "google_news_site",
            "query": "Peñarol futbol Uruguay",
            "peso": 1.0
        }
    ]

    @classmethod
    def _limpiar_texto(cls, texto: Optional[str]) -> str:
        if not texto:
            return ""
        texto = re.sub(r"<[^>]+>", " ", texto)
        texto = html.unescape(texto)
        texto = re.sub(r"\s+", " ", texto)
        return texto.strip()

    @classmethod
    def _es_noticia_penarol(cls, titulo: str, descripcion: str) -> bool:
        combinado = f"{titulo} {descripcion}".lower()
        return any(k in combinado for k in KEYWORDS_RELEVANTES)

    @classmethod
    def recolectar_de_rss(cls, url: str, fuente_nombre: str, peso: float = 1.0, es_query_especifica: bool = True) -> List[Dict[str, Any]]:
        items = []
        try:
            req = urllib.request.Request(url, headers=HEADERS_HTTP)
            with urllib.request.urlopen(req, timeout=12) as resp:
                raw_bytes = resp.read()
                try:
                    root = ET.fromstring(raw_bytes)
                except ET.ParseError:
                    root = ET.fromstring(raw_bytes.decode("utf-8", errors="replace"))

            for node in root.findall(".//item"):
                tit = cls._limpiar_texto(node.findtext("title", ""))
                link = cls._limpiar_texto(node.findtext("link", ""))
                desc = cls._limpiar_texto(node.findtext("description", ""))
                pub = cls._limpiar_texto(node.findtext("pubDate", ""))

                if not tit or not link:
                    continue

                if not es_query_especifica and not cls._es_noticia_penarol(tit, desc):
                    continue

                items.append({
                    "titulo": tit,
                    "url": link,
                    "resumen": desc[:280] + ("..." if len(desc) > 280 else ""),
                    "fuente": fuente_nombre,
                    "fecha_raw": pub,
                    "peso": peso
                })
        except Exception as e:
            logger.warning(f"[Prensa Deportiva] Error en {fuente_nombre}: {e}")

        return items

    @classmethod
    def recolectar_todas(cls, max_por_fuente: int = 15) -> List[Dict[str, Any]]:
        """Descarga y consolida noticias de todas las fuentes deportivas."""
        todas = []
        logger.info("[Prensa Deportiva] Iniciando escaneo exhaustivo de periódicos deportivos...")

        for f in cls.FUENTES_CONFIG:
            f_tipo = f["tipo"]
            f_nombre = f["nombre"]
            f_peso = f["peso"]

            if f_tipo == "rss_direct":
                url = f["url"]
                es_especifica = (f["id"] == "padre_y_decano")
            else:
                q = urllib.parse.quote_plus(f["query"], safe=":+")
                url = f"https://news.google.com/rss/search?q={q}&hl=es-419&gl=UY&ceid=UY:es-419"
                es_especifica = True

            items = cls.recolectar_de_rss(url, f_nombre, f_peso, es_query_especifica=es_especifica)
            logger.info(f"   -> [{f_nombre}]: {len(items)} noticias de Peñarol identificadas.")
            todas.extend(items[:max_por_fuente])

        # Deduplicación semántica por similitud de título
        deduplicadas = []
        titulos_vistos = set()

        for it in todas:
            # Tokenizar palabras clave principales
            palabras = [w for w in re.sub(r"[^\w\s]", "", it["titulo"].lower()).split() if len(w) > 3]
            firma = " ".join(sorted(palabras[:6]))

            if firma in titulos_vistos:
                continue

            titulos_vistos.add(firma)
            deduplicadas.append(it)

        # Ordenar por relevancia y peso
        deduplicadas.sort(key=lambda x: (x.get("peso", 1.0), len(x.get("resumen", ""))), reverse=True)
        logger.info(f"[Prensa Deportiva] Total consolidado tras deduplicación: {len(deduplicadas)} noticias verificadas.")
        return deduplicadas


if __name__ == "__main__":
    noticias = ManyaSportsPressService.recolectar_todas()
    print(f"\nTotal: {len(noticias)} noticias.")
    for n in noticias[:5]:
        print(f"[{n['fuente']}] {n['titulo']} -> {n['url']}")
