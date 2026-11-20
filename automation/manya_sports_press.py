# -*- coding: utf-8 -*-
"""
Módulo de Recolección y Filtrado Estricto de Prensa Deportiva de Peñarol — v3.0
===============================================================================
Mejoras estructurales:
  - Filtrado obligatorio por relevancia estricta de Peñarol en TODAS las fuentes.
  - Descarte automático de noticias no deportivas (política, carnaval, policiales, portadas genéricas).
  - Parseo real de fechas RFC-2822 / ISO-8601 a hora uruguaya (UTC-3).
  - Ventana de frescura estricta (máximo 10 días de antigüedad — jamás titulares viejos de 2025).
  - Ordenamiento por recencia real + autoridad de fuente.
"""

import sys
import ssl
import re
import html
import logging
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

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
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 "
        "(ServicioTI-ManyaSportsPress/3.0)"
    )
}

# Términos obligatorios en el TÍTULO para garantizar 100% foco en Peñarol
PENAROL_TITLE_KEYWORDS = [
    "peñarol", "penarol", "aurinegro", "carbonero", "manya", "mirasol",
    "campeón del siglo", "campeon del siglo", "los aromos", "diego aguirre",
    "leo fernández", "leo fernandez", "leonardo fernández", "matías arezo",
    "matias arezo", "nahuel herrera", "leonel jaime", "ruglio"
]

# Términos de ruido que deben rechazarse siempre (portadas genéricas, otros temas)
NOISE_BLACKLIST = [
    "noticias de uruguay y del mundo", "carnaval", "juicio a ", "psiquiatra",
    "policial", "homicidio", "accidente doméstico", "farándula", "espectáculos",
    "horóscopo", "quiniela", "dólar hoy", "cotización", "básquetbol femenino",
    "fútbol sala", "rugby", "tenis", "fórmula 1", "nba"
]

HOMEPAGE_EXACT_TITLES = {
    "ovación - el país uruguay",
    "el observador: noticias de uruguay y del mundo",
    "tenfield.com",
    "montevideo portal",
    "fútboluy",
    "padre y decano"
}


