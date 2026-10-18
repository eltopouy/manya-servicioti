# -*- coding: utf-8 -*-
"""
Motor de Monitoreo de Partidos en Vivo y Ciclo de Vida para Manya ServicioTI.
Gestiona las fases:
  1. PREVIA: Cobertura táctica, clima, alineaciones y TV antes del inicio.
  2. EN VIVO: Polling minuto a minuto de ESPN API (marcador, incidencias, goles).
  3. POST-PARTIDO: Pitazo final, estadísticas de posesión/tiros y crónica definitiva.
"""

import os
import sys
import json
import logging
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

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

HEADERS_HTTP = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 "
        "(ServicioTI-ManyaMatchEngine/2.0)"
    )
}

SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/uru.1/scoreboard"
TEAM_API_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/uru.1/teams/2892"
SUMMARY_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/uru.1/summary?event="


def resolve_team_crest(team_name: str, fallback_logo: str = "") -> str:
    """Resuelve la ruta del escudo oficial del club desde el catálogo local o fuentes verificadas."""
    import unicodedata
    if "peñarol" in team_name.lower() or "penarol" in team_name.lower():
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
            if slug and slug in clubes:
                return clubes[slug].get("ruta_webp", f"assets/img/escudos/escudo_{slug}.webp")
        except Exception:
            pass

    return fallback_logo or "assets/img/escudos/escudo_penarol.webp"


