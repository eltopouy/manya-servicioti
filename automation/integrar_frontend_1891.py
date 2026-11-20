# -*- coding: utf-8 -*-
"""
[LEGACY ARCHIVADO — NO EJECUTAR] integrar_frontend_1891.py
==========================================================
Script puntual de integración inicial de 1891 BD en el frontend (octubre 2026).
Hoy toda la integración 1891 BD es 100% dinámica vía `extraer_datos_1891.py`,
`manya_rival_intelligence.py` y `sync_manya_hub.py` v11.0.

Se conserva neutralizado para evitar sobrescrituras accidentales de `index.html` y `js/app.js`.
"""

import sys


def main() -> int:
    print(
        "[LEGACY ARCHIVADO] `integrar_frontend_1891.py` quedó obsoleto en Manya v11.0.\n"
        "Use en su lugar: python automation/sync_manya_hub.py --mode fast"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
