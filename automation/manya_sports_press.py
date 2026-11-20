# -*- coding: utf-8 -*-
"""
Módulo de Recolección, Limpieza y Deduplicación Difusa de Prensa Deportiva — v4.0 (Manya v11.0)
===============================================================================================
Mejoras estructurales v4.0:
  - Filtrado obligatorio por relevancia estricta de Peñarol en TODAS las fuentes.
  - Descarte automático de noticias no deportivas (política, carnaval, policiales, portadas genéricas).
  - Limpieza profunda de sufijos de medios en titulares (` - Ovación`, ` | Referí`, ` - Montevideo Portal`, etc.)
    y normalización uniforme de nombres de fuente para filtros interactivos del frontend.
  - Deduplicación difusa combinada (`difflib.SequenceMatcher >= 0.72` + Jaccard/solapamiento de tokens
    normalizados + URL canónica) para evitar cables duplicados entre dos medios en el top 10.
  - Reintentos con backoff exponencial en descargas RSS y logging limpio sin duplicación (`propagate=False`).
"""

import sys
import ssl
import re
import html
import time
import random
import difflib
import unicodedata
import urllib.error
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

AUTOMATION_DIR = Path(__file__).resolve().parent
if str(AUTOMATION_DIR) not in sys.path:
    sys.path.insert(0, str(AUTOMATION_DIR))

from manya_logging import get_manya_logger

logger = get_manya_logger("ManyaSportsPress")

UY_TZ = timezone(timedelta(hours=-3))

HEADERS_HTTP = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 "
        "(ServicioTI-ManyaSportsPress/4.0)"
    )
}

# Términos obligatorios en el TÍTULO para garantizar 100% foco en Peñarol
PENAROL_TITLE_KEYWORDS = [
    "peñarol", "penarol", "aurinegro", "carbonero", "manya", "mirasol",
    "campeón del siglo", "campeon del siglo", "los aromos", "diego aguirre",
    "leo fernández", "leo fernandez", "leonardo fernández", "matías arezo",
    "matias arezo", "nahuel herrera", "leonel jaime", "ruglio",
]

# Términos de ruido que deben rechazarse siempre (portadas genéricas, otros temas)
NOISE_BLACKLIST = [
    "noticias de uruguay y del mundo", "carnaval", "juicio a ", "psiquiatra",
    "policial", "homicidio", "accidente doméstico", "farándula", "espectáculos",
    "horóscopo", "quiniela", "dólar hoy", "cotización", "básquetbol femenino",
    "fútbol sala", "rugby", "tenis", "fórmula 1", "nba",
]

HOMEPAGE_EXACT_TITLES = {
    "ovación - el país uruguay",
    "el observador: noticias de uruguay y del mundo",
    "tenfield.com",
    "montevideo portal",
    "fútboluy",
    "padre y decano",
}

# Sufijos conocidos de medios deportivos/uruguayos para limpiar titulares
KNOWN_MEDIA_SUFFIXES = (
    "ovación digital", "ovacion digital", "ovación", "ovacion",
    "el país uruguay", "el pais uruguay", "el país", "el pais", "elpais.com.uy",
    "referí", "referi", "el observador", "elobservador.com.uy",
    "fútboluy", "futboluy", "futbol.com.uy", "montevideo portal", "montevideo.com.uy",
    "tenfield.com", "tenfield deportes", "tenfield",
    "subrayado deportes", "subrayado",
    "padre y decano", "padreydecano.com", "padreydecano",
    "la diaria deporte", "la diaria", "ladiaria",
    "espn deportes", "espn uruguay", "espn.com.uy", "espn",
    "telemundo", "teledoce", "telenoche", "canal 10", "canal 4", "canal 12",
    "caras y caretas", "medios públicos", "medios publicos", "el telégrafo", "el telegrafo",
    "sport 890", "radio universal", "carve deportiva", "100% deporte",
)

