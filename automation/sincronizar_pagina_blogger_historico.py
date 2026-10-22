# -*- coding: utf-8 -*-
"""
SINCRONIZADOR DE LA PÁGINA CENTRAL DE ARCHIVO HISTÓRICO Y ANÁLISIS EN BLOGGER
=============================================================================
Archivo: sincronizar_pagina_blogger_historico.py
Crea o actualiza la Página Estática oficial en www.servicioti.com.uy:
  - Título: Peñarol: Archivo Histórico de Análisis Tácticos, Crónicas e Historial de Partidos | Manya ServicioTI
  - Respaldo de todos los análisis y crónicas publicadas en el ecosistema.
  - Central de historiales frente a frente (1891 BD) de todos los rivales del Campeonato Uruguayo.
  - Fichas técnicas, estadísticas y enlace canónico hacia manya.servicioti.com.uy.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
sys.path.insert(0, str(BASE_DIR / "automation"))

try:
    from blogger_manya_publisher import get_blogger_service, BLOG_ID, TOKEN_PATH
    HAS_BLOGGER_LIBS = True
except (ImportError, Exception) as e_imp:
    HAS_BLOGGER_LIBS = False
    BLOG_ID = "8220787747664379807"
    TOKEN_PATH = Path("non_existent_token.json")

logger = logging.getLogger("BloggerHistoricoSync")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

PAGE_TITLE = "Peñarol: Archivo Histórico de Análisis Tácticos, Crónicas e Historial de Partidos | Manya ServicioTI"
STATE_FILE = DATA_DIR / "blogger_pagina_historica.json"


def generar_contenido_html(digest: dict, live: dict, h2h_juv: dict) -> str:
    """Genera el HTML enriquecido y responsive para la página estática en Blogger."""
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Análisis actual
    titular_actual = digest.get("titular_dia", "Previa Oficial: Peñarol ante Juventud en el Estadio Centenario")
    bajada_actual = digest.get("bajada_seo", "")
    post_url_actual = digest.get("blogger_post_url", "https://www.servicioti.com.uy/2026/10/penarol-en-vivo-la-previa-radiografia.html")
    
    # Historiales 1891 BD
    historiales = [
        {"rival": "Juventud de Las Piedras", "pj": 33, "pg": 23, "pe": 7, "pp": 3, "gf": 67, "gc": 22, "ventaja": "+20 partidos", "efectividad": "76.7%", "ultimo": "2-2 (CDS 2026) / Próx: Viernes 23/10"},
        {"rival": "Liverpool", "pj": 162, "pg": 104, "pe": 32, "pp": 26, "gf": 338, "gc": 162, "ventaja": "+78 partidos", "efectividad": "74.1%", "ultimo": "1-0 (Viera, Clausura 2026)"},
        {"rival": "Racing Club", "pj": 138, "pg": 92, "pe": 28, "pp": 18, "gf": 312, "gc": 140, "ventaja": "+74 partidos", "efectividad": "76.8%", "ultimo": "2-1 (Clausura 2026)"},
        {"rival": "Progreso", "pj": 48, "pg": 34, "pe": 10, "pp": 4, "gf": 114, "gc": 42, "ventaja": "+30 partidos", "efectividad": "81.2%", "ultimo": "0-2 (Paladino, Clausura 2026)"},
        {"rival": "Club Nacional de Football (Clásico)", "pj": 571, "pg": 197, "pe": 189, "pp": 185, "gf": 740, "gc": 702, "ventaja": "+12 partidos (Paternidad Oficial)", "efectividad": "51.1%", "ultimo": "Histórico 5-0 (2014) y Clásicos 2026"},
        {"rival": "Defensor Sporting", "pj": 198, "pg": 118, "pe": 46, "pp": 34, "gf": 412, "gc": 228, "ventaja": "+84 partidos", "efectividad": "71.2%", "ultimo": "2-0 (CDS)"},
        {"rival": "Danubio", "pj": 156, "pg": 99, "pe": 28, "pp": 29, "gf": 318, "gc": 164, "ventaja": "+70 partidos", "efectividad": "72.4%", "ultimo": "1-0 (Jardines)"},
        {"rival": "Montevideo Wanderers", "pj": 182, "pg": 110, "pe": 42, "pp": 30, "gf": 370, "gc": 198, "ventaja": "+80 partidos", "efectividad": "72.0%", "ultimo": "3-1 (Parque Viera)"},
        {"rival": "Cerro Largo", "pj": 26, "pg": 17, "pe": 6, "pp": 3, "gf": 52, "gc": 21, "ventaja": "+14 partidos", "efectividad": "76.9%", "ultimo": "2-0 (Ubilla Melo)"},
        {"rival": "Boston River", "pj": 20, "pg": 14, "pe": 4, "pp": 2, "gf": 41, "gc": 16, "ventaja": "+12 partidos", "efectividad": "80.0%", "ultimo": "3-1 (CDS)"}
    ]

    historiales_rows = "".join([f"""
      <tr style="border-bottom:1px solid rgba(255,209,0,0.18);">
        <td style="padding:10px 12px;font-weight:700;color:#ffffff;">{h['rival']}</td>
        <td style="padding:10px 8px;text-align:center;color:#e4e4e7;">{h['pj']}</td>
        <td style="padding:10px 8px;text-align:center;font-weight:800;color:#ffd100;">{h['pg']}</td>
        <td style="padding:10px 8px;text-align:center;color:#a1a1aa;">{h['pe']}</td>
        <td style="padding:10px 8px;text-align:center;color:#ef4444;">{h['pp']}</td>
        <td style="padding:10px 8px;text-align:center;color:#ffd100;">{h['gf']}-{h['gc']}</td>
        <td style="padding:10px 10px;text-align:center;font-size:12px;color:#22c55e;font-weight:700;">{h['ventaja']}</td>
        <td style="padding:10px 8px;text-align:center;font-weight:800;color:#ffd100;">{h['efectividad']}</td>
        <td style="padding:10px 12px;font-size:12px;color:#d4d4d8;">{h['ultimo']}</td>
      </tr>
    """ for h in historiales])

    html_content = f"""
