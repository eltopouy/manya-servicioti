# -*- coding: utf-8 -*-
"""
[LEGACY ARCHIVADO — NO EJECUTAR] reestructurar_tripartita_frontend.py
=====================================================================
Script puntual de reestructuración de interfaz de octubre 2026.
Reemplazado por la arquitectura frontend v11.0 y el SSR seguro de `sync_manya_hub.py`.

Se conserva neutralizado para evitar que reescriba `index.html` o `js/app.js` con
plantillas y datos obsoletos de octubre 2026.
"""

import sys


def main() -> int:
    print(
        "[LEGACY ARCHIVADO] `reestructurar_tripartita_frontend.py` quedó obsoleto en Manya v11.0.\n"
        "Use en su lugar: python automation/sync_manya_hub.py --mode fast"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