SOURCE_CANONICAL_MAP = {
    "el país": "Ovación Digital (El País)",
    "el pais": "Ovación Digital (El País)",
    "el país uruguay": "Ovación Digital (El País)",
    "ovación": "Ovación Digital (El País)",
    "ovacion": "Ovación Digital (El País)",
    "ovación digital": "Ovación Digital (El País)",
    "el observador": "Referí (El Observador)",
    "referí": "Referí (El Observador)",
    "referi": "Referí (El Observador)",
    "montevideo portal": "FútbolUy (Montevideo Portal)",
    "fútboluy": "FútbolUy (Montevideo Portal)",
    "futboluy": "FútbolUy (Montevideo Portal)",
    "futbol.com.uy": "FútbolUy (Montevideo Portal)",
    "tenfield": "Tenfield Deportes",
    "tenfield.com": "Tenfield Deportes",
    "subrayado": "Subrayado Deportes",
    "padre y decano": "Padre y Decano",
    "la diaria": "La Diaria",
    "espn": "ESPN Uruguay",
    "espn deportes": "ESPN Uruguay",
    "espn uruguay": "ESPN Uruguay",
}

DEDUP_STOPWORDS = {
    "para", "como", "sobre", "tras", "ante", "este", "esta", "estos", "estas",
    "desde", "hasta", "pero", "donde", "cuando", "porque", "entre", "hacia",
    "todo", "toda", "todos", "todas", "tiene", "tienen", "sera", "seria",
    "peñarol", "penarol", "aurinegro", "carbonero", "uruguayo", "torneo",
    "liga", "campeonato", "club", "partido", "equipo", "futbol",
}


def _strip_accents(text: str) -> str:
    norm = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in norm if not unicodedata.combining(c))


