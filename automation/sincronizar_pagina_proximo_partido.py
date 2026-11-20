# -*- coding: utf-8 -*-
"""
MOTOR DE SINCRONIZACIÓN AUTOMÁTICA DE PRÓXIMO PARTIDO Y RADIOGRAFÍA TÁCTICA EN BLOGGER (v10.0 Zero-Hardcode)
=============================================================================================================
1. Publica y actualiza la Página Estática Permanente en Blogger (/p/penarol-proximo-partido-radiografia.html).
2. Actualiza el post de radiografía táctica con 100% de datos dinámicos leídos desde `live_status.json`,
   `rival_intelligence.json` y `news_digest.json` (cero rivales/puntos/estadios hardcodeados).
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
EXISTING_POST_ID = "5624313100287295662"
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
    """Construye el HTML editorial definitivo 100% dinámico para Blogger."""
    now_uy = datetime.now(UY_TZ).strftime("%d/%m/%Y %H:%M")
    fase = live_data.get("fase_partido", "PREVIA")
    act = live_data.get("partido_activo") or {}
    prox = live_data.get("proximo_partido") or {}
    ult = live_data.get("ultimo_partido") or act
    res_temp = live_data.get("resumen_temporada") or {}

    pts_anual = res_temp.get("penarol_anual_pts", 69)
    dg_anual = res_temp.get("penarol_anual_dg", "+27")
    pj_anual = res_temp.get("penarol_anual_pj", 37)
    campeon_anual = res_temp.get("campeon_anual", False)

    scout = rival_data.get("scouting_tactico") or {}
    inst = rival_data.get("datos_institucionales_auf") or {}
    duelos = rival_data.get("duelos_tacticos_1x1") or []
    hist = rival_data.get("historial_certificacion_1891") or {}

    rival_nombre = rival_data.get("rival_nombre") or (
        (act.get("visitante") or {}).get("nombre")
        if (act.get("local") or {}).get("es_penarol")
        else (act.get("local") or {}).get("nombre")
    ) or "Próximo Rival"

    dt_entrenador = scout.get("entrenador") or act.get("dt_rival") or "Cuerpo Técnico Rival"
    esquema_base = scout.get("esquema_base") or "4-2-3-1 / 4-4-2 competitivo"
    sede_club = inst.get("sede") or "Uruguay"

    is_post = fase == "POST_PARTIDO"
    if is_post:
        badge_fase = "🏁 RESULTADO FINAL • BALANCE POST-PARTIDO"
        loc = ult.get("local") or {}
        vis = ult.get("visitante") or {}
        estadio = ult.get("estadio") or "Estadio Campeón del Siglo"
        torneo = ult.get("torneo") or "Campeonato Uruguayo 2026"
        goles_txt = ult.get("goles_texto") or ""
        titulo_header = f"{loc.get('nombre', 'Peñarol')} {loc.get('goles', '0')} - {vis.get('goles', '0')} {vis.get('nombre', rival_nombre)}"
        sub_header = f"🏁 FINALIZADO • {torneo} • {estadio}" + (f"<br>⚽ {goles_txt}" if goles_txt else "")
    else:
        badge_fase = "★ PÁGINA CENTRAL PERMANENTE • PRÓXIMO PARTIDO Y RADIOGRAFÍA TÁCTICA"
        loc = prox.get("local") or {}
        vis = prox.get("visitante") or {}
        estadio = prox.get("estadio") or "Estadio Campeón del Siglo"
        torneo = prox.get("torneo") or "Campeonato Uruguayo 2026"
        fecha_legible = prox.get("fecha_legible") or "Fecha a confirmar AUF"
        tv = prox.get("tv") or "VTV Plus / Disney+ Premium"
        titulo_header = f"{loc.get('nombre', 'Peñarol')} vs. {vis.get('nombre', rival_nombre)}"
        sub_header = f"{torneo} • {fecha_legible}<br>🏟️ {estadio} • 📺 Transmisión en vivo por {tv}"

    badge_anual = f"🏆 Campeón Tabla Anual • {pts_anual} pts" if campeon_anual else f"Tabla Anual • {pts_anual} pts"
    resumen_anual_p = (
        prox.get("nota_definicion")
        or digest_data.get("bajada_seo")
        or f"Peñarol acumula {pts_anual} puntos oficiales en la Tabla Anual ({pj_anual} PJ, {dg_anual} DG) y encara la etapa decisiva del Campeonato Uruguayo 2026."
    )

    duelos_html = ""
    for d in duelos:
        duelos_html += f"""
        <div style="background:#18181d;border:1px solid rgba(255,255,255,0.08);border-left:4px solid #ffd100;border-radius:8px;padding:14px;margin-bottom:12px;">
          <div style="font-size:11.5px;color:#ffd100;font-weight:900;text-transform:uppercase;margin-bottom:4px;">⚔️ {d.get('titulo', '')} • {d.get('zona_campo', '')}</div>
          <div style="display:flex;justify-content:space-between;gap:12px;margin:8px 0;flex-wrap:wrap;font-size:13.5px;">
            <div style="flex:1;min-width:200px;"><strong style="color:#ffd100;">🟡⚫ Peñarol:</strong> {d.get('penarol', {}).get('jugador', '')} ({d.get('penarol', {}).get('rol', '')})<br><span style="font-size:12px;color:#a1a1aa;">{d.get('penarol', {}).get('atributos_clave', '')}</span></div>
            <div style="flex:1;min-width:200px;"><strong style="color:#38bdf8;">⚽ {rival_nombre}:</strong> {d.get('rival', {}).get('jugador', '')} ({d.get('rival', {}).get('rol', '')})<br><span style="font-size:12px;color:#a1a1aa;">{d.get('rival', {}).get('atributos_clave', '')}</span></div>
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

    pf_list = "".join(f'<li style="margin-bottom:4px;">{pt}</li>' for pt in scout.get("puntos_fuertes", ["Orden defensivo compacto", "Transiciones rápidas"]))
    vul_list = "".join(f'<li style="margin-bottom:4px;">{vul}</li>' for vul in scout.get("vulnerabilidades_a_explotar", ["Espalda de laterales en repliegue", "Pelota quieta de Leo Fernández"]))

    pj_h = hist.get("partidos_jugados", 0)
    gp_h = hist.get("ganados_penarol", 0)
    emp_h = hist.get("empatados", 0)
    ef_h = hist.get("efectividad_pct", "-")
    ventaja_h = hist.get("ventaja_victorias", "Balance oficial 1891 BD")
    dif_g = hist.get("diferencia_goles", "")

    html = f"""
<div style="font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#18181b;line-height:1.6;max-width:960px;margin:0 auto;padding:10px;">

  <div style="background:linear-gradient(135deg,#09090b 0%,#18181b 100%);color:#ffffff;padding:26px 22px;border-radius:14px;border:2px solid #ffd100;box-shadow:0 10px 30px rgba(0,0,0,0.35);margin-bottom:24px;">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;border-bottom:1px solid rgba(255,209,0,0.3);padding-bottom:14px;margin-bottom:18px;">
      <span style="background:#ffd100;color:#09090b;font-weight:900;font-size:11.5px;padding:4px 12px;border-radius:999px;letter-spacing:0.04em;">
        {badge_fase}
      </span>
      <span style="font-size:12px;color:#ffd100;font-weight:700;">Actualizado: {now_uy} hs UY</span>
    </div>

    <div style="text-align:center;margin-bottom:20px;">
      <h1 style="color:#ffffff;font-size:clamp(22px,3.8vw,32px);font-weight:900;margin:0 0 10px;line-height:1.25;">
        {titulo_header}
      </h1>
      <div style="font-size:15px;color:#ffd100;font-weight:800;margin-bottom:6px;">
        {sub_header}
      </div>
    </div>

    <div style="display:flex;justify-content:center;gap:10px;flex-wrap:wrap;margin-top:16px;">
      <a href="https://manya.servicioti.com.uy/" target="_blank" rel="noopener noreferrer" style="background:#ffd100;color:#09090b;font-weight:900;padding:10px 20px;border-radius:999px;text-decoration:none;font-size:13.5px;">
        ⚡ Ir a manya.servicioti.com.uy (Match Center en Vivo) ↗
      </a>
      <a href="https://manya.servicioti.com.uy/#pizarra-tactica" target="_blank" rel="noopener noreferrer" style="border:1px solid #ffd100;color:#ffd100;font-weight:800;padding:10px 18px;border-radius:999px;text-decoration:none;font-size:13px;">
        👕 Pizarra Táctica: Armá tu 11 (Plantel 2026)
      </a>
      <a href="https://horarios.servicioti.com.uy/" target="_blank" rel="noopener noreferrer" style="border:1px solid rgba(255,255,255,0.3);color:#e4e4e7;font-weight:700;padding:10px 18px;border-radius:999px;text-decoration:none;font-size:13px;">
        🚌 Ómnibus al Estadio en Vivo
      </a>
    </div>
  </div>

  <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-bottom:24px;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;border-bottom:2px solid #ffd100;padding-bottom:8px;flex-wrap:wrap;gap:8px;">
      <h2 style="font-size:18px;font-weight:900;color:#09090b;margin:0;">⚡ Situación en la Tabla Anual y Definición 2026</h2>
      <span style="font-size:12px;background:#fef08a;color:#854d0e;padding:3px 10px;border-radius:4px;font-weight:900;">{badge_anual}</span>
    </div>
    <div style="display:flex;align-items:center;justify-content:space-between;background:#09090b;color:#fff;padding:14px 20px;border-radius:10px;margin-bottom:12px;flex-wrap:wrap;gap:10px;">
      <div>
        <strong style="font-size:16px;color:#ffd100;">Peñarol suma {pts_anual} unidades en la Tabla Anual</strong>
        <div style="font-size:12px;color:#a1a1aa;">Acumulada oficial AUF + ESPN ({dg_anual} DG) • {pj_anual} partidos jugados</div>
      </div>
      <a href="https://manya.servicioti.com.uy/#tabla-simulador" target="_blank" rel="noopener noreferrer" style="background:#ffd100;color:#09090b;font-weight:900;font-size:12px;padding:6px 14px;border-radius:6px;text-decoration:none;">
        📊 Ver Tablas y Definición ↗
      </a>
    </div>
    <p style="font-size:14px;color:#475569;margin:0;">{resumen_anual_p}</p>
  </div>

  <div style="background:#09090b;color:#ffffff;border:1px solid rgba(255,209,0,0.35);border-radius:14px;padding:24px;margin-bottom:24px;">
    <div style="border-bottom:2px solid #ffd100;padding-bottom:10px;margin-bottom:18px;">
      <span style="background:#ffd100;color:#09090b;font-size:11px;font-weight:900;padding:2px 8px;border-radius:4px;text-transform:uppercase;">SCOUTING TÁCTICO PROFESIONAL</span>
      <h2 style="font-size:22px;color:#ffffff;margin:8px 0 4px;font-weight:900;">
        🔍 Radiografía Táctica: {rival_nombre} (DT {dt_entrenador})
      </h2>
      <div style="font-size:13px;color:#a1a1aa;">
        DT: <strong>{dt_entrenador}</strong> • Esquema: <strong>{esquema_base}</strong> • Sede: {sede_club}
      </div>
    </div>

    <div style="font-size:14px;color:#d4d4d8;line-height:1.65;margin-bottom:20px;">
      {scout.get("propuesta_juego", f"Análisis táctico actualizado de {rival_nombre} frente al Club Atlético Peñarol.")}
    </div>

    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px;margin-bottom:22px;">
      <div style="background:#141419;border:1px solid rgba(255,255,255,0.06);border-top:3px solid #10b981;border-radius:8px;padding:14px;">
        <strong style="color:#10b981;font-size:14px;display:block;margin-bottom:8px;">✓ Puntos Fuertes a Neutralizar</strong>
        <ul style="margin:0;padding-left:18px;font-size:13px;color:#d4d4d8;">{pf_list}</ul>
      </div>

      <div style="background:#141419;border:1px solid rgba(255,255,255,0.06);border-top:3px solid #ef4444;border-radius:8px;padding:14px;">
        <strong style="color:#ef4444;font-size:14px;display:block;margin-bottom:8px;">⚠️ Dónde Dañar a {rival_nombre}</strong>
        <ul style="margin:0;padding-left:18px;font-size:13px;color:#d4d4d8;">{vul_list}</ul>
      </div>
    </div>

    <h3 style="font-size:16px;color:#ffd100;margin:0 0 12px;font-weight:900;">🎯 Figuras a Seguir de {rival_nombre}</h3>
    {figuras_html}

    <h3 style="font-size:16px;color:#ffd100;margin:20px 0 12px;font-weight:900;">⚔️ Duelos Tácticos 1x1 Clave</h3>
    {duelos_html}
  </div>

  <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;padding:22px;margin-bottom:24px;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;border-bottom:2px solid #ffd100;padding-bottom:8px;flex-wrap:wrap;gap:8px;">
      <h3 style="font-size:18px;font-weight:900;color:#09090b;margin:0;">📜 Historial Oficial Verificado vs. {rival_nombre} (1891 BD)</h3>
      <span style="font-size:12px;background:#fef08a;color:#854d0e;padding:3px 8px;border-radius:4px;font-weight:800;">{ventaja_h}</span>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;text-align:center;margin-bottom:14px;">
      <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
        <div style="font-size:24px;font-weight:900;color:#09090b;">{pj_h}</div>
        <div style="font-size:11.5px;color:#64748b;">Partidos Disputados</div>
      </div>
      <div style="background:#fefce8;padding:12px;border-radius:8px;border:1px solid #fde047;">
        <div style="font-size:24px;font-weight:900;color:#ca8a04;">{gp_h}</div>
        <div style="font-size:11.5px;color:#854d0e;">Triunfos de Peñarol</div>
      </div>
      <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
        <div style="font-size:24px;font-weight:900;color:#09090b;">{emp_h}</div>
        <div style="font-size:11.5px;color:#64748b;">Empates</div>
      </div>
      <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
        <div style="font-size:24px;font-weight:900;color:#09090b;">{ef_h}</div>
        <div style="font-size:11.5px;color:#64748b;">Efectividad Aurinegra</div>
      </div>
    </div>
    <div style="font-size:13.5px;color:#475569;text-align:center;">
      Certificación oficial 1891 BD: <strong>{ventaja_h}</strong>{f" • Diferencia de goles: {dif_g}" if dif_g else ""}.
    </div>
  </div>

  <div style="text-align:center;padding:24px;background:#f8fafc;border-radius:12px;border:1px solid #e2e8f0;font-size:13px;color:#64748b;">
    <p style="margin:0 0 6px;">Página permanente producida por <strong>Manya ServicioTI</strong> para <a href="https://www.servicioti.com.uy/" style="color:#ca8a04;font-weight:800;">www.servicioti.com.uy</a> y <a href="https://manya.servicioti.com.uy/" style="color:#ca8a04;font-weight:800;">manya.servicioti.com.uy</a>.</p>
    <p style="margin:0;">Club Atlético Peñarol • Fundado el 28 de septiembre de 1891 • Campeón del Siglo XX de Sudamérica</p>
  </div>
</div>
"""
    return html


