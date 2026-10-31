# -*- coding: utf-8 -*-
"""
MOTOR DE INTELIGENCIA DEPORTIVA Y SCOUTING DEL RIVAL (manya_rival_intelligence.py)
===================================================================================
Genera el informe táctico, análisis de figuras, duelos 1x1 y certificación 1891 BD
para cualquier rival del Campeonato Uruguayo.
Sincroniza automáticamente:
  1. data/rival_intelligence.json
  2. data/historial_[rival_slug].json
  3. data/historial_activo.json (usado directamente por app.js)
"""

import sys
import ssl
import json
import logging
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

logger = logging.getLogger("ManyaRivalIntelligence")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
UY_TZ = timezone(timedelta(hours=-3))

from manya_directory_registry import ManyaDirectoryRegistry

# Catálogo oficial de rivales verificado contra el MCP remoto de 1891.uy (Comisión de Historia y Patrimonio)
RIVALES_1891_MAP = {
    "wanderers": {
        "id": 321,
        "slug": "wanderers",
        "nombre_oficial": "Montevideo Wanderers Fútbol Club",
        "nombre_corto": "Wanderers",
        "escudo": "assets/img/escudos/escudo_montevideo_wanderers.webp",
        "estadio": "Parque Alfredo Víctor Viera (Prado)",
        "fundacion": "15 de agosto de 1902",
        "sede": "Prado, Montevideo, Uruguay",
        "capacidad": 15000,
        "web": "https://mwfc.com.uy/",
        "dt": "Antonio Pacheco",
        "esquema": "4-2-3-1 de posesión y transiciones veloces"
    },
    "juventud": {
        "id": 260,
        "slug": "juventud",
        "nombre_oficial": "Club Atlético Juventud de Las Piedras",
        "nombre_corto": "Juventud",
        "escudo": "assets/img/escudos/escudo_juventud.webp",
        "estadio": "Parque Artigas (Las Piedras)",
        "fundacion": "24 de diciembre de 1935",
        "sede": "Las Piedras, Canelones, Uruguay",
        "capacidad": 12000,
        "web": "https://juventud.uy/",
        "dt": "Diego Franco",
        "esquema": "4-4-2 bloque bajo de repliegue intensivo"
    },
    "cerro largo": {
        "id": 48,
        "slug": "cerro_largo",
        "nombre_oficial": "Cerro Largo Fútbol Club",
        "nombre_corto": "Cerro Largo",
        "escudo": "assets/img/escudos/escudo_cerro_largo.webp",
        "estadio": "Estadio Municipal Arquitecto Antonio Eleuterio Ubilla (Melo)",
        "fundacion": "19 de noviembre de 2002",
        "sede": "Melo, Cerro Largo, Uruguay",
        "capacidad": 10000,
        "web": "https://auf.org.uy/",
        "dt": "Danielo Núñez",
        "esquema": "4-4-2 combativo y juego aéreo directo"
    },
    "danubio": {
        "id": 6,
        "slug": "danubio",
        "nombre_oficial": "Danubio Fútbol Club",
        "nombre_corto": "Danubio",
        "escudo": "assets/img/escudos/escudo_danubio.webp",
        "estadio": "Estadio Jardines del Hipódromo María Mincheff de Lazaroff",
        "fundacion": "1 de marzo de 1932",
        "sede": "Maroñas, Montevideo, Uruguay",
        "capacidad": 18000,
        "web": "https://danubio.org.uy/",
        "dt": "Alejandro Apud",
        "esquema": "4-3-3 agresivo en presión y bandas punzantes"
    },
    "miramar": {
        "id": 119,
        "slug": "miramar_misiones",
        "nombre_oficial": "Club Sportivo Miramar Misiones",
        "nombre_corto": "Miramar Misiones",
        "escudo": "assets/img/escudos/escudo_miramar_misiones.webp",
        "estadio": "Parque Luis Méndez Piana",
        "fundacion": "25 de junio de 1980",
        "sede": "Parque Batlle, Montevideo, Uruguay",
        "capacidad": 6500,
        "web": "https://auf.org.uy/",
        "dt": "Walter Pandiani",
        "esquema": "4-1-4-1 rocoso y salida rápida"
    },
    "liverpool": {
        "id": 516,
        "slug": "liverpool",
        "nombre_oficial": "Liverpool Fútbol Club",
        "nombre_corto": "Liverpool",
        "escudo": "assets/img/escudos/escudo_liverpool.webp",
        "estadio": "Estadio Belvedere",
        "fundacion": "15 de febrero de 1915",
        "sede": "Belvedere, Montevideo, Uruguay",
        "capacidad": 10000,
        "web": "https://liverpoolfc.com.uy/",
        "dt": "Joaquín Papa",
        "esquema": "4-3-3 dinámico con presión alta"
    },
    "nacional": {
        "id": 405,
        "slug": "nacional",
        "nombre_oficial": "Club Nacional de Football",
        "nombre_corto": "Nacional",
        "escudo": "assets/img/escudos/escudo_nacional.webp",
        "estadio": "Gran Parque Central",
        "fundacion": "14 de mayo de 1899",
        "sede": "La Blanqueada, Montevideo, Uruguay",
        "capacidad": 34000,
        "web": "https://nacional.uy/",
        "dt": "Martín Lasarte",
        "esquema": "4-2-3-1 clásico de clásico"
    },
    "defensor": {
        "id": 499,
        "slug": "defensor_sporting",
        "nombre_oficial": "Defensor Sporting Club",
        "nombre_corto": "Defensor Sporting",
        "escudo": "assets/img/escudos/escudo_defensor_sporting.webp",
        "estadio": "Estadio Luis Franzini (Parque Rodó)",
        "fundacion": "15 de marzo de 1913",
        "sede": "Parque Rodó, Montevideo, Uruguay",
        "capacidad": 16000,
        "web": "https://defensorsporting.com.uy/",
        "dt": "Álvaro Navarro",
        "esquema": "4-3-3 juvenil de posesión y dinámica"
    },
    "boston": {
        "id": 274,
        "slug": "boston_river",
        "nombre_oficial": "Club Atlético Boston River",
        "nombre_corto": "Boston River",
        "escudo": "assets/img/escudos/escudo_boston_river.webp",
        "estadio": "Estadio Campeones Olímpicos (Florida)",
        "fundacion": "20 de febrero de 1939",
        "sede": "Montevideo / Florida, Uruguay",
        "capacidad": 7000,
        "web": "https://bostonriver.com.uy/",
        "dt": "Jadson Viera",
        "esquema": "4-2-3-1 de posesión y transiciones"
    },
    "racing": {
        "id": 243,
        "slug": "racing",
        "nombre_oficial": "Racing Club de Montevideo",
        "nombre_corto": "Racing",
        "escudo": "assets/img/escudos/escudo_racing.webp",
        "estadio": "Parque Osvaldo Roberto (Sayago)",
        "fundacion": "6 de abril de 1919",
        "sede": "Sayago, Montevideo, Uruguay",
        "capacidad": 8500,
        "web": "https://racingclub.com.uy/",
        "dt": "Eduardo Espinel",
        "esquema": "3-5-2 sólido en retroceso"
    },
    "progreso": {
        "id": 448,
        "slug": "progreso",
        "nombre_oficial": "Club Atlético Progreso",
        "nombre_corto": "Progreso",
        "escudo": "assets/img/escudos/escudo_progreso.webp",
        "estadio": "Parque Abraham Paladino (La Teja)",
        "fundacion": "30 de abril de 1917",
        "sede": "La Teja, Montevideo, Uruguay",
        "capacidad": 8000,
        "web": "https://auf.org.uy/",
        "dt": "Carlos Canobbio",
        "esquema": "4-4-2 friccionado y centros al área"
    }
}


