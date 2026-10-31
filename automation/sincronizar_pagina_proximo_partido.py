"""
MOTOR DE SINCRONIZACIÓN AUTOMÁTICA DE PRÓXIMO PARTIDO Y RADIOGRAFÍA TÁCTICA EN BLOGGER
======================================================================================
1. Publica y actualiza la Página Estática Permanente en Blogger (/p/penarol-proximo-partido-radiografia.html).
2. Actualiza el post existente (/2026/10/penarol-en-vivo-la-previa-radiografia.html) con la previa 100% futbolera
   del nuevo rival (Montevideo Wanderers), enlazando a la Página Permanente.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

UY_TZ = timezone(timedelta(hours=-3))
BASE_DIR = Path(__file__).resolve().parent.parent
SCRATCH_DIR = BASE_DIR.parent
TOKEN_PATH = SCRATCH_DIR / "seo_blogger_automation" / "token.json"
DATA_DIR = BASE_DIR / "data"
STATE_PAGE_FILE = DATA_DIR / "blogger_pagina_proximo_partido.json"

BLOG_ID = "8220787747664379807"
EXISTING_POST_ID = "5624313100287295662"  # Post histórico /2026/10/penarol-en-vivo-la-previa-radiografia.html
PAGE_TITLE = "Peñarol: Próximo Partido, Radiografía Táctica y Cobertura Oficial | Manya ServicioTI"
SCOPES = ["https://www.googleapis.com/auth/blogger"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s")
logger = logging.getLogger("BloggerProximoPartidoSync")


def get_blogger_service():
    """Autentica cliente OAuth2 oficial de Google Blogger v3."""
    from google.auth.transport.requests import Request
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return build("blogger", "v3", credentials=creds)


def construir_html_proximo_partido(live_data, rival_data, digest_data):
    """Construye el HTML editorial definitivo, responsivo y adaptado para Blogger."""
    now_uy = datetime.now(UY_TZ).strftime("%d/%m/%Y %H:%M")
    prox = live_data.get("proximo_partido") or {}
    scout = rival_data.get("scouting_tactico") or {}
    inst = rival_data.get("datos_institucionales_auf") or {}
    duelos = rival_data.get("duelos_tacticos_1x1") or []
    hist = rival_data.get("historial_certificacion_1891") or {}
    
    rival_nombre = "Montevideo Wanderers"
    rival_escudo = "https://manya.servicioti.com.uy/assets/img/escudos/escudo_montevideo_wanderers.webp"
    penarol_escudo = "https://manya.servicioti.com.uy/assets/img/escudos/escudo_penarol.webp"
    
    fecha_legible = prox.get("fecha_legible") or "Sábado 31/10/2026 16:30 hs"
    estadio = prox.get("estadio") or "Parque Federico Omar Saroldi (Prado)"
    torneo = prox.get("torneo") or "Torneo Clausura 2026 (Fecha 12)"
    tv = prox.get("tv") or "VTV Plus / Disney+ Premium"
    
    duelos_html = ""
    for d in duelos:
        duelos_html += f"""
        <div style="background:#18181d;border:1px solid rgba(255,255,255,0.08);border-left:4px solid #ffd100;border-radius:8px;padding:14px;margin-bottom:12px;">
          <div style="font-size:11.5px;color:#ffd100;font-weight:900;text-transform:uppercase;margin-bottom:4px;">⚔️ {d.get('titulo', '')} • {d.get('zona_campo', '')}</div>
          <div style="display:flex;justify-content:space-between;gap:12px;margin:8px 0;flex-wrap:wrap;font-size:13.5px;">
            <div style="flex:1;min-width:200px;"><strong style="color:#ffd100;">🟡⚫ Peñarol:</strong> {d.get('penarol', {}).get('jugador', '')} ({d.get('penarol', {}).get('rol', '')})<br><span style="font-size:12px;color:#a1a1aa;">{d.get('penarol', {}).get('atributos_clave', '')}</span></div>
            <div style="flex:1;min-width:200px;"><strong style="color:#38bdf8;">⚪⚫ Rival:</strong> {d.get('rival', {}).get('jugador', '')} ({d.get('rival', {}).get('rol', '')})<br><span style="font-size:12px;color:#a1a1aa;">{d.get('rival', {}).get('atributos_clave', '')}</span></div>
          </div>
          <div style="font-size:12.5px;color:#d4d4d8;background:rgba(0,0,0,0.3);padding:8px;border-radius:6px;margin-top:6px;"><strong>Clave del Duelo:</strong> {d.get('clave_del_duelo', '')}</div>
        </div>
        """

    figuras_html = ""
    for f in scout.get("figuras_a_seguir", []):
        figuras_html += f"""
        <div style="background:#141419;border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:12px;margin-bottom:8px;">
          <strong style="color:#ffd100;font-size:14px;">• {f.get('nombre', '')} ({f.get('rol', '')})</strong>
          <p style="font-size:12.5px;color:#d4d4d8;margin:4px 0 0;">{f.get('analisis', '')}</p>
        </div>
        """

    html = f"""
