# -*- coding: utf-8 -*-
"""
[LEGACY ARCHIVADO — NO EJECUTAR] actualizar_scripts_blogger.py
==============================================================
Script puntual de parcheo de generadores Blogger de octubre 2026 (reemplazado por
`blogger_manya_publisher.py`, `sincronizar_pagina_proximo_partido.py` y
`sincronizar_pagina_blogger_historico.py` v11.0 Zero-Hardcode).

Se conserva neutralizado para impedir modificaciones accidentales con datos históricos.
"""

import sys


def main() -> int:
    print(
        "[LEGACY ARCHIVADO] `actualizar_scripts_blogger.py` quedó obsoleto en Manya v11.0.\n"
        "Use en su lugar: python automation/sync_manya_hub.py --mode full"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
