# -*- coding: utf-8 -*-
"""
DAEMON Y ORQUESTADOR MAESTRO DE PARTIDOS Y PRENSA (manya_partidos_daemon.py)
=============================================================================
Coordina en tiempo real:
  1. Detección y ciclo de vida de partidos (PREVIA, EN VIVO, POST-PARTIDO).
  2. Recolección exhaustiva de prensa deportiva (Ovación, Referí, Tenfield, etc.).
  3. Redacción con Gemini Web (GFlash 3.8) y transformación visual con SEO Metadata.
  4. Publicación en Blogger API v3 bajo protocolo estricto anti-colisiones.
  5. Sincronización continua de datos en GitHub Pages (manya.servicioti.com.uy).

Modos de uso:
  python automation/manya_partidos_daemon.py --once
  python automation/manya_partidos_daemon.py --daemon
"""

import os
import sys
import time
import json
import asyncio
import logging
import argparse
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

logger = logging.getLogger("ManyaDaemon")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_IG_DIR = BASE_DIR / "assets" / "ig"
UY_TZ = timezone(timedelta(hours=-3))

from manya_anti_collision import CentralAutomationLock, ScheduleSafety, ManyaBloggerCatalog
from manya_sports_press import ManyaSportsPressService
from manya_match_engine import ManyaMatchEngine
from manya_gemini_web_engine import ManyaGeminiWebEngine
from manya_seo_metadata import ManyaSEOMetadataService
from blogger_manya_publisher import publish_manya_article_to_blogger


def git_commit_and_push(mensaje: str):
    """Sincroniza los cambios hacia GitHub Pages."""
    try:
        subprocess.run(["git", "add", "data/", "assets/", "index.html"], cwd=str(BASE_DIR), check=False)
        res = subprocess.run(["git", "commit", "-m", mensaje], cwd=str(BASE_DIR), capture_output=True, text=True)
        if "nothing to commit" not in res.stdout and "nothing to commit" not in res.stderr:
            subprocess.run(["git", "push", "origin", "main"], cwd=str(BASE_DIR), check=True, timeout=45)
            logger.info(f"[GitHub Pages] ✓ Cambios empujados a main: '{mensaje}'")
    except Exception as e:
        logger.warning(f"[GitHub Pages] Aviso al sincronizar git: {e}")