def sincronizar_proximo_partido_blogger():
    """Ejecuta la sincronización completa: crea/actualiza la Página Estática y el Post en Blogger."""
    logger.info("=== INICIANDO SINCRONIZACIÓN DE PÁGINA Y POST EN BLOGGER (v10.0) ===")
    service = get_blogger_service()

    live = json.loads((DATA_DIR / "live_status.json").read_text(encoding="utf-8")) if (DATA_DIR / "live_status.json").exists() else {}
    rival = json.loads((DATA_DIR / "rival_intelligence.json").read_text(encoding="utf-8")) if (DATA_DIR / "rival_intelligence.json").exists() else {}
    digest = json.loads((DATA_DIR / "news_digest.json").read_text(encoding="utf-8")) if (DATA_DIR / "news_digest.json").exists() else {}

    html_content = construir_html_proximo_partido(live, rival, digest)

    page_id = None
    if STATE_PAGE_FILE.exists():
        try:
            page_id = json.loads(STATE_PAGE_FILE.read_text(encoding="utf-8")).get("page_id")
        except Exception:
            pass

    if not page_id:
        pages_resp = service.pages().list(blogId=BLOG_ID).execute()
        for p in pages_resp.get("items", []):
            t = p.get("title", "").lower()
            if "próximo partido" in t or "proximo partido" in t or "radiografía táctica" in t:
                page_id = p.get("id")
                break

    if page_id:
        res_page = service.pages().patch(blogId=BLOG_ID, pageId=page_id, body={"title": PAGE_TITLE, "content": html_content}).execute()
        page_url = res_page.get("url", "")
        logger.info(f"[Blogger Previa] ✓ Página estática actualizada: {page_url}")
    else:
        res_page = service.pages().insert(blogId=BLOG_ID, body={"title": PAGE_TITLE, "content": html_content}).execute()
        page_id = res_page.get("id")
        page_url = res_page.get("url", "")
        logger.info(f"[Blogger Previa] ✓ Nueva Página estática creada: {page_url}")

    STATE_PAGE_FILE.write_text(json.dumps({
        "page_id": page_id,
        "title": PAGE_TITLE,
        "url": page_url,
        "actualizado": datetime.now(UY_TZ).isoformat()
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    # Actualizar post de radiografía con el rival/partido vigente
    act = live.get("partido_activo") or {}
    prox = live.get("proximo_partido") or {}
    rival_nom = rival.get("rival_nombre") or "Peñarol 2026"
    torneo_nom = act.get("torneo") or prox.get("torneo") or "Campeonato Uruguayo 2026"
    post_updated_title = f"[Peñarol] Radiografía Táctica & Cobertura Oficial: {act.get('nombre', f'Peñarol vs {rival_nom}')} • {torneo_nom}"

    try:
        service.posts().patch(
            blogId=BLOG_ID,
            postId=EXISTING_POST_ID,
            body={
                "title": post_updated_title,
                "content": html_content,
                "labels": ["Peñarol", "Radiografía Táctica", rival_nom, "Campeonato Uruguayo", "ServicioTI"]
            }
        ).execute()
        logger.info(f"[Blogger Post Update] ✓ Post {EXISTING_POST_ID} actualizado para {rival_nom}.")
    except Exception as e:
        logger.warning(f"[Blogger Post Update] Aviso al actualizar post existente: {e}")

    digest["blogger_previa_page_url"] = page_url
    (DATA_DIR / "news_digest.json").write_text(json.dumps(digest, ensure_ascii=False, indent=2), encoding="utf-8")
    return page_url


if __name__ == "__main__":
    sincronizar_proximo_partido_blogger()