<div style="font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#18181b;line-height:1.6;max-width:960px;margin:0 auto;padding:10px;">

  <!-- ENCABEZADO OFICIAL DE LA PÁGINA PERMANENTE -->
  <div style="background:linear-gradient(135deg,#09090b 0%,#18181b 100%);color:#ffffff;padding:26px 22px;border-radius:14px;border:2px solid #ffd100;box-shadow:0 10px 30px rgba(0,0,0,0.35);margin-bottom:24px;">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;border-bottom:1px solid rgba(255,209,0,0.3);padding-bottom:14px;margin-bottom:18px;">
      <span style="background:#ffd100;color:#09090b;font-weight:900;font-size:11.5px;padding:4px 12px;border-radius:999px;letter-spacing:0.04em;">
        ★ PÁGINA CENTRAL PERMANENTE • PRÓXIMO PARTIDO Y RADIOGRAFÍA TÁCTICA
      </span>
      <span style="font-size:12px;color:#ffd100;font-weight:700;">Actualizado: {now_uy} hs</span>
    </div>

    <!-- TARJETA DEL PRÓXIMO PARTIDO -->
    <div style="text-align:center;margin-bottom:20px;">
      <h1 style="color:#ffffff;font-size:clamp(22px,3.8vw,32px);font-weight:900;margin:0 0 10px;line-height:1.25;">
        Montevideo Wanderers vs. Peñarol
      </h1>
      <div style="font-size:15px;color:#ffd100;font-weight:800;margin-bottom:6px;">
        {torneo} • {fecha_legible}
      </div>
      <div style="font-size:13.5px;color:#a1a1aa;">
        🏟️ {estadio} • 📺 Transmisión en vivo por {tv}
      </div>
    </div>

    <!-- BOTONES DE ACCESO DIRECTO -->
    <div style="display:flex;justify-content:center;gap:10px;flex-wrap:wrap;margin-top:16px;">
      <a href="https://manya.servicioti.com.uy/" target="_blank" rel="noopener noreferrer" style="background:#ffd100;color:#09090b;font-weight:900;padding:10px 20px;border-radius:999px;text-decoration:none;font-size:13.5px;box-shadow:0 4px 15px rgba(255,209,0,0.3);">
        ⚡ Ir a manya.servicioti.com.uy (Match Center en Vivo) ↗
      </a>
      <a href="https://manya.servicioti.com.uy/#pizarra-tactica" target="_blank" rel="noopener noreferrer" style="border:1px solid #ffd100;color:#ffd100;font-weight:800;padding:10px 18px;border-radius:999px;text-decoration:none;font-size:13px;">
        👕 Pizarra Táctica: Armá tu 11 vs Wanderers
      </a>
      <a href="https://horarios.servicioti.com.uy/" target="_blank" rel="noopener noreferrer" style="border:1px solid rgba(255,255,255,0.3);color:#e4e4e7;font-weight:700;padding:10px 18px;border-radius:999px;text-decoration:none;font-size:13px;">
        🚌 Ómnibus al Parque Saroldi (Prado) en Vivo
      </a>
    </div>
  </div>

  <!-- AVISO DE PÁGINA PERMANENTE -->
  <div style="background:#fefce8;border:1px solid #fde047;border-left:4px solid #ca8a04;padding:14px 18px;border-radius:8px;margin-bottom:24px;color:#713f12;font-size:13.5px;">
    <strong>ℹ️ Página Permanente Oficial de ServicioTI:</strong> Esta URL se mantiene constante y se actualiza de manera automática al término de cada encuentro para ofrecerte la radiografía táctica, datos del rival, árbitros, venta de entradas y la previa del siguiente compromiso del Club Atlético Peñarol.
  </div>

  <!-- BLOQUE: CONTEXTO RECIENTE Y SITUACIÓN DE LA TABLA ANUAL -->
  <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-bottom:24px;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;border-bottom:2px solid #ffd100;padding-bottom:8px;">
      <h2 style="font-size:18px;font-weight:900;color:#09090b;margin:0;">⚡ Situación en la Tabla Anual y Definición del Torneo</h2>
      <span style="font-size:12px;background:#fef08a;color:#854d0e;padding:3px 10px;border-radius:4px;font-weight:900;">Líder Solitario • 65 pts</span>
    </div>
    <div style="display:flex;align-items:center;justify-content:space-between;background:#09090b;color:#fff;padding:14px 20px;border-radius:10px;margin-bottom:12px;flex-wrap:wrap;gap:10px;">
      <div>
        <strong style="font-size:16px;color:#ffd100;">Peñarol lidera la Tabla Anual con 65 unidades</strong>
        <div style="font-size:12px;color:#a1a1aa;">Ventaja de 2 puntos sobre el escolta con 4 fechas restantes • Saldo de goles: +34</div>
      </div>
      <a href="https://manya.servicioti.com.uy/#tabla-simulador" target="_blank" rel="noopener noreferrer" style="background:#ffd100;color:#09090b;font-weight:900;font-size:12px;padding:6px 14px;border-radius:6px;text-decoration:none;">
        📊 Simular Tabla Anual en Vivo ↗
      </a>
    </div>
    <p style="font-size:14px;color:#475569;margin:0;">
      El equipo de Diego Aguirre salta al campo del Parque Federico Omar Saroldi oficiando como local a puertas cerradas para su público por sanción al CDS, con el objetivo supremo de sumar tres puntos vitales para mantener la punta de la Tabla Anual.
    </p>
  </div>

  <!-- RADIOGRAFÍA TÁCTICA DEL RIVAL: MONTEVIDEO WANDERERS -->
  <div style="background:#09090b;color:#ffffff;border:1px solid rgba(255,209,0,0.35);border-radius:14px;padding:24px;margin-bottom:24px;box-shadow:0 4px 20px rgba(0,0,0,0.2);">
    <div style="border-bottom:2px solid #ffd100;padding-bottom:10px;margin-bottom:18px;">
      <span style="background:#ffd100;color:#09090b;font-size:11px;font-weight:900;padding:2px 8px;border-radius:4px;text-transform:uppercase;">SCOUTING TÁCTICO PROFESIONAL</span>
      <h2 style="font-size:22px;color:#ffffff;margin:8px 0 4px;font-weight:900;">
        🔍 Radiografía Táctica: {rival_nombre} (DT Mathías Corujo)
      </h2>
      <div style="font-size:13px;color:#a1a1aa;">
        DT: <strong>{scout.get('entrenador', 'Mathías Corujo')}</strong> • Esquema: <strong>{scout.get('esquema_base', '4-2-3-1 de posesión y circulación')}</strong> • Sede: {inst.get('sede', 'Prado')}
      </div>
    </div>

    <div style="font-size:14px;color:#d4d4d8;line-height:1.65;margin-bottom:20px;">
      {scout.get("propuesta_juego", "Montevideo Wanderers, conducido tácticamente por Mathías 'Chiche' Corujo, presenta un equipo ordenado y dinámico, respaldado por la experiencia de Fabricio Formiliano en el fondo, Gonzalo Freitas en el medio y la velocidad de Jonathan Urretaviscaya en ataque junto a Mateo Levato.")}
    </div>

    <!-- FORTALEZAS Y VULNERABILIDADES -->
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px;margin-bottom:22px;">
      <div style="background:#141419;border:1px solid rgba(255,255,255,0.06);border-top:3px solid #10b981;border-radius:8px;padding:14px;">
        <strong style="color:#10b981;font-size:14px;display:block;margin-bottom:8px;">✓ Puntos Fuertes a Neutralizar</strong>
        <ul style="margin:0;padding-left:18px;font-size:13px;color:#d4d4d8;">
          {"".join(f'<li style="margin-bottom:4px;">{pt}</li>' for pt in scout.get('puntos_fuertes', ['Circulación media fluida', 'Peligro en pelota quieta de Viudez']))}
        </ul>
      </div>

      <div style="background:#141419;border:1px solid rgba(255,255,255,0.06);border-top:3px solid #ef4444;border-radius:8px;padding:14px;">
        <strong style="color:#ef4444;font-size:14px;display:block;margin-bottom:8px;">⚠️ Dónde Dañar a Wanderers</strong>
        <ul style="margin:0;padding-left:18px;font-size:13px;color:#d4d4d8;">
          {"".join(f'<li style="margin-bottom:4px;">{vul}</li>' for vul in scout.get('vulnerabilidades_a_explotar', ['Presión alta de Peñarol sobre la salida bohemia', 'Espaldas de los laterales en transición rápida']))}
        </ul>
      </div>
    </div>

    <!-- FIGURAS A SEGUIR -->
    <h3 style="font-size:16px;color:#ffd100;margin:0 0 12px;font-weight:900;">🎯 Figuras a Seguir de Montevideo Wanderers</h3>
    {figuras_html}

    <!-- DUELOS TÁCTICOS 1X1 -->
    <h3 style="font-size:16px;color:#ffd100;margin:20px 0 12px;font-weight:900;">⚔️ Duelos Tácticos 1x1 Clave en el Prado</h3>
    {duelos_html}
  </div>

  <!-- CERTIFICACIÓN HISTÓRICA 1891 BD -->
  <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;padding:22px;margin-bottom:24px;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;border-bottom:2px solid #ffd100;padding-bottom:8px;flex-wrap:wrap;gap:8px;">
      <h3 style="font-size:18px;font-weight:900;color:#09090b;margin:0;">📜 Historial Oficial Verificado (1891 BD)</h3>
      <span style="font-size:12px;background:#fef08a;color:#854d0e;padding:3px 8px;border-radius:4px;font-weight:800;">+108 Victorias Mirasoles</span>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;text-align:center;margin-bottom:14px;">
      <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
        <div style="font-size:24px;font-weight:900;color:#09090b;">{hist.get('partidos_jugados', '204')}</div>
        <div style="font-size:11.5px;color:#64748b;">Partidos Disputados</div>
      </div>
      <div style="background:#fefce8;padding:12px;border-radius:8px;border:1px solid #fde047;">
        <div style="font-size:24px;font-weight:900;color:#ca8a04;">{hist.get('ganados_penarol', '132')}</div>
        <div style="font-size:11.5px;color:#854d0e;">Triunfos de Peñarol</div>
      </div>
      <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
        <div style="font-size:24px;font-weight:900;color:#09090b;">{hist.get('empatados', '48')}</div>
        <div style="font-size:11.5px;color:#64748b;">Empates</div>
      </div>
      <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
        <div style="font-size:24px;font-weight:900;color:#09090b;">{hist.get('efectividad_pct', '73.2%')}</div>
        <div style="font-size:11.5px;color:#64748b;">Efectividad Aurinegra</div>
      </div>
    </div>
    <div style="font-size:13.5px;color:#475569;text-align:center;">
      Marcada supremacía histórica para el Decano: <strong>{hist.get('ventaja_victorias', '+108 partidos a favor del Decano')}</strong> con {hist.get('diferencia_goles', '+224')} goles de diferencia.
    </div>
  </div>

  <!-- PIE DE PÁGINA -->
  <div style="text-align:center;padding:24px;background:#f8fafc;border-radius:12px;border:1px solid #e2e8f0;font-size:13px;color:#64748b;">
    <p style="margin:0 0 6px;">Página permanente producida por <strong>Manya ServicioTI</strong> para <a href="https://www.servicioti.com.uy/" style="color:#ca8a04;font-weight:800;">www.servicioti.com.uy</a> y <a href="https://manya.servicioti.com.uy/" style="color:#ca8a04;font-weight:800;">manya.servicioti.com.uy</a>.</p>
    <p style="margin:0;">Club Atlético Peñarol • Fundado el 28 de septiembre de 1891 • Campeón del Siglo XX de Sudamérica</p>
  </div>

