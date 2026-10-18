# -*- coding: utf-8 -*-
"""
PUBLICADOR AUTOMÁTICO DE CRÓNICAS AURINEGRAS EN BLOGGER (blogger_manya_publisher.py)
====================================================================================
Toma el artículo redactado por Gemini Web (GFlash 3.8) en `data/news_digest.json`
y las imágenes transformadas con metadatos SEO en `assets/ig/`, y publica/actualiza
automáticamente la entrada en `https://www.servicioti.com.uy` (Blog ID: 8220787747664379807)
bajo el estándar v5.0 para monetizar con AdSense todo el tráfico aurinegro.

Garantías Anti-Colisión:
  1. Adquiere lock atómico 'blogger_api' mediante CentralAutomationLock.
  2. Verifica ventanas horarias libres mediante ScheduleSafety.
  3. Registra en ManyaBloggerCatalog (SQLite) para evitar duplicados.
"""

import os
import sys
import json
import html
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

logger = logging.getLogger("ManyaBloggerPublisher")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SCRATCH_DIR = BASE_DIR.parent
TOKEN_PATH = SCRATCH_DIR / "seo_blogger_automation" / "token.json"
BLOG_ID = "8220787747664379807"
SCOPES = ["https://www.googleapis.com/auth/blogger"]

UY_TZ = timezone(timedelta(hours=-3))

from manya_anti_collision import CentralAutomationLock, ScheduleSafety, ManyaBloggerCatalog


def get_blogger_service():
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return build("blogger", "v3", credentials=creds)


