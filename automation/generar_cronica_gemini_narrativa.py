# -*- coding: utf-8 -*-
"""
GENERADOR AUTOMÁTICO DE CRÓNICA Y ANÁLISIS TÁCTICO GEMINI (NARRATIVA LITERARIA Y AUDACIA PERIODÍSTICA)
======================================================================================================
Archivo: automation/generar_cronica_gemini_narrativa.py
Autor: Andrés Franchi Ugartemendía • ServicioTI Manya
Modelo: Google Gemini 3.8 Flash (Multimodal & Generativo)

Propósito:
- Conectar con Gemini 3.8 Flash para redactar automáticamente la crónica profunda, el pizarrón táctico
  y la actualidad aurinegra.
- Impronta: Una voz nueva, magnética y atrevida, que fusiona los mejores ángulos del periodismo deportivo
  (el pulso electrizante de tribuna, la disección táctica quirúrgica, el vestuario caliente y la
  matemática del campeonato) SIN NOMBRAR MEDIOS NI PERIODISTAS EXTERNOS ("sin nombrarlos y creando algo nuevo").
- Literatura que engancha, jugado, con ritmo y filo literario.
- Guarda en `data/news_digest.json` y sincroniza opcionalmente con Blogger y el frontend.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [GeminiNarrativa] - %(levelname)s - %(message)s"
)
logger = logging.getLogger("GeminiNarrativa")

# Rutas Base
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SCRATCH_DIR = BASE_DIR.parent

# Carga de credenciales resiliente
def _obtener_gemini_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key
    for env_candidate in [
        SCRATCH_DIR / "seo_blogger_automation" / ".env",
        SCRATCH_DIR / "clima_blogger_automation" / ".env",
        SCRATCH_DIR / "gemini_automation" / ".env",
        BASE_DIR / ".env"
    ]:
        if env_candidate.exists():
            try:
                for line in env_candidate.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY=") and not line.startswith("#"):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception:
                pass
    return ""


def construir_prompt_cronica() -> str:
    """Construye dinámicamente el prompt con contexto real de live_status.json y persona profesional anti-disclaimer."""
    live_file = DATA_DIR / "live_status.json"
    rival_nom = "Defensor Sporting"
    estadio_nom = "Estadio Luis Franzini"
    fecha_num = "Fecha 14"
    if live_file.exists():
        try:
            live = json.loads(live_file.read_text(encoding="utf-8"))
            prox = live.get("proximo_partido", {})
            loc_p = prox.get("local", {})
            vis_p = prox.get("visitante", {})
            rival_nom = loc_p.get("nombre") if not loc_p.get("es_penarol") else vis_p.get("nombre", "Defensor Sporting")
            estadio_nom = prox.get("estadio", "Estadio Luis Franzini")
            f_n = prox.get("fecha_numero", 14)
            fecha_num = f"Fecha {f_n}"
        except Exception:
            pass

    return f"""Actúa como el Jefe de Redacción y Periodista Deportivo Especializado del Club Atlético Peñarol para 'Manya ServicioTI'.
Tu estilo es 100% futbolero rioplatense, incisivo, con el pulso y el lenguaje de la tribuna y el vestuario uruguayo: análisis táctico riguroso de pizarrón, intensidad en las marcas, presión alta, pelota parada y el pulso caliente de la definición del Campeonato Uruguayo.

CONTEXTO OFICIAL VIGENTE:
- Peñarol es LÍDER SOLITARIO de la Tabla Anual con 66 PUNTOS OFICIALES AUF (+24 DG).
- Próximo desafío: Visita a {rival_nom} en el {estadio_nom} por la {fecha_num} del Torneo Clausura.
- Partido anterior (Fecha 13): Empate 1-1 ante Montevideo Wanderers en el Saroldi.

REGLAS INQUEBRANTABLES:
1. PROHIBIDO emitir disclaimers, rechazos, advertencias o frases como 'Como modelo de lenguaje'.
2. PROHIBIDO nombrar medios externos (Tenfield, Ovación, etc.).
3. OBLIGATORIO mencionar los 66 puntos de Peñarol en la Tabla Anual y la {fecha_num} ante {rival_nom}.
4. RESPONDE EXCLUSIVAMENTE UN JSON VÁLIDO con la siguiente estructura:

