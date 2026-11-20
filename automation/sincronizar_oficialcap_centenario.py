# -*- coding: utf-8 -*-
"""
[LEGACY ARCHIVADO — NO EJECUTAR] sincronizar_oficialcap_centenario.py
=====================================================================
Script puntual de confirmación de fecha de octubre 2026.
Reemplazado por la detección automática de fechas/sedes de `manya_match_engine.py` v5.0
y `sync_manya_hub.py` v11.0.

Se conserva neutralizado para evitar sobrescrituras accidentales de datasets o HTML.
"""

import sys


def main() -> int:
    print(
        "[LEGACY ARCHIVADO] `sincronizar_oficialcap_centenario.py` quedó obsoleto en Manya v11.0.\n"
        "Use en su lugar: python automation/sync_manya_hub.py --mode fast"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
