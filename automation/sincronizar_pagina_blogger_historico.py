# -*- coding: utf-8 -*-
"""
SINCRONIZADOR DE LA PÁGINA CENTRAL DE ARCHIVO HISTÓRICO Y ANÁLISIS EN BLOGGER — v11.0 (Zero-Hardcode)
=====================================================================================================
Crea o actualiza la Página Estática oficial en www.servicioti.com.uy:
  - Título: Peñarol: Archivo Histórico de Análisis Tácticos, Crónicas e Historial de Partidos | Manya ServicioTI
  - Renderiza 100% dinámicamente el análisis actual (`data/news_digest.json`), los últimos resultados
    oficiales (`data/live_status.json`), los historiales frente a frente verificados en `data/historial_*.json`
    y las crónicas publicadas en `data/manya_blogger_catalog.db` (cero hardcodes de fechas o rivales).
"""

import sys
import json
import html
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
AUTOMATION_DIR = BASE_DIR / "automation"
DATA_DIR = BASE_DIR / "data"
if str(AUTOMATION_DIR) not in sys.path:
    sys.path.insert(0, str(AUTOMATION_DIR))

from manya_logging import get_manya_logger

logger = get_manya_logger("BloggerHistoricoSync")
UY_TZ = timezone(timedelta(hours=-3))

try:
    from blogger_manya_publisher import get_blogger_service, BLOG_ID, TOKEN_PATH
    HAS_BLOGGER_LIBS = True
except (ImportError, Exception):
    HAS_BLOGGER_LIBS = False
    BLOG_ID = "8220787747664379807"
    TOKEN_PATH = Path("non_existent_token.json")

PAGE_TITLE = "Peñarol: Archivo Histórico de Análisis Tácticos, Crónicas e Historial de Partidos | Manya ServicioTI"
STATE_FILE = DATA_DIR / "blogger_pagina_historica.json"
CATALOG_DB = DATA_DIR / "manya_blogger_catalog.db"


def _load_dynamic_historiales() -> List[Dict[str, Any]]:
    """Carga todos los historiales oficiales 1891 BD disponibles en `data/historial_*.json` sin duplicados."""
    rows: List[Dict[str, Any]] = []
    seen_slugs = set()

    candidates = []
    active_f = DATA_DIR / "historial_activo.json"
    if active_f.exists():
        candidates.append(active_f)
    candidates.extend(sorted(DATA_DIR.glob("historial_*.json")))

    for fp in candidates:
        try:
            doc = json.loads(fp.read_text(encoding="utf-8"))
            res = doc.get("resumen") or {}
            slug = doc.get("rival_slug") or fp.stem.replace("historial_", "")
            if not slug or slug in seen_slugs or not res.get("partidos_jugados"):
                continue
            seen_slugs.add(slug)
            ultimos = doc.get("ultimos_enfrentamientos") or []
            ultimo_txt = ""
            if ultimos:
                u0 = ultimos[0]
                ultimo_txt = f"{u0.get('marcador', '')} ({u0.get('fecha', '')})".strip()
            rows.append({
                "rival": doc.get("rival_oficial") or doc.get("rival") or slug.replace("_", " ").title(),
                "pj": res.get("partidos_jugados", 0),
                "pg": res.get("ganados_penarol", 0),
                "pe": res.get("empatados", 0),
                "pp": res.get("perdidos_penarol", 0),
                "gf": res.get("goles_penarol", 0),
                "gc": res.get("goles_rival", 0),
                "ventaja": res.get("ventaja_victorias", ""),
                "efectividad": res.get("efectividad_pct", "0%"),
                "ultimo": ultimo_txt or "Verificado 1891 BD",
            })
        except Exception:
            continue

    rows.sort(key=lambda r: int(r.get("pj") or 0), reverse=True)
    return rows


