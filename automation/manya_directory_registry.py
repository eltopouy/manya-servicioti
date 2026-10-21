# -*- coding: utf-8 -*-
"""
MANYA DIRECTORY REGISTRY (manya_directory_registry.py)
======================================================
Capa de abstracción y base de datos de fuentes oficiales, portales de clubes,
APIs y medios periodísticos para todo el ecosistema de automatización.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

logger = logging.getLogger("ManyaDirectoryRegistry")

BASE_DIR = Path(__file__).resolve().parent.parent
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
        Ej: get_club('juventud') o get_club('JUV') o get_club('Juventud de Las Piedras').
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
    
    juv = ManyaDirectoryRegistry.get_club("juventud")
    if juv:
        print(f"\nClub verificado: {juv['nombre_oficial']} (DT: {juv.get('dt_actual')})")
        print(f"Estadio: {juv.get('estadio_propio')} | Web: {juv.get('web_oficial')}")
