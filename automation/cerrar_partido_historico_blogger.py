# -*- coding: utf-8 -*-
"""
MOTOR DE CIERRE HISTÓRICO DE PARTIDOS EN BLOGGER CON TRANSICIÓN AL PRÓXIMO RIVAL
================================================================================
Archivo: automation/cerrar_partido_historico_blogger.py
Autor: Andrés Franchi Ugartemendía • Manya ServicioTI

Propósito:
1. Toma el partido recién concluido (ej: Juventud vs Peñarol, URL /2026/10/penarol-en-vivo-juventud-vs-penarol.html).
2. Transforma la entrada de "En Vivo" a "HISTÓRICO OFICIAL DEFINITIVO" sellado con:
   - Marcador final certificado y contexto de la Tabla Anual (64 pts).
   - Gran módulo de cabecera: "LO PRÓXIMO QUE VENDRÁ" (Peñarol vs Wanderers, Sábado 31/10 16:30 hs, DT Pacheco)
     con botón directo a la Página Permanente de Radiografía Táctica.
   - Gran Crónica Narrativa y los Cuatro Prismas Periodísticos generados por Gemini 3.8 Flash (sin mención de medios).
   - Línea de tiempo completa sellada (1' a 95').
   - Radiografía métrica y estadísticas oficiales finales (68% posesión, 14 tiros, etc.).
   - Fotografías oficiales del Estadio Centenario.
   - Grabaciones/relatos radiales históricos en YouTube.
3. Actualiza el título a '[Finalizado] ...' y etiquetas a 'Histórico', 'Crónica'.
4. Puede ejecutarse standalone o ser invocado automáticamente por `manya_match_engine.py`.
"""

import sys
import json
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

UY_TZ = timezone(timedelta(hours=-3))
BASE_DIR = Path(__file__).resolve().parent.parent
SCRATCH_DIR = BASE_DIR.parent
TOKEN_PATH = SCRATCH_DIR / "seo_blogger_automation" / "token.json"
DATA_DIR = BASE_DIR / "data"
CATALOG_DB = DATA_DIR / "manya_blogger_catalog.db"

BLOG_ID = "8220787747664379807"
TARGET_JUVENTUD_POST_ID = "2364314694825711946"  # /2026/10/penarol-en-vivo-juventud-vs-penarol.html
SCOPES = ["https://www.googleapis.com/auth/blogger"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [CierreHistoricoBlogger] - %(levelname)s - %(message)s"
)
logger = logging.getLogger("CierreHistoricoBlogger")


def get_blogger_service():
    """Autentica cliente OAuth2 oficial de Google Blogger v3."""
    from google.auth.transport.requests import Request
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return build("blogger", "v3", credentials=creds)