class ManyaSportsPressService:
    """Recolector, filtrador estricto de frescura y deduplicador difuso de prensa deportiva aurinegra."""

    FUENTES_CONFIG = [
        {
            "id": "ovacion_el_pais",
            "nombre": "Ovación Digital (El País)",
            "tipo": "google_news_site",
            "query": 'site:elpais.com.uy "Peñarol" when:7d',
            "peso": 1.25,
        },
        {
            "id": "referi_el_observador",
            "nombre": "Referí (El Observador)",
            "tipo": "google_news_site",
            "query": 'site:elobservador.com.uy "Peñarol" when:7d',
            "peso": 1.25,
        },
        {
            "id": "futbol_uy",
            "nombre": "FútbolUy (Montevideo Portal)",
            "tipo": "google_news_site",
            "query": 'site:montevideo.com.uy "Peñarol" when:7d',
            "peso": 1.20,
        },
        {
            "id": "tenfield_deportes",
            "nombre": "Tenfield Deportes",
            "tipo": "google_news_site",
            "query": 'site:tenfield.com.uy "Peñarol" when:10d',
            "peso": 1.15,
        },
        {
            "id": "subrayado_deportes",
            "nombre": "Subrayado Deportes",
            "tipo": "google_news_site",
            "query": 'site:subrayado.com.uy "Peñarol" when:7d',
            "peso": 1.10,
        },
        {
            "id": "padre_y_decano",
            "nombre": "Padre y Decano",
            "tipo": "rss_direct",
            "url": "https://www.padreydecano.com/cms/feed/",
            "peso": 1.20,
        },
        {
            "id": "google_news_penarol",
            "nombre": "Prensa Deportiva Uruguay",
            "tipo": "google_news_site",
            "query": '"Peñarol" Campeonato Uruguayo OR Clausura OR Tabla Anual OR Final when:7d',
            "peso": 1.05,
        },
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
        if any(k in tit_l for k in PENAROL_TITLE_KEYWORDS):
            return True
        return False

    @classmethod
    def _normalize_source_label(cls, raw_source: str, fallback: str) -> str:
        if not raw_source:
            return fallback
        clean = raw_source.strip()
        norm = _strip_accents(clean).lower()
        for k, v in SOURCE_CANONICAL_MAP.items():
            if norm == _strip_accents(k).lower():
                return v
        return clean

    @classmethod
    def _clean_google_title_and_source(cls, raw_title: str, default_source: str) -> Tuple[str, str]:
        """
        Elimina sufijos repetidos o encadenados de nombre de medio en titulares
        (` - Ovación`, ` | Referí`, ` - Montevideo Portal`, ` — El País`, etc.)
        y retorna `(titular_limpio, fuente_detectada)`.
        """
        title = (raw_title or "").strip()
        detected_source = default_source

        # Separadores estándar de titulares RSS / Google News
        sep_pattern = re.compile(r"\s+(?:-|–|—|\|)\s+")

        # Hasta 3 pasadas para casos como "Titular - Ovación - EL PAÍS Uruguay"
        for pass_idx in range(3):
            matches = list(sep_pattern.finditer(title))
            if not matches:
                break
            last_m = matches[-1]
            left = title[:last_m.start()].strip()
            right = title[last_m.end():].strip()
            if len(left) < 18 or not right:
                break

            right_norm = _strip_accents(right).lower().strip(" .·•")
            is_known_media = any(
                right_norm == _strip_accents(ms).lower()
                or _strip_accents(ms).lower() in right_norm
                for ms in KNOWN_MEDIA_SUFFIXES
            )
            # En la primera pasada, Google News siempre agrega " - <Medio>" corto (<42 chars)
            if is_known_media or (pass_idx == 0 and len(right) <= 42 and last_m.group(0).strip() in ("-", "|")):
                if detected_source == default_source or is_known_media:
                    detected_source = cls._normalize_source_label(right, detected_source)
                title = left
            else:
                break

        # Limpiar puntuación residual en extremos
        title = title.strip(" -–—|")
        return title, detected_source

    @classmethod
    def _normalize_title_for_dedup(cls, titulo: str) -> str:
        t = _strip_accents(titulo).lower()
        t = re.sub(r"[^a-z0-9\s]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    @classmethod
    def _title_tokens_for_dedup(cls, norm_title: str) -> set:
        return {
            w for w in norm_title.split()
            if len(w) > 3 and w not in DEDUP_STOPWORDS
        }

    @classmethod
    def _is_similar_title(cls, norm_a: str, toks_a: set, norm_b: str, toks_b: set, threshold: float = 0.72) -> bool:
        """Detecta duplicados difusos combinando SequenceMatcher (>=0.72) y similitud de tokens (Jaccard/Overlap)."""
        if not norm_a or not norm_b:
            return False
        if norm_a == norm_b:
            return True

        # 1. Similitud de secuencia global (SequenceMatcher >= 0.72)
        seq_ratio = difflib.SequenceMatcher(None, norm_a, norm_b).ratio()
        if seq_ratio >= threshold:
            return True

        # 2. Similitud léxica sobre tokens informativos normalizados
        if toks_a and toks_b:
            inter = len(toks_a & toks_b)
            union = len(toks_a | toks_b)
            jaccard = inter / union if union else 0.0
            if jaccard >= 0.55 or (inter >= 4 and jaccard >= 0.48):
                return True
            min_len = min(len(toks_a), len(toks_b))
            overlap = inter / min_len if min_len else 0.0
            if min_len >= 4 and inter >= 4 and overlap >= 0.68:
                return True
            if min_len >= 3 and overlap >= threshold:
                return True
            if min_len >= 2 and overlap >= 0.72 and seq_ratio >= 0.55:
                return True

        return False

    @classmethod
    def _fetch_rss_bytes(cls, url: str, timeout: int = 12, retries: int = 2) -> Optional[bytes]:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        last_err: Optional[Exception] = None
        for attempt in range(max(1, retries)):
            try:
                req = urllib.request.Request(url, headers=HEADERS_HTTP)
                with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
                    return resp.read()
            except urllib.error.HTTPError as e:
                last_err = e
                if e.code not in (408, 429, 500, 502, 503, 504):
                    break
            except Exception as e:
                last_err = e
            if attempt < retries - 1:
                time.sleep(0.6 * (2 ** attempt) + random.uniform(0.0, 0.2))
        if last_err:
            raise last_err
        return None

    @classmethod
    def recolectar_de_rss(cls, url: str, fuente_nombre: str, peso: float = 1.0, max_age_days: int = 10) -> List[Dict[str, Any]]:
        items = []
        now_uy = datetime.now(UY_TZ)

        try:
            raw_bytes = cls._fetch_rss_bytes(url, timeout=12, retries=2)
            if not raw_bytes:
                return items
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
                source_label = fuente_nombre if fuente_nombre != "Prensa Deportiva Uruguay" else cls._normalize_source_label(detected_src, "Prensa Deportiva Uruguay")

                if not cls._es_noticia_valida_penarol(tit, desc):
                    continue

                pub_dt = cls._parse_pubdate(pub)
                if not pub_dt:
                    continue
                age_hours = (now_uy - pub_dt).total_seconds() / 3600.0
                if age_hours < -6 or age_hours > (max_age_days * 24):
                    continue

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
                    "peso": peso,
                })
        except Exception as e:
            logger.warning(f"[Prensa Deportiva] Aviso en {fuente_nombre}: {e}")

        return items

    @classmethod
    def deduplicar_noticias(cls, noticias: List[Dict[str, Any]], similarity_threshold: float = 0.72) -> List[Dict[str, Any]]:
        """Deduplica titulares repetidos o cables casi idénticos preservando la versión más reciente/autoritativa."""
        ordenadas = sorted(
            noticias,
            key=lambda x: (x.get("timestamp", 0), x.get("peso", 1.0)),
            reverse=True,
        )
        deduplicadas: List[Dict[str, Any]] = []
        vistas_urls = set()
        vistas_firmas: List[Tuple[str, set]] = []

        for it in ordenadas:
            url_key = (it.get("url") or "").strip().lower()
            if url_key and url_key in vistas_urls:
                continue

            norm_tit = cls._normalize_title_for_dedup(it.get("titulo", ""))
            toks_tit = cls._title_tokens_for_dedup(norm_tit)
            if not norm_tit:
                continue

            es_dup = any(
                cls._is_similar_title(norm_tit, toks_tit, prev_norm, prev_toks, threshold=similarity_threshold)
                for prev_norm, prev_toks in vistas_firmas
            )
            if es_dup:
                continue

            if url_key:
                vistas_urls.add(url_key)
            vistas_firmas.append((norm_tit, toks_tit))
            deduplicadas.append(it)

        return deduplicadas

    @classmethod
    def recolectar_todas(cls, max_por_fuente: int = 12, max_age_days: int = 10) -> List[Dict[str, Any]]:
        """Descarga, limpia sufijos, filtra por frescura/Peñarol, deduplica difusamente y ordena por fecha real."""
        todas = []
        logger.info("[Prensa Deportiva] Escaneando medios deportivos uruguayos (v4.0 • filtro estricto Peñarol <= 10 días)...")

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

        deduplicadas = cls.deduplicar_noticias(todas, similarity_threshold=0.72)
        descartadas = len(todas) - len(deduplicadas)
        logger.info(
            f"[Prensa Deportiva] ✓ Consolidado vigente y deduplicado: {len(deduplicadas)} noticias "
            f"(eliminados {descartadas} cables duplicados/similares)."
        )
        return deduplicadas


if __name__ == "__main__":
    noticias = ManyaSportsPressService.recolectar_todas()
    print(f"\nTotal vigentes: {len(noticias)} noticias.")
    for i, n in enumerate(noticias[:12], 1):
        print(f"  {i:2d}. [{n['fuente']}] ({n['fecha']}) {n['titulo']}")
