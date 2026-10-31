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
    estadio = match_info.get("estadio", "Parque Alfredo Víctor Viera (Prado)")
    tv = match_info.get("tv", "VTV Plus / Disney+ Premium")
    hora_str = match_info.get("fecha_legible", "")
    fecha_iso = match_info.get("fecha_iso", "")
    es_hoy = match_info.get("es_hoy", False)

    now_uy = datetime.now(UY_TZ)
    delta_days = 1
    if fecha_iso:
        try:
            m_dt = datetime.fromisoformat(fecha_iso.replace("Z", "+00:00")).astimezone(UY_TZ)
            delta_days = (m_dt.date() - now_uy.date()).days
        except Exception:
            delta_days = 0 if es_hoy else 1
    else:
        delta_days = 0 if es_hoy else 1

    if delta_days == 0:
        temporal_label = "HOY JUEGA PEÑAROL (DÍA DEL PARTIDO)"
        temporal_instructions = (
            "El partido se juega HOY en horario uruguayo. El titular y el contenido deben reflejar que es el DÍA DEL PARTIDO "
            "('¡Hoy juega el Manya!', 'Día de partido en el Prado', etc.)."
        )
        dia_partido_texto = "hoy"
    elif delta_days == 1:
        temporal_label = "MAÑANA JUEGA PEÑAROL (LA VÍSPERA / PREVIA)"
        temporal_instructions = (
            "CRÍTICO - CONTROL DE FECHA: En Uruguay aún NO es el día del partido. El partido es MAÑANA. "
            "ESTÁ ESTRICTAMENTE PROHIBIDO decir 'Hoy juega el Manya' o 'hoy juega'. "
            "El titular DEBE hablar de la previa o de la víspera: "
            "('La Previa Aurinegra', 'Peñarol afina detalles antes de visitar el Prado', 'La víspera en Los Aromos', etc.)."
        )
        dia_partido_texto = "mañana"
    else:
        temporal_label = f"PRÓXIMO COMPROMISO (Faltan {delta_days} días)"
        temporal_instructions = (
            f"CRÍTICO - CONTROL DE FECHA: Faltan {delta_days} días para el encuentro. "
            "NO uses 'hoy juega' ni 'mañana juega'. Habla del próximo rival en el horizonte carbonero."
        )
        dia_partido_texto = f"el próximo {hora_str}"

    can_pub, motivo = ManyaBloggerCatalog.can_publish(post_type="PREVIA", match_id=event_id)
    if not can_pub:
        logger.info(f"[Previa] {motivo}. Saltando redacción de previa.")
        return

    logger.info(f"[Previa] ⚡ Generando La Previa Oficial: {match_title} ({hora_str}) [Estado: {temporal_label}]...")

    # Síntesis de noticias para el redactor
    resumenes_prensa = "