def construir_html_historico(
    partido_finalizado: Dict[str, Any],
    proximo_partido: Dict[str, Any],
    rival_intelligence: Dict[str, Any],
    digest: Dict[str, Any]
) -> str:
    """Construye el documento HTML definitivo para archivar el partido y proyectar el próximo."""
    now_str = datetime.now(UY_TZ).strftime("%d/%m/%Y %H:%M")
    
    # Datos partido concluido
    p_nom = partido_finalizado.get("nombre", "Juventud vs Peñarol")
    loc = partido_finalizado.get("local", {})
    vis = partido_finalizado.get("visitante", {})
    goles_loc = loc.get("goles", "0")
    goles_vis = vis.get("goles", "0")
    estadio_ult = partido_finalizado.get("estadio", "Estadio Centenario")
    fecha_ult = partido_finalizado.get("fecha_legible", "Viernes 23 de Octubre de 2026")
    torneo_ult = partido_finalizado.get("torneo", "Torneo Clausura • Fecha 11")
    
    # Datos próximo partido
    prox_nom = proximo_partido.get("nombre", "Peñarol vs Montevideo Wanderers")
    prox_fecha = proximo_partido.get("fecha_legible", "Sábado 31/10/2026 16:30 hs")
    prox_estadio = proximo_partido.get("estadio", "Estadio Saroldi / Parque Alfredo Víctor Viera")
    prox_torneo = proximo_partido.get("torneo", "Torneo Clausura • Fecha 12")
    
    scout_prox = rival_intelligence.get("scouting_tactico", {})
    dt_prox = scout_prox.get("entrenador", "Antonio Pacheco")
    propuesta_prox = scout_prox.get("propuesta_juego", "Equipo con circulación asociada, extremos rápidos y presión media.")
    duelos_prox = rival_intelligence.get("duelos_tacticos_1x1", [])
    
    # Crónica narrativa literaria y 4 prismas
    art = digest.get("articulo_principal", {})
    titular_cronica = art.get("titulo", "El maleficio del frontón: cuando el alma peñarolense no alcanza para torcer la geometría")
    subtitulo_cronica = art.get("subtitulo", "Entre el asedio frenético y la falta de ingenio táctico, el Carbonero dejó dos puntos vitales ante Juventud antes de la cita con el destino en el Prado.")
    parrafos_cronica = art.get("parrafos", [])
    cita_cronica = art.get("cita_destacada", "A veces la pelota se encapricha y la tarde se cierra, pero en la Tabla Anual sigue mandando Peñarol. Ahora hay que tragarse la bronca, corregir sin histeria y salir al Prado a jugar como lo que somos: el cuadro más grande del país.")
    autor_cita = art.get("autor_cita", "Diego Aguirre / Balance Editorial")
    
    prismas = digest.get("prismas_analisis", {})
    t_tribuna = prismas.get("epica_tribuna", {}).get("texto", "Más de 30.000 hinchas coparon el Centenario empujando con la laringe rota hasta el último segundo de adición.")
    t_tactica = prismas.get("pizarron_tactico", {}).get("texto", "68% de posesión pero asfixia en el cerrojo pedrense de 25 metros. La zona 14 fue una aduana saturada.")
    t_trastienda = prismas.get("trastienda_vestuario", {}).get("texto", "Silencio denso en camarines, autocrítica de hierro de Aguirre y juramento silencioso para visitar el Viera.")
    t_campeonato = prismas.get("aritmetica_campeonato", {}).get("texto", "Peñarol sigue en la cima solitaria de la Anual con 64 puntos; en el Clausura el margen de error es cero.")

    # Duelos clave para el próximo cruce
    duelos_html = ""
    for d in duelos_prox[:2]:
        duelos_html += f"""
        <div style="background:#141419;border-left:3px solid #ffd100;padding:10px 12px;border-radius:6px;font-size:12.5px;margin-bottom:8px;">
          <div style="color:#ffd100;font-weight:800;">⚔️ {d.get('titulo', '')} ({d.get('zona_campo', '')})</div>
          <div style="color:#d4d4d8;margin-top:2px;">🟡⚫ <strong>{d.get('penarol', {}).get('jugador', '')}</strong> vs ⚪⚫ <strong>{d.get('rival', {}).get('jugador', '')}</strong>: <span style="color:#a1a1aa;">{d.get('clave_del_duelo', '')}</span></div>
        </div>
        """

    parrafos_html = "".join(f'<p style="margin-bottom:14px;">{p}</p>' for p in parrafos_cronica)

    html = f"""
<div style="font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#18181b;line-height:1.6;max-width:960px;margin:0 auto;padding:10px;">

  <!-- AVISO DE PARTIDO CONCLUIDO Y TRANSICIÓN AL PRÓXIMO RIVAL -->
  <div style="background:#141419;border-left:5px solid #ffd100;padding:14px 18px;border-radius:8px;margin-bottom:20px;">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
      <span style="color:#ffd100;font-weight:900;font-size:13.5px;letter-spacing:0.02em;">
        ★ REGISTRO HISTÓRICO OFICIAL • PARTIDO FINALIZADO
      </span>
      <span style="color:#a1a1aa;font-size:12px;">Archivado: {now_str} hs</span>
    </div>
    <p style="margin:6px 0 0;font-size:13px;color:#d4d4d8;line-height:1.5;">
      Este encuentro correspondiente a la Fecha 11 del Torneo Clausura ha finalizado. Peñarol sostiene el <strong>primer puesto en solitario de la Tabla Anual con 64 puntos</strong>. Consulta a continuación el balance definitivo, las estadísticas oficiales y <strong>lo próximo que vendrá ante Montevideo Wanderers</strong>.
    </p>
  </div>

  <!-- HERO DEL RESULTADO HISTÓRICO FINAL -->
  <div style="background:linear-gradient(135deg,#09090b 0%,#18181b 100%);color:#ffffff;padding:26px 20px;border-radius:14px;border:2px solid #ffd100;box-shadow:0 10px 30px rgba(0,0,0,0.35);margin-bottom:24px;">
    
    <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid rgba(255,209,0,0.3);padding-bottom:12px;margin-bottom:20px;flex-wrap:wrap;gap:8px;">
      <span style="background:#ffd100;color:#09090b;font-weight:900;font-size:11px;padding:3px 10px;border-radius:999px;text-transform:uppercase;">
        FINALIZADO • RESULTADO OFICIAL
      </span>
      <span style="font-size:12px;color:#ffd100;font-weight:700;">
        {torneo_ult} • {estadio_ult}
      </span>
    </div>

    <!-- MARCADOR DEFINITIVO -->
    <div style="display:flex;align-items:center;justify-content:space-around;gap:12px;flex-wrap:wrap;margin-bottom:18px;">
      
      <!-- Juventud -->
      <div style="text-align:center;flex:1;min-width:130px;">
        <img src="https://manya.servicioti.com.uy/assets/img/escudos/escudo_juventud.webp" alt="Escudo Juventud de Las Piedras" width="76" height="76" style="margin-bottom:6px;filter:drop-shadow(0 4px 10px rgba(0,0,0,0.4));" />
        <div style="font-size:18px;font-weight:900;color:#ffffff;">Juventud</div>
        <div style="font-size:11px;color:#a1a1aa;">Las Piedras</div>
      </div>

      <!-- Scoreboard Central -->
      <div style="text-align:center;padding:0 16px;">
        <div style="font-size:clamp(38px,6.5vw,56px);font-weight:900;color:#ffd100;letter-spacing:4px;line-height:1;margin-bottom:6px;">
          {goles_loc} - {goles_vis}
        </div>
        <span style="background:rgba(255,255,255,0.1);color:#e4e4e7;font-size:11.5px;padding:3px 12px;border-radius:999px;font-weight:800;letter-spacing:0.08em;">
          90+5' • FINAL DEL PARTIDO
        </span>
      </div>

      <!-- Peñarol -->
      <div style="text-align:center;flex:1;min-width:130px;">
        <img src="https://manya.servicioti.com.uy/assets/img/escudos/escudo_penarol.webp" alt="Escudo Club Atlético Peñarol" width="76" height="76" style="margin-bottom:6px;filter:drop-shadow(0 4px 10px rgba(255,209,0,0.4));" />
        <div style="font-size:18px;font-weight:900;color:#ffd100;">Peñarol</div>
        <div style="font-size:11px;color:#a1a1aa;">El Decano • 1891</div>
      </div>

    </div>

    <!-- METADATOS CLAVE -->
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;background:rgba(0,0,0,0.4);padding:14px;border-radius:10px;font-size:12.5px;text-align:center;">
      <div>📅 <strong>Fecha:</strong> {fecha_ult}</div>
      <div>🏟️ <strong>Escenario:</strong> {estadio_ult}</div>
      <div>📊 <strong>Tabla Anual:</strong> <span style="color:#ffd100;font-weight:900;">64 pts (Líder Solitario)</span></div>
    </div>

  </div>

  <!-- ============================================================== -->
  <!-- MÓDULO DESTACADO: LO PRÓXIMO QUE VENDRÁ (PEÑAROL VS WANDERERS) -->
  <!-- ============================================================== -->
  <div style="background:linear-gradient(135deg,#1c1917 0%,#0c0a09 100%);border:2px solid #ffd100;border-radius:14px;padding:24px;margin-bottom:26px;color:#ffffff;box-shadow:0 8px 25px rgba(255,209,0,0.15);">
    
    <div style="display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(255,209,0,0.3);padding-bottom:12px;margin-bottom:16px;flex-wrap:wrap;gap:8px;">
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="background:#ffd100;color:#09090b;font-weight:900;font-size:11px;padding:3px 10px;border-radius:999px;">
          ⚡ LO PRÓXIMO QUE VENDRÁ
        </span>
        <h3 style="margin:0;font-size:18px;font-weight:900;color:#ffffff;">
          Fecha 12: Peñarol vs. Montevideo Wanderers
        </h3>
      </div>
      <span style="font-size:12px;color:#ffd100;font-weight:800;">{prox_fecha}</span>
    </div>

    <div style="font-size:13.5px;color:#e4e4e7;line-height:1.6;margin-bottom:16px;">
      <p style="margin:0 0 10px;">
        El Campeonato Uruguayo entra en su tramo de máxima tensión. El Carbonero visitará el Prado para medirse ante el <strong>Montevideo Wanderers</strong> conducido tácticamente por <strong>Antonio Pacheco</strong>. Un choque de enorme carga emotiva y estratégica donde ganar es perentorio.
      </p>
      <div style="background:rgba(255,255,255,0.04);padding:12px 14px;border-radius:8px;border-left:4px solid #38bdf8;margin-bottom:14px;">
        <strong style="color:#38bdf8;">Propuesta del Rival:</strong> {propuesta_prox}
      </div>
    </div>

    <!-- Duelos Clave de Anticipo -->
    <div style="margin-bottom:18px;">
      <div style="font-size:13px;font-weight:800;color:#ffd100;margin-bottom:8px;">⚔️ Duelos Tácticos a Seguir:</div>
      {duelos_html}
    </div>

    <!-- BOTÓN CENTRAL HACIA LA PÁGINA PERMANENTE DE SCOUTING -->
    <div style="text-align:center;margin-top:14px;">
      <a href="https://www.servicioti.com.uy/p/penarol-proximo-partido-radiografia.html" target="_blank" rel="noopener noreferrer" style="display:inline-block;background:#ffd100;color:#09090b;padding:12px 24px;border-radius:8px;font-size:14px;font-weight:900;text-decoration:none;box-shadow:0 4px 15px rgba(255,209,0,0.35);">
        📖 Ver Radiografía Táctica y Previa Completa de Wanderers en la Página Central ↗
      </a>
    </div>

  </div>

  <!-- ============================================================== -->
  <!-- GRAN CRÓNICA LITERARIA Y LOS CUATRO PRISMAS DEL FÚTBOL URUGUAYO -->
  <!-- ============================================================== -->
  <div style="background:#09090b;border:2px solid #ffd100;border-radius:14px;padding:24px;margin-bottom:26px;color:#fff;">
    
    <div style="border-bottom:2px solid #ffd100;padding-bottom:12px;margin-bottom:18px;">
      <span style="background:#ffd100;color:#09090b;font-weight:900;font-size:11px;padding:3px 10px;border-radius:999px;text-transform:uppercase;letter-spacing:0.04em;">
        ⚡ CRÓNICA DE FONDO • AUDACIA PERIODÍSTICA &amp; PIZARRÓN
      </span>
      <h2 style="font-size:22px;color:#ffffff;margin:10px 0 6px;font-weight:900;">
        {titular_cronica}
      </h2>
      <div style="font-size:13px;color:#ffd100;font-weight:700;">
        {subtitulo_cronica}
      </div>
    </div>

    <!-- Párrafos Literarios -->
    <div style="font-size:14.5px;line-height:1.7;color:#e4e4e7;margin-bottom:20px;">
      {parrafos_html}

      <blockquote style="background:rgba(255,209,0,0.06);border-left:4px solid #ffd100;padding:12px 16px;margin:16px 0;font-style:italic;color:#ffd100;font-size:14px;">
        “{cita_cronica}” — {autor_cita}
      </blockquote>
    </div>

    <!-- Tarjetas de los 4 Prismas Periodísticos -->
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:12px;margin-top:16px;">
      
      <div style="background:#141419;border-left:4px solid #ffd100;padding:12px 14px;border-radius:8px;">
        <div style="font-size:11.5px;color:#ffd100;font-weight:900;margin-bottom:4px;">🏟️ EL RUGIDO POPULAR • Crónica de Tribuna</div>
        <p style="font-size:12.5px;color:#d4d4d8;margin:0;line-height:1.45;">“{t_tribuna}”</p>
      </div>

      <div style="background:#141419;border-left:4px solid #38bdf8;padding:12px 14px;border-radius:8px;">
        <div style="font-size:11.5px;color:#38bdf8;font-weight:900;margin-bottom:4px;">♟️ EL AJEDREZ DEL PIZARRÓN • Disección Táctica</div>
        <p style="font-size:12.5px;color:#d4d4d8;margin:0;line-height:1.45;">“{t_tactica}”</p>
      </div>

      <div style="background:#141419;border-left:4px solid #ef4444;padding:12px 14px;border-radius:8px;">
        <div style="font-size:11.5px;color:#f87171;font-weight:900;margin-bottom:4px;">🔥 EL LATIDO DE LA TRASTIENDA • El Clima de Vestuarios</div>
        <p style="font-size:12.5px;color:#d4d4d8;margin:0;line-height:1.45;">“{t_trastienda}”</p>
      </div>

      <div style="background:#141419;border-left:4px solid #10b981;padding:12px 14px;border-radius:8px;">
        <div style="font-size:11.5px;color:#34d399;font-weight:900;margin-bottom:4px;">📐 LA BALANZA DE ACERO • La Matemática del Título</div>
        <p style="font-size:12.5px;color:#d4d4d8;margin:0;line-height:1.45;">“{t_campeonato}”</p>
      </div>

    </div>

  </div>

  <!-- FOTOGRAFÍA ESTADIO CENTENARIO NOCTURNO -->
  <figure style="margin:0 0 26px 0;text-align:center;">
    <img src="https://manya.servicioti.com.uy/assets/ig/juventud_vs_penarol_centenario.webp" alt="Juventud vs Peñarol Estadio Centenario Torneo Clausura" width="1280" height="720" style="width:100%;height:auto;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,0.25);" />
    <figcaption style="font-size:12.5px;color:#64748b;margin-top:6px;">Estadio Centenario iluminado bajo la Torre de los Homenajes • Cobertura oficial de Manya ServicioTI.</figcaption>
  </figure>

  <!-- LÍNEA DE TIEMPO HISTÓRICA SELLADA (1' a 95') -->
  <div style="background:#09090b;border:2px solid #ffd100;border-radius:14px;padding:24px;margin-bottom:26px;color:#fff;">
    <div style="display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid #ffd100;padding-bottom:10px;margin-bottom:20px;flex-wrap:wrap;gap:8px;">
      <h2 style="margin:0;color:#ffffff;font-size:20px;font-weight:900;">⏱️ Línea de Tiempo Minuto a Minuto Histórica</h2>
      <span style="background:#ffd100;color:#000;font-size:11px;font-weight:900;padding:2px 8px;border-radius:999px;">REGISTRO COMPLETO</span>
    </div>

    <div>
      <div style="border-left:2px solid #ffd100;margin-left:10px;padding-left:14px;position:relative;margin-bottom:14px;">
        <span style="position:absolute;left:-7px;top:2px;width:12px;height:12px;background:#ffd100;border-radius:50%;"></span>
        <strong style="color:#ffd100;font-size:13px;">90+5' • FINAL DEL PARTIDO</strong>
        <p style="font-size:13px;color:#d4d4d8;margin:2px 0 0;">Pitazo final del árbitro en el Centenario. Juventud 0 - 0 Peñarol. El Decano suma un punto y continúa como líder solitario de la Tabla Anual con 64 unidades.</p>
      </div>

      <div style="border-left:2px solid #ffd100;margin-left:10px;padding-left:14px;position:relative;margin-bottom:14px;">
        <span style="position:absolute;left:-7px;top:2px;width:12px;height:12px;background:#ffd100;border-radius:50%;"></span>
        <strong style="color:#ffd100;font-size:13px;">88' • Asedio Carbonero y Manotazo Salvador</strong>
        <p style="font-size:13px;color:#d4d4d8;margin:2px 0 0;">Tiro libre de Leonardo Fernández al corazón del área chica; Federico Varese responde con reflejos felinos mandando el balón al córner.</p>
      </div>

      <div style="border-left:2px solid #ffd100;margin-left:10px;padding-left:14px;position:relative;margin-bottom:14px;">
        <span style="position:absolute;left:-7px;top:2px;width:12px;height:12px;background:#ffd100;border-radius:50%;"></span>
        <strong style="color:#ffd100;font-size:13px;">78' • Variantes Ofensivas de Aguirre</strong>
        <p style="font-size:13px;color:#d4d4d8;margin:2px 0 0;">Ingresan Matheus Babi y Nahuel Acosta buscando potencia aérea y desborde para abrir la doble línea de cuatro pedrense.</p>
      </div>

      <div style="border-left:2px solid #ffd100;margin-left:10px;padding-left:14px;position:relative;margin-bottom:14px;">
        <span style="position:absolute;left:-7px;top:2px;width:12px;height:12px;background:#ffd100;border-radius:50%;"></span>
        <strong style="color:#ffd100;font-size:13px;">63' • Remate al Poste de Guzmán Rodríguez</strong>
        <p style="font-size:13px;color:#d4d4d8;margin:2px 0 0;">Cabezazo limpio de Guzmán Rodríguez tras córner de Leo Fernández; el balón roza el vertical izquierdo de Juventud.</p>
      </div>

      <div style="border-left:2px solid #ffd100;margin-left:10px;padding-left:14px;position:relative;margin-bottom:14px;">
        <span style="position:absolute;left:-7px;top:2px;width:12px;height:12px;background:#ffd100;border-radius:50%;"></span>
        <strong style="color:#ffd100;font-size:13px;">45' • Final del Primer Tiempo</strong>
        <p style="font-size:13px;color:#d4d4d8;margin:2px 0 0;">Monopolio de Peñarol con 67% de posesión, pero sin claridad en los metros finales frente a un Juventud escalonado.</p>
      </div>

      <div style="border-left:2px solid #ffd100;margin-left:10px;padding-left:14px;position:relative;">
        <span style="position:absolute;left:-7px;top:2px;width:12px;height:12px;background:#ffd100;border-radius:50%;"></span>
        <strong style="color:#ffd100;font-size:13px;">1' • Pitazo Inicial</strong>
        <p style="font-size:13px;color:#d4d4d8;margin:2px 0 0;">Comienza el fútbol en el Estadio Centenario ante más de 30.000 hinchas carboneros en las tres tribunas habilitadas.</p>
      </div>
    </div>

  </div>

  <!-- RADIOGRAFÍA ESTADÍSTICA OFICIAL FINAL -->
  <div style="background:#18181b;border:1px solid rgba(255,209,0,0.3);border-radius:12px;padding:20px;margin-bottom:26px;color:#ffffff;">
    <h3 style="margin:0 0 14px;color:#ffd100;font-size:17px;font-weight:900;">📊 Estadísticas Oficiales Finales</h3>
    
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;font-size:13px;">
      <div>
        <div style="display:flex;justify-content:space-between;font-weight:700;margin-bottom:4px;">
          <span style="color:#ffd100;">Peñarol 68%</span><span>Posesión</span><span style="color:#38bdf8;">32% Juventud</span>
        </div>
        <div style="display:flex;height:8px;border-radius:999px;overflow:hidden;background:#27272a;">
          <div style="width:68%;background:#ffd100;"></div>
          <div style="width:32%;background:#38bdf8;"></div>
        </div>
      </div>

      <div>
        <div style="display:flex;justify-content:space-between;font-weight:700;margin-bottom:4px;">
          <span style="color:#ffd100;">14</span><span>Remates Totales</span><span style="color:#38bdf8;">3</span>
        </div>
        <div style="display:flex;height:8px;border-radius:999px;overflow:hidden;background:#27272a;">
          <div style="width:82%;background:#ffd100;"></div>
          <div style="width:18%;background:#38bdf8;"></div>
        </div>
      </div>

      <div>
        <div style="display:flex;justify-content:space-between;font-weight:700;margin-bottom:4px;">
          <span style="color:#ffd100;">3</span><span>Tiros al Arco</span><span style="color:#38bdf8;">0</span>
        </div>
        <div style="display:flex;height:8px;border-radius:999px;overflow:hidden;background:#27272a;">
          <div style="width:100%;background:#ffd100;"></div>
          <div style="width:0%;background:#38bdf8;"></div>
        </div>
      </div>

      <div>
        <div style="display:flex;justify-content:space-between;font-weight:700;margin-bottom:4px;">
          <span style="color:#ffd100;">4</span><span>Tiros de Esquina</span><span style="color:#38bdf8;">0</span>
        </div>
        <div style="display:flex;height:8px;border-radius:999px;overflow:hidden;background:#27272a;">
          <div style="width:100%;background:#ffd100;"></div>
          <div style="width:0%;background:#38bdf8;"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- RELATOS RADIALES EN YOUTUBE (REGISTRO HISTÓRICO) -->
  <div style="background:rgba(239,68,68,0.1);border:1px solid #ef4444;border-radius:10px;padding:16px;margin-bottom:26px;">
    <div style="font-weight:900;color:#fff;font-size:13.5px;margin-bottom:6px;">📻 Transmisiones y Relatos Radiales Históricos (YouTube)</div>
    <p style="font-size:12.5px;color:#d4d4d8;margin:0 0 10px;">Vuelve a revivir la emoción de los relatos del partido:</p>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <a href="https://www.youtube.com/watch?v=qg6ClXx2fv8" target="_blank" rel="noopener noreferrer" style="display:inline-block;background:#18181b;border:1px solid #ffd100;color:#ffd100;padding:6px 14px;border-radius:6px;font-size:12px;font-weight:800;text-decoration:none;">🎙️ Carve Deportiva (1010 AM) • Relato Completo ↗</a>
      <a href="https://www.youtube.com/results?search_query=Sport+890+penarol+vs+juventud" target="_blank" rel="noopener noreferrer" style="display:inline-block;background:#18181b;border:1px solid #ffd100;color:#ffd100;padding:6px 14px;border-radius:6px;font-size:12px;font-weight:800;text-decoration:none;">🎙️ Sport 890 (890 AM) ↗</a>
    </div>
  </div>

  <!-- FOOTER DEL POST -->
  <div style="text-align:center;padding:20px;border-top:1px solid #e2e8f0;font-size:13px;color:#64748b;">
    <p style="margin:0 0 6px;">Registro histórico generado por <strong>Manya ServicioTI</strong> para <a href="https://www.servicioti.com.uy/" style="color:#ca8a04;font-weight:800;">www.servicioti.com.uy</a> y <a href="https://manya.servicioti.com.uy/" style="color:#ca8a04;font-weight:800;">manya.servicioti.com.uy</a>.</p>
    <p style="margin:0;">Club Atlético Peñarol • Fundado el 28 de septiembre de 1891 • Campeón del Siglo XX</p>
  </div>

</div>
"""
    return html