class ManyaSportsPressService:
    """Recolector, filtrador estricto de frescura y rankeador de prensa deportiva aurinegra."""

    FUENTES_CONFIG = [
        {
            "id": "ovacion_el_pais",
            "nombre": "Ovación Digital (El País)",
            "tipo": "google_news_site",
            "query": 'site:elpais.com.uy "Peñarol" when:7d',
            "peso": 1.25
        },
        {
            "id": "referi_el_observador",
            "nombre": "Referí (El Observador)",
            "tipo": "google_news_site",
            "query": 'site:elobservador.com.uy "Peñarol" when:7d',
            "peso": 1.25
        },
        {
            "id": "futbol_uy",
            "nombre": "FútbolUy (Montevideo Portal)",
            "tipo": "google_news_site",
            "query": 'site:montevideo.com.uy "Peñarol" when:7d',
            "peso": 1.20
        },
        {
            "id": "tenfield_deportes",
            "nombre": "Tenfield Deportes",
            "tipo": "google_news_site",
            "query": 'site:tenfield.com.uy "Peñarol" when:10d',
            "peso": 1.15
        },
        {
            "id": "subrayado_deportes",
            "nombre": "Subrayado Deportes",
            "tipo": "google_news_site",
            "query": 'site:subrayado.com.uy "Peñarol" when:7d',
            "peso": 1.10
        },
        {
            "id": "padre_y_decano",
            "nombre": "Padre y Decano",
            "tipo": "rss_direct",
            "url": "https://www.padreydecano.com/cms/feed/",
            "peso": 1.20
        },
        {
            "id": "google_news_penarol",
            "nombre": "Prensa Deportiva Uruguay",
            "tipo": "google_news_site",
            "query": '"Peñarol" Campeonato Uruguayo OR Clausura OR Tabla Anual when:7d',
            "peso": 1.05
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
    def _parse_pubdate(cls, pub_str: str) -> Optional[datetime]:
        if not pub_str:
            return None
        try:
            dt = parsedate_to_datetime(pub_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(UY_TZ)
        except Exception:
            pass
        try:
            return datetime.fromisoformat(pub_str.replace("Z", "+00:00")).astimezone(UY_TZ)
        except Exception:
            return None

    @classmethod
    def _es_noticia_valida_penarol(cls, titulo: str, descripcion: str) -> bool:
        tit_l = titulo.lower().strip()
        if len(tit_l) < 18 or tit_l in HOMEPAGE_EXACT_TITLES:
            return False
        if any(bad in tit_l for bad in NOISE_BLACKLIST):
            return False
        # El título DEBE mencionar explícitamente a Peñarol o sus referentes/símbolos
        if any(k in tit_l for k in PENAROL_TITLE_KEYWORDS):
            return True
        return False

    @classmethod
    def _clean_google_title_and_source(cls, raw_title: str, default_source: str) -> tuple[str, str]:
        """Limpia el sufijo ' - El Observador' de los títulos de Google News RSS."""
        parts = raw_title.rsplit(" - ", 1)
        if len(parts) == 2 and len(parts[0]) > 20 and len(parts[1]) < 45:
            return parts[0].strip(), parts[1].strip()
        return raw_title.strip(), default_source

    @classmethod
    def recolectar_de_rss(cls, url: str, fuente_nombre: str, peso: float = 1.0, max_age_days: int = 10) -> List[Dict[str, Any]]:
        items = []
        now_uy = datetime.now(UY_TZ)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            req = urllib.request.Request(url, headers=HEADERS_HTTP)
            with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
                raw_bytes = resp.read()
                try:
                    root = ET.fromstring(raw_bytes)
                except ET.ParseError:
                    root = ET.fromstring(raw_bytes.decode("utf-8", errors="replace"))

            for node in root.findall(".//item"):
                raw_tit = cls._limpiar_texto(node.findtext("title", ""))
                link = cls._limpiar_texto(node.findtext("link", ""))
                desc = cls._limpiar_texto(node.findtext("description", ""))
                pub = cls._limpiar_texto(node.findtext("pubDate", ""))

                if not raw_tit or not link:
                    continue

                tit, detected_src = cls._clean_google_title_and_source(raw_tit, fuente_nombre)
                source_label = fuente_nombre if fuente_nombre != "Prensa Deportiva Uruguay" else detected_src

                # Filtro estricto de relevancia de Peñarol
                if not cls._es_noticia_valida_penarol(tit, desc):
                    continue

                # Filtro estricto de fecha / frescura
                pub_dt = cls._parse_pubdate(pub)
                if not pub_dt:
                    continue
                age_hours = (now_uy - pub_dt).total_seconds() / 3600.0
                if age_hours < -6 or age_hours > (max_age_days * 24):
                    continue

                # Si la descripción de Google News solo repite el título, generar bajada limpia
                desc_clean = desc
                if not desc_clean or desc_clean.lower().startswith(tit[:30].lower()):
                    desc_clean = f"Cobertura deportiva verificada publicada por {source_label} el {pub_dt.strftime('%d/%m/%Y a las %H:%M hs')}."

                items.append({
                    "titulo": tit,
                    "url": link,
                    "resumen": desc_clean[:240] + ("..." if len(desc_clean) > 240 else ""),
                    "fuente": source_label,
                    "fecha": pub_dt.strftime("%d/%m/%Y %H:%M"),
                    "fecha_iso": pub_dt.isoformat(),
                    "fecha_raw": pub_dt.strftime("%d/%m/%Y %H:%M hs"),
                    "antiguedad_horas": round(max(0.0, age_hours), 1),
                    "timestamp": pub_dt.timestamp(),
                    "peso": peso
                })
        except Exception as e:
            logger.warning(f"[Prensa Deportiva] Aviso en {fuente_nombre}: {e}")

        return items

    @classmethod
    def recolectar_todas(cls, max_por_fuente: int = 12, max_age_days: int = 10) -> List[Dict[str, Any]]:
        """Descarga, filtra por frescura/Peñarol, deduplica y ordena por fecha real."""
        todas = []
        logger.info("[Prensa Deportiva] Escaneando medios deportivos uruguayos (filtro estricto Peñarol <= 10 días)...")

        for f in cls.FUENTES_CONFIG:
            f_tipo = f["tipo"]
            f_nombre = f["nombre"]
            f_peso = f["peso"]

            if f_tipo == "rss_direct":
                url = f["url"]
            else:
                q = urllib.parse.quote_plus(f["query"])
                url = f"https://news.google.com/rss/search?q={q}&hl=es-419&gl=UY&ceid=UY:es-419"

            items = cls.recolectar_de_rss(url, f_nombre, f_peso, max_age_days=max_age_days)
            logger.info(f"   -> [{f_nombre}]: {len(items)} noticias vigentes de Peñarol.")
            todas.extend(items[:max_por_fuente])

        # Ordenar por recencia primero antes de deduplicar (conservar siempre la cobertura más fresca)
        todas.sort(key=lambda x: (x.get("timestamp", 0), x.get("peso", 1.0)), reverse=True)

        deduplicadas = []
        firmas_vistas = []
        stop_words = {"para", "como", "sobre", "tras", "ante", "este", "esta", "desde", "hasta", "peñarol", "penarol", "uruguayo", "torneo"}

        for it in todas:
            palabras = {
                w for w in re.sub(r"[^\w\s]", "", it["titulo"].lower()).split()
                if len(w) > 3 and w not in stop_words
            }
            if not palabras:
                continue
            es_dup = False
            for f_prev in firmas_vistas:
                inter = len(palabras & f_prev)
                if inter >= max(2, int(min(len(palabras), len(f_prev)) * 0.55)):
                    es_dup = True
                    break
            if es_dup:
                continue
            firmas_vistas.append(palabras)
            deduplicadas.append(it)

        logger.info(f"[Prensa Deportiva] ✓ Total consolidado vigente y deduplicado: {len(deduplicadas)} noticias de Peñarol.")
        return deduplicadas


if __name__ == "__main__":
    noticias = ManyaSportsPressService.recolectar_todas()
    print(f"\nTotal vigentes: {len(noticias)} noticias.")
    for i, n in enumerate(noticias[:12], 1):
        print(f"  {i:2d}. [{n['fuente']}] ({n['fecha']}) {n['titulo']}")