def ejecutar_ciclo_previa(match_info: dict, noticias_prensa: list):
    """Genera la cobertura de Previa Oficial si aún no se ha publicado hoy."""
    event_id = match_info.get("event_id", "")
    match_title = match_info.get("nombre", "Liverpool vs Peñarol")
    estadio = match_info.get("estadio", "Estadio de Primera División")
    tv = match_info.get("tv", "VTV Plus / Disney+")
    hora_str = match_info.get("fecha_legible", "")

    can_pub, motivo = ManyaBloggerCatalog.can_publish(post_type="PREVIA", match_id=event_id)
    if not can_pub:
        logger.info(f"[Previa] {motivo}. Saltando redacción de previa.")
        return

    logger.info(f"[Previa] ⚡ Generando La Previa Oficial: {match_title} ({hora_str})...")

    # Síntesis de noticias para el redactor
    resumenes_prensa = "\n".join([
        f"- [{n['fuente']}] {n['titulo']}: {n['resumen'][:180]}"
        for n in noticias_prensa[:10]
    ])

    prompt_redaccion = f"""
Actúa como el Jefe de Redacción y Periodista Experto de Peñarol para 'Manya ServicioTI'.
HOY JUEGA PEÑAROL: {match_title}.
Estadio: {estadio}.
Fecha y Hora: {hora_str}.
Televisación: {tv}.

Contexto reciente de periódicos uruguayos (Ovación, Referí, Tenfield, Padre y Decano):
{resumenes_prensa}

REGLAS EDITORIALES OBLIGATORIAS:
1. Responde ÚNICAMENTE en formato JSON plano válido (sin markdown ```json).
2. Tono: apasionado, respetuoso pero 100% aurinegro y profesional.
3. Estructura del JSON requerida:
{{
  "titular_dia": "Frase contundente sobre la previa del partido",
  "bajada_seo": "Resumen periodístico SEO con Peñarol, rival, estadio y cómo verlo.",
  "claves_60_segundos": [
    {{"icono": "⚽", "titulo": "Clave Táctica", "detalle": "Detalle del planteo de Diego Aguirre..."}},
    {{"icono": "🔥", "titulo": "La Figura a Seguir", "detalle": "Rendimiento esperado de Arezo / atacantes..."}},
    {{"icono": "📺", "titulo": "Transmisión y Horario", "detalle": "Hora oficial de Uruguay y canales VTV Plus / Disney+..."}},
    {{"icono": "📊", "titulo": "Puntos en Juego", "detalle": "Impacto directo en el Clausura y la Tabla Anual..."}}
  ],
  "articulo_principal": {{
    "titulo": "Título extenso de la previa",
    "subtitulo": "Subtítulo periodístico",
    "parrafos": [
      "Párrafo 1: El clima previo en Los Aromos y la concentración aurinegra...",
      "Párrafo 2: El rival de turno, su momento y cómo contrarrestar su juego...",
      "Párrafo 3: El once probable de Peñarol, retornos y variantes tácticas...",
      "Párrafo 4: La expectativa de los hinchas y el peso de sumar de a tres en la Tabla Anual..."
    ],
    "preguntas_frecuentes": [
      {{"q": "¿A qué hora juega Peñarol hoy y dónde verlo?", "a": "Peñarol juega a las {hora_str} en {estadio}, televisado por {tv}."}},
      {{"q": "¿Cómo formaría Peñarol?", "a": "Diego Aguirre perfila un esquema ofensivo con los futbolistas en mejor rodaje físico."}},
      {{"q": "¿Qué se juega Peñarol en este partido?", "a": "Puntos vitales para la punta de la Tabla Anual y la definición del Clausura."}}
    ]
  }}
}}
"""

    with CentralAutomationLock.acquire("gemini_web_profile", timeout_sec=120):
        res_json = ManyaGeminiWebEngine.generar_texto_gflash_38(prompt_redaccion)

    if res_json and "articulo_principal" in res_json:
        doc_digest = {
            "actualizado": datetime.now(UY_TZ).strftime("%d/%m/%Y %H:%M"),
            "modelo_ia": "Google Gemini Web (GFlash 3.8 Multimodal)",
            "fase_publicacion": "PREVIA",
            "partido_id": event_id,
            "titular_dia": res_json.get("titular_dia", f"La Previa: {match_title}"),
            "bajada_seo": res_json.get("bajada_seo", ""),
            "claves_60_segundos": res_json.get("claves_60_segundos", []),
            "articulo_principal": res_json.get("articulo_principal", {}),
            "noticias_fuentes": noticias_prensa[:8]
        }
        (DATA_DIR / "news_digest.json").write_text(json.dumps(doc_digest, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("[Previa] ✓ data/news_digest.json actualizado con la previa oficial.")

        # Publicar en Blogger
        post_url = publish_manya_article_to_blogger(post_type="PREVIA", match_id=event_id)
        git_commit_and_push(f"feat(previa): publicar previa {match_title} en vivo")


def ejecutar_ciclo_en_vivo(match_info: dict):
    """Actualización en tiempo real durante el partido (polling ESPN hacia manya.servicioti.com.uy)."""
    match_title = match_info.get("nombre", "")
    reloj = match_info.get("minuto_reloj", "")
    logger.info(f"[En Vivo] 🔴 Partido en juego: {match_title} | Reloj: {reloj}")
    ManyaMatchEngine.generate_updated_live_status()
    git_commit_and_push(f"live(partido): actualización en directo {match_title} ({reloj})")


def ejecutar_ciclo_cronica(match_info: dict, noticias_prensa: list):
    """Genera la crónica definitiva post-partido y la publica en Blogger."""
    event_id = match_info.get("event_id", "")
    match_title = match_info.get("nombre", "Partido de Peñarol")
    loc = match_info.get("local", {})
    vis = match_info.get("visitante", {})
    marcador = f"{loc.get('nombre')} {loc.get('goles')} - {vis.get('goles')} {vis.get('nombre')}"

    can_pub, motivo = ManyaBloggerCatalog.can_publish(post_type="CRONICA", match_id=event_id)
    if not can_pub:
        logger.info(f"[Crónica] {motivo}. Saltando redacción de crónica final.")
        return

    logger.info(f"[Crónica] 🏁 Generando Crónica Definitiva: {marcador}...")

    # Obtener detalles avanzados oficiales de ESPN
    adv = ManyaMatchEngine.fetch_match_summary_details(event_id)
    stats_raw = json.dumps(adv.get("estadisticas", {}), ensure_ascii=False)

    prompt_cronica = f"""
Actúa como el Jefe de Deportes y Cronista Oficial de Peñarol para 'Manya ServicioTI'.
EL PARTIDO HA FINALIZADO: {marcador}.
Estadio: {match_info.get('estadio')}.
Estadísticas oficiales del encuentro:
{stats_raw}

Titulares Peñarol: {', '.join(adv.get('titulares_penarol', []))}
Suplentes Peñarol: {', '.join(adv.get('suplentes_penarol', []))}

REGLAS EDITORIALES OBLIGATORIAS:
1. Responde ÚNICAMENTE en formato JSON plano válido (sin markdown ```json).
2. Tono: analítico, épico, deportivo y riguroso.
3. Estructura del JSON requerida:
{{
  "titular_dia": "Titular contundente con el resultado y lo demostrado en cancha",
  "bajada_seo": "Crónica y análisis del partido {marcador}, figuras, goles y tabla de posiciones.",
  "claves_60_segundos": [
    {{"icono": "⚽", "titulo": "Resultado Final", "detalle": "Desenlace y marcador final del encuentro..."}},
    {{"icono": "⭐", "titulo": "Figura del Partido", "detalle": "El jugador más influyente en el trámite..."}},
    {{"icono": "📊", "titulo": "Estadísticas Clave", "detalle": "Posesión, tiros al arco y solidez defensiva..."}},
    {{"icono": "🏆", "titulo": "Tabla de Posiciones", "detalle": "Cómo queda Peñarol en el torneo y la Anual..."}}
  ],
  "articulo_principal": {{
    "titulo": "Crónica: Análisis exhaustivo del partido",
    "subtitulo": "El balance del aurinegro tras el pitazo final",
    "parrafos": [
      "Párrafo 1: El arranque del juego, intensidad y propuesta en el primer tiempo...",
      "Párrafo 2: Los momentos determinantes, incidencias y resolución en las áreas...",
      "Párrafo 3: Las intervenciones tácticas del cuerpo técnico y rendimiento individual...",
      "Párrafo 4: Conclusiones hacia el próximo objetivo y el balance para la hinchada..."
    ],
    "preguntas_frecuentes": [
      {{"q": "¿Cómo terminó el partido de Peñarol?", "a": "El encuentro finalizó con marcador {marcador}."}},
      {{"q": "¿Cómo impacta este resultado en la Tabla Anual?", "a": "Peñarol consolida su posición en la vanguardia del fútbol uruguayo."}}
    ]
  }}
}}
"""

    with CentralAutomationLock.acquire("gemini_web_profile", timeout_sec=120):
        res_json = ManyaGeminiWebEngine.generar_texto_gflash_38(prompt_cronica)

    if res_json and "articulo_principal" in res_json:
        doc_digest = {
            "actualizado": datetime.now(UY_TZ).strftime("%d/%m/%Y %H:%M"),
            "modelo_ia": "Google Gemini Web (GFlash 3.8 Multimodal)",
            "fase_publicacion": "CRONICA",
            "partido_id": event_id,
            "titular_dia": res_json.get("titular_dia", f"Crónica: {marcador}"),
            "bajada_seo": res_json.get("bajada_seo", ""),
            "claves_60_segundos": res_json.get("claves_60_segundos", []),
            "articulo_principal": res_json.get("articulo_principal", {}),
            "noticias_fuentes": noticias_prensa[:8]
        }
        (DATA_DIR / "news_digest.json").write_text(json.dumps(doc_digest, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("[Crónica] ✓ data/news_digest.json actualizado con la crónica final.")

        # Publicar en Blogger
        post_url = publish_manya_article_to_blogger(post_type="CRONICA", match_id=event_id)
        git_commit_and_push(f"feat(cronica): publicar crónica oficial {marcador}")


def ejecutar_orquestador(modo: str = "once"):
    logger.info("=" * 70)
    logger.info(f"=== INICIANDO VIGILANTE DE PARTIDOS Y PRENSA MANYA (MODO: {modo}) ===")
    logger.info("=" * 70)

    while True:
        try:
            # 1. Actualizar estado y detectar partido
            status_live = ManyaMatchEngine.generate_updated_live_status()
            fase = status_live.get("fase_partido", "SIN_PARTIDO_HOY")
            match_info = status_live.get("partido_activo", {})

            # 1b. Sincronizar efemérides del día (1891 BD)
            try:
                from extraer_datos_1891 import extraer_efemerides_hoy
                extraer_efemerides_hoy()
            except Exception as ex_1891:
                logger.warning(f"[1891 BD] Aviso actualizando efemérides: {ex_1891}")

            # 1c. Sincronizar scouting táctico del rival (AUF + 1891 + Ovación)
            try:
                from manya_rival_intelligence import generar_informe_rival
                rival_equipo = match_info.get("visitante", {}) if match_info.get("local", {}).get("es_penarol") else match_info.get("local", {})
                generar_informe_rival(rival_equipo.get("nombre", "juventud"))
            except Exception as ex_scout:
                logger.warning(f"[Scout] Aviso generando scouting del rival: {ex_scout}")

            # 1c. Sincronizar scouting táctico del rival (AUF + 1891 + Ovación)
            try:
                from manya_rival_intelligence import generar_informe_rival
                rival_equipo = match_info.get("visitante", {}) if match_info.get("local", {}).get("es_penarol") else match_info.get("local", {})
                generar_informe_rival(rival_equipo.get("nombre", "juventud"))
            except Exception as ex_scout:
                logger.warning(f"[Scout] Aviso generando scouting del rival: {ex_scout}")

            # 2. Recolectar prensa deportiva exhaustiva
            noticias = ManyaSportsPressService.recolectar_todas(max_por_fuente=10)

            # 3. Acciones según fase del partido
            if fase == "PREVIA":
                ejecutar_ciclo_previa(match_info, noticias)
            elif fase == "EN_VIVO":
                ejecutar_ciclo_en_vivo(match_info)
            elif fase == "FINALIZADO":
                ejecutar_ciclo_cronica(match_info, noticias)
            else:
                logger.info("[Orquestador] No hay partido en curso en este momento. Sistema en vigilia.")

        except Exception as e:
            logger.error(f"[Orquestador] Excepción en ciclo del vigilante: {e}", exc_info=True)

        if modo == "once":
            logger.info("[Orquestador] Ejecución única completada.")
            break

        # Tiempos de espera adaptativos para modo daemon
        if fase == "EN_VIVO":
            time.sleep(180)  # Polling cada 3 minutos en vivo
        elif fase == "PREVIA":
            time.sleep(900)  # Chequeo cada 15 minutos en previa
        else:
            time.sleep(3600)  # Chequeo cada hora en reposo


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daemon de partidos y noticias de Peñarol")
    parser.add_argument("--daemon", action="store_true", help="Ejecutar en modo servicio continuo")
    parser.add_argument("--once", action="store_true", help="Ejecutar un solo ciclo y finalizar")
    args = parser.parse_args()

    ejecutar_orquestador(modo="daemon" if args.daemon else "once")