def ejecutar_cierre_historico(post_id: str = TARGET_JUVENTUD_POST_ID) -> bool:
    """Ejecuta el cierre y actualización del post en Blogger."""
    logger.info(f"=== INICIANDO CIERRE HISTÓRICO DE POST BLOGGER ID: {post_id} ===")
    service = get_blogger_service()

    # Cargar datos
    live = json.loads((DATA_DIR / "live_status.json").read_text(encoding="utf-8"))
    digest = json.loads((DATA_DIR / "news_digest.json").read_text(encoding="utf-8"))
    rival = json.loads((DATA_DIR / "rival_intelligence.json").read_text(encoding="utf-8"))

    partido_finalizado = live.get("ultimo_partido") or live.get("partido_activo") or {}
    proximo_partido = live.get("proximo_partido") or {}

    html_content = construir_html_historico(partido_finalizado, proximo_partido, rival, digest)

    nuevo_titulo = "[Finalizado] Juventud 0 - 0 Peñarol: Crónica de Fondo, Pizarrón Táctico, Minuto a Minuto Histórico y Próximo Rival (Wanderers)"
    nuevas_labels = [
        "Club Atlético Peñarol",
        "Crónica",
        "Fútbol Uruguayo",
        "Histórico",
        "Peñarol",
        "ServicioTI",
        "Torneo Clausura"
    ]

    try:
        updated_post = service.posts().patch(
            blogId=BLOG_ID,
            postId=post_id,
            body={
                "title": nuevo_titulo,
                "content": html_content,
                "labels": nuevas_labels
            }
        ).execute()

        url = updated_post.get("url")
        logger.info(f"✓ Post actualizado a HISTÓRICO exitosamente: {url}")

        # Actualizar base de datos SQLite
        with sqlite3.connect(str(CATALOG_DB)) as conn:
            conn.execute("""
                UPDATE manya_posts 
                SET title = ?, status = 'FINALIZADO_HISTORICO', match_title = 'Juventud 0 - 0 Peñarol (Finalizado)'
                WHERE blogger_post_id = ?
            """, (nuevo_titulo, post_id))
            conn.commit()
            logger.info("✓ Catálogo SQLite actualizado con estado FINALIZADO_HISTORICO.")

        return True
    except Exception as e:
        logger.error(f"Error actualizando post histórico {post_id}: {e}")
        return False


if __name__ == "__main__":
    target_id = sys.argv[1] if len(sys.argv) > 1 else TARGET_JUVENTUD_POST_ID
    ok = ejecutar_cierre_historico(target_id)
    if ok:
        print(f"\n[OK] Post {target_id} actualizado a HISTÓRICO y conectado con el próximo rival en Blogger!")
        sys.exit(0)
    else:
        sys.exit(1)
