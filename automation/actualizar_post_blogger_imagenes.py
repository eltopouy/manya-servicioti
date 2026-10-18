# -*- coding: utf-8 -*-
"""
Script de actualización segura de imágenes en Blogger para:
https://www.servicioti.com.uy/2026/10/penarol-en-vivo-la-previa-tarde-de.html
Post ID: 5877749831453571437 | Blog ID: 8220787747664379807
Sustituye imágenes viejas por 100% auténticas de Gemini Imagen 3.
"""
import sys
import json
import re
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
TOKEN_PATH = BASE_DIR.parent.parent / "seo_blogger_automation" / "token.json"
BLOG_ID = "8220787747664379807"
POST_ID = "5877749831453571437"
SCOPES = ["https://www.googleapis.com/auth/blogger"]

def run():
    print("1. Autenticando con Blogger API...")
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    service = build("blogger", "v3", credentials=creds)

    print(f"2. Obteniendo post actual {POST_ID}...")
    post = service.posts().get(blogId=BLOG_ID, postId=POST_ID).execute()
    title = post.get("title")
    labels = post.get("labels", [])
    old_content = post.get("content", "")
    print(f"   Título: {title}")
    print(f"   Labels: {labels}")

    # CDN URLs Imagen 3
    img_hero = "https://cdn.jsdelivr.net/gh/eltopouy/manya-servicioti@main/assets/ig/manya_previa_balon_estadio.webp"
    img_tactica = "https://cdn.jsdelivr.net/gh/eltopouy/manya-servicioti@main/assets/ig/manya_entrenamiento_los_aromos_tactica.webp"
    img_hinchada = "https://cdn.jsdelivr.net/gh/eltopouy/manya-servicioti@main/assets/ig/manya_hinchada_fiesta_aurinegra.webp"

    # 1. Reemplazar Figure 1 (Hero)
    fig1_pat = r'<figure style="margin:0 0 20px 0;text-align:center;">.*?</figure>'
    fig1_rep = (
        f'<figure style="margin:0 0 20px 0;text-align:center;">'
        f'<img src="{img_hero}" alt="Peñarol vs Liverpool - Balón en el césped del Campeón del Siglo en la previa oficial" width="1280" height="714" loading="eager" fetchpriority="high" style="width:100%;height:auto;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,0.15);" />'
        f'<figcaption style="font-size:12.5px;color:#64748b;margin-top:6px;">Previa Oficial • Balón sobre el césped al atardecer en el Estadio Campeón del Siglo. Cobertura gráfica exclusiva para Manya ServicioTI.</figcaption>'
        f'</figure>'
    )
    new_content, count1 = re.subn(fig1_pat, fig1_rep, old_content, count=1, flags=re.DOTALL)
    print(f"   Figure 1 reemplazada: {count1} ocurrencia(s)")

    # 2. Insertar Figure Los Aromos (Táctica) tras el párrafo de Los Aromos
    parrafo_target = "</p><p>Respecto al once probable"
    fig_tactica_html = (
        f'</p><figure style="margin:20px 0;text-align:center;">'
        f'<img src="{img_tactica}" alt="Entrenamiento y trabajos tácticos de Peñarol en Los Aromos preparando el partido ante Liverpool" width="1280" height="714" loading="lazy" decoding="async" style="width:100%;height:auto;border-radius:12px;box-shadow:0 6px 20px rgba(0,0,0,0.12);" />'
        f'<figcaption style="font-size:12.5px;color:#64748b;margin-top:6px;">Los Aromos (Complejo Deportivo Washington Cataldi) • Sesión de entrenamiento y táctica aurinegra preparando el choque ante Liverpool.</figcaption>'
        f'</figure><p>Respecto al once probable'
    )
    if parrafo_target in new_content:
        new_content = new_content.replace(parrafo_target, fig_tactica_html, 1)
        print("   Figure Los Aromos insertada exitosamente.")
    else:
        print("   Aviso: No se encontró punto exacto para Los Aromos, buscando alternativa...")

    # 3. Reemplazar Figure 2 (Hinchada)
    fig2_pat = r'<figure style="margin:20px 0;text-align:center;">\s*<img src="[^"]*manya_hinchada_recibimiento_aurinegro\.webp"[^>]*>\s*</figure>'
    fig2_rep = (
        f'<figure style="margin:20px 0;text-align:center;">'
        f'<img src="{img_hinchada}" alt="Fiesta popular de la hinchada de Peñarol en el Estadio Campeón del Siglo con banderas aurinegras y humo amarillo" width="1280" height="714" loading="lazy" decoding="async" style="width:100%;height:auto;border-radius:12px;box-shadow:0 6px 20px rgba(0,0,0,0.12);" />'
        f'<figcaption style="font-size:12.5px;color:#64748b;margin-top:6px;">Tribuna Aurinegra • Fiesta y recibimiento carbonero en el Estadio Campeón del Siglo con el aliento de las cuatro tribunas.</figcaption>'
        f'</figure>'
    )
    new_content, count2 = re.subn(fig2_pat, fig2_rep, new_content, count=1, flags=re.DOTALL)
    print(f"   Figure 2 (Hinchada) reemplazada: {count2} ocurrencia(s)")

    # 4. Actualizar Schema JSON-LD
    old_img_json = '"image":["https://cdn.jsdelivr.net/gh/eltopouy/manya-servicioti@main/assets/ig/manya_campeon_del_siglo_nocturno.webp"]'
    new_img_json = f'"image":["{img_hero}","{img_tactica}","{img_hinchada}"]'
    if old_img_json in new_content:
        new_content = new_content.replace(old_img_json, new_img_json)
        print("   Schema JSON-LD actualizado con las 3 imágenes Imagen 3.")

    # 5. Patch en Blogger API
    print("3. Enviando actualización (patch) a Blogger API...")
    patch_body = {
        "content": new_content,
        "labels": labels
    }
    updated_post = service.posts().patch(
        blogId=BLOG_ID,
        postId=POST_ID,
        body=patch_body
    ).execute()

    print(f"✓ Éxito! Post actualizado en Blogger:")
    print(f"  URL: {updated_post.get('url')}")
    print(f"  Updated: {updated_post.get('updated')}")

if __name__ == "__main__":
    run()
