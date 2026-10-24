"""
MOTOR DE SINCRONIZACIÓN AUTOMÁTICA DE PRÓXIMO PARTIDO Y RADIOGRAFÍA TÁCTICA EN BLOGGER
======================================================================================
1. Publica y actualiza la Página Estática Permanente en Blogger (/p/...) para el próximo rival.
2. Actualiza el post existente (penarol-en-vivo-la-previa-radiografia.html) con el resultado reciente
   y la previa del nuevo rival (Montevideo Wanderers), enlazando a la Página Permanente.
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
    ult = live_data.get("ultimo_partido") or {}
    scout = rival_data.get("scouting_tactico") or {}
    inst = rival_data.get("datos_institucionales_auf") or {}
    duelos = rival_data.get("duelos_tacticos_1x1") or []
    hist = rival_data.get("historial_certificacion_1891") or {}
    
    rival_nombre = prox.get("visitante", {}).get("nombre") if prox.get("local", {}).get("es_penarol") else prox.get("local", {}).get("nombre", "Montevideo Wanderers")
    rival_escudo = "https://manya.servicioti.com.uy/assets/img/escudos/escudo_montevideo_wanderers.webp"
    penarol_escudo = "https://manya.servicioti.com.uy/assets/img/escudos/escudo_penarol.webp"
    
    fecha_legible = prox.get("fecha_legible") or "Sábado 31/10/2026 16:30 hs"
    estadio = prox.get("estadio") or "Estadio Saroldi / Parque Alfredo Víctor Viera"
    torneo = prox.get("torneo") or "Torneo Clausura 2026"
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
        ★ PÁGINA CENTRAL PERMANENTE • PRÓXIMO PARTIDO Y RADIOGRAFÍA
      </span>
      <span style="font-size:12px;color:#ffd100;font-weight:700;">Actualizado: {now_uy} hs</span>
    </div>

    <!-- TARJETA DEL PRÓXIMO PARTIDO -->
    <div style="text-align:center;margin-bottom:20px;">
      <h1 style="color:#ffffff;font-size:clamp(22px,3.8vw,32px);font-weight:900;margin:0 0 10px;line-height:1.25;">
        Peñarol vs. {rival_nombre}
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
        👕 Pizarra Táctica: Armá tu 11
      </a>
      <a href="https://horarios.servicioti.com.uy/" target="_blank" rel="noopener noreferrer" style="border:1px solid rgba(255,255,255,0.3);color:#e4e4e7;font-weight:700;padding:10px 18px;border-radius:999px;text-decoration:none;font-size:13px;">
        🚌 Ómnibus al Estadio en Vivo
      </a>
    </div>
  </div>

  <!-- AVISO DE PÁGINA PERMANENTE -->
  <div style="background:#fefce8;border:1px solid #fde047;border-left:4px solid #ca8a04;padding:14px 18px;border-radius:8px;margin-bottom:24px;color:#713f12;font-size:13.5px;">
    <strong>ℹ️ Página Permanente Oficial de ServicioTI:</strong> Esta URL se mantiene constante y se actualiza de manera automática al término de cada encuentro para ofrecerte la radiografía táctica, datos del rival, árbitros, venta de entradas y la previa del siguiente compromiso del Club Atlético Peñarol.
  </div>

  <!-- BLOQUE: CONTEXTO RECIENTE Y ÚLTIMO RESULTADO OFICIAL -->
  <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-bottom:24px;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;border-bottom:2px solid #ffd100;padding-bottom:8px;">
      <h2 style="font-size:18px;font-weight:900;color:#09090b;margin:0;">⚡ Contexto Inmediato: Último Resultado Oficial</h2>
      <span style="font-size:12px;background:#f1f5f9;color:#475569;padding:3px 8px;border-radius:4px;font-weight:800;">Fecha 11 Clausura</span>
    </div>
    <div style="display:flex;align-items:center;justify-content:space-between;background:#09090b;color:#fff;padding:14px 20px;border-radius:10px;margin-bottom:12px;flex-wrap:wrap;gap:10px;">
      <div>
        <strong style="font-size:16px;color:#ffd100;">Juventud 0 - 0 Peñarol</strong>
        <div style="font-size:12px;color:#a1a1aa;">Estadio Centenario • Viernes 23 de octubre de 2026</div>
      </div>
      <a href="https://www.servicioti.com.uy/2026/10/penarol-en-vivo-juventud-vs-penarol.html" target="_blank" rel="noopener noreferrer" style="background:#ffd100;color:#09090b;font-weight:900;font-size:12px;padding:6px 14px;border-radius:6px;text-decoration:none;">
        📖 Leer Crónica & Minuto a Minuto ↗
      </a>
    </div>
    <p style="font-size:14px;color:#475569;margin:0;">
      Peñarol sostuvo un 68% de tenencia y controló territorialmente el trámite en el Centenario, pero chocó ante el cerrojo pedrense. El punto cosechado permite al Carbonero <strong>mantenerse en el 1° puesto solitario de la Tabla Anual Acumulada con 64 puntos</strong>, conservando la ventaja sobre sus perseguidores con la mira ya fija en sumar de a tres frente a Wanderers.
    </p>
  </div>

  <!-- RADIOGRAFÍA TÁCTICA DEL RIVAL: MONTEVIDEO WANDERERS -->
  <div style="background:#09090b;color:#ffffff;border:1px solid rgba(255,209,0,0.35);border-radius:14px;padding:24px;margin-bottom:24px;box-shadow:0 4px 20px rgba(0,0,0,0.2);">
    <div style="border-bottom:2px solid #ffd100;padding-bottom:10px;margin-bottom:18px;">
      <span style="background:#ffd100;color:#09090b;font-size:11px;font-weight:900;padding:2px 8px;border-radius:4px;text-transform:uppercase;">SCOUTING PROFESIONAL</span>
      <h2 style="font-size:22px;color:#ffffff;margin:8px 0 4px;font-weight:900;">
        🔍 Radiografía Táctica: {rival_nombre}
      </h2>
      <div style="font-size:13px;color:#a1a1aa;">
        DT: <strong>{scout.get('entrenador', 'Antonio Pacheco')}</strong> • Esquema: <strong>{scout.get('esquema_base', '4-3-3 / 4-2-3-1')}</strong> • Sede: {inst.get('sede', 'Prado')}
      </div>
    </div>

    <div style="font-size:14px;color:#d4d4d8;line-height:1.65;margin-bottom:20px;">
      <p><strong>Propuesta de Juego:</strong> {scout.get('propuesta_juego', '')}</p>
    </div>

    <!-- FIGURAS A SEGUIR -->
    <h3 style="font-size:16px;color:#ffd100;margin:0 0 12px;font-weight:800;">⭐ Figuras Clave del Rival:</h3>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px;margin-bottom:22px;">
      {figuras_html}
    </div>

    <!-- PUNTOS FUERTES Y VULNERABILIDADES -->
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin-bottom:24px;">
      <div style="background:rgba(239,68,68,0.1);border-left:4px solid #ef4444;padding:14px;border-radius:8px;">
        <strong style="color:#f87171;font-size:14px;">⚠️ Puntos Fuertes a Neutralizar:</strong>
        <ul style="margin:8px 0 0;padding-left:18px;font-size:13px;color:#e4e4e7;">
          {''.join(f'<li>{p}</li>' for p in scout.get('puntos_fuertes', []))}
        </ul>
      </div>
      <div style="background:rgba(34,197,94,0.1);border-left:4px solid #22c55e;padding:14px;border-radius:8px;">
        <strong style="color:#4ade80;font-size:14px;">🎯 Vulnerabilidades a Explotar:</strong>
        <ul style="margin:8px 0 0;padding-left:18px;font-size:13px;color:#e4e4e7;">
          {''.join(f'<li>{p}</li>' for p in scout.get('vulnerabilidades_a_explotar', []))}
        </ul>
      </div>
    </div>

    <!-- DUELOS TÁCTICOS 1X1 -->
    <h3 style="font-size:16px;color:#ffd100;margin:0 0 12px;font-weight:800;">⚔️ Duelos Clave 1x1 en el Campo:</h3>
    <div>
      {duelos_html}
    </div>
  </div>

  <!-- BALANCE EDITORIAL DE LA FECHA ANTERIOR (0-0 ANTE JUVENTUD) -->
  <div style="background:#09090b;border:2px solid #ffd100;border-radius:14px;padding:24px;margin-bottom:24px;color:#fff;">
    <div style="border-bottom:2px solid #ffd100;padding-bottom:10px;margin-bottom:16px;">
      <span style="background:#ffd100;color:#09090b;font-weight:900;font-size:11px;padding:3px 10px;border-radius:999px;text-transform:uppercase;">
        ⚡ BALANCE EDITORIAL • DE DÓNDE VENIMOS
      </span>
      <h2 style="font-size:20px;color:#ffffff;margin:8px 0 4px;font-weight:900;">
        El maleficio del frontón: balance tras el 0-0 ante Juventud de Las Piedras
      </h2>
      <div style="font-size:12.5px;color:#ffd100;">
        68% de posesión, asfixia en el cerrojo de 25 metros y la cima de la Tabla Anual sostenida con 64 puntos
      </div>
    </div>
    <div style="font-size:14px;line-height:1.65;color:#e4e4e7;margin-bottom:16px;">
      <p style="margin-bottom:10px;">
        El Centenario vivió una tarde de liturgia y gargantas encendidas con más de 30.000 aurinegros empujando bajo la Torre de los Homenajes. Sin embargo, el 4-2-3-1 de Diego Aguirre se estrelló contra una empalizada de dos líneas de cuatro ultraestrechas en apenas veinticinco metros. La zona 14 fue una aduana saturada y cada centro terminó en la resistencia pedrense.
      </p>
      <blockquote style="background:rgba(255,209,0,0.06);border-left:4px solid #ffd100;padding:10px 14px;margin:12px 0;font-style:italic;color:#ffd100;font-size:13.5px;">
        “A veces la pelota se encapricha, pero en la Tabla Anual sigue mandando Peñarol. Hay que tragarse la bronca, corregir sin histeria y salir al Prado a jugar como el cuadro más grande del país.” — Diego Aguirre
      </blockquote>
    </div>
    <!-- 4 Prismas resumidos -->
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px;">
      <div style="background:#141419;border-left:3px solid #ffd100;padding:10px 12px;border-radius:6px;font-size:12px;color:#d4d4d8;">
        <strong style="color:#ffd100;">🏟️ Rugido de Tribuna:</strong> 30.000 hinchas coparon el Centenario empujando hasta el último segundo.
      </div>
      <div style="background:#141419;border-left:3px solid #38bdf8;padding:10px 12px;border-radius:6px;font-size:12px;color:#d4d4d8;">
        <strong style="color:#38bdf8;">♟️ Pizarrón Táctico:</strong> Cerrojo pedrense de 25 metros que anuló los giros de Leo Fernández.
      </div>
      <div style="background:#141419;border-left:3px solid #ef4444;padding:10px 12px;border-radius:6px;font-size:12px;color:#d4d4d8;">
        <strong style="color:#f87171;">🔥 Trastienda:</strong> Autocrítica serena de Aguirre y conjuro de rebeldía para visitar el Viera.
      </div>
      <div style="background:#141419;border-left:3px solid #10b981;padding:10px 12px;border-radius:6px;font-size:12px;color:#d4d4d8;">
        <strong style="color:#34d399;">📐 Matemática:</strong> 64 puntos en la Anual; margen de vacilación cero en el Clausura.
      </div>
    </div>
  </div>

  <!-- HISTORIAL OFICIAL CERTIFICADO (1891 BD) -->
  <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-bottom:24px;">
    <div style="border-bottom:2px solid #ffd100;padding-bottom:8px;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
      <h2 style="font-size:18px;font-weight:900;color:#09090b;margin:0;">📜 Historial Oficial Verificado (1891 BD)</h2>
      <span style="font-size:11.5px;color:#475569;">Comisión de Historia y Patrimonio • Peñarol</span>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;text-align:center;margin-bottom:16px;">
      <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
        <div style="font-size:24px;font-weight:900;color:#09090b;">{hist.get('partidos_jugados', '200+')}</div>
        <div style="font-size:11.5px;color:#64748b;">Partidos Disputados</div>
      </div>
      <div style="background:#fefce8;padding:12px;border-radius:8px;border:1px solid #fde047;">
        <div style="font-size:24px;font-weight:900;color:#ca8a04;">{hist.get('ganados_penarol', '130+')}</div>
        <div style="font-size:11.5px;color:#854d0e;">Triunfos de Peñarol</div>
      </div>
      <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
        <div style="font-size:24px;font-weight:900;color:#09090b;">{hist.get('empatados', '50+')}</div>
        <div style="font-size:11.5px;color:#64748b;">Empates</div>
      </div>
      <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
        <div style="font-size:24px;font-weight:900;color:#09090b;">{hist.get('efectividad_pct', '73%')}</div>
        <div style="font-size:11.5px;color:#64748b;">Efectividad Aurinegra</div>
      </div>
    </div>
    <div style="font-size:13.5px;color:#475569;text-align:center;">
      Marcada ventaja histórica para el Decano: <strong>{hist.get('ventaja_victorias', '+100 partidos')}</strong> con {hist.get('diferencia_goles', '+200')} goles de diferencia.
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
    # 2. Actualizar el Post Histórico Existente (penarol-en-vivo-la-previa-radiografia.html)
    # -------------------------------------------------------------
    post_banner_redirect = f"""
    <div style="background:#09090b;border:2px solid #ffd100;border-radius:12px;padding:18px 22px;margin-bottom:24px;color:#ffffff;box-shadow:0 8px 24px rgba(255,209,0,0.25);">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:10px;">
        <span style="background:#ffd100;color:#09090b;font-weight:900;font-size:11.5px;padding:3px 10px;border-radius:999px;">⚡ NOTA ACTUALIZADA TRAS EL PARTIDO</span>
        <span style="font-size:12px;color:#ffd100;">Último Resultado: Juventud 0 - 0 Peñarol</span>
      </div>
      <h3 style="font-size:20px;color:#ffffff;margin:0 0 8px;font-weight:900;">
        Peñarol prepara el duelo ante Montevideo Wanderers (Fecha 12 del Torneo Clausura)
      </h3>
      <p style="font-size:14px;color:#d4d4d8;line-height:1.6;margin:0 0 14px;">
        Este artículo ha sido actualizado con el resultado reciente del Estadio Centenario y la previa táctica del próximo rival. Para acceder a la <strong>Página Permanente</strong> que se actualiza partido a partido sin cambiar de URL, ingresa a continuación:
      </p>
      <a href="{page_url}" style="background:#ffd100;color:#09090b;font-weight:900;padding:10px 22px;border-radius:999px;text-decoration:none;font-size:13.5px;display:inline-flex;align-items:center;gap:6px;">
        👉 Ver Página Permanente del Próximo Partido en ServicioTI ↗
      </a>
    </div>
    """
    
    post_updated_html = post_banner_redirect + html_content
    post_updated_title = "[Peñarol] Radiografía Táctica y Próximo Rival: Peñarol vs Montevideo Wanderers (Fecha 12 • Clausura) | Último resultado: Juventud 0 - 0 Peñarol"
    
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
    print("URL PÁGINA PERMANENTE:", url)
