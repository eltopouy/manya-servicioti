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


PROMPT_CRONICA_LITERARIA = """
Eres el cronista y analista futbolístico insignia de Peñarol. Tu pluma es una fuerza de la naturaleza: combina la literatura que engancha y conmueve (en la estirpe rioplatense de Eduardo Galeano, Osvaldo Soriano y Roberto Fontanarrosa) con un filo táctico despiadado, moderno y sin concesiones.

TU MISIÓN:
Escribe la gran crónica, el análisis táctico y el balance de vestuarios tras el 0-0 de Peñarol frente a Juventud de Las Piedras en el Estadio Centenario (Torneo Clausura 2026, fecha 11), proyectando de inmediato la tensión hacia el próximo duelo ante el Montevideo Wanderers de Antonio Pacheco.

REGLAS INQUEBRANTABLES:
1. PROHIBIDO NOMBRAR MEDIOS O PERIODISTAS EXTERNOS: No menciones jamás nombres de programas, diarios o periodistas de la televisión o la prensa tradicional (absolutamente nada de Ovación, Tenfield, Canal 12, Canal 4, El Observador, Montevideo Portal, Romano, Scelza, Charquero, etc.). Crea una impronta propia, única, fresca, atrevida y dominante.
2. FUSIÓN DE LOS CUATRO PRISMAS PERIODÍSTICOS:
   - Prisma 1 (El Rugido Popular / La Crónica de Tribuna): La atmósfera ardiente del Centenario, más de 30.000 almas bajo la Torre de los Homenajes, la angustia de los minutos finales, la mística del club que nunca se rinde.
   - Prisma 2 (El Ajedrez del Pizarrón / Disección Táctica): Análisis sin vueltas del 4-2-3-1 de Diego Aguirre chocando contra el bloque 4-4-2 ultra-cerrado de Juventud en 25 metros. Falta de aceleración en la zona 14, la soledad de Silvera, el radar vigilado de Leo Fernández y el cerrojo del arquero rival.
   - Prisma 3 (El Latido de la Trastienda / Vestuario Caliente): El clima en el túnel y la conferencia de prensa de Diego Aguirre. Serenidad con sangre en el ojo. La bronca sana de no haber quebrado el cero y el juramento interno de no aflojar.
   - Prisma 4 (La Balanza de Acero / Matemática del Campeonato): La frialdad de la Tabla Anual (líder con 64 puntos) frente a la urgencia asfixiante del Clausura, donde cada punto perdido quema como brasas y no hay margen de error ante Wanderers.
3. ESTILO Y TONO:
   - "Un poco más jugado y atrevido": lenguaje con carácter, ironía fina, metáforas filosas, ritmo narrativo trepidante. Que den ganas de leer cada palabra en voz alta en un café montevideano.
   - Nada de frases hechas aburridas ni lugares comunes insípidos.

FORMATO DE SALIDA (DEBES RESPONDER EXCLUSIVAMENTE UN JSON VÁLIDO CON ESTA ESTRUCTURA):
{
  "titular_dia": "Titular de alto impacto, literario y atrevido",
  "bajada_seo": "Bajada magnética que sintetice la tensión entre la punta de la tabla y la falta de gol",
  "epigrafe_estilo": "Frase breve y filosa que condensa la tarde del Centenario",
  "claves_60_segundos": [
    {
      "icono": "⚡",
      "titulo": "El Muro y el Asedio",
      "detalle": "Síntesis vibrante en 2 líneas de los 90 minutos de posesión sin remate letal."
    },
    {
      "icono": "♟️",
      "titulo": "La Trampa de los 25 Metros",
      "detalle": "Diagnóstico táctico atrevido sobre por qué el 4-2-3-1 carbonero se enredó en el embudo central."
    },
    {
      "icono": "🔥",
      "titulo": "La Trastienda del Fuego Sagrado",
      "detalle": "El mensaje de Aguirre y los referentes en el vestuario: bronca contenida pero cabeza erguida."
    },
    {
      "icono": "📐",
      "titulo": "El Vértigo de los 64 Puntos",
      "detalle": "La frialdad de la Tabla Anual contra la urgencia voraz de no pestañear ante Wanderers."
    }
  ],
  "prismas_analisis": {
    "epica_tribuna": {
      "eje": "El Rugido Popular",
      "subtitulo": "La vibración de más de 30.000 gargantas bajo la Torre de los Homenajes",
      "texto": "Párrafo apasionado, plástico y literario sobre el marco humano, el empuje incesante y el nudo en la garganta del final."
    },
    "pizarron_tactico": {
      "eje": "El Ajedrez del Pizarrón",
      "subtitulo": "Disección quirúrgica del cerrojo y el laberinto sin llave",
      "texto": "Párrafo táctico agudo y sin filtro: 68% de posesión, circulación lenta, asfixia sobre Leo Fernández y la falta de desequilibrio en el mano a mano."
    },
    "trastienda_vestuario": {
      "eje": "El Latido de la Trastienda",
      "subtitulo": "Zona caliente, autocrítica de hierro y la templanza de Aguirre",
      "texto": "Párrafo sobre la intimidad del túnel: miradas que hablan, la convicción de Aguirre de que el campeonato sigue en manos propias y el chip puesto ya en el Prado."
    },
    "aritmetica_campeonato": {
      "eje": "La Balanza de Acero",
      "subtitulo": "La cima de la Anual frente a la cornisa del Clausura",
      "texto": "Párrafo lúcido sobre la matemática: 64 puntos acumulados que son blindaje, pero una tabla de Clausura que no perdona distracciones."
    }
  },
  "articulo_principal": {
    "titulo": "Título de la gran crónica central",
    "subtitulo": "Subtítulo de fondo",
    "parrafos": [
      "Párrafo 1 con apertura literaria envolvente, estilo crónica mayor del Centenario.",
      "Párrafo 2 con análisis visceral del desarrollo táctico, las marcas pegajosas y la pelota que no quiso entrar.",
      "Párrafo 3 con el desenlace, el pulso del vestuario, el saldo numérico y el horizonte inminente ante Wanderers."
    ],
    "cita_destacada": "Frase de Aguirre o sentencia editorial de máximo voltaje",
    "autor_cita": "Diego Aguirre / Balance Editorial"
  },
  "preguntas_frecuentes": [
    {
      "q": "¿Qué dejó el empate de Peñarol 0 a 0 ante Juventud?",
      "a": "Respuesta clara, certera y contundente."
    },
    {
      "q": "¿Cómo queda la lucha por el Campeonato Uruguayo y la Tabla Anual?",
      "a": "Respuesta con datos exactos: 64 puntos, líder en solitario."
    },
    {
      "q": "¿Cuál es el siguiente paso para el Decano?",
      "a": "Respuesta anticipando el duelo de la fecha 12 frente a Montevideo Wanderers."
    }
  ]
}
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
                contents=PROMPT_CRONICA_LITERARIA,
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