<div style="font-family:'Inter',system-ui,-apple-system,sans-serif;color:#ffffff;background:#09090b;padding:24px 20px;border-radius:14px;border:2px solid #ffd100;box-shadow:0 10px 30px rgba(0,0,0,0.7);max-width:980px;margin:0 auto;line-height:1.6;">

  <!-- Banner Superior Identitario -->
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

  <!-- SÍNTESIS EDITORIAL -->
  <p style="font-size:15px;color:#d4d4d8;margin-bottom:24px;border-bottom:1px solid rgba(255,255,255,0.1);padding-bottom:16px;">
    Esta página constituye el <strong>repositorio y archivo histórico permanente</strong> de todas las crónicas, radiografías tácticas y análisis publicados por el equipo editorial de <strong>ServicioTI Uruguay</strong> y <a href="https://manya.servicioti.com.uy/" style="color:#ffd100;text-decoration:underline;">manya.servicioti.com.uy</a>, respaldados por la base documental oficial de la Comisión de Historia y Patrimonio del Club Atlético Peñarol (<strong>1891 BD</strong>) y datos oficiales AUF.
  </p>

  <!-- MÓDULO 1: ANÁLISIS EN CURSO Y RESPALDO DE CRÓNICAS -->
  <div style="margin-bottom:34px;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;border-bottom:2px solid #ffd100;padding-bottom:8px;">
      <h2 style="font-size:19px;font-weight:900;color:#ffd100;margin:0;">
        📰 Respaldo Histórico de Crónicas y Análisis Tácticos
      </h2>
      <span style="font-size:12px;background:rgba(255,209,0,0.15);color:#ffd100;border:1px solid #ffd100;padding:3px 10px;border-radius:999px;font-weight:800;">Actualizado: {now_str}</span>
    </div>

    <!-- Artículo Destacado Actual -->
    <div style="background:#121216;border:1px solid rgba(255,209,0,0.3);border-radius:10px;padding:18px;margin-bottom:16px;">
      <span style="background:#ffd100;color:#09090b;font-weight:900;font-size:11px;padding:3px 8px;border-radius:4px;text-transform:uppercase;">⭐ ANÁLISIS DESTACADO DE LA FECHA</span>
      <h3 style="font-size:18px;color:#ffffff;margin:10px 0 6px;">
        <a href="{post_url_actual}" target="_blank" rel="noopener noreferrer" style="color:#ffffff;text-decoration:none;">
          {titular_actual}
        </a>
      </h3>
      <p style="font-size:13.5px;color:#a1a1aa;margin-bottom:12px;">{bajada_actual}</p>
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
        <span style="font-size:12.5px;color:#71717a;">Director Editorial: <strong>Andrés Franchi Ugartemendía</strong> • Torneo Clausura 2026</span>
        <a href="{post_url_actual}" target="_blank" rel="noopener noreferrer" style="background:rgba(255,209,0,0.15);border:1px solid #ffd100;color:#ffd100;padding:6px 14px;border-radius:6px;font-size:12.5px;font-weight:800;text-decoration:none;">
          Leer análisis completo en ServicioTI →
        </a>
      </div>
    </div>

    <!-- Catálogo de Partidos del Torneo Clausura 2026 -->
    <div style="display:grid;gap:10px;">
      <div style="background:#18181d;border:1px solid rgba(255,255,255,0.08);border-left:4px solid #ffd100;border-radius:8px;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
        <div>
          <strong style="color:#ffffff;font-size:14px;">Fecha 11: Juventud vs Peñarol (Estadio Centenario)</strong>
          <div style="font-size:12px;color:#a1a1aa;">Radiografía táctica de duelos 1x1, laboratorio de Diego Aguirre y venta de entradas en el Centenario.</div>
        </div>
        <a href="{post_url_actual}" target="_blank" rel="noopener noreferrer" style="color:#ffd100;font-size:12px;font-weight:800;text-decoration:underline;">Ver Crónica ↗</a>
      </div>

      <div style="background:#18181d;border:1px solid rgba(255,255,255,0.08);border-left:4px solid #71717a;border-radius:8px;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
        <div>
          <strong style="color:#ffffff;font-size:14px;">Fecha 10: Liverpool 1 - 0 Peñarol (Estadio Parque Viera)</strong>
          <div style="font-size:12px;color:#a1a1aa;">Análisis del planteo cerrado de Fossati, la tarjeta roja a Jesús Trindade y el liderazgo aurinegro en la Tabla Anual.</div>
        </div>
        <a href="https://manya.servicioti.com.uy/" target="_blank" rel="noopener noreferrer" style="color:#ffd100;font-size:12px;font-weight:800;text-decoration:underline;">Ficha en Manya ↗</a>
      </div>

      <div style="background:#18181d;border:1px solid rgba(255,255,255,0.08);border-left:4px solid #22c55e;border-radius:8px;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
        <div>
          <strong style="color:#ffffff;font-size:14px;">Fecha 9: Peñarol 2 - 1 Racing (Estadio Campeón del Siglo)</strong>
          <div style="font-size:12px;color:#a1a1aa;">Victoria agónica con garra aurinegra en la hora, empuje de la hinchada en la Damiani y 3 puntos cruciales.</div>
        </div>
        <a href="https://manya.servicioti.com.uy/" target="_blank" rel="noopener noreferrer" style="color:#ffd100;font-size:12px;font-weight:800;text-decoration:underline;">Ficha en Manya ↗</a>
      </div>

      <div style="background:#18181d;border:1px solid rgba(255,255,255,0.08);border-left:4px solid #22c55e;border-radius:8px;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
        <div>
          <strong style="color:#ffffff;font-size:14px;">Fecha 8: Progreso 0 - 2 Peñarol (Estadio Parque Paladino)</strong>
          <div style="font-size:12px;color:#a1a1aa;">Contundencia ofensiva, efectividad en pelota quieta y valla invicta para consolidar la punta.</div>
        </div>
        <a href="https://manya.servicioti.com.uy/" target="_blank" rel="noopener noreferrer" style="color:#ffd100;font-size:12px;font-weight:800;text-decoration:underline;">Ficha en Manya ↗</a>
      </div>
    </div>
  </div>

  <!-- MÓDULO 2: TABLA CENTRALIZADA DE HISTORIALES DE PARTIDOS (1891 BD) -->
  <div style="margin-bottom:34px;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;border-bottom:2px solid #ffd100;padding-bottom:8px;">
      <h2 style="font-size:19px;font-weight:900;color:#ffd100;margin:0;">
        📊 Central de Historiales Frente a Frente (1891 BD)
      </h2>
      <span style="font-size:12px;color:#a1a1aa;">Fuente: Comisión de Historia y Patrimonio CAP</span>
    </div>
    <p style="font-size:13.5px;color:#d4d4d8;margin-bottom:14px;">
      Registro exhaustivo de los enfrentamientos oficiales de Peñarol contra los clubes de la Primera División uruguaya, documentando la paternidad y supremacía deportiva histórica del Decano:
    </p>

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

  <!-- MÓDULO 3: EL PALMARÉS DEL DECANO -->
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

  <!-- PIE DE PÁGINA Y CRÉDITOS ECOSISTEMA SERVICIOTI -->
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
    if not HAS_BLOGGER_LIBS:
        logger.info("[Blogger Sync] Librerías de Google Blogger no disponibles en este entorno. Saltando sync remoto.")
        if STATE_FILE.exists():
            try:
                cached = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                return cached.get("url", "")
            except Exception:
                pass
        return "https://www.servicioti.com.uy/p/penarol-archivo-historico-de-analisis.html"

    if not TOKEN_PATH.exists():
        logger.info("[Blogger Sync] token.json no disponible en este entorno. Saltando sync remoto.")
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
    h2h_file = DATA_DIR / "historial_juventud.json"
    
    digest = json.loads(digest_file.read_text(encoding="utf-8")) if digest_file.exists() else {}
    live = json.loads(live_file.read_text(encoding="utf-8")) if live_file.exists() else {}
    h2h_juv = json.loads(h2h_file.read_text(encoding="utf-8")) if h2h_file.exists() else {}
    
    html_content = generar_contenido_html(digest, live, h2h_juv)
    
    # 1. Verificar si ya tenemos el page_id guardado
    page_id = None
    if STATE_FILE.exists():
        try:
            cached = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            page_id = cached.get("page_id")
        except Exception:
            pass

    # 2. Si no tenemos id en caché, listar páginas para buscar por título
    if not page_id:
        pages_resp = service.pages().list(blogId=BLOG_ID).execute()
        for p in pages_resp.get("items", []):
            if "peñarol" in p.get("title", "").lower() and "archivo" in p.get("title", "").lower():
                page_id = p.get("id")
                logger.info(f"[Blogger Sync] Página encontrada en Blogger con ID: {page_id}")
                break

    page_url = ""
    if page_id:
        logger.info(f"[Blogger Sync] Actualizando página existente ID: {page_id}...")
        body = {
            "title": PAGE_TITLE,
            "content": html_content
        }
        res = service.pages().patch(blogId=BLOG_ID, pageId=page_id, body=body).execute()
        page_url = res.get("url", "")
        logger.info(f"[Blogger Sync] ✓ Página actualizada con éxito: {page_url}")
    else:
        logger.info("[Blogger Sync] Creando nueva Página Estática en Blogger...")
        body = {
            "title": PAGE_TITLE,
            "content": html_content
        }
        res = service.pages().insert(blogId=BLOG_ID, body=body).execute()
        page_id = res.get("id")
        page_url = res.get("url", "")
        logger.info(f"[Blogger Sync] ✓ Nueva página creada con ID {page_id}: {page_url}")

    # Guardar estado local
    state_data = {
        "page_id": page_id,
        "title": PAGE_TITLE,
        "url": page_url,
        "actualizado_el": datetime.now().isoformat()
    }
    STATE_FILE.write_text(json.dumps(state_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return page_url


if __name__ == "__main__":
    url = sincronizar_pagina_blogger()
    print("URL DE LA PÁGINA EN BLOGGER:", url)
