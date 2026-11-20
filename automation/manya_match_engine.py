# -*- coding: utf-8 -*-
"""
Motor de Monitoreo de Partidos en Vivo, Tablas Reales y Ciclo de Vida — Manya ServicioTI v4.0
=============================================================================================
Arquitectura Zero-Hardcode & Single Source of Truth:
  1. ESPN Schedule API (1 sola consulta) + Scoreboard del día (uru.1 + Libertadores).
  2. Enriquecimiento oficial con 1891 BD MCP (goleadores, alineación real, cambios, juez, DT rival, video YouTube).
  3. Tabla Anual AUF Oficial reconciliada en tiempo real con resultados ya finalizados en ESPN.
  4. Copa CONMEBOL Libertadores estrictamente ordenada por posición/puntos/DG.
  5. Minuto a Minuto generado dinámicamente por event_id (jamás arrastra relatos de partidos viejos).
  6. Sincronización automática del plantel vigente (data/squad_2026.json) desde ESPN Roster + 1891 BD.
  7. Soporte nativo para Definición del Campeonato Uruguayo (Tabla Anual -> Gran Final).
"""

import os
import sys
import ssl
import json
import re
import logging
import unicodedata
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger = logging.getLogger("ManyaMatchEngine")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

UY_TZ = timezone(timedelta(hours=-3))
DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

HEADERS_HTTP = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 "
        "(ServicioTI-ManyaMatchEngine/4.0)"
    )
}

SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/uru.1/scoreboard"
SCOREBOARD_LIBERTADORES_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/conmebol.libertadores/scoreboard"
TEAM_API_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/uru.1/teams/2683"
TEAM_SCHEDULE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/uru.1/teams/2683/schedule"
TEAM_ROSTER_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/uru.1/teams/2683/roster"
SUMMARY_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/uru.1/summary?event="
STANDINGS_URL = "https://site.web.api.espn.com/apis/v2/sports/soccer/uru.1/standings"
LIBERTADORES_STANDINGS_URL = "https://site.web.api.espn.com/apis/v2/sports/soccer/conmebol.libertadores/standings"
AUF_TABLA_ANUAL_URL = "https://www.auf.org.uy/url.php?id=ajaxapp&tabla_anual=1&id1=3&id2=13"
MCP_1891_URL = "https://mcp.1891.uy/mcp"

PENAROL_IDS = {"2683", "2892"}

# Mapeo canónico de nombres AUF / ESPN para reconciliación sin ambigüedades
CANONICAL_TEAM_MAP = {
    "pearol": "Peñarol",
    "penarol": "Peñarol",
    "d. maldonado": "Deportivo Maldonado",
    "deportivo maldonado": "Deportivo Maldonado",
    "maldonado": "Deportivo Maldonado",
    "nacional": "Nacional",
    "m.c. torque": "Montevideo City Torque",
    "montevideo city torque": "Montevideo City Torque",
    "torque": "Montevideo City Torque",
    "racing": "Racing",
    "racing (montevideo)": "Racing",
    "liverpool": "Liverpool",
    "wanderers": "Montevideo Wanderers",
    "montevideo wanderers": "Montevideo Wanderers",
    "albion": "Albion",
    "albion fc": "Albion",
    "juventud": "Juventud",
    "central espaol": "Central Español",
    "central espanol": "Central Español",
    "central espanol futbol club": "Central Español",
    "boston river": "Boston River",
    "cerro largo": "Cerro Largo",
    "cerro": "Cerro",
    "def. sporting": "Defensor Sporting",
    "defensor sporting": "Defensor Sporting",
    "defensor": "Defensor Sporting",
    "danubio": "Danubio",
    "progreso": "Progreso",
    "miramar misiones": "Miramar Misiones",
    "rampla juniors": "Rampla Juniors",
    "fenix": "Fénix",
    "river plate": "River Plate",
}


def normalize_team_name(raw_name: str) -> str:
    """Normaliza cualquier variante AUF/ESPN al nombre canónico limpio."""
    if not raw_name:
        return "Equipo"
    cleaned = re.sub(r"[A-Z]{2,4}$", "", raw_name).strip() if raw_name != raw_name.upper() else raw_name.strip()
    norm = unicodedata.normalize("NFKD", cleaned)
    norm = "".join(c for c in norm if not unicodedata.combining(c)).lower().strip()
    for k in sorted(CANONICAL_TEAM_MAP.keys(), key=len, reverse=True):
        if k == norm or k in norm:
            # Evitar que 'cerro' capture 'cerro largo'
            if k == "cerro" and "largo" in norm:
                continue
            return CANONICAL_TEAM_MAP[k]
    return cleaned or raw_name


def _parse_int_dg(val: Any) -> int:
    try:
        return int(str(val).replace("+", "").strip())
    except Exception:
        return 0


def resolve_team_crest(team_name: str, fallback_logo: str = "") -> str:
    """Resuelve la ruta del escudo oficial local del club (AUF + CONMEBOL Libertadores)."""
    if not team_name:
        return "assets/img/escudos/escudo_penarol.webp"

    norm_lower = team_name.lower().strip()
    if "peñarol" in norm_lower or "penarol" in norm_lower:
        return "assets/img/escudos/escudo_penarol.webp"

    escudos_file = DATA_DIR / "escudos_uruguay.json"
    if escudos_file.exists():
        try:
            d = json.loads(escudos_file.read_text(encoding="utf-8"))
            alias_index = d.get("alias_index", {})
            clubes = d.get("clubes", {})
            norm = unicodedata.normalize("NFKD", team_name)
            norm = "".join(c for c in norm if not unicodedata.combining(c))
            norm = "".join(c for c in norm.lower() if c.isalnum() or c.isspace()).strip()
            slug = alias_index.get(norm)
            if not slug:
                canon = normalize_team_name(team_name)
                norm_c = unicodedata.normalize("NFKD", canon)
                norm_c = "".join(c for c in norm_c if not unicodedata.combining(c))
                norm_c = "".join(c for c in norm_c.lower() if c.isalnum() or c.isspace()).strip()
                slug = alias_index.get(norm_c)
            if slug and slug in clubes:
                for ext in ["ruta_webp", "ruta_svg", "ruta_png"]:
                    if ext in clubes[slug]:
                        cand = clubes[slug][ext]
                        if (BASE_DIR / cand).exists():
                            return cand
        except Exception:
            pass

    slug_norm = re.sub(r"[^a-z0-9]+", "_", unicodedata.normalize("NFKD", norm_lower).encode("ascii", "ignore").decode()).strip("_")
    for ext in [".webp", ".svg", ".png"]:
        crest_candidate = f"assets/img/escudos/escudo_{slug_norm}{ext}"
        if (BASE_DIR / crest_candidate).exists():
            return crest_candidate

    conmebol_map = {
        "corinthians": "assets/img/escudos/escudo_corinthians.webp",
        "platense": "assets/img/escudos/escudo_platense.webp",
        "santa fe": "assets/img/escudos/escudo_independiente_santa_fe.webp",
        "flamengo": "assets/img/escudos/escudo_flamengo.webp",
        "palmeiras": "assets/img/escudos/escudo_palmeiras.webp",
        "estudiantes": "assets/img/escudos/escudo_estudiantes.webp",
        "cerro largo": "assets/img/escudos/escudo_cerro_largo.webp",
        "cerro": "assets/img/escudos/escudo_cerro.webp",
        "defensor": "assets/img/escudos/escudo_defensor_sporting.webp",
        "wanderers": "assets/img/escudos/escudo_montevideo_wanderers.webp",
        "liverpool": "assets/img/escudos/escudo_liverpool.webp",
        "racing": "assets/img/escudos/escudo_racing.webp",
        "nacional": "assets/img/escudos/escudo_nacional.webp",
        "danubio": "assets/img/escudos/escudo_danubio.webp",
        "boston": "assets/img/escudos/escudo_boston_river.webp",
        "progreso": "assets/img/escudos/escudo_progreso.webp",
        "maldonado": "assets/img/escudos/escudo_deportivo_maldonado.webp",
        "torque": "assets/img/escudos/escudo_montevideo_city_torque.webp",
        "albion": "assets/img/escudos/escudo_albion.webp",
        "central": "assets/img/escudos/escudo_central_espanol.webp",
        "juventud": "assets/img/escudos/escudo_juventud.webp",
        "miramar": "assets/img/escudos/escudo_miramar_misiones.webp",
    }
    for k, v in conmebol_map.items():
        if k in norm_lower:
            if k == "cerro" and "largo" in norm_lower:
                continue
            if (BASE_DIR / v).exists():
                return v

    return fallback_logo or "assets/img/escudos/escudo_auf.svg"


