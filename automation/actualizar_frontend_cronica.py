# -*- coding: utf-8 -*-
"""
[LEGACY ARCHIVADO — NO EJECUTAR] actualizar_frontend_cronica.py
===============================================================
Script puntual de migración de octubre 2026 (reemplazado completamente por
`automation/sync_manya_hub.py` v11.0 y su sincronizador SSR seguro con BeautifulSoup).

Se conserva neutralizado para evitar ejecuciones accidentales que puedan sobrescribir
`index.html`, `js/app.js` o `data/news_digest.json` con contenido histórico obsoleto.
"""

import sys


def main() -> int:
    print(
        "[LEGACY ARCHIVADO] `actualizar_frontend_cronica.py` quedó obsoleto en Manya v11.0.\n"
        "Use en su lugar: python automation/sync_manya_hub.py --mode fast"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