</div>
"""
    return html


def sincronizar_proximo_partido_blogger():
    """Ejecuta la sincronización completa: crea/actualiza la Página Estática y actualiza el Post."""
    logger.info("=== INICIANDO SINCRONIZACIÓN DE PÁGINA Y POST DE PRÓXIMO PARTIDO EN BLOGGER ===")
    service = get_blogger_service()
    
    live_file = DATA_DIR / "live_status.json"
    rival_file = DATA_DIR / "rival_intelligence.json"
    digest_file = DATA_DIR / "news_digest.json"
    
    live = json.loads(live_file.read_text(encoding="utf-8")) if live_file.exists() else {}
    rival = json.loads(rival_file.read_text(encoding="utf-8")) if rival_file.exists() else {}
    digest = json.loads(digest_file.read_text(encoding="utf-8")) if digest_file.exists() else {}
    
    html_content = construir_html_proximo_partido(live, rival, digest)
    
    # -------------------------------------------------------------
    # 1. Gestionar la Página Estática Permanente en Blogger (/p/...)
    # -------------------------------------------------------------
    page_id = None
    if STATE_PAGE_FILE.exists():
        try:
            cached = json.loads(STATE_PAGE_FILE.read_text(encoding="utf-8"))
            page_id = cached.get("page_id")
        except Exception:
            pass
            
    if not page_id:
        pages_resp = service.pages().list(blogId=BLOG_ID).execute()
        for p in pages_resp.get("items", []):
            t = p.get("title", "").lower()
            if "próximo partido" in t or "proximo partido" in t or "radiografía táctica" in t:
                page_id = p.get("id")
                logger.info(f"[Blogger Previa] Página estática existente encontrada con ID: {page_id}")
                break

    page_url = ""
    if page_id:
        logger.info(f"[Blogger Previa] Actualizando Página Estática ID: {page_id}...")
        body = {"title": PAGE_TITLE, "content": html_content}
        res_page = service.pages().patch(blogId=BLOG_ID, pageId=page_id, body=body).execute()
        page_url = res_page.get("url", "")
        logger.info(f"[Blogger Previa] ✓ Página estática actualizada: {page_url}")
    else:
        logger.info("[Blogger Previa] Creando nueva Página Estática Permanente en Blogger...")
        body = {"title": PAGE_TITLE, "content": html_content}
        res_page = service.pages().insert(blogId=BLOG_ID, body=body).execute()
        page_id = res_page.get("id")
        page_url = res_page.get("url", "")
        logger.info(f"[Blogger Previa] ✓ Nueva Página estática creada con éxito: {page_url}")

    # Guardar estado de la página estática
    page_state = {
        "page_id": page_id,
        "title": PAGE_TITLE,
        "url": page_url,
        "actualizado": datetime.now(UY_TZ).isoformat()
    }
    STATE_PAGE_FILE.write_text(json.dumps(page_state, ensure_ascii=False, indent=2), encoding="utf-8")

    # -------------------------------------------------------------
    # 2. Actualizar el Post Existente (penarol-en-vivo-la-previa-radiografia.html)
    # -------------------------------------------------------------
    post_banner_redirect = f"""
    <div style="background:#09090b;border:2px solid #ffd100;border-radius:12px;padding:18px 22px;margin-bottom:24px;color:#ffffff;box-shadow:0 8px 24px rgba(255,209,0,0.25);">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:10px;">
        <span style="background:#ffd100;color:#09090b;font-weight:900;font-size:11.5px;padding:3px 10px;border-radius:999px;">⚡ PREVIA CONFIRMADA • FECHA 12 CLAUSURA</span>
        <span style="font-size:12px;color:#ffd100;">Sábado 31/10 16:30 hs • Parque Saroldi</span>
      </div>
      <h3 style="font-size:20px;color:#ffffff;margin:0 0 8px;font-weight:900;">
        Peñarol vs Montevideo Wanderers (DT Mathías Corujo) en el Parque Saroldi
      </h3>
      <p style="font-size:14px;color:#d4d4d8;line-height:1.6;margin:0 0 14px;">
        El Carbonero lidera la Tabla Anual con 65 unidades y recibe al conjunto bohemio en el Parque Saroldi (a puertas cerradas para Peñarol por sanción AUF, con entradas para Wanderers vía Tickantel). Consulta a continuación la radiografía táctica completa, duelos 1x1, figuras a seguir y el historial 1891 BD:
      </p>
      <a href="{page_url}" style="background:#ffd100;color:#09090b;font-weight:900;padding:10px 22px;border-radius:999px;text-decoration:none;font-size:13.5px;display:inline-flex;align-items:center;gap:6px;">
        👉 Ver Radiografía Táctica Completa en ServicioTI ↗
      </a>
    </div>
    """
    
    post_updated_html = post_banner_redirect + html_content
    post_updated_title = "[Peñarol] Radiografía Táctica & Previa Oficial: Peñarol vs Montevideo Wanderers • Torneo Clausura (Fecha 12)"
    
    try:
        logger.info(f"[Blogger Post Update] Actualizando post existente ID: {EXISTING_POST_ID}...")
        service.posts().patch(
            blogId=BLOG_ID,
            postId=EXISTING_POST_ID,
            body={
                "title": post_updated_title,
                "content": post_updated_html,
                "labels": ["Peñarol", "Previa", "Radiografía Táctica", "Montevideo Wanderers", "Torneo Clausura", "ServicioTI"]
            }
        ).execute()
        logger.info(f"[Blogger Post Update] ✓ Post existente {EXISTING_POST_ID} actualizado exitosamente con el próximo rival Wanderers.")
    except Exception as e:
        logger.warning(f"[Blogger Post Update] Aviso al actualizar post existente: {e}")

    # -------------------------------------------------------------
    # 3. Guardar URLs en news_digest.json y live_status.json
    # -------------------------------------------------------------
    digest["blogger_previa_page_url"] = page_url
    digest_file.write_text(json.dumps(digest, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info(f"[Blogger Sync Completo] URL de la Página Permanente: {page_url}")
    return page_url


if __name__ == "__main__":
    url = sincronizar_proximo_partido_blogger()