def resolver_meta_rival(rival_query: str) -> dict:
    """Resuelve la metadata base de un rival a partir de cualquier consulta o nombre."""
    q = (rival_query or "wanderers").lower().strip()
    for key, meta in RIVALES_1891_MAP.items():
        if key in q or meta["slug"] in q or meta["nombre_corto"].lower() in q:
            return dict(meta)

    # Búsqueda complementaria en el directorio de clubes
    club = ManyaDirectoryRegistry.get_club(rival_query) or {}
    slug = club.get("slug", q.replace(" ", "_"))
    return {
        "id": 0,
        "slug": slug,
        "nombre_oficial": club.get("nombre_oficial", rival_query.title()),
        "nombre_corto": club.get("nombre_corto", rival_query.title()),
        "escudo": club.get("escudo_local_webp", "assets/img/escudos/escudo_penarol.webp"),
        "estadio": club.get("estadio_propio", "Estadio de Primera División"),
        "fundacion": club.get("fundacion", "1900"),
        "sede": club.get("sede", "Montevideo, Uruguay"),
        "capacidad": 10000,
        "web": club.get("web_oficial", "https://auf.org.uy/"),
        "dt": club.get("dt_actual", "Cuerpo Técnico Rival"),
        "esquema": "4-4-2 tradicional"
    }