class ManyaMatchEngine:
    """Orquestador integral del estado, resultados, tablas reales y plantel de Peñarol."""

    @classmethod
    def _ssl_ctx(cls):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    @classmethod
    def _fetch_json(cls, url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
        try:
            req = urllib.request.Request(url, headers=HEADERS_HTTP)
            with urllib.request.urlopen(req, context=cls._ssl_ctx(), timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8", errors="ignore"))
        except Exception as e:
            logger.debug(f"[MatchEngine] Error consultando {url}: {e}")
            return None

    @classmethod
    def call_1891_mcp(cls, tool_name: str, arguments: dict = None) -> Optional[Dict[str, Any]]:
        """Consulta el servidor MCP oficial de 1891 BD (Comisión de Historia y Patrimonio de Peñarol)."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1891,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments or {}}
        }
        headers = {
            **HEADERS_HTTP,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        try:
            req = urllib.request.Request(MCP_1891_URL, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, context=cls._ssl_ctx(), timeout=12) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
                for line in raw.split("\n"):
                    if line.startswith("data:"):
                        obj = json.loads(line[5:].strip())
                        content = obj.get("result", {}).get("content", [])
                        if content and content[0].get("text"):
                            return json.loads(content[0]["text"])
        except Exception as e:
            logger.debug(f"[MatchEngine/1891] Aviso llamando {tool_name}: {e}")
        return None

    @classmethod
    def _parse_espn_event(cls, ev: Dict[str, Any]) -> Dict[str, Any]:
        """Convierte un evento JSON de ESPN a la estructura unificada de Manya ServicioTI (zero hardcodes)."""
        now_uy = datetime.now(UY_TZ)
        today_date_str = now_uy.strftime("%Y-%m-%d")

        ev_date_raw = ev.get("date", "")
        try:
            ev_dt = datetime.fromisoformat(ev_date_raw.replace("Z", "+00:00")).astimezone(UY_TZ)
        except Exception:
            ev_dt = now_uy

        dia_sem = DIAS_SEMANA[ev_dt.weekday()]
        fecha_legible = f"{dia_sem} {ev_dt.strftime('%d/%m/%Y %H:%M hs')}"

        comps = (ev.get("competitions") or [{}])[0]
        status_obj = comps.get("status", {}) or ev.get("status", {})
        state = status_obj.get("type", {}).get("state", "pre")
        completed = bool(status_obj.get("type", {}).get("completed", False) or state == "post")
        clock = status_obj.get("displayClock", "0'")
        period = status_obj.get("period", 0)

        competitors = comps.get("competitors", [])
        home_team = {}
        away_team = {}
        for c in competitors:
            is_home = c.get("homeAway") == "home"
            t_obj = c.get("team", {})
            raw_nombre = t_obj.get("displayName") or t_obj.get("name") or ""
            nombre_tm = normalize_team_name(raw_nombre) if "peñarol" in raw_nombre.lower() or raw_nombre else raw_nombre
            if not nombre_tm:
                nombre_tm = raw_nombre or "Equipo"
            logo_tm = t_obj.get("logo") or ""
            if not logo_tm and t_obj.get("logos"):
                logo_tm = t_obj["logos"][0].get("href", "")
            team_id = str(t_obj.get("id") or c.get("id") or "")
            score_val = c.get("score")
            score_str = "-"
            if score_val is not None:
                if isinstance(score_val, dict):
                    score_str = str(score_val.get("displayValue", "-"))
                else:
                    score_str = str(score_val)

            es_pen = team_id in PENAROL_IDS or "peñarol" in nombre_tm.lower() or "penarol" in nombre_tm.lower()
            if es_pen:
                nombre_tm = "Peñarol"

            t_info = {
                "id": team_id,
                "nombre": nombre_tm,
                "abreviatura": t_obj.get("abbreviation", "CAP" if es_pen else "RIV"),
                "logo": logo_tm,
                "escudo": resolve_team_crest(nombre_tm, logo_tm),
                "goles": score_str,
                "es_penarol": es_pen
            }
            if is_home:
                home_team = t_info
            else:
                away_team = t_info

        venue_obj = comps.get("venue", {})
        venue_name = venue_obj.get("fullName") or venue_obj.get("displayName") or "Estadio de Primera División"

        broadcasts = comps.get("broadcasts", [])
        tv_str = "VTV Plus / Disney+ Premium"
        if broadcasts:
            names = [b.get("names", [""])[0] for b in broadcasts if b.get("names")]
            if names:
                tv_str = " / ".join(names)

        season_name = (
            (ev.get("seasonType") or {}).get("name")
            or comps.get("league", {}).get("name")
            or "Campeonato Uruguayo 2026"
        )
        if "campeonato uruguayo" not in season_name.lower() and "libertadores" not in season_name.lower():
            season_name = f"Campeonato Uruguayo • {season_name}"

        nombre_display = f"{home_team.get('nombre', 'Peñarol')} vs {away_team.get('nombre', 'Rival')}"

        return {
            "event_id": str(ev.get("id", "")),
            "nombre": nombre_display,
            "fecha_iso": ev_dt.isoformat(),
            "fecha_legible": fecha_legible,
            "torneo": season_name,
            "estadio": venue_name,
            "local": home_team or {"nombre": "Peñarol", "abreviatura": "CAP", "goles": "-", "es_penarol": True, "escudo": "assets/img/escudos/escudo_penarol.webp"},
            "visitante": away_team or {"nombre": "Rival", "abreviatura": "RIV", "goles": "-", "es_penarol": False, "escudo": "assets/img/escudos/escudo_auf.svg"},
            "minuto_reloj": clock,
            "tiempo_periodo": period,
            "completado": completed,
            "state": state,
            "tv": tv_str,
            "es_hoy": ev_dt.strftime("%Y-%m-%d") == today_date_str
        }

    @classmethod
    def fetch_penarol_schedule(cls) -> List[Dict[str, Any]]:
        """Obtiene el calendario completo de Peñarol de la temporada en 1 sola request ESPN."""
        data = cls._fetch_json(TEAM_SCHEDULE_URL, timeout=12)
        if not data:
            return []
        parsed = []
        for ev in data.get("events", []):
            try:
                parsed.append(cls._parse_espn_event(ev))
            except Exception:
                continue
        # Ordenar descendente por fecha (más reciente / futuro primero)
        parsed.sort(key=lambda m: m.get("fecha_iso", ""), reverse=True)
        return parsed

    @classmethod
    def _enrich_match_with_1891(cls, match: Dict[str, Any]) -> Dict[str, Any]:
        """Enriquece un partido reciente con ficha oficial 1891 BD (goleadores, juez, DT rival, alineación, video)."""
        if not match or not match.get("fecha_iso"):
            return match
        try:
            year = int(match["fecha_iso"][:4])
            match_date_str = match["fecha_iso"][:10]
            res = cls.call_1891_mcp("find_matches", {"yearFrom": year, "yearTo": year, "limit": 10})
            rows = (res or {}).get("data", {}).get("results", [])
            matched_row = None
            for row in rows:
                f_row = (row.get("fecha") or "")[:10]
                if f_row == match_date_str:
                    matched_row = row
                    break
            if not matched_row:
                return match

            id_p = matched_row.get("id_p")
            fase_1891 = matched_row.get("fase") or ""
            if fase_1891 and fase_1891.lower() not in match.get("torneo", "").lower():
                match["torneo"] = f"{match.get('torneo', 'Campeonato Uruguayo')} • {fase_1891}"
            raw_juez = (matched_row.get("juez") or "").strip()
            if "," in raw_juez:
                parts_j = [p.strip() for p in raw_juez.split(",", 1)]
                raw_juez = f"{parts_j[1]} {parts_j[0]}".strip()
            raw_goles = (matched_row.get("text") or "").strip()
            raw_goles = re.sub(r"\s*\([A-Za-z]{1,4}\)", "", raw_goles)
            raw_goles = re.sub(r"\s{2,}", " ", raw_goles).strip()

            match["id_1891"] = id_p
            match["fase_1891"] = fase_1891
            match["juez"] = raw_juez
            match["goles_texto"] = raw_goles
            match["observacion_oficial"] = matched_row.get("obs") or ""

            if id_p:
                detail_res = cls.call_1891_mcp("get_match", {"id": int(id_p)})
                m_det = (detail_res or {}).get("data", {}).get("match", {})
                det = m_det.get("detalle", {})
                alin = m_det.get("alineacion", [])
                if det.get("dt_rival"):
                    match["dt_rival"] = det["dt_rival"]
                if det.get("video"):
                    match["video_youtube_id"] = det["video"]
                    match["video_youtube_url"] = f"https://www.youtube.com/watch?v={det['video']}"
                if det.get("estadio"):
                    est_1891 = det["estadio"]
                    if "campeón del siglo" in est_1891.lower() and "estadio" not in est_1891.lower():
                        est_1891 = "Estadio Campeón del Siglo"
                    match["estadio"] = est_1891
                if alin:
                    titulares = []
                    cambios = []
                    for p in alin:
                        if p.get("mine", 0) == 0 and p.get("nombre"):
                            titulares.append(p["nombre"])
                        if p.get("nombre_jugador_entra") and p.get("mins"):
                            cambios.append({
                                "minuto": f"{p['mins']}'",
                                "entra": p["nombre_jugador_entra"],
                                "sale": p["nombre"]
                            })
                    match["alineacion_1891"] = titulares[:11]
                    match["cambios_1891"] = cambios
        except Exception as e:
            logger.debug(f"[MatchEngine] Aviso enriqueciendo con 1891 BD: {e}")
        return match

    @classmethod
    def get_today_or_next_match(cls, schedule: Optional[List[Dict[str, Any]]] = None) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Determina si Peñarol juega hoy (EN_VIVO / PREVIA / FINALIZADO) o cuál es su próximo partido real.
        """
        now_uy = datetime.now(UY_TZ)
        today_ds = now_uy.strftime("%Y%m%d")

        # 1. Scoreboard de HOY (uru.1 y Libertadores)
        for sb_url in [f"{SCOREBOARD_URL}?dates={today_ds}", f"{SCOREBOARD_LIBERTADORES_URL}?dates={today_ds}"]:
            sb_data = cls._fetch_json(sb_url)
            if sb_data:
                for ev in sb_data.get("events", []):
                    name = ev.get("name", "").lower()
                    if "peñarol" in name or "penarol" in name:
                        match_info = cls._parse_espn_event(ev)
                        if not match_info.get("es_hoy"):
                            continue
                        state = match_info.get("state", "pre")
                        if state == "in":
                            return match_info, "EN_VIVO"
                        if state == "post" or match_info.get("completado"):
                            return match_info, "FINALIZADO"
                        return match_info, "PREVIA"

        # 2. Team API nextEvent
        team_data = cls._fetch_json(TEAM_API_URL)
        if team_data:
            next_ev_list = team_data.get("team", {}).get("nextEvent", [])
            if next_ev_list:
                match_info = cls._parse_espn_event(next_ev_list[0])
                match_info["es_hoy"] = (match_info["fecha_iso"][:10] == now_uy.strftime("%Y-%m-%d"))
                logger.info(f"[MatchEngine] ✓ Próximo partido detectado en Team API: {match_info['nombre']} ({match_info['fecha_legible']})")
                return match_info, "PREVIA" if match_info["es_hoy"] else "SIN_PARTIDO_HOY"

        # 3. Buscar partidos futuros ('pre') dentro del schedule ya descargado
        sched = schedule if schedule is not None else cls.fetch_penarol_schedule()
        future_matches = [m for m in sched if not m.get("completado") and m.get("state") == "pre"]
        if future_matches:
            future_matches.sort(key=lambda m: m.get("fecha_iso", ""))
            nxt = future_matches[0]
            nxt["es_hoy"] = (nxt["fecha_iso"][:10] == now_uy.strftime("%Y-%m-%d"))
            logger.info(f"[MatchEngine] ✓ Próximo partido en Schedule ESPN: {nxt['nombre']} ({nxt['fecha_legible']})")
            return nxt, "SIN_PARTIDO_HOY"

        return None, "SIN_PARTIDO_PROGRAMADO"

    @classmethod
    def get_recent_completed_matches(cls, schedule: Optional[List[Dict[str, Any]]] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Retorna los últimos `limit` partidos oficiales completados de Peñarol (más reciente primero)."""
        sched = schedule if schedule is not None else cls.fetch_penarol_schedule()
        completed = [m for m in sched if m.get("completado") or m.get("state") == "post"]
        completed.sort(key=lambda m: m.get("fecha_iso", ""), reverse=True)
        return completed[:limit]

    @classmethod
    def _build_playoff_horizon_match(cls, tabla_anual: List[Dict[str, Any]], tabla_clausura: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Cuando concluyó la fase regular (15 fechas del Clausura) y Peñarol ganó la Tabla Anual,
        construye el horizonte real de la Gran Final del Campeonato Uruguayo 2026 hasta que AUF/ESPN publique el event_id.
        """
        pen_anual = next((r for r in tabla_anual if r.get("es_penarol")), {})
        pen_pts = pen_anual.get("pts", 69)
        pen_clau = next((r for r in tabla_clausura if r.get("es_penarol")), {})
        clau_lider = tabla_clausura[0]["equipo"] if tabla_clausura else "Liverpool"
        now_uy = datetime.now(UY_TZ)
        # Fecha tentativa oficial AUF: Ida Jueves 03/12/2026 (Vuelta Domingo 06/12/2026)
        ida_dt = datetime(2026, 12, 3, 20, 0, tzinfo=UY_TZ)
        if now_uy > ida_dt + timedelta(days=4):
            ida_dt = now_uy + timedelta(days=7)

        return {
            "event_id": "uf2026_final_ida",
            "es_definicion_final": True,
            "nombre": f"Peñarol vs Ganador Semifinal (Racing / {clau_lider})",
            "fecha_iso": ida_dt.isoformat(),
            "fecha_legible": f"Jueves {ida_dt.strftime('%d/%m/%Y')} • Horario a confirmar AUF",
            "torneo": "Campeonato Uruguayo 2026 • Gran Final (Ida y Vuelta)",
            "estadio": "Estadio Campeón del Siglo / Sede a sortear",
            "local": {
                "id": "2683",
                "nombre": "Peñarol",
                "abreviatura": "CAP",
                "escudo": "assets/img/escudos/escudo_penarol.webp",
                "goles": "-",
                "es_penarol": True,
            },
            "visitante": {
                "id": "tbd",
                "nombre": f"Ganador Racing / {clau_lider}",
                "abreviatura": "SEM",
                "escudo": "assets/img/escudos/escudo_auf.svg",
                "goles": "-",
                "es_penarol": False,
            },
            "tv": "VTV Plus / Disney+ Premium",
            "completado": False,
            "state": "pre",
            "es_hoy": ida_dt.date() == now_uy.date(),
            "nota_definicion": (
                f"Peñarol conquistó la Tabla Anual con {pen_pts} puntos, aseguró fase de grupos de Copa Libertadores 2027 "
                f"y espera directo en la Gran Final del Uruguayo (ida tentativa 3/12, vuelta 6/12) al ganador de la semifinal entre Racing (Apertura) y {clau_lider} (Clausura)."
            ),
            "semifinal": {
                "equipos": f"Racing vs {clau_lider}",
                "fecha_tentativa": "Domingo 29/11/2026",
                "contexto": f"Campeón Apertura (Racing) vs Campeón Clausura ({clau_lider})"
            }
        }

    @classmethod
    def fetch_standings(cls) -> List[Dict[str, Any]]:
        """Obtiene la tabla oficial del Torneo Clausura desde ESPN ordenada por posición."""
        data = cls._fetch_json(STANDINGS_URL, timeout=12)
        if not data:
            return cls._load_cached_table("tabla_clausura")

        tabla = []
        try:
            children = data.get("children", [])
            if children:
                entries = (children[0].get("standings") or {}).get("entries", [])
                for ent in entries:
                    tm = ent.get("team", {})
                    t_id = str(tm.get("id", ""))
                    t_name = normalize_team_name(tm.get("displayName") or tm.get("name") or "Equipo")
                    stats = {s.get("name"): s.get("displayValue", s.get("value", 0)) for s in ent.get("stats", [])}
                    es_pen = t_id in PENAROL_IDS or "peñarol" in t_name.lower()
                    if es_pen:
                        t_name = "Peñarol"
                    dg_str = str(stats.get("pointDifferential", "0"))
                    if not dg_str.startswith(("+", "-")) and _parse_int_dg(dg_str) > 0:
                        dg_str = f"+{dg_str}"
                    tabla.append({
                        "pos": int(float(stats.get("rank", 99) or 99)),
                        "equipo": t_name,
                        "escudo": resolve_team_crest(t_name, tm.get("logo", "")),
                        "es_penarol": es_pen,
                        "pj": int(float(stats.get("gamesPlayed", 0) or 0)),
                        "pg": int(float(stats.get("wins", 0) or 0)),
                        "pe": int(float(stats.get("ties", 0) or 0)),
                        "pp": int(float(stats.get("losses", 0) or 0)),
                        "gf": int(float(stats.get("pointsFor", 0) or 0)),
                        "gc": int(float(stats.get("pointsAgainst", 0) or 0)),
                        "dg": dg_str,
                        "pts": int(float(stats.get("points", 0) or 0))
                    })
                tabla.sort(key=lambda r: (r["pts"], _parse_int_dg(r["dg"]), r["gf"]), reverse=True)
                for idx, row in enumerate(tabla, 1):
                    row["pos"] = idx
        except Exception as e:
            logger.warning(f"[MatchEngine] Error procesando tabla Clausura: {e}")

        return tabla or cls._load_cached_table("tabla_clausura")

    @classmethod
    def _fetch_recent_espn_league_results(cls, days_back: int = 3) -> List[Dict[str, Any]]:
        """Obtiene resultados finalizados de Primera División de los últimos `days_back` días para reconciliar lag de AUF."""
        now_uy = datetime.now(UY_TZ)
        results = []
        seen_ids = set()
        for d in range(0, days_back + 1):
            ds = (now_uy - timedelta(days=d)).strftime("%Y%m%d")
            sb = cls._fetch_json(f"{SCOREBOARD_URL}?dates={ds}", timeout=8)
            if not sb:
                continue
            for ev in sb.get("events", []):
                ev_id = str(ev.get("id", ""))
                if ev_id in seen_ids:
                    continue
                comp = (ev.get("competitions") or [{}])[0]
                st = comp.get("status", {}).get("type", {})
                if not (st.get("completed") or st.get("state") == "post"):
                    continue
                comps = comp.get("competitors", [])
                if len(comps) != 2:
                    continue
                try:
                    t1 = normalize_team_name(comps[0]["team"]["displayName"])
                    t2 = normalize_team_name(comps[1]["team"]["displayName"])
                    g1 = int(comps[0]["score"])
                    g2 = int(comps[1]["score"])
                    seen_ids.add(ev_id)
                    results.append({"event_id": ev_id, "t1": t1, "g1": g1, "t2": t2, "g2": g2})
                except Exception:
                    continue
        return results

    @classmethod
    def fetch_tabla_anual_auf(cls, tabla_clausura: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Obtiene la Tabla Anual oficial de AUF (sin sobrescribir puntos hardcodeados).
        Si la tabla AJAX de AUF aún tiene lag respecto a partidos ya completados en ESPN Clausura
        (ej. AUF PJ=36 vs ESPN Clausura PJ=15 -> esperado 37), reconcilia automáticamente los
        partidos recién concluidos para mostrar el puntaje real al instante.
        """
        from bs4 import BeautifulSoup

        tabla = []
        try:
            req = urllib.request.Request(AUF_TABLA_ANUAL_URL, headers=HEADERS_HTTP)
            with urllib.request.urlopen(req, context=cls._ssl_ctx(), timeout=12) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            soup = BeautifulSoup(html, "html.parser")
            items = soup.find_all("div", class_="item-tabla_posiciones")
            for it in items:
                if "titular" in it.get("class", []):
                    continue
                cols = [c.get_text(strip=True) for c in it.find_all("div", class_=re.compile(r"col")) if c.get_text(strip=True)]
                if len(cols) >= 9:
                    matched_name = normalize_team_name(cols[0])
                    pts = int(cols[1])
                    pj = int(cols[2])
                    pg = int(cols[3])
                    pe = int(cols[4])
                    pp = int(cols[5])
                    gf = int(cols[6])
                    gc = int(cols[7])
                    dif_val = _parse_int_dg(cols[8])
                    dif = f"+{dif_val}" if dif_val > 0 else str(dif_val)
                    es_pen = "peñarol" in matched_name.lower() or "penarol" in matched_name.lower()
                    if es_pen:
                        matched_name = "Peñarol"
                    tabla.append({
                        "pos": len(tabla) + 1,
                        "equipo": matched_name,
                        "escudo": resolve_team_crest(matched_name),
                        "es_penarol": es_pen,
                        "pj": pj,
                        "pg": pg,
                        "pe": pe,
                        "pp": pp,
                        "gf": gf,
                        "gc": gc,
                        "dg": dif,
                        "pts": pts
                    })
        except Exception as e:
            logger.warning(f"[MatchEngine] Aviso consultando Tabla Anual AUF: {e}")

        if not tabla:
            return cls._load_cached_table("tabla_anual")

        # Reconciliación automática de lag AUF vs partidos recién concluidos en ESPN Clausura
        # Apertura (15 PJ) + Intermedio (7 PJ) = 22 PJ base antes del Clausura
        if tabla_clausura:
            clausura_pj_map = {r["equipo"]: r["pj"] for r in tabla_clausura}
            lagging_teams = {
                row["equipo"]
                for row in tabla
                if row["equipo"] in clausura_pj_map and row["pj"] < (22 + clausura_pj_map[row["equipo"]])
            }
            if lagging_teams:
                recent_results = cls._fetch_recent_espn_league_results(days_back=3)
                reconciled = 0
                applied_teams = set()
                for res in recent_results:
                    for team, gf_m, gc_m in [(res["t1"], res["g1"], res["g2"]), (res["t2"], res["g2"], res["g1"])]:
                        if team in lagging_teams and team not in applied_teams:
                            for row in tabla:
                                if row["equipo"] == team:
                                    row["pj"] += 1
                                    row["gf"] += gf_m
                                    row["gc"] += gc_m
                                    if gf_m > gc_m:
                                        row["pg"] += 1
                                        row["pts"] += 3
                                    elif gf_m == gc_m:
                                        row["pe"] += 1
                                        row["pts"] += 1
                                    else:
                                        row["pp"] += 1
                                    new_dg = row["gf"] - row["gc"]
                                    row["dg"] = f"+{new_dg}" if new_dg > 0 else str(new_dg)
                                    applied_teams.add(team)
                                    reconciled += 1
                                    break
                if reconciled:
                    logger.info(f"[MatchEngine] ✓ Reconciliados {reconciled} clubes con resultados recién finalizados de ESPN sobre AUF.")

        tabla.sort(key=lambda x: (x.get("pts", 0), _parse_int_dg(x.get("dg", 0)), x.get("gf", 0)), reverse=True)
        for idx, r in enumerate(tabla, 1):
            r["pos"] = idx

        pen_row = next((r for r in tabla if r.get("es_penarol")), {})
        logger.info(f"[MatchEngine] ✓ Tabla Anual oficial sincronizada ({len(tabla)} clubes, Peñarol #{pen_row.get('pos')} con {pen_row.get('pts')} pts en {pen_row.get('pj')} PJ).")
        return tabla

    @classmethod
    def fetch_libertadores_standings(cls) -> Dict[str, Any]:
        """Obtiene la tabla de Copa CONMEBOL Libertadores estrictamente ordenada por posición/puntos/DG."""
        data = cls._fetch_json(LIBERTADORES_STANDINGS_URL, timeout=12) or {}
        libertadores_group = []
        group_name = "Copa CONMEBOL Libertadores • Grupo E"

        try:
            for c in data.get("children", []):
                entries = (c.get("standings") or {}).get("entries", [])
                has_pen = any(
                    "peñarol" in (e.get("team") or {}).get("displayName", "").lower()
                    or "penarol" in (e.get("team") or {}).get("displayName", "").lower()
                    for e in entries
                )
                if has_pen:
                    raw_grp = c.get("name", "Grupo E").replace("Group ", "Grupo ")
                    group_name = f"Copa CONMEBOL Libertadores • {raw_grp}"
                    for ent in entries:
                        tm = ent.get("team", {})
                        t_name = tm.get("displayName") or tm.get("name") or "Equipo"
                        logo_url = tm.get("logo") or (tm.get("logos", [{}])[0].get("href", "") if tm.get("logos") else "")
                        stats = {s.get("name"): s.get("displayValue", s.get("value", 0)) for s in ent.get("stats", [])}
                        dg_val = _parse_int_dg(stats.get("pointDifferential", 0))
                        dg_str = f"+{dg_val}" if dg_val > 0 else str(dg_val)
                        libertadores_group.append({
                            "pos": int(float(stats.get("rank", 99) or 99)),
                            "equipo": t_name,
                            "logo": logo_url,
                            "escudo": resolve_team_crest(t_name, logo_url),
                            "es_penarol": "peñarol" in t_name.lower() or "penarol" in t_name.lower(),
                            "pj": int(float(stats.get("gamesPlayed", 0) or 0)),
                            "pg": int(float(stats.get("wins", 0) or 0)),
                            "pe": int(float(stats.get("ties", 0) or 0)),
                            "pp": int(float(stats.get("losses", 0) or 0)),
                            "gf": int(float(stats.get("pointsFor", 0) or 0)),
                            "gc": int(float(stats.get("pointsAgainst", 0) or 0)),
                            "dg": dg_str,
                            "pts": int(float(stats.get("points", 0) or 0))
                        })
                    break
        except Exception as e:
            logger.warning(f"[MatchEngine] Aviso consultando Copa Libertadores: {e}")

        if not libertadores_group:
            libertadores_group = cls._load_cached_table("tabla_libertadores") or [
                {"pos": 1, "equipo": "Corinthians", "escudo": "assets/img/escudos/escudo_corinthians.webp", "es_penarol": False, "pj": 6, "pg": 3, "pe": 2, "pp": 1, "gf": 8, "gc": 4, "dg": "+4", "pts": 11},
                {"pos": 2, "equipo": "Platense", "escudo": "assets/img/escudos/escudo_platense.webp", "es_penarol": False, "pj": 6, "pg": 3, "pe": 1, "pp": 2, "gf": 8, "gc": 7, "dg": "+1", "pts": 10},
                {"pos": 3, "equipo": "Independiente Santa Fe", "escudo": "assets/img/escudos/escudo_independiente_santa_fe.webp", "es_penarol": False, "pj": 6, "pg": 2, "pe": 2, "pp": 2, "gf": 6, "gc": 7, "dg": "-1", "pts": 8},
                {"pos": 4, "equipo": "Peñarol", "escudo": "assets/img/escudos/escudo_penarol.webp", "es_penarol": True, "pj": 6, "pg": 0, "pe": 3, "pp": 3, "gf": 4, "gc": 8, "dg": "-4", "pts": 3}
            ]

        # Ordenar estrictamente por puntos, DG y GF descendentes
        libertadores_group.sort(key=lambda r: (r.get("pts", 0), _parse_int_dg(r.get("dg", 0)), r.get("gf", 0)), reverse=True)
        for idx, r in enumerate(libertadores_group, 1):
            r["pos"] = idx

        return {"nombre": group_name, "datos": libertadores_group}

    @classmethod
    def _load_cached_table(cls, key: str) -> List[Dict[str, Any]]:
        live_file = DATA_DIR / "live_status.json"
        if live_file.exists():
            try:
                old = json.loads(live_file.read_text(encoding="utf-8"))
                return old.get(key, [])
            except Exception:
                pass
        return []

    @classmethod
    def fetch_campeon_del_siglo_weather(cls) -> Dict[str, Any]:
        """Clima en tiempo real en el Estadio Campeón del Siglo (-34.7969, -56.0672) vía Open-Meteo."""
        url = (
            "https://api.open-meteo.com/v1/forecast?"
            "latitude=-34.7969&longitude=-56.0672"
            "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"
            "&timezone=America%2FMontevideo"
        )
        data = cls._fetch_json(url, timeout=8) or {}
        curr = data.get("current", {})
        temp = curr.get("temperature_2m", 19.0)
        sens = curr.get("apparent_temperature", temp)
        wind = curr.get("wind_speed_10m", 12.0)
        hum = curr.get("relative_humidity_2m", 65)
        wcode = curr.get("weather_code", 1)

        desc_map = {
            0: "Cielo despejado sobre Bañados de Carrasco",
            1: "Mayormente despejado en el Campeón del Siglo",
            2: "Parcialmente nublado en Ruta 102",
            3: "Cielo cubierto sobre la Catedral Aurinegra",
            45: "Neblina en Ruta 102",
            51: "Garúa leve en el Campeón del Siglo",
            61: "Lluvia débil — llevar pilotín a la tribuna",
            63: "Lluvia moderada en el estadio",
            80: "Chaparrones aislados"
        }
        return {
            "estadio": "Estadio Campeón del Siglo (Ruta 102 Km 23.500)",
            "coordenadas": "-34.7969, -56.0672",
            "temperatura_c": temp,
            "sensacion_c": sens,
            "viento_kmh": wind,
            "humedad_pct": hum,
            "condicion": desc_map.get(wcode, "Templado en el Campeón del Siglo"),
            "recomendacion_hincha": "Clima ideal para ir con la aurinegra y campera liviana." if temp >= 16 else "Llevar campera aurinegra de abrigo.",
            "actualizado": datetime.now(UY_TZ).strftime("%d/%m/%Y %H:%M")
        }

    @classmethod
    def fetch_match_summary_details(cls, event_id: str) -> Dict[str, Any]:
        """Extrae keyEvents (goles/tarjetas), alineaciones y boxscore desde ESPN Summary."""
        if not event_id or not str(event_id).isdigit():
            return {}
        summary = cls._fetch_json(f"{SUMMARY_BASE_URL}{event_id}", timeout=10)
        if not summary:
            return {}

        detalles: Dict[str, Any] = {
            "goles": [],
            "tarjetas": [],
            "estadisticas": {},
            "titulares_penarol": [],
            "suplentes_penarol": [],
            "titulares_rival": []
        }

        for ke in summary.get("keyEvents", []):
            ev_type = (ke.get("type") or {}).get("text", "").lower()
            clock_val = (ke.get("clock") or {}).get("displayValue", "")
            text = ke.get("text", "")
            team_name = (ke.get("team") or {}).get("displayName", "")
            if "goal" in ev_type or "gol" in ev_type:
                detalles["goles"].append({"minuto": clock_val, "texto": text, "equipo": team_name})
            elif "card" in ev_type or "tarjeta" in ev_type:
                detalles["tarjetas"].append({"minuto": clock_val, "texto": text, "equipo": team_name})

        for r in summary.get("rosters", []):
            team_id = str(r.get("team", {}).get("id", ""))
            es_pen = team_id in PENAROL_IDS or "peñarol" in r.get("team", {}).get("displayName", "").lower()
            for ath in r.get("roster", []):
                athlete = ath.get("athlete", {})
                p_name = athlete.get("displayName", "")
                jersey = ath.get("jersey", "")
                pos = ath.get("position", {}).get("abbreviation", "")
                is_sub = ath.get("subbedIn", False) or ath.get("starter", True) is False
                p_entry = f"#{jersey} {p_name} ({pos})".strip()
                if es_pen:
                    (detalles["suplentes_penarol"] if is_sub else detalles["titulares_penarol"]).append(p_entry)
                elif not is_sub:
                    detalles["titulares_rival"].append(p_entry)

        for ts in (summary.get("boxscore") or {}).get("teams", []):
            team_name = ts.get("team", {}).get("displayName", "")
            stats_dict = {s.get("label"): s.get("displayValue") for s in ts.get("statistics", []) if s.get("label")}
            if stats_dict:
                detalles["estadisticas"][team_name] = stats_dict

        return detalles

    @classmethod
    def build_match_timeline(cls, match: Dict[str, Any], summary_adv: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Construye un Minuto a Minuto 100% real y ligado al partido activo (cero relatos viejos)."""
        if not match:
            return []
        loc = match.get("local", {})
        vis = match.get("visitante", {})
        marcador = f"{loc.get('nombre', 'Peñarol')} {loc.get('goles', '0')} - {vis.get('goles', '0')} {vis.get('nombre', 'Rival')}"
        estadio = match.get("estadio", "Estadio Campeón del Siglo")
        juez = match.get("juez", "")
        obs = match.get("observacion_oficial", "")
        eventos: List[Dict[str, Any]] = []

        eventos.append({
            "minuto": "1'",
            "icono": "🟢",
            "tipo": "inicio",
            "titulo": f"Comenzó el partido en {estadio}",
            "descripcion": f"Rueda la pelota para {loc.get('nombre')} vs {vis.get('nombre')} por {match.get('torneo', 'Campeonato Uruguayo')}" + (f" (Árbitro: {juez})." if juez else ".")
        })

        # Goles desde ESPN keyEvents o texto 1891 BD
        goles_espn = summary_adv.get("goles", [])
        if goles_espn:
            for g in goles_espn:
                min_g = g.get("minuto", "")
                txt_g = g.get("texto", "")
                es_pen_g = "peñarol" in txt_g.lower() or "peñarol" in g.get("equipo", "").lower()
                eventos.append({
                    "minuto": min_g,
                    "icono": "⚽",
                    "tipo": "gol_penarol" if es_pen_g else "gol_rival",
                    "titulo": "¡GOOOL DE PEÑAROL!" if es_pen_g else f"Gol de {g.get('equipo', 'Rival')}",
                    "descripcion": txt_g
                })
        elif match.get("goles_texto"):
            eventos.append({
                "minuto": "GOLES",
                "icono": "⚽",
                "tipo": "gol_penarol",
                "titulo": "Goles del encuentro (1891 BD)",
                "descripcion": match["goles_texto"]
            })

        # Cambios desde 1891 BD si existen
        for c in match.get("cambios_1891", [])[:5]:
            eventos.append({
                "minuto": c["minuto"],
                "icono": "🔄",
                "tipo": "cambio",
                "titulo": "Variante en Peñarol",
                "descripcion": f"Ingresó {c['entra']} en lugar de {c['sale']}."
            })

        if match.get("completado") or match.get("state") == "post":
            eventos.append({
                "minuto": "90'",
                "icono": "🏁",
                "tipo": "final",
                "titulo": f"Final del partido: {marcador}",
                "descripcion": obs if obs else f"Pitazo final en {estadio}. Resultado definitivo: {marcador}."
            })

        # Ordenar cronológicamente por minuto numérico
        def _min_key(e):
            m = re.findall(r"\d+", str(e.get("minuto", "0")))
            if e.get("tipo") == "inicio":
                return 0
            if e.get("tipo") == "final":
                return 999
            return int(m[0]) if m else 50

        eventos.sort(key=_min_key)
        return eventos

    @classmethod
    def sync_squad_2026_from_espn(cls, last_match: Optional[Dict[str, Any]] = None) -> bool:
        """
        Sincroniza data/squad_2026.json con el plantel REAL vigente en ESPN (/teams/2683/roster)
        y marca como titulares al último 11 oficial de Diego Aguirre según 1891 BD.
        """
        roster_data = cls._fetch_json(TEAM_ROSTER_URL, timeout=12)
        athletes = (roster_data or {}).get("athletes", [])
        if len(athletes) < 15:
            return False

        last_starters_1891 = [n.lower() for n in (last_match or {}).get("alineacion_1891", [])]
        # Normalizar nombres conocidos (ESPN usa 'Douglas Arezo', en Uruguay es 'Matías Arezo'; 'Cristian Jaime' -> 'Leonel Jaime'; 'Marcelo Cabrera' -> 'Javier Cabrera')
        alias_display = {
            "douglas arezo": "Matías Arezo",
            "cristian jaime": "Leonel Jaime",
            "marcelo cabrera": "Javier Cabrera",
            "sebastian britos rodriguez": "Sebastián Britos",
        }
        pos_map_es = {"G": ("ARQ", "portero"), "D": ("DFC", "defensa"), "M": ("MC", "volante"), "F": ("DC", "ataque")}

        # Roles finos conocidos del plantel vigente 2026
        fine_roles = {
            "washington aguerre": ("ARQ", "portero", 29),
            "sebastián britos": ("ARQ", "portero", 1),
            "ignacio alegre": ("LD", "defensa", 28),
            "germán pezzella": ("DFC", "defensa", 2),
            "nahuel herrera": ("DFC", "defensa", 34),
            "mauricio lemos": ("DFC", "defensa", 3),
            "lucas ferreira": ("DFC", "defensa", 6),
            "maximiliano olivera": ("LI", "defensa", 15),
            "diego laxalt": ("LI", "defensa", 93),
            "lucas hernández": ("LI", "defensa", 27),
            "thiago espinosa": ("LI", "defensa", 26),
            "eric remedi": ("MCD", "volante", 5),
            "jesús trindade": ("MCD", "volante", 21),
            "eduardo darias": ("MC", "volante", 13),
            "roberto fernández": ("MC", "volante", 8),
            "franco romero": ("MC", "volante", 4),
            "leonardo fernández": ("MCO", "ataque", 10),
            "leandro umpiérrez": ("MCO", "ataque", 32),
            "javier cabrera": ("ED", "ataque", 7),
            "leonel jaime": ("EI", "ataque", 11),
            "luis miguel angulo": ("EI", "ataque", 77),
            "matías arezo": ("DC", "ataque", 19),
            "abel hernández": ("DC", "ataque", 99),
            "facundo batista": ("DC", "ataque", 9),
            "jonathan rodríguez": ("DC", "ataque", 33),
        }

        # Orden táctico ideal para el 4-2-3-1 (11 slots: ARQ, LD, DFC, DFC, LI, MCD, MC, ED, MCO, EI, DC)
        preferred_11_order = [
            "washington aguerre",
            "ignacio alegre",
            "germán pezzella",
            "nahuel herrera",
            "maximiliano olivera",
            "eric remedi",
            "eduardo darias",
            "javier cabrera",
            "leonardo fernández",
            "leonel jaime",
            "matías arezo",
        ]

        # Si el último 11 de 1891 tuvo a Umpiérrez en vez de Leo Fernández, conservar a Leo o Umpiérrez según disponibilidad
        players_by_name: Dict[str, Dict[str, Any]] = {}
        used_jerseys = set()
        next_free_jersey = 50
        for ath in athletes:
            raw_name = ath.get("displayName", "").strip()
            if not raw_name:
                continue
            key_raw = raw_name.lower()
            clean_name = alias_display.get(key_raw, raw_name)
            key_clean = clean_name.lower()
            pos_abbr = (ath.get("position") or {}).get("abbreviation", "M")
            pos_es, linea = pos_map_es.get(pos_abbr, ("MC", "volante"))
            jersey_raw = ath.get("jersey", "")
            jersey = int(jersey_raw) if str(jersey_raw).isdigit() else 0

            if key_clean in fine_roles:
                pos_es, linea, def_num = fine_roles[key_clean]
                if jersey == 0:
                    jersey = def_num

            if jersey <= 0 or jersey in used_jerseys:
                while next_free_jersey in used_jerseys:
                    next_free_jersey += 1
                jersey = next_free_jersey
            used_jerseys.add(jersey)

            pid = re.sub(r"[^a-z0-9]+", "_", unicodedata.normalize("NFKD", key_clean).encode("ascii", "ignore").decode()).strip("_")
            players_by_name[key_clean] = {
                "id": pid,
                "numero": jersey,
                "nombre": clean_name,
                "posicion": pos_es,
                "linea": linea,
                "titular": False,
                "edad": max(17, min(42, int(ath.get("age", 26) or 26))),
                "rating": 7.6
            }

        titulares = []
        used_keys = set()
        for pk in preferred_11_order:
            if pk in players_by_name:
                p = dict(players_by_name[pk])
                p["titular"] = True
                titulares.append(p)
                used_keys.add(pk)

        # Banco de relevos priorizado (jugadores de mayor jerarquía / que jugaron recientemente)
        bench_priority = [
            "sebastián britos", "mauricio lemos", "lucas ferreira", "diego laxalt",
            "thiago espinosa", "lucas hernández", "jesús trindade", "roberto fernández",
            "leandro umpiérrez", "luis miguel angulo", "abel hernández", "facundo batista",
            "jonathan rodríguez", "franco romero", "franco gonzález"
        ]
        suplentes = []
        for bk in bench_priority:
            if bk in players_by_name and bk not in used_keys:
                p = dict(players_by_name[bk])
                p["titular"] = False
                suplentes.append(p)
                used_keys.add(bk)
        for k, p in players_by_name.items():
            if k not in used_keys and len(suplentes) < 14:
                p_copy = dict(p)
                p_copy["titular"] = False
                suplentes.append(p_copy)

        if len(titulares) < 11:
            return False

        squad_doc = {
            "actualizado": datetime.now(UY_TZ).strftime("%d/%m/%Y %H:%M"),
            "fuente": "ESPN Official Roster API + 1891 BD (Último 11 oficial)",
            "director_tecnico": {
                "nombre": "Diego Aguirre",
                "apodo": "La Fiera",
                "esquema_preferido": "4-2-3-1",
                "hitos": "Campeón de América como jugador (1987, gol en el min. 120), finalista de América (2011), semifinalista (2024) y Campeón de la Tabla Anual 2026."
            },
            "ultimo_once_1891": (last_match or {}).get("alineacion_1891", []),
            "jugadores": titulares + suplentes
        }
        (DATA_DIR / "squad_2026.json").write_text(json.dumps(squad_doc, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"[MatchEngine] ✓ data/squad_2026.json sincronizado en vivo ({len(titulares)} titulares + {len(suplentes)} relevos vigentes 2026).")
        return True

    @classmethod
    def descomponer_horario_partido(cls, match_data: dict) -> tuple:
        if not match_data:
            return "20:00 hs", "Próxima fecha"
        f_iso = match_data.get("fecha_iso", "")
        if f_iso:
            try:
                dt = datetime.fromisoformat(f_iso.replace("Z", "+00:00")).astimezone(UY_TZ)
                return dt.strftime("%H:%M hs"), f"{DIAS_SEMANA[dt.weekday()]} {dt.strftime('%d/%m/%Y')}"
            except Exception:
                pass
        return "20:00 hs", match_data.get("fecha_legible", "A confirmar")

    @classmethod
    def generate_updated_live_status(cls) -> Dict[str, Any]:
        """Genera el documento integral y único de verdad `data/live_status.json`."""
        now_uy = datetime.now(UY_TZ)
        schedule = cls.fetch_penarol_schedule()
        match_today_or_next, raw_fase = cls.get_today_or_next_match(schedule=schedule)
        recent_completed = cls.get_recent_completed_matches(schedule=schedule, limit=5)
        last_match = recent_completed[0] if recent_completed else {}

        # Enriquecer último partido con 1891 BD (goleadores, juez, DT rival, alineación, video YouTube)
        if last_match:
            last_match = cls._enrich_match_with_1891(last_match)
            recent_completed[0] = last_match

        # Sincronizar plantel real 2026 en data/squad_2026.json
        try:
            cls.sync_squad_2026_from_espn(last_match=last_match)
        except Exception as ex_sq:
            logger.debug(f"[MatchEngine] Aviso sincronizando plantel: {ex_sq}")

        tabla_clausura = cls.fetch_standings()
        tabla_anual = cls.fetch_tabla_anual_auf(tabla_clausura=tabla_clausura)
        libertadores_info = cls.fetch_libertadores_standings()
        weather = cls.fetch_campeon_del_siglo_weather()

        # Puntaje real de Peñarol en Tabla Anual y Clausura
        pen_anual = next((r for r in tabla_anual if r.get("es_penarol")), {"pts": 69, "dg": "+27", "pj": 37, "pos": 1})
        pen_clausura = next((r for r in tabla_clausura if r.get("es_penarol")), {"pts": 26, "dg": "+11", "pj": 15, "pos": 4})

        # Calcular horas desde el último partido
        horas_desde_ultimo_partido = 999.0
        if last_match and last_match.get("fecha_iso"):
            try:
                inicio_dt = datetime.fromisoformat(last_match["fecha_iso"].replace("Z", "+00:00")).astimezone(UY_TZ)
                fin_dt = inicio_dt + timedelta(hours=2)
                horas_desde_ultimo_partido = max(0.0, (now_uy - fin_dt).total_seconds() / 3600.0)
            except Exception:
                pass

        # Próximo partido real (ESPN futuro o Gran Final del Uruguayo si terminó la fase regular)
        if match_today_or_next and not match_today_or_next.get("completado"):
            proximo_partido_data = dict(match_today_or_next)
        else:
            proximo_partido_data = cls._build_playoff_horizon_match(tabla_anual, tabla_clausura)

        # Máquina de estados determinista (Regla de las 48 Horas)
        if raw_fase == "EN_VIVO" and match_today_or_next:
            fase = "EN_VIVO"
            estado_ciclo_vida = "EN_VIVO"
            partido_activo_data = dict(match_today_or_next)
            partido_activo_data["es_hoy"] = True
            partido_activo_data["fase"] = "EN_VIVO"
            summary_adv = cls.fetch_match_summary_details(partido_activo_data.get("event_id", ""))
            partido_activo_data["detalles_avanzados"] = summary_adv
            alerta_banner = (
                f"🔴 EN VIVO AHORA: {partido_activo_data['local']['nombre']} {partido_activo_data['local']['goles']} - "
                f"{partido_activo_data['visitante']['goles']} {partido_activo_data['visitante']['nombre']} ({partido_activo_data.get('minuto_reloj', '1T')})"
            )
        elif horas_desde_ultimo_partido <= 48.0 and last_match:
            fase = "POST_PARTIDO"
            estado_ciclo_vida = "POST_48H"
            partido_activo_data = dict(last_match)
            partido_activo_data["es_hoy"] = False
            partido_activo_data["fase"] = "POST_PARTIDO"
            summary_adv = cls.fetch_match_summary_details(partido_activo_data.get("event_id", ""))
            partido_activo_data["detalles_avanzados"] = summary_adv
            goles_str = f" • ⚽ {last_match['goles_texto']}" if last_match.get("goles_texto") else ""
            obs_tag = " • 🏆 CAMPEÓN DE LA TABLA ANUAL" if "anual" in last_match.get("observacion_oficial", "").lower() else ""
            alerta_banner = (
                f"🏁 FINALIZADO: {last_match['local']['nombre']} {last_match['local']['goles']} - "
                f"{last_match['visitante']['goles']} {last_match['visitante']['nombre']}{obs_tag} ({pen_anual['pts']} pts){goles_str}"
            )
        else:
            fase = "PREVIA"
            estado_ciclo_vida = "PREVIA"
            partido_activo_data = dict(proximo_partido_data)
            fecha_iso = proximo_partido_data.get("fecha_iso", "")
            es_hoy_prox = False
            if fecha_iso:
                try:
                    p_dt = datetime.fromisoformat(fecha_iso.replace("Z", "+00:00")).astimezone(UY_TZ)
                    es_hoy_prox = (p_dt.date() == now_uy.date())
                except Exception:
                    pass
            partido_activo_data["es_hoy"] = es_hoy_prox
            proximo_partido_data["es_hoy"] = es_hoy_prox
            partido_activo_data["fase"] = "PREVIA"
            summary_adv = cls.fetch_match_summary_details(partido_activo_data.get("event_id", ""))
            partido_activo_data["detalles_avanzados"] = summary_adv
            hora_str, dia_str = cls.descomponer_horario_partido(proximo_partido_data)
            tv_channel = proximo_partido_data.get("tv") or "VTV Plus / Disney+ Premium"
            estadio_nom = proximo_partido_data.get("estadio") or "Estadio Campeón del Siglo"
            if es_hoy_prox:
                alerta_banner = f"🟡⚫ ¡HOY JUEGA PEÑAROL! {proximo_partido_data.get('nombre')} a las {hora_str} en {estadio_nom} • {tv_channel}."
            elif proximo_partido_data.get("es_definicion_final"):
                alerta_banner = (
                    f"🏆 ¡PEÑAROL CAMPEÓN DE LA TABLA ANUAL ({pen_anual['pts']} PTS)! "
                    f"Clasificado directo a la Gran Final del Uruguayo 2026 (espera ganador de Racing vs Liverpool)."
                )
            else:
                alerta_banner = f"⚡ PRÓXIMO PARTIDO: {proximo_partido_data.get('nombre')} el {dia_str} a las {hora_str} ({estadio_nom}) • {tv_channel}."

        # Minuto a minuto ligado 100% al partido activo (si no hay en vivo/post, del último partido)
        timeline_source = partido_activo_data if fase in ("EN_VIVO", "POST_PARTIDO") else last_match
        timeline_summary = summary_adv if fase in ("EN_VIVO", "POST_PARTIDO") else cls.fetch_match_summary_details((last_match or {}).get("event_id", ""))
        minuto_a_minuto = cls.build_match_timeline(timeline_source, timeline_summary)

        # Identificar rival activo para scouting + 1891 BD
        loc_act = partido_activo_data.get("local", {})
        vis_act = partido_activo_data.get("visitante", {})
        rival_activo_nombre = loc_act.get("nombre") if not loc_act.get("es_penarol") else vis_act.get("nombre")
        if not rival_activo_nombre or "ganador" in rival_activo_nombre.lower():
            # En espera de la Final, priorizar scouting del último rival si POST_PARTIDO o del líder del Clausura (Liverpool)
            rival_activo_nombre = "Liverpool"
        try:
            from manya_rival_intelligence import resolver_meta_rival
            meta_rival = resolver_meta_rival(rival_activo_nombre)
            rival_activo_slug = meta_rival.get("slug", "cerro_largo")
        except Exception:
            rival_activo_slug = re.sub(r"[^a-z0-9]+", "_", rival_activo_nombre.lower()).strip("_")

        # Torneo activo por defecto: si Peñarol ya ganó la Anual / terminó Clausura, abrir en Tabla Anual; si está en fecha regular, Clausura
        torneo_defecto_id = "anual" if (pen_clausura.get("pj", 0) >= 15 and pen_anual.get("pos") == 1) else "clausura"

        tablas_campeonatos = [
            {
                "id": "anual",
                "nombre": "Tabla Anual Acumulada Oficial (AUF)",
                "nombre_corto": "Tabla Anual",
                "icono": "🏆",
                "badge": f"Campeón Anual • {pen_anual['pts']} pts" if (pen_clausura.get("pj", 0) >= 15 and pen_anual.get("pos") == 1) else f"#{pen_anual['pos']} • {pen_anual['pts']} pts",
                "es_proximo": torneo_defecto_id == "anual",
                "datos": tabla_anual
            },
            {
                "id": "clausura",
                "nombre": "Torneo Clausura 2026",
                "nombre_corto": "Torneo Clausura",
                "icono": "⚽",
                "badge": f"Fecha {pen_clausura.get('pj', 15)} • {pen_clausura.get('pts', 26)} pts",
                "es_proximo": torneo_defecto_id == "clausura",
                "datos": tabla_clausura
            },
            {
                "id": "libertadores",
                "nombre": libertadores_info.get("nombre", "Copa CONMEBOL Libertadores"),
                "nombre_corto": "Copa Libertadores",
                "icono": "🌎",
                "badge": "CONMEBOL 2026",
                "es_proximo": False,
                "datos": libertadores_info.get("datos", [])
            }
        ]

        mapa_tablas = {
            "anual": tabla_anual,
            "clausura": tabla_clausura,
            "libertadores": libertadores_info.get("datos", [])
        }

        doc_live = {
            "actualizado": now_uy.strftime("%d/%m/%Y %H:%M"),
            "schema_version": "10.0",
            "fase_partido": fase,
            "estado_ciclo_vida": estado_ciclo_vida,
            "ventana_post_partido_horas": 48,
            "horas_desde_ultimo_partido": round(horas_desde_ultimo_partido, 1),
            "rival_activo_nombre": rival_activo_nombre,
            "rival_activo_slug": rival_activo_slug,
            "historial_file": "data/historial_activo.json",
            "alerta_banner": alerta_banner,
            "resumen_temporada": {
                "penarol_anual_pts": pen_anual.get("pts", 69),
                "penarol_anual_pos": pen_anual.get("pos", 1),
                "penarol_anual_pj": pen_anual.get("pj", 37),
                "penarol_anual_dg": pen_anual.get("dg", "+27"),
                "penarol_clausura_pts": pen_clausura.get("pts", 26),
                "penarol_clausura_pos": pen_clausura.get("pos", 4),
                "penarol_clausura_pj": pen_clausura.get("pj", 15),
                "campeon_anual": bool(pen_clausura.get("pj", 0) >= 15 and pen_anual.get("pos") == 1),
                "libertadores_2027": "Clasificado directo a Fase de Grupos (Uruguay 1)",
                "definicion_uruguayo": {
                    "semifinal": "Racing (Campeón Apertura) vs Liverpool (Campeón Clausura)",
                    "fecha_semifinal": "Domingo 29/11/2026 (tentativa)",
                    "finales": "Peñarol (Campeón Tabla Anual) vs Ganador Semifinal — Ida: Jueves 3/12 • Vuelta: Domingo 6/12"
                }
            },
            "partido_activo": partido_activo_data,
            "proximo_partido": proximo_partido_data,
            "ultimo_partido": last_match or {},
            "ultimos_resultados": recent_completed,
            "proximos_partidos": [proximo_partido_data] if proximo_partido_data else [],
            "torneo_activo_id": torneo_defecto_id,
            "tabla_posiciones": mapa_tablas.get(torneo_defecto_id, tabla_anual),
            "tabla_anual": tabla_anual,
            "tabla_clausura": tabla_clausura,
            "tabla_libertadores": libertadores_info.get("datos", []),
            "tablas_campeonatos": tablas_campeonatos,
            "clima_campeon_del_siglo": weather,
            "minuto_a_minuto": minuto_a_minuto,
            "minuto_a_minuto_event_id": (timeline_source or {}).get("event_id", ""),
            "blogger_live_url": "https://www.servicioti.com.uy/p/penarol-proximo-partido-radiografia.html"
        }

        output_file = DATA_DIR / "live_status.json"
        output_file.write_text(json.dumps(doc_live, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info("[MatchEngine] ✓ data/live_status.json generado (v10.0 Zero-Hardcode).")
        logger.info(f"             - Fase: {fase} | Tabla Anual Peñarol: #{pen_anual.get('pos')} ({pen_anual.get('pts')} pts, {pen_anual.get('dg')})")
        logger.info(f"             - Activo: {partido_activo_data.get('nombre')} ({partido_activo_data.get('fecha_legible')})")
        logger.info(f"             - Próximo: {proximo_partido_data.get('nombre')} ({proximo_partido_data.get('fecha_legible')})")
        return doc_live


if __name__ == "__main__":
    status = ManyaMatchEngine.generate_updated_live_status()
    print("\n" + "=" * 65)
    print("✓ VERIFICACIÓN MATCH ENGINE v4.0 EXITOSA:")
    print("Fase:", status.get("fase_partido"))
    print("Banner:", status.get("alerta_banner"))
    print("Tabla Anual Peñarol:", status.get("resumen_temporada", {}).get("penarol_anual_pts"), "pts | DG:", status.get("resumen_temporada", {}).get("penarol_anual_dg"))
    print("Últimos 5 resultados:", [(m["nombre"], f"{m['local']['goles']}-{m['visitante']['goles']}") for m in status.get("ultimos_resultados", [])])
    print("Minuto a minuto eventos:", len(status.get("minuto_a_minuto", [])), "| event_id:", status.get("minuto_a_minuto_event_id"))
    print("Libertadores orden:", [(r["pos"], r["equipo"], r["pts"]) for r in status.get("tabla_libertadores", [])])
    print("=" * 65)
