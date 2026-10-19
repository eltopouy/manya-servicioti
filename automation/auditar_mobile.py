# -*- coding: utf-8 -*-
"""
AUDITORÍA INTEGRAL DE VISUALIZACIÓN MÓVIL EN MANYA SERVICIOTI
Prueba en múltiples dispositivos móviles reales (iPhone 14, Android 360px, iPhone SE)
"""
import http.server
import socketserver
import threading
import time
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PORT = 8894
BASE_DIR = Path(__file__).resolve().parent.parent

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)
    def log_message(self, *a):
        pass

httpd = socketserver.TCPServer(('127.0.0.1', PORT), QuietHandler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
time.sleep(0.3)

viewports = [
    ("iPhone 14 (390x844)", 390, 844),
    ("Narrow Android (360x800)", 360, 800),
    ("Compact iPhone SE (375x667)", 375, 667)
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for name, w, h in viewports:
        print(f"\n=======================================================")
        print(f" AUDITANDO: {name}")
        print(f"=======================================================")
        page = browser.new_page(viewport={"width": w, "height": h}, is_mobile=True, has_touch=True)
        page.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="networkidle")
        page.wait_for_timeout(800)

        # 1. Comprobar desbordamiento horizontal
        scroll_w = page.evaluate("document.documentElement.scrollWidth")
        inner_w = page.evaluate("window.innerWidth")
        has_h_overflow = scroll_w > inner_w
        print(f"[*] Desbordamiento horizontal: {'¡HAY OVERFLOW!' if has_h_overflow else 'OK (Sin desbordamiento)'}")
        print(f"    scrollWidth: {scroll_w}px | innerWidth: {inner_w}px | Delta: {scroll_w - inner_w}px")

        # 2. Encontrar elementos específicos que causen desbordamiento
        overflowing = page.evaluate("""() => {
            const bad = [];
            const docWidth = window.innerWidth;
            document.querySelectorAll('*').forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.right > docWidth + 1.5) {
                    bad.push({
                        tag: el.tagName.toLowerCase(),
                        id: el.id,
                        className: (typeof el.className === 'string') ? el.className.slice(0, 40) : '',
                        right: Math.round(rect.right),
                        width: Math.round(rect.width),
                        diff: Math.round(rect.right - docWidth)
                    });
                }
            });
            return bad;
        }""")

        if overflowing:
            print(f"[!] Se encontraron {len(overflowing)} elementos que sobrepasan la pantalla:")
            for o in overflowing[:8]:
                print(f"    -> <{o['tag']} id='{o['id']}' class='{o['className']}'> width={o['width']}px, sobresale +{o['diff']}px")
        else:
            print("[✓] Ningún elemento sobresale horizontalmente.")

        # 3. Métricas de usabilidad táctil y fuentes
        nav_status = page.evaluate("""() => {
            const nav = document.querySelector('.manya-nav');
            if (!nav) return null;
            return {
                overflowX: getComputedStyle(nav).overflowX,
                scrollWidth: nav.scrollWidth,
                clientWidth: nav.clientWidth,
                linksCount: nav.querySelectorAll('a').length
            };
        }""")
        print(f"[*] Menú de navegación móvil: {nav_status}")

        # 4. Tabla de posiciones en móvil
        table_status = page.evaluate("""() => {
            const table = document.querySelector('.standings-table');
            const wrap = table ? table.parentElement : null;
            return {
                tableWidth: table ? table.offsetWidth : 0,
                wrapWidth: wrap ? wrap.offsetWidth : 0,
                wrapOverflowX: wrap ? getComputedStyle(wrap).overflowX : ''
            };
        }""")
        print(f"[*] Tabla de Posiciones: {table_status}")

        # 5. Pizarra táctica en móvil
        pitch_status = page.evaluate("""() => {
            const pitch = document.querySelector('#tactical-pitch');
            const tokens = document.querySelectorAll('.player-token');
            const labels = document.querySelectorAll('.player-label');
            return {
                pitchWidth: pitch ? pitch.offsetWidth : 0,
                pitchHeight: pitch ? pitch.offsetHeight : 0,
                tokenSize: tokens.length ? getComputedStyle(tokens[0]).width : 0,
                labelFontSize: labels.length ? getComputedStyle(labels[0]).fontSize : 0
            };
        }""")
        print(f"[*] Pizarra Táctica: {pitch_status}")

        # 6. Portada Visual (Módulo 0)
        hero_status = page.evaluate("""() => {
            const card = document.querySelector('.hero-instagram-post .ig-post-card');
            const actions = document.querySelector('.ig-post-actions-bar');
            return {
                cardWidth: card ? card.offsetWidth : 0,
                actionsFlexWrap: actions ? getComputedStyle(actions).flexWrap : '',
                actionsWidth: actions ? actions.offsetWidth : 0
            };
        }""")
        print(f"[*] Portada Visual: {hero_status}")

        # Captura
        slug = name.split()[0].lower()
        out_shot = BASE_DIR / "automation" / f"_audit_{slug}_{w}x{h}.png"
        page.screenshot(path=str(out_shot), full_page=True)
        print(f"[✓] Captura guardada en: {out_shot}")

        page.close()
    browser.close()

httpd.shutdown()
print("\n[✓] Auditoría móvil completada.")