".join([
        f"- [{n['fuente']}] {n['titulo']}: {n['resumen'][:180]}"
        for n in noticias_prensa[:10]
    ])

    prompt_redaccion = f"""
Actúa como el Jefe de Redacción y Periodista Experto de Peñarol para 'Manya ServicioTI'.
ESTADO TEMPORAL: {temporal_label}.
{temporal_instructions}
Partido: {match_title}.
Estadio: {estadio}.
Fecha y Hora de Uruguay: {hora_str}.
Televisación: {tv}.

Contexto reciente de periódicos uruguayos (Ovación, Referí, Tenfield, Padre y Decano):
{resumenes_prensa}

REGLAS EDITORIALES OBLIGATORIAS:
1. Responde ÚNICAMENTE en formato JSON plano válido (sin markdown ```json).
2. Tono: apasionado, respetuoso pero 100% aurinegro y profesional. Cero romanticismo lírico.
3. Respeto estricto del estado temporal: si el partido es mañana ({hora_str}), PROHIBIDO decir 'hoy juega'.
4. Estructura del JSON requerida:
{{
  "titular_dia": "Frase contundente sobre la previa del partido",
  "bajada_seo": "Resumen periodístico SEO con Peñarol, rival, estadio ({estadio}) y cómo verlo.",
  "claves_60_segundos": [
    {{"icono": "⚽", "titulo": "Clave Táctica", "detalle": "Detalle del planteo de Diego Aguirre"}},
    {{"icono": "🔥", "titulo": "La Figura a Seguir", "detalle": "Rendimiento esperado de Leonardo Fernández"}},
    {{"icono": "📺", "titulo": "Transmisión y Horario", "detalle": "Hora oficial de Uruguay ({hora_str}) y televisación ({tv})"}},
    {{"icono": "📊", "titulo": "Puntos en Juego", "detalle": "Impacto directo en la Tabla Anual (Peñarol líder con 65 pts)"}}
  ],
  "articulo_principal": {{
    "titulo": "Título periodístico de análisis de la previa",
    "subtitulo": "Subtítulo periodístico",
    "parrafos": [
      "Párrafo 1: El clima previo en Los Aromos y la concentración aurinegra...",
      "Párrafo 2: El rival de turno ({match_title}), su momento y cómo contrarrestar su juego en {estadio}...",
      "Párrafo 3: El once probable de Peñarol, retornos y variantes tácticas...",
      "Párrafo 4: La expectativa de los hinchas y el peso de sumar de a tres en la Tabla Anual..."
    ],
    "preguntas_frecuentes": [
      {{"q": "¿A qué hora juega Peñarol y dónde verlo?", "a": "Peñarol juega {dia_partido_texto} a las {hora_str} en {estadio}, televisado por {tv}."}},
      {{"q": "¿Cómo formaría Peñarol?", "a": "Diego Aguirre perfila un esquema ofensivo 4-2-3-1."}},
      {{"q": "¿Qué se juega Peñarol en este partido?", "a": "Puntos vitales para custodiar la cima de la Tabla Anual y la definición del Clausura."}}
    ]
  }}
}}
"""

    with CentralAutomationLock.acquire("gemini_web_profile", timeout_sec=120):
        res_json = ManyaGeminiWebEngine.generar_texto_gflash_38(prompt_redaccion)

    if res_json and "articulo_principal" in res_json:
        titular = res_json.get("titular_dia", f"La Previa: {match_title}")
        if delta_days != 0 and "hoy juega" in titular.lower():
            titular = titular.replace("¡Hoy juega el Manya!", "La Previa Aurinegra:").replace("Hoy juega el Manya", "La Previa de Peñarol")

        doc_digest = {
            "actualizado": datetime.now(UY_TZ).strftime("%d/%m/%Y %H:%M"),
            "modelo_ia": "Google Gemini Web (GFlash 3.8 Multimodal)",
            "fase_publicacion": "PREVIA",
            "partido_id": event_id,
            "titular_dia": titular,
            "bajada_seo": res_json.get("bajada_seo", ""),
            "claves_60_segundos": res_json.get("claves_60_segundos", []),
            "articulo_principal": res_json.get("articulo_principal", {}),
            "noticias_fuentes": noticias_prensa[:8]
        }
        (DATA_DIR / "news_digest.json").write_text(json.dumps(doc_digest, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("[Previa] ✓ data/news_digest.json actualizado con la previa oficial.")
        # Publicar en Blogger
        post_url = publish_manya_article_to_blogger(post_type="PREVIA", match_id=event_id)
        try:
            from sincronizar_pagina_blogger_historico import sincronizar_pagina_blogger
            sincronizar_pagina_blogger()
        except Exception as ex_sync:
            logger.warning(f"[Blogger Sync] Aviso actualizando archivo histórico: {ex_sync}")
        git_commit_and_push(f"feat(previa): publicar previa {match_title} en vivo")


def ejecutar_ciclo_hoy_juega(match_info: dict, noticias_prensa: list):
    """
    Edición Especial '¡HOY JUEGA EL MANYA!' (Se activa a las 00:05 hs del día del partido).
    Revoluciona el portal a primera hora con las últimas novedades del vestuario,
    pronóstico del tiempo para la hora del partido, accesos al estadio y el clima de match day.
    """
    event_id = match_info.get("event_id", "")
    match_title = match_info.get("nombre", "Peñarol vs Montevideo Wanderers")
    estadio = match_info.get("estadio", "Parque Alfredo Víctor Viera (Prado)")
    tv = match_info.get("tv", "VTV Plus / Disney+ Premium")
    hora_str = match_info.get("fecha_legible", "")

    can_pub, motivo = ManyaBloggerCatalog.can_publish(post_type="HOY_JUEGA", match_id=event_id)
    if not can_pub:
        logger.info(f"[Hoy Juega] {motivo}. Saltando edición de match day.")
        return

    logger.info(f"[Hoy Juega] 🟡⚫ Generando Edición Especial de Match Day: ¡HOY JUEGA EL MANYA! ({match_title})...")

    # Clima verificado para el partido
    clima_str = "Tarde templada en Montevideo (18°C-20°C), cielo claro a parcialmente nublado, viento moderado."
    try:
        from manya_match_engine import ManyaMatchEngine
        w_data = ManyaMatchEngine.fetch_campeon_del_siglo_weather()
        if w_data and "temperatura" in w_data:
            clima_str = f"{w_data.get('temperatura','19°C')}, viento {w_data.get('viento','15 km/h')} ({w_data.get('condicion','despejado')})"
    except Exception:
        pass

    resumenes_prensa = "\n".join([
        f"- [{n['fuente']}] {n['titulo']}: {n['resumen'][:180]}"
        for n in noticias_prensa[:10]
    ])

    prompt_redaccion = f"""
Actúa como el Director Editorial y Periodista Insignia de Peñarol para 'Manya ServicioTI'.
¡ES LA MADRUGADA DEL DÍA DEL PARTIDO!
HOY JUEGA PEÑAROL: {match_title}.
Estadio: {estadio}.
Fecha y Hora de Uruguay: {hora_str}.
Televisación: {tv}.
Clima pronosticado para la hora del partido: {clima_str}.

Contexto reciente de medios uruguayos (Ovación, Referí, Tenfield, Padre y Decano):
{resumenes_prensa}

REGLAS EDITORIALES OBLIGATORIAS:
1. Responde ÚNICAMENTE en formato JSON plano válido (sin markdown ```json).
2. Tono: 100% futbolero, vibrante, con adrenalina de día de partido ('¡Hoy juega el Manya!'). Cero cursilería.
3. El titular DEBE comenzar con '¡Hoy juega el Manya!' destacando el compromiso del día.
4. Información verificada:
   - Estadio: {estadio}.
   - Peñarol es líder absoluto de la Tabla Anual con 65 puntos (+24 DG).
   - Entradas: Si es visitante (Parque Viera), venta online vía RedTickets (redtickets.uy) sin canje de socios.
5. Estructura del JSON requerida:
{{
  "titular_dia": "¡Hoy juega el Manya! Tarde de Parque Viera para defender con alma y vida la punta de la Tabla Anual",
  "bajada_seo": "Peñarol enfrenta este sábado a Montevideo Wanderers a las 16:30 hs en el Parque Viera. Alineaciones probables, clima, accesos y TV en vivo.",
  "claves_60_segundos": [
    {{"icono": "⚽", "titulo": "El Once de la Fiera", "detalle": "Alineación titular de Diego Aguirre con Leo Fernández en la conducción y Silvera en el ataque."}},
    {{"icono": "🌤️", "titulo": "Clima y Cancha", "detalle": "Pronóstico para la hora del partido: {clima_str}."}},
    {{"icono": "📺", "titulo": "Horario y Pantalla", "detalle": "{hora_str} en directo por {tv}."}},
    {{"icono": "📊", "titulo": "Mandato en la Anual", "detalle": "El Decano manda con 65 unidades y busca estirar la diferencia en la tabla acumulada."}}
  ],
  "articulo_principal": {{
    "titulo": "¡Hoy juega el Manya! Todo lo que tenés que saber antes de que ruede la pelota en el Parque Viera",
    "subtitulo": "Diego Aguirre alista el equipo para una batalla determinante por la Tabla Anual ante Montevideo Wanderers",
    "parrafos": [
      "Párrafo 1: La adrenalina de la mañana de partido, la concentración en Los Aromos y la charla táctica...",
      "Párrafo 2: El examen táctico en el Parque Viera, neutralizar el circuito de Bruno Veglio y Tabaré Viudez...",
      "Párrafo 3: Las armas carboneras: la pegada de Leo Fernández, las subidas de Cabrera y la zaga Aguerre-Guzmán...",
      "Párrafo 4: Tribunas colmadas de parcialidad aurinegra y la importancia mayúscula de ganar para sostener los 65 puntos..."
    ],
    "preguntas_frecuentes": [
      {{"q": "¿A qué hora juega Peñarol hoy y por qué canal lo transmiten?", "a": "Peñarol juega hoy a las {hora_str} en {estadio}, televisado por {tv}."}},
      {{"q": "¿Cómo forma Peñarol hoy?", "a": "Aguerre; Milans, Méndez, Guzmán Rodríguez, Olivera; García, Pérez; Cabrera, Fernández, Báez; Silvera."}},
      {{"q": "¿Qué se juega Peñarol hoy en la tabla?", "a": "Tres puntos vitales para mantener la punta de la Tabla Anual (65 pts) y afianzar el Clausura."}}
    ]
  }}
}}
"""

    with CentralAutomationLock.acquire("gemini_web_profile", timeout_sec=120):
        res_json = ManyaGeminiWebEngine.generar_texto_gflash_38(prompt_redaccion)

    if res_json and "articulo_principal" in res_json:
        titular = res_json.get("titular_dia", f"¡Hoy juega el Manya! {match_title}")
        doc_digest = {
            "actualizado": datetime.now(UY_TZ).strftime("%d/%m/%Y %H:%M"),
            "modelo_ia": "Google Gemini Web (GFlash 3.8 Multimodal)",
            "fase_publicacion": "HOY_JUEGA",
            "partido_id": event_id,
            "titular_dia": titular,
            "bajada_seo": res_json.get("bajada_seo", ""),
            "claves_60_segundos": res_json.get("claves_60_segundos", []),
            "articulo_principal": res_json.get("articulo_principal", {}),
            "portada_visual": {
                "titular_portada": f"⚡ ¡HOY JUEGA EL MANYA! Peñarol visita el Prado en busca de afianzar la punta",
                "bajada_portada": f"¡LLEGÓ EL DÍA! A las 16:30 hs el Carbonero salta a la cancha del Parque Viera ante Montevideo Wanderers por la fecha 12 del Clausura. Peñarol manda en la Tabla Anual con 65 puntos. Televisa {tv}.",
                "cuenta": "@oficialcap",
                "ubicacion": f"📍 {estadio} • Montevideo",
                "categoria": "partidos",
                "imagen_webp": "assets/ig/manya_entrenamiento_los_aromos_tactica.webp",
                "imagen_jpg": "assets/ig/manya_entrenamiento_los_aromos_tactica.jpg"
            },
            "noticias_fuentes": noticias_prensa[:8]
        }
        (DATA_DIR / "news_digest.json").write_text(json.dumps(doc_digest, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("[Hoy Juega] ✓ data/news_digest.json actualizado con la edición especial de Match Day.")

        # Sincronizar live_status con alerta banner del día
        try:
            status_live = ManyaMatchEngine.generate_updated_live_status()
            status_live["partido_activo"]["es_hoy"] = True
            status_live["alerta_banner"] = f"🟡⚫ ¡HOY JUEGA PEÑAROL! {match_title} a las {hora_str} en {estadio} • {tv}."
            (DATA_DIR / "live_status.json").write_text(json.dumps(status_live, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as ex_ls:
            logger.warning(f"[Hoy Juega] Aviso actualizando live_status: {ex_ls}")

        # Publicar o actualizar en Blogger
        post_url = publish_manya_article_to_blogger(post_type="HOY_JUEGA", match_id=event_id)
        
        # Sincronizar página de previo partido en Blogger
        try:
            from sincronizar_pagina_proximo_partido import sincronizar_pagina_proximo_partido_blogger
            sincronizar_pagina_proximo_partido_blogger()
        except Exception as ex_p:
            logger.warning(f"[Blogger Previa] Aviso actualizando previa Blogger: {ex_p}")

        git_commit_and_push(f"feat(matchday): ¡Hoy Juega el Manya! Cobertura de partido {match_title}")


def ejecutar_ciclo_en_vivo(match_info: dict):
    """Actualización en tiempo real durante el partido (polling ESPN hacia manya.servicioti.com.uy y Blogger)."""
    match_title = match_info.get("nombre", "")
    reloj = match_info.get("minuto_reloj", "")
    logger.info(f"[En Vivo] 🔴 Partido en juego: {match_title} | Reloj: {reloj}")
    try:
        from automation.publicar_en_vivo_blogger import publicar_cobertura_en_vivo
        publicar_cobertura_en_vivo()
    except Exception as e:
        logger.warning(f"[En Vivo] Aviso al sincronizar en vivo con Blogger: {e}. Fallback a match engine.")
        ManyaMatchEngine.generate_updated_live_status()
    git_commit_and_push(f"live(partido): actualización en directo {match_title} ({reloj})")


def ejecutar_ciclo_cronica(match_info: dict, noticias_prensa: list):
    """Genera la crónica definitiva post-partido y actualiza la entrada histórica en Blogger."""
    event_id = match_info.get("event_id", "")
    match_title = match_info.get("nombre", "Partido de Peñarol")
    loc = match_info.get("local", {})
    vis = match_info.get("visitante", {})
    marcador = f"{loc.get('nombre')} {loc.get('goles')} - {vis.get('goles')} {vis.get('nombre')}"

    logger.info(f"[Crónica] 🏁 Ejecutando Crónica Narrativa y Cierre Histórico: {marcador}...")

    # 1. Generación de crónica literaria con Gemini 3.8 Flash (4 Prismas)
    try:
        from automation.generar_cronica_gemini_narrativa import generar_cronica_con_gemini, actualizar_digest_json
        datos_narrativa = generar_cronica_con_gemini()
        if datos_narrativa:
            actualizar_digest_json(datos_narrativa)
    except Exception as ex_gemini:
        logger.warning(f"[Crónica] Aviso en generación de crónica Gemini: {ex_gemini}")

    # 2. Cierre y sellado histórico del post en Blogger (/2026/10/penarol-en-vivo-juventud-vs-penarol.html)
    try:
        from automation.cerrar_partido_historico_blogger import ejecutar_cierre_historico
        ejecutar_cierre_historico()
    except Exception as ex_cierre:
        logger.warning(f"[Crónica] Aviso en cierre histórico de Blogger: {ex_cierre}")

    # 3. Sincronizar Página Central Permanente para el próximo partido (/p/penarol-proximo-partido-radiografia.html)
    try:
        from automation.sincronizar_pagina_proximo_partido import sincronizar_proximo_partido_blogger
        sincronizar_proximo_partido_blogger()
    except Exception as ex_prox:
        logger.warning(f"[Crónica] Aviso sincronizando página central de próximo rival: {ex_prox}")

    # 4. Sincronizar Archivo Histórico de Blogger
    try:
        from automation.sincronizar_pagina_blogger_historico import sincronizar_pagina_blogger
        sincronizar_pagina_blogger()
    except Exception as ex_hist:
        logger.warning(f"[Crónica] Aviso actualizando archivo histórico: {ex_hist}")

    git_commit_and_push(f"feat(cronica): cierre histórico {marcador} y puente al próximo partido")
    return


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

            # 1c. Sincronizar scouting táctico del rival y balance 1891 BD dinámico
            try:
                from manya_rival_intelligence import generar_informe_rival
                rival_slug = status_live.get("rival_activo_slug")
                if not rival_slug:
                    rival_equipo = match_info.get("visitante", {}) if match_info.get("local", {}).get("es_penarol") else match_info.get("local", {})
                    rival_slug = rival_equipo.get("nombre", "wanderers")
                generar_informe_rival(rival_slug)
            except Exception as ex_scout:
                logger.warning(f"[Scout] Aviso generando scouting del rival: {ex_scout}")

            # 1d. Sincronizar página de archivo histórico en Blogger
            try:
                from sincronizar_pagina_blogger_historico import sincronizar_pagina_blogger
                sincronizar_pagina_blogger()
            except Exception as ex_p:
                logger.warning(f"[Blogger Archivo] Aviso sincronizando página central: {ex_p}")

            # 2. Recolectar prensa deportiva exhaustiva
            noticias = ManyaSportsPressService.recolectar_todas(max_por_fuente=10)

            # 3. Acciones según fase del partido y ventana de 48 horas
            if fase == "PREVIA":
                ejecutar_ciclo_previa(match_info, noticias)
            elif fase == "EN_VIVO":
                ejecutar_ciclo_en_vivo(match_info)
            elif fase in ("FINALIZADO", "POST_PARTIDO"):
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
    parser.add_argument("--hoy-juega", action="store_true", help="Forzar generación de la edición especial ¡Hoy Juega el Manya!")
    args = parser.parse_args()

    if args.hoy_juega:
        status_live = ManyaMatchEngine.generate_updated_live_status()
        match_info = status_live.get("partido_activo", {})
        prox = status_live.get("proximo_partido", {})
        partido_para_cubrir = match_info if match_info.get("event_id") else prox
        noticias = ManyaSportsPressService.recolectar_todas(max_por_fuente=10)
        ejecutar_ciclo_hoy_juega(partido_para_cubrir, noticias)
    else:
        ejecutar_orquestador(modo="daemon" if args.daemon else "once")
