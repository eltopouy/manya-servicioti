# -*- coding: utf-8 -*-
"""
MANYA DIRECTORY REGISTRY (manya_directory_registry.py)
======================================================
Capa de abstracción y base de datos de fuentes oficiales, portales de clubes,
APIs y medios periodísticos para todo el ecosistema de automatización.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

BASE_DIR = Path(__file__).resolve().parent.parent
AUTOMATION_DIR = BASE_DIR / "automation"
if str(AUTOMATION_DIR) not in sys.path:
    sys.path.insert(0, str(AUTOMATION_DIR))

from manya_logging import get_manya_logger

logger = get_manya_logger("ManyaDirectoryRegistry")
CATALOG_PATH = BASE_DIR / "data" / "fuentes_catalogo.json"


class ManyaDirectoryRegistry:
    _cached_data: Optional[Dict[str, Any]] = None

    @classmethod
    def load(cls) -> Dict[str, Any]:
        """Carga el catálogo de fuentes con almacenamiento en caché en memoria."""
        if cls._cached_data is None:
            if not CATALOG_PATH.exists():
                raise FileNotFoundError(f"No se encontró el catálogo de fuentes en {CATALOG_PATH}")
            try:
                cls._cached_data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error(f"Error cargando catálogo de fuentes: {e}")
                cls._cached_data = {}
        return cls._cached_data

    @classmethod
    def get_club(cls, query: str) -> Optional[Dict[str, Any]]:
        """
        Busca un club de Primera División por slug, nombre corto, nombre oficial o abreviatura.
        Ej: get_club('liverpool') o get_club('CAP') o get_club('Club Atlético Peñarol').
        """
        cat = cls.load()
        clubes = cat.get("clubes_primera_division_2026", {})
        q_norm = query.lower().strip()

        # 1. Coincidencia directa por clave
        if q_norm in clubes:
            res = dict(clubes[q_norm])
            res["slug"] = q_norm
            return res

        # 2. Búsqueda por abreviatura o nombres
        for slug, data in clubes.items():
            if data.get("abreviatura", "").lower() == q_norm:
                res = dict(data)
                res["slug"] = slug
                return res
            if q_norm in data.get("nombre_corto", "").lower() or q_norm in data.get("nombre_oficial", "").lower():
                res = dict(data)
                res["slug"] = slug
                return res

        return None

    @classmethod
    def get_rival_sources(cls, rival_name: str) -> Dict[str, Any]:
        """
        Retorna el mapa completo de fuentes oficiales para scouting del rival.
        """
        cat = cls.load()
        club = cls.get_club(rival_name) or {}
        
        return {
            "rival_info": club,
            "auf_portal": cat.get("organismos_oficiales", {}).get("auf_liga", {}),
            "1891_mcp": cat.get("historia_y_patrimonio", {}).get("1891_bd_mcp", {}),
            "1891_partidos": cat.get("historia_y_patrimonio", {}).get("1891_bd_partidos", {}),
            "prensa": cat.get("prensa_deportiva", {})
        }

    @classmethod
    def get_all_clubs(cls) -> Dict[str, Any]:
        """Retorna todos los clubes de Primera División registrados."""
        return cls.load().get("clubes_primera_division_2026", {})

    @classmethod
    def get_source_url(cls, category: str, key: str) -> Optional[str]:
        """Obtiene la URL directa de cualquier recurso del catálogo."""
        cat = cls.load()
        section = cat.get(category, {})
        item = section.get(key, {})
        return item.get("url") or item.get("url_base")


if __name__ == "__main__":
    reg = ManyaDirectoryRegistry.load()
    print(f"Catálogo cargado versión {reg.get('version')}:")
    print(f" - Organismos: {len(reg.get('organismos_oficiales', {}))}")
    print(f" - Medios de Prensa: {len(reg.get('prensa_deportiva', {}))}")
    print(f" - Clubes de Primera: {len(reg.get('clubes_primera_division_2026', {}))}")

    sample_query = "penarol"
    live_file = BASE_DIR / "data" / "live_status.json"
    if live_file.exists():
        try:
            sample_query = json.loads(live_file.read_text(encoding="utf-8")).get("rival_activo_slug") or sample_query
        except Exception:
            pass
    club = ManyaDirectoryRegistry.get_club(sample_query)
    if club:
        print(f"\nClub verificado: {club['nombre_oficial']} (DT: {club.get('dt_actual')})")
        print(f"Estadio: {club.get('estadio_propio')} | Web: {club.get('web_oficial')}")