def publish_manya_article_to_blogger(post_type: str = "NOTICIA_DIARIA", match_id: str = "") -> Optional[str]:
    # 1. Comprobar seguridad de horario
    is_safe, msg_safe = ScheduleSafety.is_safe_to_publish()
    if not is_safe:
        logger.warning(f"[Blogger Peñarol] {msg_safe} Postergando publicación.")
        return None

    # 2. Comprobar catálogo anti-duplicados
    can_pub, msg_can = ManyaBloggerCatalog.can_publish(post_type=post_type, match_id=match_id)
    if not can_pub:
        logger.info(f"[Blogger Peñarol] [SKIP] {msg_can}")
        # Retornar URL existente si está en el catálogo
        return None

    digest_file = DATA_DIR / "news_digest.json"
    live_file = DATA_DIR / "live_status.json"
    if not digest_file.exists():
        logger.warning("[Blogger Peñarol] No existe data/news_digest.json todavía.")
        return None

    digest = json.loads(digest_file.read_text(encoding="utf-8"))
    live = json.loads(live_file.read_text(encoding="utf-8")) if live_file.exists() else {}

    art = digest.get("articulo_principal", {})
    tit_base = art.get('titulo') or digest.get('titular_dia', 'Actualidad de Peñarol')

    if post_type == "PREVIA":
        title = f"[Peñarol en Vivo - La Previa] {tit_base}"
    elif post_type == "CRONICA":
        title = f"[Peñarol en Vivo - Crónica] {tit_base}"
    else:
        title = f"[Peñarol en Vivo] {tit_base}"

    seo_desc = digest.get("bajada_seo", "Actualidad del Club Atlético Peñarol en vivo: Tabla Anual, Los Aromos, entradas en el Campeón del Siglo y estadísticas en Manya ServicioTI.")
    claves = digest.get("claves_60_segundos", [])
    parrafos = art.get("parrafos", [])
    faqs = art.get("preguntas_frecuentes", [])
    prox = live.get("proximo_partido", {})
    partido_activo = live.get("partido_activo", {})

    hero_img_cdn = "https://cdn.jsdelivr.net/gh/eltopouy/manya-servicioti@main/assets/ig/manya_previa_balon_estadio.webp"
    second_img_cdn = "https://cdn.jsdelivr.net/gh/eltopouy/manya-servicioti@main/assets/ig/manya_hinchada_fiesta_aurinegra.webp"

    claves_html = "".join(
        f'<div style="background:#18181b;border:1px solid #3f3f46;border-left:4px solid #ffd100;padding:12px 14px;border-radius:8px;">'
        f'<div style="font-weight:800;color:#ffd100;font-size:14px;margin-bottom:4px;">{c.get("icono","⚽")} {html.escape(c.get("titulo",""))}</div>'
        f'<div style="color:#e4e4e7;font-size:13.5px;line-height:1.5;">{html.escape(c.get("detalle",""))}</div>'
        f'</div>'
        for c in claves
    )

    parrafos_html = "".join(f"<p>{html.escape(p)}</p>" for p in parrafos)

    faqs_html = "".join(
        f'<details style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 16px;margin-bottom:10px;">'
        f'<summary style="font-weight:700;color:#0f172a;cursor:pointer;">{html.escape(f.get("q",""))}</summary>'
        f'<p style="margin:8px 0 0 0;color:#334155;font-size:14.5px;">{html.escape(f.get("a",""))}</p>'
        f'</details>'
        for f in faqs
    )

    # Detalle de partido activo si es día de partido
    partido_header_html = ""
    if partido_activo.get("nombre"):
        loc = partido_activo.get("local", {})
        vis = partido_activo.get("visitante", {})
        estadio = partido_activo.get("estadio", "Estadio Campeón del Siglo")
        tv = partido_activo.get("tv", "VTV Plus / Disney+")
        fase_txt = live.get("fase_partido", "PREVIA")

        from manya_match_engine import resolve_team_crest
        loc_nombre = loc.get("nombre", "Local")
        vis_nombre = vis.get("nombre", "Visitante")
        loc_crest = resolve_team_crest(loc_nombre, loc.get("logo", ""))
        vis_crest = resolve_team_crest(vis_nombre, vis.get("logo", ""))

        def _to_logo_url(crest_path, espn_logo):
            if espn_logo and espn_logo.startswith("http"):
                return espn_logo
            if crest_path and not crest_path.startswith("http"):
                return f"https://cdn.jsdelivr.net/gh/eltopouy/manya-servicioti@main/{crest_path}"
            return crest_path or "https://a.espncdn.com/i/teamlogos/soccer/500/2683.png"

        loc_img = _to_logo_url(loc_crest, loc.get("logo"))
        vis_img = _to_logo_url(vis_crest, vis.get("logo"))

        partido_header_html = f"""
        <div style="background:#111827;border:1px solid #eab308;padding:16px 20px;border-radius:12px;margin-bottom:20px;color:#f9fafb;">
          <div style="font-size:12px;font-weight:800;color:#facc15;text-transform:uppercase;margin-bottom:10px;text-align:center;">⚽ Cobertura Oficial • {fase_txt}</div>
          <div style="display:flex;align-items:center;justify-content:center;gap:18px;margin-bottom:10px;flex-wrap:wrap;">
            <div style="display:flex;align-items:center;gap:10px;">
              <img src="{loc_img}" alt="{html.escape(loc_nombre)}" width="38" height="38" style="object-fit:contain;vertical-align:middle;" />
              <strong style="font-size:18px;color:#ffffff;">{html.escape(loc_nombre)} {loc.get('goles','-')}</strong>
            </div>
            <div style="font-weight:900;color:#ffd100;font-size:16px;">VS</div>
            <div style="display:flex;align-items:center;gap:10px;">
              <strong style="font-size:18px;color:#ffffff;">{vis.get('goles','-')} {html.escape(vis_nombre)}</strong>
              <img src="{vis_img}" alt="{html.escape(vis_nombre)}" width="38" height="38" style="object-fit:contain;vertical-align:middle;" />
            </div>
          </div>
          <div style="font-size:13px;color:#d1d5db;text-align:center;">📍 <strong>Estadio:</strong> {html.escape(estadio)} | 📺 <strong>TV:</strong> {html.escape(tv)}</div>
        </div>
        """

    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "SportsTeam",
                "@id": "https://manya.servicioti.com.uy/#penarol",
                "name": "Club Atlético Peñarol",
                "alternateName": ["Peñarol", "Carbonero", "Manya", "Aurinegro", "CURCC"],
                "foundingDate": "1891-09-28",
                "sport": "Soccer",
                "url": "https://manya.servicioti.com.uy/"
            },
            {
                "@type": "NewsArticle",
                "headline": title[:110],
                "description": seo_desc,
                "image": [hero_img_cdn],
                "datePublished": datetime.now(UY_TZ).strftime("%Y-%m-%dT%H:%M:%S-03:00"),
                "dateModified": datetime.now(UY_TZ).strftime("%Y-%m-%dT%H:%M:%S-03:00"),
                "author": {"@type": "Person", "name": "Andrés Franchi Ugartemendía", "url": "https://www.servicioti.com.uy/"},
                "publisher": {"@type": "Organization", "name": "ServicioTI Uruguay", "url": "https://www.servicioti.com.uy/"},
                "about": {"@id": "https://manya.servicioti.com.uy/#penarol"}
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": f.get("q", ""), "acceptedAnswer": {"@type": "Answer", "text": f.get("a", "")}}
                    for f in faqs
                ]
            }
        ]
    }
    schema_script = f'<script type="application/ld+json">{json.dumps(graph, ensure_ascii=False, separators=(",", ":"))}</script>'

    content_html = (
        f'<div class="sti-bajada-seo" role="doc-abstract" style="background:linear-gradient(135deg,#fefce8 0%,#fef08a 100%);border-left:4px solid #ca8a04;padding:12px 16px;border-radius:0 10px 10px 0;margin:0 0 18px 0;font-size:14.5px;color:#0f172a;">'
        f'<strong>Síntesis ServicioTI:</strong> {html.escape(seo_desc)}</div>'
        f'<div style="font-family:system-ui,-apple-system,sans-serif;color:#1e293b;line-height:1.72;max-width:880px;margin:0 auto;">'
        f'{partido_header_html}'
        f'<div style="background:linear-gradient(135deg,#09090b 0%,#18181b 100%);border:2px solid #ffd100;color:#fff;padding:24px;border-radius:14px;margin-bottom:22px;">'
        f'<div style="display:inline-block;background:#ffd100;color:#09090b;font-weight:900;font-size:12px;padding:4px 12px;border-radius:999px;text-transform:uppercase;margin-bottom:10px;">★ Glorioso Peñarol • Cobertura Manya ServicioTI</div>'
        f'<h2 style="margin:0 0 8px 0;color:#fff;font-size:23px;">{html.escape(art.get("subtitulo") or title)}</h2>'
        f'<p style="margin:0 0 16px 0;color:#d4d4d8;font-size:14.5px;">Compromiso oficial: <strong>{html.escape(prox.get("local",{}).get("nombre","Peñarol"))} vs {html.escape(prox.get("visitante",{}).get("nombre","Rival"))}</strong> ({html.escape(prox.get("fecha_legible",""))}) en {html.escape(prox.get("estadio","Estadio Campeón del Siglo"))}.</p>'
        f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;margin-bottom:16px;">{claves_html}</div>'
        f'<a href="https://manya.servicioti.com.uy/" style="display:inline-block;background:#ffd100;color:#09090b;font-weight:800;padding:10px 18px;border-radius:8px;text-decoration:none;font-size:14px;">⚡ Abrir Radar en Vivo, Pizarra Táctica y Marcador en manya.servicioti.com.uy →</a>'
        f'</div>'
        f'<figure style="margin:0 0 20px 0;text-align:center;">'
        f'<img src="{hero_img_cdn}" alt="{html.escape(title)}" width="1280" height="720" loading="eager" fetchpriority="high" style="width:100%;height:auto;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,0.15);" />'
        f'<figcaption style="font-size:12.5px;color:#64748b;margin-top:6px;">Estadio Campeón del Siglo • Cobertura gráfica exclusiva de Manya ServicioTI.</figcaption>'
        f'</figure>'
        f'{parrafos_html}'
        f'<figure style="margin:20px 0;text-align:center;">'
        f'<img src="{second_img_cdn}" alt="Hinchada del Club Atlético Peñarol en el Estadio Campeón del Siglo" width="1280" height="720" loading="lazy" decoding="async" style="width:100%;height:auto;border-radius:12px;" />'
        f'</figure>'
        f'<h2 style="font-size:19px;color:#0f172a;border-bottom:2px solid #fde047;padding-bottom:6px;margin-top:26px;">❓ Preguntas Frecuentes del Hincha Carbonero</h2>'
        f'{faqs_html}'
        f'<div style="background:#09090b;color:#fff;padding:18px 20px;border-radius:12px;margin-top:24px;border-left:5px solid #ffd100;">'
        f'<strong>🚌 ¿Vas al Estadio?</strong> Consulta las frecuencias de ómnibus CUTCSA y COPSA en nuestro <a href="https://horarios.servicioti.com.uy/" style="color:#ffd100;font-weight:700;">Radar de Horarios en Vivo</a> o explora la <a href="https://manya.servicioti.com.uy/" style="color:#ffd100;font-weight:700;">Central Interactiva de Peñarol (manya.servicioti.com.uy)</a>.'
        f'</div>'
        f'</div>'
        f'{schema_script}'
    )

    # 3. Adquirir lock atómico 'blogger_api' para no colisionar con otros scripts
    with CentralAutomationLock.acquire("blogger_api", timeout_sec=90):
        try:
            service = get_blogger_service()
            labels = ["Peñarol", "Club Atlético Peñarol", "Fútbol Uruguayo", "Deportes Uruguay", "ServicioTI"]

            # Si es PREVIA, buscar si ya había una previa de hoy para actualizarla; si es CRÓNICA o NOTICIA_DIARIA, insertar nueva
            existing = service.posts().list(blogId=BLOG_ID, maxResults=10).execute().get("items", [])
            target_post = None
            if post_type == "PREVIA":
                target_post = next((p for p in existing if "[Peñarol en Vivo - La Previa]" in (p.get("title") or "")), None)

            if target_post:
                res = service.posts().patch(
                    blogId=BLOG_ID,
                    postId=target_post["id"],
                    body={"title": title, "content": content_html, "labels": labels}
                ).execute()
                post_url = res.get("url")
                post_id = res.get("id")
                logger.info(f"[Blogger Peñarol] ✓ Post actualizado ({post_type}): {post_url}")
            else:
                res = service.posts().insert(
                    blogId=BLOG_ID,
                    body={"title": title, "content": content_html, "labels": labels}
                ).execute()
                post_url = res.get("url")
                post_id = res.get("id")
                logger.info(f"[Blogger Peñarol] ✓ Nuevo post publicado ({post_type}): {post_url}")

            # 4. Registrar en catálogo SQLite de Peñarol
            total_palabras = sum(len(p.split()) for p in parrafos)
            ManyaBloggerCatalog.register_post(
                post_type=post_type,
                match_id=match_id,
                match_title=partido_activo.get("nombre", tit_base),
                blogger_post_id=post_id,
                blogger_url=post_url,
                title=title,
                word_count=total_palabras
            )

            # 5. Guardar la URL publicada en news_digest.json
            digest["blogger_post_url"] = post_url
            digest_file.write_text(json.dumps(digest, ensure_ascii=False, indent=2), encoding="utf-8")
            return post_url
        except Exception as e:
            logger.error(f"[Blogger Peñarol] Error al publicar en Blogger: {e}")
            return None


if __name__ == "__main__":
    url = publish_manya_article_to_blogger(post_type="NOTICIA_DIARIA")
    print("Publicado / Actualizado:", url)