class ManyaMatchEngine:
    """Orquestador del estado y datos de partidos de Peñarol."""

    @classmethod
    def _fetch_json(cls, url: str) -> Optional[Dict[str, Any]]:
        try:
            req = urllib.request.Request(url, headers=HEADERS_HTTP)
            with urllib.request.urlopen(req, timeout=12) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.warning(f"[MatchEngine] Error consultando {url}: {e}")
            return None

    @classmethod
    def get_today_or_next_match(cls) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Consulta el Scoreboard de ESPN para determinar si Peñarol juega hoy.
        Retorna (info_partido, fase) donde fase puede ser:
          - 'PREVIA': Juega hoy pero no ha empezado.
          - 'EN_VIVO': En juego en este momento.
          - 'FINALIZADO': Jugó hoy y ya concluyó.
          - 'SIN_PARTIDO_HOY': No juega hoy (retorna el próximo partido del calendario).
        """
        sb_data = cls._fetch_json(SCOREBOARD_URL)
        now_uy = datetime.now(UY_TZ)
        today_date_str = now_uy.strftime("%Y-%m-%d")

        if sb_data:
            events = sb_data.get("events", [])
            for ev in events:
                name = ev.get("name", "")
                if "peñarol" in name.lower() or "penarol" in name.lower():
                    # Encontramos evento de Peñarol en el scoreboard de hoy
                    ev_date_raw = ev.get("date", "")
                    try:
                        ev_dt = datetime.fromisoformat(ev_date_raw.replace("Z", "+00:00")).astimezone(UY_TZ)
                    except Exception:
                        ev_dt = now_uy

                    comps = ev.get("competitions", [{}])[0]
                    status_obj = comps.get("status", {})
                    state = status_obj.get("type", {}).get("state", "pre")  # 'pre', 'in', 'post'
                    completed = status_obj.get("type", {}).get("completed", False)
                    clock = status_obj.get("displayClock", "0'")
                    period = status_obj.get("period", 0)

                    competitors = comps.get("competitors", [])
                    home_team = {}
                    away_team = {}
                    for c in competitors:
                        is_home = c.get("homeAway") == "home"
                        nombre_tm = c.get("team", {}).get("displayName", "")
                        logo_tm = c.get("team", {}).get("logo", "")
                        t_info = {
                            "id": c.get("id"),
                            "nombre": nombre_tm,
                            "abreviatura": c.get("team", {}).get("abbreviation", ""),
                            "logo": logo_tm,
                            "escudo": resolve_team_crest(nombre_tm, logo_tm),
                            "goles": c.get("score", "0"),
                            "es_penarol": "2892" in str(c.get("id")) or "peñarol" in c.get("team", {}).get("name", "").lower()
                        }
                        if is_home:
                            home_team = t_info
                        else:
                            away_team = t_info

                    venue = comps.get("venue", {}).get("displayName", "Estadio de Primera División")
                    broadcasts = comps.get("broadcasts", [])
                    tv_str = "VTV Plus / Disney+ Premium"
                    if broadcasts:
                        names = [b.get("names", [""])[0] for b in broadcasts if b.get("names")]
                        if names:
                            tv_str = " / ".join(names)

                    match_info = {
                        "event_id": str(ev.get("id")),
                        "nombre": name,
                        "fecha_iso": ev_dt.isoformat(),
                        "fecha_legible": ev_dt.strftime("%d/%m/%Y %H:%M hs"),
                        "torneo": comps.get("league", {}).get("name", "Campeonato Uruguayo • Clausura"),
                        "estadio": venue,
                        "local": home_team,
                        "visitante": away_team,
                        "minuto_reloj": clock,
                        "tiempo_periodo": period,
                        "completado": completed,
                        "tv": tv_str,
                        "es_hoy": ev_dt.strftime("%Y-%m-%d") == today_date_str
                    }

                    if state == "in":
                        return match_info, "EN_VIVO"
                    elif state == "post" or completed:
                        return match_info, "FINALIZADO"
                    else:
                        return match_info, "PREVIA"

        # Si no hubo partido de Peñarol en el scoreboard de hoy, buscar próximo en el fixture oficial
        team_data = cls._fetch_json(TEAM_API_URL)
        next_event = None
        if team_data:
            nxt = team_data.get("team", {}).get("nextEvent", [])
            if nxt:
                ev = nxt[0]
                ev_date_raw = ev.get("date", "")
                try:
                    ev_dt = datetime.fromisoformat(ev_date_raw.replace("Z", "+00:00")).astimezone(UY_TZ)
                except Exception:
                    ev_dt = now_uy + timedelta(days=3)

                comps = ev.get("competitions", [{}])[0]
                venue = comps.get("venue", {}).get("fullName", "Estadio Campeón del Siglo")
                competitors = comps.get("competitors", [])
                home_team, away_team = {}, {}
                for c in competitors:
                    nombre_tm = c.get("team", {}).get("name", "")
                    logo_tm = c.get("team", {}).get("logo", "")
                    t_info = {
                        "id": c.get("id"),
                        "nombre": nombre_tm,
                        "abreviatura": c.get("team", {}).get("abbreviation", ""),
                        "logo": logo_tm,
                        "escudo": resolve_team_crest(nombre_tm, logo_tm),
                        "goles": "-",
                        "es_penarol": "2892" in str(c.get("id")) or "peñarol" in c.get("team", {}).get("name", "").lower()
                    }
                    if c.get("homeAway") == "home":
                        home_team = t_info
                    else:
                        away_team = t_info

                next_event = {
                    "event_id": str(ev.get("id")),
                    "nombre": ev.get("name", "Peñarol vs Rival"),
                    "fecha_iso": ev_dt.isoformat(),
                    "fecha_legible": ev_dt.strftime("%d/%m/%Y %H:%M hs"),
                    "torneo": "Campeonato Uruguayo • Clausura",
                    "estadio": venue,
                    "local": home_team or {"nombre": "Peñarol", "abreviatura": "CAP", "goles": "-", "es_penarol": True},
                    "visitante": away_team or {"nombre": "Rival", "abreviatura": "RIV", "goles": "-", "es_penarol": False},
                    "minuto_reloj": "0'",
                    "tiempo_periodo": 0,
                    "completado": False,
                    "tv": "VTV Plus / Disney+",
                    "es_hoy": False
                }

        return next_event, "SIN_PARTIDO_HOY"

    @classmethod
    def fetch_match_summary_details(cls, event_id: str) -> Dict[str, Any]:
        """Obtiene detalles avanzados (boxscore, formaciones, incidencias y goles)."""
        summary = cls._fetch_json(f"{SUMMARY_BASE_URL}{event_id}")
        if not summary:
            return {}

        detalles = {
            "goles": [],
            "tarjetas": [],
            "estadisticas": {},
            "titulares_penarol": [],
            "suplentes_penarol": [],
            "titulares_rival": []
        }

        # Extraer rosters / alineaciones
        rosters = summary.get("rosters", [])
        for r in rosters:
            team_id = str(r.get("team", {}).get("id", ""))
            es_pen = team_id == "2892" or "peñarol" in r.get("team", {}).get("displayName", "").lower()
            roster_list = r.get("roster", [])
            for ath in roster_list:
                athlete = ath.get("athlete", {})
                player_name = athlete.get("displayName", "")
                jersey = ath.get("jersey", "")
                position = ath.get("position", {}).get("abbreviation", "")
                is_sub = ath.get("subbedIn", False) or ath.get("starter", True) is False

                p_entry = f"{jersey} - {player_name} ({position})".strip()
                if es_pen:
                    if is_sub:
                        detalles["suplentes_penarol"].append(p_entry)
                    else:
                        detalles["titulares_penarol"].append(p_entry)
                else:
                    if not is_sub:
                        detalles["titulares_rival"].append(p_entry)

        # Extraer boxscore
        boxscore = summary.get("boxscore", {})
        teams_stats = boxscore.get("teams", [])
        for ts in teams_stats:
            team_name = ts.get("team", {}).get("displayName", "")
            stats_raw = ts.get("statistics", [])
            stats_dict = {s.get("label"): s.get("displayValue") for s in stats_raw}
            detalles["estadisticas"][team_name] = stats_dict

        return detalles

    @classmethod
    def generate_updated_live_status(cls) -> Dict[str, Any]:
        """Genera el documento integral `data/live_status.json`."""
        match_info, fase = cls.get_today_or_next_match()
        now_uy = datetime.now(UY_TZ)

        summary_adv = {}
        if match_info and match_info.get("event_id"):
            summary_adv = cls.fetch_match_summary_details(match_info["event_id"])

        # Banner de alerta interactivo para manya.servicioti.com.uy
        if fase == "EN_VIVO":
            alerta_banner = f"🔴 EN VIVO AHORA: {match_info['local']['nombre']} {match_info['local']['goles']} - {match_info['visitante']['goles']} {match_info['visitante']['nombre']} ({match_info['minuto_reloj']})"
        elif fase == "PREVIA":
            alerta_banner = f"⚡ ¡HOY JUEGA PEÑAROL! {match_info['nombre']} a las {match_info['fecha_legible']} en {match_info['estadio']}. Vivilo en vivo por {match_info['tv']}."
        elif fase == "FINALIZADO":
            alerta_banner = f"🏁 FINAL: {match_info['local']['nombre']} {match_info['local']['goles']} - {match_info['visitante']['goles']} {match_info['visitante']['nombre']} ({match_info['estadio']})"
        else:
            alerta_banner = f"🟡⚫ Próximo partido del Glorioso Peñarol: {match_info['nombre'] if match_info else 'Por definir'} ({match_info['fecha_legible'] if match_info else ''})"

        # Preservar o refrescar tabla de posiciones existente
        existing_status_file = DATA_DIR / "live_status.json"
        tabla_pos = []
        clima_cds = {}
        if existing_status_file.exists():
            try:
                with open(existing_status_file, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                    tabla_pos = old_data.get("tabla_posiciones", [])
                    clima_cds = old_data.get("clima_campeon_del_siglo", {})
            except Exception:
                pass

        doc_live = {
            "actualizado": now_uy.strftime("%d/%m/%Y %H:%M"),
            "fase_partido": fase,
            "alerta_banner": alerta_banner,
            "partido_activo": {
                "es_hoy": match_info.get("es_hoy", False) if match_info else False,
                "fase": fase,
                "id": match_info.get("event_id") if match_info else "",
                "nombre": match_info.get("nombre") if match_info else "",
                "fecha_iso": match_info.get("fecha_iso") if match_info else "",
                "fecha_legible": match_info.get("fecha_legible") if match_info else "",
                "torneo": match_info.get("torneo") if match_info else "",
                "estadio": match_info.get("estadio") if match_info else "",
                "local": match_info.get("local") if match_info else {},
                "visitante": match_info.get("visitante") if match_info else {},
                "minuto_reloj": match_info.get("minuto_reloj", "0'") if match_info else "0'",
                "completado": match_info.get("completado", False) if match_info else False,
                "tv": match_info.get("tv", "VTV Plus / Disney+") if match_info else "VTV Plus / Disney+",
                "detalles_avanzados": summary_adv
            },
            "proximo_partido": match_info or {},
            "tabla_posiciones": tabla_pos,
            "clima_campeon_del_siglo": clima_cds
        }

        with open(DATA_DIR / "live_status.json", "w", encoding="utf-8") as f:
            json.dump(doc_live, f, indent=2, ensure_ascii=False)

        logger.info(f"[MatchEngine] ✓ data/live_status.json actualizado en fase '{fase}' ({alerta_banner[:65]}...)")
        return doc_live


if __name__ == "__main__":
    status = ManyaMatchEngine.generate_updated_live_status()
    print("\nResultado MatchEngine:")
    print("Fase:", status.get("fase_partido"))
    print("Banner:", status.get("alerta_banner"))
    print("Partido Activo:", status.get("partido_activo", {}).get("nombre"))