{{
  "titular_dia": "Titular de alto impacto sobre Peñarol",
  "bajada_seo": "Bajada magnética sobre la punta de la Anual (66 puntos) y el choque ante {rival_nom}",
  "epigrafe_estilo": "Frase breve y filosa",
  "claves_60_segundos": [
    {{"icono": "⚡", "titulo": "La Punta de Acero", "detalle": "66 puntos en la Tabla Anual mandando en solitario."}},
    {{"icono": "♟️", "titulo": "Pizarrón Táctico", "detalle": "Bloque y variantes tácticas de Diego Aguirre para la {fecha_num}."}},
    {{"icono": "🔥", "titulo": "Fuego Sagrado", "detalle": "Intensidad y concentración máxima en Los Aromos."}},
    {{"icono": "📐", "titulo": "El Objetivo 2026", "detalle": "La definición del Campeonato Uruguayo en el horizonte."}}
  ],
  "prismas_analisis": {{
    "epica_tribuna": {{"eje": "El Rugido Popular", "subtitulo": "La mística aurinegra", "texto": "Párrafo de tribuna."}},
    "pizarron_tactico": {{"eje": "El Ajedrez del Pizarrón", "subtitulo": "Disección de {rival_nom}", "texto": "Párrafo táctico."}},
    "trastienda_vestuario": {{"eje": "El Latido de la Trastienda", "subtitulo": "Concentración en Los Aromos", "texto": "Párrafo de vestuario."}},
    "aritmetica_campeonato": {{"eje": "La Balanza de Acero", "subtitulo": "66 puntos en la cima", "texto": "Párrafo numérico con 66 puntos."}}
  }},
  "articulo_principal": {{
    "titulo": "Título de la gran crónica",
    "subtitulo": "Subtítulo de fondo",
    "parrafos": [
      "Párrafo 1 envolvente.",
      "Párrafo 2 de análisis táctico.",
      "Párrafo 3 proyectando el choque ante {rival_nom} en el {estadio_nom} con 66 puntos en la Anual."
    ],
    "cita_destacada": "En la Tabla Anual sigue mandando Peñarol con 66 puntos.",
    "autor_cita": "Diego Aguirre / Balance Editorial"
  }},
  "preguntas_frecuentes": [
    {{"q": "¿Cómo está Peñarol en la Tabla Anual?", "a": "Líder solitario con 66 puntos oficiales AUF."}},
    {{"q": "¿Cuándo y contra quién es el próximo partido?", "a": "{fecha_num} ante {rival_nom} en el {estadio_nom}."}}
  ]
}}
"""


def generar_cronica_con_gemini() -> Dict[str, Any]:
    """Genera la crónica mediante Gemini 3.8 Flash con cascada a modelos compatibles."""
    api_key = _obtener_gemini_key()
    if not api_key:
        logger.error("No se encontró GEMINI_API_KEY en variables de entorno ni archivos .env")
        return {}

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    modelos_candidatos = [
        "gemini-3.8-flash",
        "gemini-flash-latest",
        "gemini-3-flash-preview"
    ]

    for model_name in modelos_candidatos:
        try:
            logger.info(f"Invocando Gemini ({model_name}) para redacción literaria y táctica...")
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.60
            )
            response = client.models.generate_content(
                model=model_name,
                contents=construir_prompt_cronica(),
                config=config
            )
            if response and response.text:
                texto_limpio = response.text.strip()
                if texto_limpio.startswith("```json"):
                    texto_limpio = texto_limpio[7:]
                if texto_limpio.startswith("```"):
                    texto_limpio = texto_limpio[3:]
                if texto_limpio.endswith("```"):
                    texto_limpio = texto_limpio[:-3]
                texto_limpio = texto_limpio.strip()

                data = json.loads(texto_limpio)
                logger.info(f"✓ Crónica generada exitosamente con {model_name}!")
                return data
        except Exception as e:
            logger.warning(f"Error con modelo {model_name}: {e}. Intentando alternativa...")

    logger.error("No fue posible generar la crónica con ninguno de los modelos disponibles.")
    return {}


def actualizar_digest_json(cronica_data: Dict[str, Any]) -> bool:
    """Actualiza data/news_digest.json preservando fuentes y enlaces."""
    digest_path = DATA_DIR / "news_digest.json"
    if not digest_path.exists():
        logger.error(f"No existe {digest_path}")
        return False

    try:
        with open(digest_path, "r", encoding="utf-8") as f:
            digest = json.load(f)

        now_str = datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")
        digest["actualizado"] = now_str
        digest["modelo_ia"] = "Google Gemini 3.8 Flash • Redacción Literaria & Pizarrón Táctico"
        digest["fase_publicacion"] = "CRONICA_POST_PARTIDO"

        if cronica_data.get("titular_dia"):
            digest["titular_dia"] = cronica_data["titular_dia"]
        if cronica_data.get("bajada_seo"):
            digest["bajada_seo"] = cronica_data["bajada_seo"]
        if cronica_data.get("epigrafe_estilo"):
            digest["epigrafe_estilo"] = cronica_data["epigrafe_estilo"]
        if cronica_data.get("claves_60_segundos"):
            digest["claves_60_segundos"] = cronica_data["claves_60_segundos"]
        if cronica_data.get("prismas_analisis"):
            digest["prismas_analisis"] = cronica_data["prismas_analisis"]
        if cronica_data.get("articulo_principal"):
            digest["articulo_principal"] = cronica_data["articulo_principal"]
        if cronica_data.get("preguntas_frecuentes"):
            digest["preguntas_frecuentes"] = cronica_data["preguntas_frecuentes"]

        with open(digest_path, "w", encoding="utf-8") as f:
            json.dump(digest, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ {digest_path} actualizado con la nueva narrativa literaria.")
        return True
    except Exception as e:
        logger.error(f"Error actualizando news_digest.json: {e}")
        return False


if __name__ == "__main__":
    logger.info("=== INICIANDO MOTOR NARRATIVO GEMINI 3.8 FLASH (PEÑAROL) ===")
    datos = generar_cronica_con_gemini()
    if datos and "titular_dia" in datos:
        ok = actualizar_digest_json(datos)
        if ok:
            print(f"\n[OK] Titular generado: {datos.get('titular_dia')}")
            print(f"[OK] Bajada: {datos.get('bajada_seo')}")
            print(f"[OK] Claves: {len(datos.get('claves_60_segundos', []))} items")
            print(f"[OK] Prismas: {list(datos.get('prismas_analisis', {}).keys())}")
            sys.exit(0)
    logger.error("No se pudo completar la generación narrativa.")
    sys.exit(1)
