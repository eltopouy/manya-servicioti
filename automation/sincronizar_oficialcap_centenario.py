# -*- coding: utf-8 -*-
"""
Script de sincronización de la confirmación oficial de Peñarol (@oficialcap):
Partido: Juventud vs Peñarol
Estadio: Estadio Centenario
Fecha: Viernes 23 de octubre de 2026
Hora: 20:00 hs
Torneo: Torneo Clausura 2026 (Fecha 11)
"""

import re
import sys
import json
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def actualizar_index_html():
    index_file = BASE_DIR / "index.html"
    content = index_file.read_text(encoding="utf-8")

    # 1. Instagram header
    content = content.replace("Última Hora</span>", "Hace 1 h</span>")
    content = content.replace("📍 Complejo Deportivo Los Aromos • Montevideo", "📍 Estadio Centenario • Montevideo")
    content = content.replace("⭐ EDICIÓN OFICIAL</span>", "⭐ @OFICIALCAP</span>")
    content = content.replace("📸 NOTICIA CENTRAL DEL DÍA</span>", "📸 COMUNICADO OFICIAL</span>")

    # 2. Instagram headline and caption
    old_headline = "Peñarol y la obsesión por la Tabla Anual: El laboratorio de Aguirre entre Los Aromos y la Catedral"
    new_headline = "🔜 Oficial @oficialcap: Juventud vs Peñarol este Viernes a las 20:00 hs en el Estadio Centenario"
    content = content.replace(old_headline, new_headline)

    new_caption = (
        "<strong>🔜 ¡PRÓXIMO PARTIDO CONFIRMADO!</strong><br>\n"
        "            🆚 <strong>Juventud</strong><br>\n"
        "            🏟️ <strong>Estadio Centenario</strong><br>\n"
        "            🏆 <strong>Torneo Clausura 2026</strong><br>\n"
        "            🗓️ <strong>Viernes 23 de octubre</strong><br>\n"
        "            🕗 <strong>20:00 horas</strong><br><br>\n"
        "            El club pedrense fijó el mítico <strong>Estadio Centenario</strong> para recibir a Peñarol. Venta y canje de entradas habilitados para toda la parcialidad carbonera en TickAntel y locales Redpagos (Tribunas Ámsterdam, Olímpica y América)."
    )
    content = re.sub(
        r'<p id="hero-post-text" class="ig-post-text">.*?</p>',
        f'<p id="hero-post-text" class="ig-post-text">\n            {new_caption}\n          </p>',
        content,
        flags=re.DOTALL
    )

    # 3. Match Center
    content = content.replace("Sábado 24/10/2026 16:00 hs • Clausura Fecha 11", "Viernes 23/10/2026 20:00 hs • Clausura Fecha 11")
    content = content.replace("Estadio Juventud Parque Artigas (Las Piedras)", "Estadio Centenario (Montevideo)")
    content = content.replace(
        "Habilitado en <strong>Redpagos y TickAntel</strong> para hinchas aurinegros en Las Piedras.",
        "Habilitado en <strong>TickAntel y Redpagos</strong> para hinchas aurinegros en el Estadio Centenario (Tribunas Ámsterdam, Olímpica y América)."
    )

    # 4. Countdown numbers fallback
    content = re.sub(r'<div id="cd-days" class="cd-num">\d+</div>', '<div id="cd-days" class="cd-num">02</div>', content)
    content = re.sub(r'<div id="cd-hours" class="cd-num">\d+</div>', '<div id="cd-hours" class="cd-num">23</div>', content)
    content = re.sub(r'<div id="cd-mins" class="cd-num">\d+</div>', '<div id="cd-mins" class="cd-num">35</div>', content)

    index_file.write_text(content, encoding="utf-8")
    print("✓ index.html actualizado con la sede en el Estadio Centenario y horario de @oficialcap.")


def actualizar_instagram_feed():
    ig_file = DATA_DIR / "instagram_feed.json"
    if not ig_file.exists():
        return
    posts = json.loads(ig_file.read_text(encoding="utf-8"))

    oficial_post = {
        "id": "oficialcap_proximo_partido_centenario",
        "titulo": "🔜 Oficial @oficialcap: Juventud vs Peñarol este Viernes a las 20:00 hs en el Estadio Centenario",
        "cuenta": "@oficialcap",
        "categoria": "partidos",
        "categoria_badge": "⭐ Oficial @oficialcap",
        "likes": 42890,
        "comments": 1340,
        "url_post": "https://www.instagram.com/oficialcap/",
        "caption": "🔜 🆚 Juventud 🏟️ Estadio Centenario 🏆 Torneo Clausura 2026 🗓️ Viernes 23 de octubre 🕗 20:00 horas. ¡A copar el Centenario!",
        "imagen_webp": "assets/ig/manya_campeon_del_siglo_nocturno.webp",
        "imagen_jpg": "assets/ig/manya_campeon_del_siglo_nocturno.jpg",
        "seo_alt": "Juventud vs Peñarol en el Estadio Centenario - Viernes 23 de octubre 20:00 hs - Torneo Clausura 2026",
        "kb_webp": 91.2
    }

    # Colocar de primero o reemplazar si ya existía
    posts = [p for p in posts if p.get("id") != "oficialcap_proximo_partido_centenario"]
    posts.insert(0, oficial_post)

    ig_file.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
    print("✓ data/instagram_feed.json actualizado con el post oficial de @oficialcap.")


def actualizar_news_digest():
    digest_file = DATA_DIR / "news_digest.json"
    if not digest_file.exists():
        return
    digest = json.loads(digest_file.read_text(encoding="utf-8"))

    # Actualizar mención en las claves de 60 segundos
    claves = digest.get("claves_60_segundos", [])
    for c in claves:
        if "Juventud" in c.get("titulo", "") or "Próxima Cita" in c.get("titulo", ""):
            c["detalle"] = "El Decano visita a Juventud este viernes 23 de octubre a las 20:00 hs en el Estadio Centenario por la 11ª fecha del Clausura. Venta en TickAntel y Redpagos."

    # Actualizar preguntas frecuentes
    faqs = digest.get("articulo_principal", {}).get("preguntas_frecuentes", [])
    for f in faqs:
        if "próximo partido" in f.get("q", "").lower():
            f["a"] = "Peñarol enfrentará a Juventud en el Estadio Centenario el viernes 23 de octubre de 2026 a las 20:00 horas, con transmisión en vivo por VTV Plus y Disney+."

    digest_file.write_text(json.dumps(digest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("✓ data/news_digest.json actualizado.")


if __name__ == "__main__":
    actualizar_index_html()
    actualizar_instagram_feed()
    actualizar_news_digest()