def _load_published_archive_links(limit: int = 8) -> List[Dict[str, str]]:
    """Lee el registro de crónicas y previas publicadas desde la BD local SQLite si existe."""
    if not CATALOG_DB.exists():
        return []
    out: List[Dict[str, str]] = []
    try:
        with sqlite3.connect(str(CATALOG_DB)) as conn:
            cur = conn.execute(
                "SELECT title, blogger_url, post_type, published_date, match_title "
                "FROM manya_posts ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            for title, url, ptype, pdate, mtitle in cur.fetchall():
                if url:
                    out.append({
                        "title": title or mtitle or "Cobertura Peñarol",
                        "url": url,
                        "type": ptype or "CRONICA",
                        "date": pdate or "",
                    })
    except Exception:
        pass
    return out


def generar_contenido_html(digest: dict, live: dict, h2h_activo: dict = None) -> str:
    """Genera el HTML enriquecido, responsive y 100% dinámico (Zero-Hardcode) para Blogger."""
    now_str = datetime.now(UY_TZ).strftime("%d/%m/%Y %H:%M hs UY")

    titular_actual = digest.get("titular_dia") or "Actualidad Oficial del Club Atlético Peñarol"
    bajada_actual = digest.get("bajada_seo") or ""
    post_url_actual = digest.get("blogger_post_url") or live.get("blogger_live_url") or "https://www.servicioti.com.uy/p/penarol-proximo-partido-radiografia.html"
    res_temp = live.get("resumen_temporada") or {}
    pts_anual = res_temp.get("penarol_anual_pts", 0)
    dg_anual = res_temp.get("penarol_anual_dg", "")

    # Últimos resultados reales desde live_status.json
    recientes = live.get("ultimos_resultados") or []
    recientes_cards = []
    for m in recientes[:6]:
        loc = m.get("local") or {}
        vis = m.get("visitante") or {}
        l_nom = loc.get("nombre", "Local")
        v_nom = vis.get("nombre", "Visitante")
        l_g = loc.get("goles", "-")
        v_g = vis.get("goles", "-")
        try:
            g_pen = int(l_g) if loc.get("es_penarol") else int(v_g)
            g_riv = int(v_g) if loc.get("es_penarol") else int(l_g)
            border_c = "#22c55e" if g_pen > g_riv else ("#eab308" if g_pen == g_riv else "#ef4444")
        except Exception:
            border_c = "#ffd100"
        goles_info = f" • ⚽ {m['goles_texto']}" if m.get("goles_texto") else ""
        recientes_cards.append(f"""
      <div style="background:#18181d;border:1px solid rgba(255,255,255,0.08);border-left:4px solid {border_c};border-radius:8px;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
        <div>
          <strong style="color:#ffffff;font-size:14px;">{html.escape(l_nom)} {html.escape(str(l_g))} - {html.escape(str(v_g))} {html.escape(v_nom)}</strong>
          <div style="font-size:12px;color:#a1a1aa;">{html.escape(m.get('torneo', 'Campeonato Uruguayo'))} • {html.escape(m.get('fecha_legible', ''))} • {html.escape(m.get('estadio', ''))}{html.escape(goles_info)}</div>
        </div>
        <a href="https://manya.servicioti.com.uy/" target="_blank" rel="noopener noreferrer" style="color:#ffd100;font-size:12px;font-weight:800;text-decoration:underline;">Ficha en Manya ↗</a>
      </div>""")

    recientes_html = "".join(recientes_cards) or (
        '<div style="color:#a1a1aa;font-size:13px;">Consultá el calendario y resultados en vivo en manya.servicioti.com.uy.</div>'
    )

    # Archivo de publicaciones en Blogger desde catálogo SQLite
    archive_posts = _load_published_archive_links(limit=6)
    archive_html = ""
    if archive_posts:
        items_a = "".join(
            f'<li style="margin-bottom:6px;"><a href="{html.escape(p["url"])}" target="_blank" rel="noopener noreferrer" style="color:#ffd100;font-weight:700;text-decoration:none;">{html.escape(p["title"])}</a> <span style="color:#71717a;font-size:11.5px;">({html.escape(p["date"])})</span></li>'
            for p in archive_posts
        )
        archive_html = f"""
    <div style="background:#121216;border:1px solid rgba(255,209,0,0.2);border-radius:10px;padding:16px;margin-top:14px;">
      <strong style="color:#ffd100;font-size:13.5px;display:block;margin-bottom:8px;">📚 Últimas Crónicas y Previas Publicadas en ServicioTI</strong>
      <ul style="margin:0;padding-left:18px;font-size:13px;color:#d4d4d8;">{items_a}</ul>
    </div>"""

    # Historiales 1891 BD reales cargados desde data/historial_*.json
    historiales = _load_dynamic_historiales()
    historiales_rows = "".join([f"""
      <tr style="border-bottom:1px solid rgba(255,209,0,0.18);">
        <td style="padding:10px 12px;font-weight:700;color:#ffffff;">{html.escape(str(h['rival']))}</td>
        <td style="padding:10px 8px;text-align:center;color:#e4e4e7;">{html.escape(str(h['pj']))}</td>
        <td style="padding:10px 8px;text-align:center;font-weight:800;color:#ffd100;">{html.escape(str(h['pg']))}</td>
        <td style="padding:10px 8px;text-align:center;color:#a1a1aa;">{html.escape(str(h['pe']))}</td>
        <td style="padding:10px 8px;text-align:center;color:#ef4444;">{html.escape(str(h['pp']))}</td>
        <td style="padding:10px 8px;text-align:center;color:#ffd100;">{html.escape(str(h['gf']))}-{html.escape(str(h['gc']))}</td>
        <td style="padding:10px 10px;text-align:center;font-size:12px;color:#22c55e;font-weight:700;">{html.escape(str(h['ventaja']))}</td>
        <td style="padding:10px 8px;text-align:center;font-weight:800;color:#ffd100;">{html.escape(str(h['efectividad']))}</td>
        <td style="padding:10px 12px;font-size:12px;color:#d4d4d8;">{html.escape(str(h['ultimo']))}</td>
      </tr>
    """ for h in historiales])

    anual_tag = f" • Tabla Anual: {pts_anual} pts ({dg_anual} DG)" if pts_anual else ""

    html_content = f"""
<div style="font-family:'Inter',system-ui,-apple-system,sans-serif;color:#ffffff;background:#09090b;padding:24px 20px;border-radius:14px;border:2px solid #ffd100;box-shadow:0 10px 30px rgba(0,0,0,0.7);max-width:980px;margin:0 auto;line-height:1.6;">

  <div style="background:linear-gradient(135deg, rgba(255,209,0,0.2) 0%, rgba(9,9,11,0.95) 100%);border-left:5px solid #ffd100;border-radius:10px;padding:20px;margin-bottom:26px;">
    <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;">
      <img src="https://cdn.jsdelivr.net/gh/eltopouy/manya-servicioti@main/assets/img/escudo_penarol_oficial.svg" alt="Escudo Oficial Peñarol 1891" width="54" height="68" style="object-fit:contain;" />
      <div>
        <h1 style="font-size:24px;font-weight:900;color:#ffd100;margin:0 0 4px;letter-spacing:-0.02em;">
          ★ CLUB ATLÉTICO PEÑAROL: ARCHIVO HISTÓRICO Y CENTRAL DE ANÁLISIS
        </h1>
        <p style="font-size:13.5px;color:#e4e4e7;margin:0;">
          <strong>Decano del Fútbol Uruguayo (Fundado el 28 de septiembre de 1891)</strong> • Club Campeón del Siglo XX de Sudamérica (IFFHS) • 5 Libertadores • 3 Intercontinentales • 54 Uruguayos.
        </p>
      </div>
    </div>
    <div style="margin-top:16px;display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
      <a href="https://manya.servicioti.com.uy/" target="_blank" rel="noopener noreferrer" style="background:#ffd100;color:#09090b;font-weight:900;padding:8px 16px;border-radius:999px;text-decoration:none;font-size:13px;display:inline-flex;align-items:center;gap:6px;">
        ⚡ Ir a manya.servicioti.com.uy (Match Center en Vivo) ↗
      </a>
      <a href="https://manya.servicioti.com.uy/#pizarra-tactica" target="_blank" rel="noopener noreferrer" style="border:1px solid #ffd100;color:#ffd100;font-weight:700;padding:8px 16px;border-radius:999px;text-decoration:none;font-size:13px;">
        👕 Pizarra Táctica: Armá tu 11
      </a>
      <a href="https://horarios.servicioti.com.uy/" target="_blank" rel="noopener noreferrer" style="border:1px solid rgba(255,255,255,0.2);color:#d4d4d8;font-weight:700;padding:8px 16px;border-radius:999px;text-decoration:none;font-size:13px;">
        🚌 Ómnibus al Estadio Campeón del Siglo
      </a>
    </div>
  </div>

  <p style="font-size:15px;color:#d4d4d8;margin-bottom:24px;border-bottom:1px solid rgba(255,255,255,0.1);padding-bottom:16px;">
    Esta página constituye el <strong>repositorio y archivo histórico permanente</strong> de todas las crónicas, radiografías tácticas y análisis publicados por <strong>ServicioTI Uruguay</strong> y <a href="https://manya.servicioti.com.uy/" style="color:#ffd100;text-decoration:underline;">manya.servicioti.com.uy</a>, respaldados por la Comisión de Historia y Patrimonio del Club Atlético Peñarol (<strong>1891 BD</strong>) y datos oficiales AUF.
  </p>

  <div style="margin-bottom:34px;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;border-bottom:2px solid #ffd100;padding-bottom:8px;flex-wrap:wrap;gap:8px;">
      <h2 style="font-size:19px;font-weight:900;color:#ffd100;margin:0;">
        📰 Respaldo Histórico de Crónicas y Resultados Recientes
      </h2>
      <span style="font-size:12px;background:rgba(255,209,0,0.15);color:#ffd100;border:1px solid #ffd100;padding:3px 10px;border-radius:999px;font-weight:800;">Actualizado: {now_str}</span>
    </div>

    <div style="background:#121216;border:1px solid rgba(255,209,0,0.3);border-radius:10px;padding:18px;margin-bottom:16px;">
      <span style="background:#ffd100;color:#09090b;font-weight:900;font-size:11px;padding:3px 8px;border-radius:4px;text-transform:uppercase;">⭐ ANÁLISIS DESTACADO VIGENTE</span>
      <h3 style="font-size:18px;color:#ffffff;margin:10px 0 6px;">
        <a href="{html.escape(post_url_actual)}" target="_blank" rel="noopener noreferrer" style="color:#ffffff;text-decoration:none;">
          {html.escape(titular_actual)}
        </a>
      </h3>
      <p style="font-size:13.5px;color:#a1a1aa;margin-bottom:12px;">{html.escape(bajada_actual)}</p>
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
        <span style="font-size:12.5px;color:#71717a;">Director Editorial: <strong>Andrés Franchi Ugartemendía</strong>{html.escape(anual_tag)}</span>
        <a href="{html.escape(post_url_actual)}" target="_blank" rel="noopener noreferrer" style="background:rgba(255,209,0,0.15);border:1px solid #ffd100;color:#ffd100;padding:6px 14px;border-radius:6px;font-size:12.5px;font-weight:800;text-decoration:none;">
          Leer análisis completo en ServicioTI →
        </a>
      </div>
    </div>

    <div style="display:grid;gap:10px;">
      {recientes_html}
    </div>
    {archive_html}
  </div>

  <div style="margin-bottom:34px;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;border-bottom:2px solid #ffd100;padding-bottom:8px;flex-wrap:wrap;gap:8px;">
      <h2 style="font-size:19px;font-weight:900;color:#ffd100;margin:0;">
        📊 Central de Historiales Frente a Frente Verificados (1891 BD)
      </h2>
      <span style="font-size:12px;color:#a1a1aa;">Fuente: Comisión de Historia y Patrimonio CAP</span>
    </div>
    <div style="overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:13px;text-align:left;background:#121216;border-radius:8px;overflow:hidden;">
        <thead>
          <tr style="background:#18181d;border-bottom:2px solid #ffd100;color:#ffd100;font-weight:800;font-size:12px;text-transform:uppercase;">
            <th style="padding:10px 12px;">Rival</th>
            <th style="padding:10px 8px;text-align:center;">PJ</th>
            <th style="padding:10px 8px;text-align:center;">PG (CAP)</th>
            <th style="padding:10px 8px;text-align:center;">PE</th>
            <th style="padding:10px 8px;text-align:center;">PP</th>
            <th style="padding:10px 8px;text-align:center;">Goles</th>
            <th style="padding:10px 10px;text-align:center;">Ventaja Oficial</th>
            <th style="padding:10px 8px;text-align:center;">Efectividad</th>
            <th style="padding:10px 12px;">Último Choque Oficial</th>
          </tr>
        </thead>
        <tbody>
          {historiales_rows}
        </tbody>
      </table>
    </div>
  </div>

  <div style="background:#121216;border:1px solid rgba(255,209,0,0.25);border-radius:10px;padding:20px;margin-bottom:28px;">
    <h3 style="font-size:17px;font-weight:900;color:#ffd100;margin:0 0 12px;">
      🏆 El Palmarés Más Glorioso del Continente
    </h3>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;text-align:center;">
      <div style="background:rgba(0,0,0,0.6);padding:14px;border-radius:8px;border:1px solid rgba(255,209,0,0.15);">
        <div style="font-size:28px;font-weight:900;color:#ffd100;">5</div>
        <div style="font-size:13px;font-weight:700;color:#fff;">Copas Libertadores</div>
        <div style="font-size:11px;color:#a1a1aa;margin-top:2px;">1960, 1961, 1966, 1982, 1987</div>
      </div>
      <div style="background:rgba(0,0,0,0.6);padding:14px;border-radius:8px;border:1px solid rgba(255,209,0,0.15);">
        <div style="font-size:28px;font-weight:900;color:#ffd100;">3</div>
        <div style="font-size:13px;font-weight:700;color:#fff;">Copas Intercontinentales</div>
        <div style="font-size:11px;color:#a1a1aa;margin-top:2px;">1961, 1966, 1982 (Tricampeón Mundial)</div>
      </div>
      <div style="background:rgba(0,0,0,0.6);padding:14px;border-radius:8px;border:1px solid rgba(255,209,0,0.15);">
        <div style="font-size:28px;font-weight:900;color:#ffd100;">54</div>
        <div style="font-size:13px;font-weight:700;color:#fff;">Campeonatos Uruguayos</div>
        <div style="font-size:11px;color:#a1a1aa;margin-top:2px;">Dos Quinquenios de Oro (58-62 / 93-97)</div>
      </div>
      <div style="background:rgba(0,0,0,0.6);padding:14px;border-radius:8px;border:1px solid rgba(255,209,0,0.15);">
        <div style="font-size:28px;font-weight:900;color:#ffd100;">#1</div>
        <div style="font-size:13px;font-weight:700;color:#fff;">Campeón del Siglo XX</div>
        <div style="font-size:11px;color:#a1a1aa;margin-top:2px;">Distinción oficial IFFHS Sudamérica</div>
      </div>
    </div>
  </div>

  <div style="border-top:1px solid rgba(255,255,255,0.1);padding-top:16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;font-size:12px;color:#71717a;">
    <div>
      Desarrollado y coordinado por <strong>Andrés Franchi Ugartemendía</strong> • Ecosistema <a href="https://www.servicioti.com.uy/" style="color:#ffd100;text-decoration:none;">ServicioTI Uruguay</a>.
    </div>
    <div style="display:flex;gap:12px;">
      <a href="https://manya.servicioti.com.uy/" target="_blank" rel="noopener noreferrer" style="color:#ffd100;text-decoration:none;font-weight:700;">manya.servicioti.com.uy ↗</a>
      <a href="https://horarios.servicioti.com.uy/" target="_blank" rel="noopener noreferrer" style="color:#ffd100;text-decoration:none;font-weight:700;">Radar de Ómnibus ↗</a>
    </div>
  </div>

</div>
"""
    return html_content


def sincronizar_pagina_blogger() -> str:
    """Busca si la página ya existe en Blogger; si existe la actualiza, si no la crea."""
    if not HAS_BLOGGER_LIBS or not TOKEN_PATH.exists():
        logger.info("[Blogger Sync] Credenciales/librerías de Blogger no disponibles en este entorno. Saltando sync remoto.")
        if STATE_FILE.exists():
            try:
                cached = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                return cached.get("url", "")
            except Exception:
                pass
        return "https://www.servicioti.com.uy/p/penarol-archivo-historico-de-analisis.html"

    service = get_blogger_service()

    digest_file = DATA_DIR / "news_digest.json"
    live_file = DATA_DIR / "live_status.json"
    h2h_file = DATA_DIR / "historial_activo.json"

    digest = json.loads(digest_file.read_text(encoding="utf-8")) if digest_file.exists() else {}
    live = json.loads(live_file.read_text(encoding="utf-8")) if live_file.exists() else {}
    h2h_activo = json.loads(h2h_file.read_text(encoding="utf-8")) if h2h_file.exists() else {}

    html_content = generar_contenido_html(digest, live, h2h_activo)

    page_id = None
    if STATE_FILE.exists():
        try:
            cached = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            page_id = cached.get("page_id")
        except Exception:
            pass

    if not page_id:
        pages_resp = service.pages().list(blogId=BLOG_ID).execute()
        for p in pages_resp.get("items", []):
            if "peñarol" in p.get("title", "").lower() and "archivo" in p.get("title", "").lower():
                page_id = p.get("id")
                logger.info(f"[Blogger Sync] Página encontrada en Blogger con ID: {page_id}")
                break

    if page_id:
        logger.info(f"[Blogger Sync] Actualizando página existente ID: {page_id}...")
        res = service.pages().patch(
            blogId=BLOG_ID,
            pageId=page_id,
            body={"title": PAGE_TITLE, "content": html_content},
        ).execute()
        page_url = res.get("url", "")
        logger.info(f"[Blogger Sync] ✓ Página histórica actualizada con éxito: {page_url}")
    else:
        logger.info("[Blogger Sync] Creando nueva Página Estática en Blogger...")
        res = service.pages().insert(
            blogId=BLOG_ID,
            body={"title": PAGE_TITLE, "content": html_content},
        ).execute()
        page_id = res.get("id")
        page_url = res.get("url", "")
        logger.info(f"[Blogger Sync] ✓ Nueva página creada con ID {page_id}: {page_url}")

    state_data = {
        "page_id": page_id,
        "title": PAGE_TITLE,
        "url": page_url,
        "actualizado_el": datetime.now(UY_TZ).isoformat(),
    }
    STATE_FILE.write_text(json.dumps(state_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return page_url


if __name__ == "__main__":
    url = sincronizar_pagina_blogger()
    print("URL DE LA PÁGINA EN BLOGGER:", url)