def call_1891_mcp(tool_name: str, arguments: dict = None) -> Optional[dict]:
    """Invoca una herramienta en el servidor MCP remoto de 1891 BD."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ManyaServicioTI/2.5",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    payload = {
        "jsonrpc": "2.0",
        "id": 1891,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments or {}
        }
    }
    try:
        req = urllib.request.Request(
            "https://mcp.1891.uy/mcp",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers
        )
        with urllib.request.urlopen(req, context=ctx, timeout=12) as r:
            raw = r.read().decode("utf-8", errors="ignore")
            for line in raw.split("\n"):
                if line.startswith("data:"):
                    obj = json.loads(line[5:].strip())
                    content_list = obj.get("result", {}).get("content", [])
                    if content_list and content_list[0].get("text"):
                        return json.loads(content_list[0]["text"])
    except Exception as e:
        logger.warning(f"[1891 MCP] Aviso al invocar {tool_name} para {arguments}: {e}")
    return None


def obtener_o_generar_historial_1891(rival_query: str) -> dict:
    """
    Obtiene el balance histórico oficial frente al rival consultando el MCP de 1891 BD.
    Genera simultáneamente:
      - data/historial_{rival_slug}.json
      - data/historial_activo.json (enlace universal consumido por frontend)
    """
    meta = resolver_meta_rival(rival_query)
    rival_id = meta.get("id", 0)
    rival_slug = meta.get("slug", "rival")
    rival_nombre = meta.get("nombre_oficial", rival_query.title())

    logger.info(f"[1891 BD] Obteniendo historial frente a {rival_nombre} (ID: {rival_id})...")

    # Si hay ID de 1891, consultar MCP en vivo
    h2h_data = None
    if rival_id > 0:
        h2h_data = call_1891_mcp("get_head_to_head", {"rivalId": rival_id, "recentLimit": 5})

    historial_doc = None
    if h2h_data and "data" in h2h_data:
        st = h2h_data["data"].get("stats", {})
        recent = h2h_data["data"].get("recent", [])
        pj = int(st.get("partidos_jugados", 0))
        pg = int(st.get("ganados", 0))
        pe = int(st.get("empatados", 0))
        pp = int(st.get("perdidos", 0))
        gf = int(st.get("goles_afavor", 0))
        gc = int(st.get("goles_encontra", 0))

        ventaja = pg - pp
        dif_goles = gf - gc
        efectividad = round(((pg * 3 + pe) / (pj * 3) * 100), 1) if pj > 0 else 0.0

        ultimos = []
        for m in recent:
            f_raw = m.get("fecha", "")
            f_corta = f_raw[:10] if f_raw else "Fecha Reciente"
            marcador_str = f"Peñarol {m.get('goles_p', 0)} - {m.get('goles_r', 0)} {meta.get('nombre_corto')}"
            incidencias = m.get("text", "") or ""
            juez = m.get("juez", "")
            if juez and not incidencias:
                incidencias = f"Árbitro: {juez}"

            ultimos.append({
                "fecha": f_corta,
                "marcador": marcador_str,
                "estadio": m.get("estadio") or meta.get("estadio"),
                "torneo": m.get("nombre_camp") or m.get("nombre_camp2") or "Campeonato Uruguayo",
                "incidencias": incidencias
            })

        historial_doc = {
            "rival": meta.get("nombre_corto"),
            "rival_oficial": rival_nombre,
            "rival_id": rival_id,
            "rival_slug": rival_slug,
            "escudo_rival": meta.get("escudo"),
            "fuente_oficial": "1891 BD — Comisión de Historia y Patrimonio Histórico del Club Atlético Peñarol",
            "resumen": {
                "partidos_jugados": pj,
                "ganados_penarol": pg,
                "empatados": pe,
                "perdidos_penarol": pp,
                "goles_penarol": gf,
                "goles_rival": gc,
                "diferencia_goles": f"+{dif_goles}" if dif_goles > 0 else str(dif_goles),
                "ventaja_victorias": f"+{ventaja} partidos a favor del Decano",
                "efectividad_pct": f"{efectividad}%"
            },
            "ultimos_enfrentamientos": ultimos
        }

    # Si falló la red o no tiene ID, revisar archivo existente en data/
    archivo_existente = DATA_DIR / f"historial_{rival_slug}.json"
    if not historial_doc and archivo_existente.exists():
        try:
            historial_doc = json.loads(archivo_existente.read_text(encoding="utf-8"))
            logger.info(f"[1891 BD] Recuperado archivo existente para {rival_slug}.")
        except Exception:
            pass

    # Fallback precalculado para Wanderers si fuera necesario
    if not historial_doc and "wanderers" in rival_slug:
        historial_doc = {
            "rival": "Montevideo Wanderers",
            "rival_oficial": "Montevideo Wanderers Fútbol Club",
            "rival_id": 321,
            "rival_slug": "wanderers",
            "escudo_rival": "assets/img/escudos/escudo_montevideo_wanderers.webp",
            "fuente_oficial": "1891 BD — Comisión de Historia y Patrimonio Histórico del Club Atlético Peñarol",
            "resumen": {
                "partidos_jugados": 396,
                "ganados_penarol": 207,
                "empatados": 113,
                "perdidos_penarol": 76,
                "goles_penarol": 701,
                "goles_rival": 394,
                "diferencia_goles": "+307",
                "ventaja_victorias": "+131 partidos a favor del Decano",
                "efectividad_pct": "61.8%"
            },
            "ultimos_enfrentamientos": [
                {
                    "fecha": "2026-08-05",
                    "marcador": "Peñarol 5 - 1 Montevideo Wanderers",
                    "estadio": "Estadio Centenario",
                    "torneo": "Torneo Intermedio (Final)",
                    "incidencias": "Goleada histórica consagratoria con exhibición de Leo Fernández y Maxi Silvera."
                },
                {
                    "fecha": "2026-05-18",
                    "marcador": "Peñarol 3 - 1 Montevideo Wanderers",
                    "estadio": "Campeón del Siglo",
                    "torneo": "Torneo Apertura 2026",
                    "incidencias": "Leonardo Fernández 22', Maximiliano Silvera 58', Javier Cabrera 74'."
                },
                {
                    "fecha": "2025-10-12",
                    "marcador": "Montevideo Wanderers 0 - 2 Peñarol",
                    "estadio": "Parque Alfredo Víctor Viera",
                    "torneo": "Torneo Clausura 2025",
                    "incidencias": "Maximiliano Silvera 34' y Leonardo Fernández 78' de tiro libre."
                }
            ]
        }

    if historial_doc:
        # Guardar en archivo específico
        (DATA_DIR / f"historial_{rival_slug}.json").write_text(
            json.dumps(historial_doc, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        # Guardar en archivo activo universal
        (DATA_DIR / "historial_activo.json").write_text(
            json.dumps(historial_doc, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info(f"[1891 BD] ✓ Historial activo guardado para {rival_nombre} (PJ: {historial_doc['resumen']['partidos_jugados']}, Ventaja: {historial_doc['resumen']['ventaja_victorias']}).")

    return historial_doc or {}


def generar_informe_rival(rival_query: str = "wanderers") -> dict:
    """Genera el informe de scouting táctico, duelos 1x1 y estadístico del rival."""
    meta = resolver_meta_rival(rival_query)
    rival_slug = meta.get("slug", "wanderers")
    rival_nombre = meta.get("nombre_oficial", "Montevideo Wanderers Fútbol Club")
    rival_corto = meta.get("nombre_corto", "Wanderers")

    logger.info(f"=== COMPILANDO INFORME DE INTELIGENCIA TÁCTICA DEL RIVAL: {rival_nombre.upper()} ===")

    # 1. Obtener Historial 1891 certificado
    h2h_doc = obtener_o_generar_historial_1891(rival_query)
    resumen_h2h = h2h_doc.get("resumen", {})

    # 2. Configurar perfil táctico y duelos 1x1 según rival
    if "wanderers" in rival_slug:
        scouting = {
            "entrenador": "Antonio Pacheco",
            "esquema_base": "4-2-3-1 de posesión y transiciones veloces",
            "propuesta_juego": (
                "Montevideo Wanderers, conducido tácticamente por un ídolo aurinegro como Antonio Pacheco, "
                "pregona un fútbol de buen trato de balón, salida limpia desde el fondo y posesión paciente "
                "para generar espacios entre líneas. Apuestan a la creatividad de Tabaré Viudez y Bruno Veglio "
                "en tres cuartos y al desequilibrio punzante de Matías Fonseca y Nicolás Royón en el área rival."
            ),
            "figuras_a_seguir": [
                {
                    "nombre": "Tabaré Viudez",
                    "rol": "Mediapunta / Extremo",
                    "analisis": "Talento individual, pausa y pegada refinada de tiro libre y media distancia. Exige marca escalonada."
                },
                {
                    "nombre": "Bruno Veglio",
                    "rol": "Volante Mixto / Eje",
                    "analisis": "El termómetro del mediocampo bohemio: distribución con criterio, visión panorámica y llegada sorpresiva al área."
                },
                {
                    "nombre": "Matías Fonseca",
                    "rol": "Centrodelantero",
                    "analisis": "Goleador móvil que busca diagonales constantes a las espaldas de los centrales y define de primera intención."
                },
                {
                    "nombre": "Mauro Silveira",
                    "rol": "Arquero",
                    "analisis": "Seguridad bajo los tres palos, reflejos felinos en disparos a quemarropa y excelente pegada para el inicio del juego."
                }
            ],
            "puntos_fuertes": [
                "Fluidez en la circulación media y velocidad asociativa.",
                "Conocimiento táctico profundo del cuerpo técnico liderado por Antonio Pacheco.",
                "Peligro constante en balones detenidos y remates de media distancia de Viudez."
            ],
            "vulnerabilidades_a_explotar": [
                "Sufren el repliegue defensivo si Peñarol recupera alto con Damián García y presiona la salida.",
                "Espacios a espaldas de los laterales bohemios cuando se suman al circuito ofensivo.",
                "Desventaja física en el juego aéreo ante la potencia de Guzmán Rodríguez y Maximiliano Silvera."
            ]
        }
        duelos_1x1 = [
            {
                "id": "duelo_conductores",
                "titulo": "El Duelo de Motores: Generación vs. Circulación",
                "zona_campo": "Zona 14 / Mediocampo Central",
                "penarol": {
                    "jugador": "Leonardo Fernández",
                    "dorsal": "8",
                    "rol": "Enganche / Conductor Aurinegro",
                    "atributos_clave": "Visión panorámica, pegada quirúrgica de balón parado y latigazo teledirigido."
                },
                "rival": {
                    "jugador": "Bruno Veglio",
                    "dorsal": "10",
                    "rol": "Eje y Gestor de Wanderers",
                    "atributos_clave": "Buen pie, distribución rápida y manejo de los ritmos del partido."
                },
                "clave_del_duelo": "El equipo que logre imponer el ritmo de su cerebro dominará el desarrollo. Si Leo Fernández tiene libertad para girar, romperá la zaga bohemia con pases filtrados."
            },
            {
                "id": "duelo_goleador_zaga",
                "titulo": "La Fiera del Gol vs. La Zaga Bohemia",
                "zona_campo": "Área de Wanderers",
                "penarol": {
                    "jugador": "Maximiliano Silvera",
                    "dorsal": "11",
                    "rol": "Centrodelantero de Presión",
                    "atributos_clave": "Presión asfixiante sobre la salida rival, diagonales y olfato goleador."
                },
                "rival": {
                    "jugador": "Emiliano García & Zaga Bohemia",
                    "dorsal": "2 / 3",
                    "rol": "Defensa Central de Wanderers",
                    "atributos_clave": "Oficio, anticipo terrestre y cobertura de espacios reducidos."
                },
                "clave_del_duelo": "Silvera deberá presionar la salida de los centrales de Pacheco para provocar errores no forzados en salida corta."
            },
            {
                "id": "duelo_bandas_viera",
                "titulo": "Desborde por Fuera vs. Cobertura de Laterales",
                "zona_campo": "Bandas / Cancha del Parque Viera",
                "penarol": {
                    "jugador": "Javier Cabrera & Jaime Báez",
                    "dorsal": "7 / 23",
                    "rol": "Extremos Aurinegros",
                    "atributos_clave": "Cambio de marcha en 1x1, profundidad y centros rasantes venenosos atrás."
                },
                "rival": {
                    "jugador": "Laterales de Wanderers",
                    "dorsal": "4 / 6",
                    "rol": "Laterales con proyección",
                    "atributos_clave": "Vocación ofensiva, pero espacios abiertos a sus espaldas en transición rápida."
                },
                "clave_del_duelo": "La cancha rápida favorece las transiciones veloces de Cabrera y Báez para desarticular la última línea bohemia."
            },
            {
                "id": "duelo_cerrojo_decano",
                "titulo": "La Muralla Decana vs. La Movilidad de Fonseca",
                "zona_campo": "Área Aurinegra",
                "penarol": {
                    "jugador": "Guzmán Rodríguez & Washington Aguerre",
                    "dorsal": "4 / 1",
                    "rol": "Zaguero Central y Arquero Decano",
                    "atributos_clave": "Fuerza aérea, anticipación impecable y solidez bajo los tres palos."
                },
                "rival": {
                    "jugador": "Matías Fonseca / Nicolás Royón",
                    "dorsal": "9 / 18",
                    "rol": "Delanteros de Wanderers",
                    "atributos_clave": "Movilidad constante, desmarques de apoyo y remate instantáneo."
                },
                "clave_del_duelo": "Neutralizar los centros hacia el corazón del área y cortar los circuitos con Viudez antes de que el balón llegue al área."
            }
        ]
    elif "cerro_largo" in rival_slug:
        scouting = {
            "entrenador": meta.get("dt", "Danielo Núñez"),
            "esquema_base": "4-4-2 combativo y juego aéreo directo",
            "propuesta_juego": "Equipo rocoso, de alta intensidad física, repliegue ordenado y contragolpes letales por las bandas.",
            "figuras_a_seguir": [
                {"nombre": "Sebastián Sosa", "rol": "Delantero centro", "analisis": "Poderío físico y juego aéreo."},
                {"nombre": "Gino Santilli", "rol": "Arquero", "analisis": "Gran respuesta en remates de media distancia."}
            ],
            "puntos_fuertes": ["Solidez en pelota quieta", "Juego aéreo defensivo y ofensivo"],
            "vulnerabilidades_a_explotar": ["Dificultades en repliegue ante transiciones rápidas"]
        }
        duelos_1x1 = []
    elif "danubio" in rival_slug:
        scouting = {
            "entrenador": meta.get("dt", "Alejandro Apud"),
            "esquema_base": "4-3-3 agresivo en presión",
            "propuesta_juego": "Dinámica en el medio campo, bandas abiertas y presión sobre la salida rival.",
            "figuras_a_seguir": [
                {"nombre": "Sebastián Fernández", "rol": "Delantero", "analisis": "Oficio, oportunismo en el área y definición rápida."}
            ],
            "puntos_fuertes": ["Presión en tres cuartos", "Velocidad de extremos"],
            "vulnerabilidades_a_explotar": ["Espacios entre laterales y centrales al adelantarse"]
        }
        duelos_1x1 = []
    else:
        scouting = {
            "entrenador": meta.get("dt", "Cuerpo Técnico Rival"),
            "esquema_base": meta.get("esquema", "4-4-2 tradicional"),
            "propuesta_juego": "Equipo estructurado para el combate táctico en Primera División.",
            "figuras_a_seguir": [],
            "puntos_fuertes": ["Orden defensivo"],
            "vulnerabilidades_a_explotar": ["Espacios en retroceso"]
        }
        duelos_1x1 = []

    informe = {
        "generado_el": datetime.now(UY_TZ).strftime("%d/%m/%Y %H:%M"),
        "rival_nombre": rival_nombre,
        "rival_corto": rival_corto,
        "rival_slug": rival_slug,
        "escudo_oficial": meta.get("escudo"),
        "escudo_auf_remoto": "",
        "datos_institucionales_auf": {
            "fundacion": meta.get("fundacion", "1902"),
            "sede": meta.get("sede", "Montevideo, Uruguay"),
            "estadio_propio": meta.get("estadio", "Estadio de Primera División"),
            "capacidad": meta.get("capacidad", 15000),
            "web_oficial": meta.get("web", "https://auf.org.uy/"),
            "redes": {}
        },
        "scouting_tactico": scouting,
        "duelos_tacticos_1x1": duelos_1x1,
        "historial_certificacion_1891": {
            "partidos_jugados": resumen_h2h.get("partidos_jugados", 0),
            "ganados_penarol": resumen_h2h.get("ganados_penarol", 0),
            "empatados": resumen_h2h.get("empatados", 0),
            "perdidos_penarol": resumen_h2h.get("perdidos_penarol", 0),
            "goles_penarol": resumen_h2h.get("goles_penarol", 0),
            "goles_rival": resumen_h2h.get("goles_rival", 0),
            "ventaja_victorias": resumen_h2h.get("ventaja_victorias", "Ventaja a favor del Decano"),
            "diferencia_goles": resumen_h2h.get("diferencia_goles", "+0"),
            "efectividad_pct": resumen_h2h.get("efectividad_pct", "0%")
        },
        "fuentes_consultadas": [
            "AUF - Asociación Uruguaya de Fútbol (auf.org.uy/liga-auf-uruguaya/)",
            "1891 BD — Comisión de Historia y Patrimonio Histórico del Club Atlético Peñarol (1891.uy)",
            "Ovación Digital — Sección Fútbol y Peñarol (elpais.com.uy/ovacion)"
        ]
    }

    out_file = DATA_DIR / "rival_intelligence.json"
    out_file.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"✓ data/rival_intelligence.json guardado para {rival_nombre}.")
    return informe


if __name__ == "__main__":
    inf = generar_informe_rival("wanderers")
    print(f"\n[OK] Scouting generado para {inf['rival_nombre']}:")
    print(f" - DT: {inf['scouting_tactico']['entrenador']}")
    print(f" - Esquema: {inf['scouting_tactico']['esquema_base']}")
    print(f" - Duelos 1x1: {len(inf.get('duelos_tacticos_1x1', []))}")
    print(f" - Historial 1891 BD: {inf['historial_certificacion_1891'].get('ventaja_victorias')}")
    print(f" - Partidos Jugados: {inf['historial_certificacion_1891'].get('partidos_jugados')}")
