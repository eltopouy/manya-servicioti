# -*- coding: utf-8 -*-
"""
MOTOR GEMINI WEB MULTIMODAL (TRANSFORMACIÓN DE IMÁGENES + REDACCIÓN GFLASH 3.8)
===============================================================================
Archivo: manya_gemini_web_engine.py
1. Transformación Visual Automática en Gemini Web:
   - Sube cada foto obtenida (Instagram @oficialcap / @padreydecano o prensa) a Gemini Web
     usando el perfil persistente `~/.gemini_automation_profile`.
   - Gemini Web analiza la imagen original, decide automáticamente qué quitar (textos sobreimpresos,
     marcas de agua, ruido visual, fondos distractores) y qué potenciar/agregar (iluminación épica
     nocturna de estadio, atmósfera oro y carbón #FFD100/#0A0A0A, nitidez 35mm profesional),
     generando una nueva imagen transformada 16:9 libre de derechos y 100% original.
   - Si una imagen con rostros específicos activa filtro en Imagen 3, aplica el motor de
     Transformación Cinematográfica Aurinegra (Color Grading Oro/Carbón + Viñeta + Nitidez + Encuadre)
     y blindaje completo de metadatos SEO EXIF/GPS/XMP con `ManyaSEOMetadataService`.
2. Redacción Periodística con Gemini Web (GFlash 3.8) + Cascada Resiliente:
   - Redacta el "Resumen Aurinegro en 60 Segundos" y los artículos profundos para `manya.servicioti.com.uy`
     y `www.servicioti.com.uy` (Blogger).
"""

import os
import re
import sys
import json
import time
import base64
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw

from manya_seo_metadata import ManyaSEOMetadataService

logger = logging.getLogger("ManyaGeminiWebEngine")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

PROFILE_DIR = Path(os.path.expanduser("~")) / ".gemini_automation_profile"
SCRATCH_DIR = Path(__file__).resolve().parent.parent.parent


def _load_env_vars() -> Dict[str, str]:
    env_vars = {}
    for candidate in [
        SCRATCH_DIR / "seo_blogger_automation" / ".env",
        SCRATCH_DIR / "clima_blogger_automation" / ".env",
        SCRATCH_DIR / "gemini_automation" / ".env",
    ]:
        if candidate.exists():
            try:
                for line in candidate.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        env_vars.setdefault(k.strip(), v.strip())
            except Exception:
                pass
    return env_vars


ENV_VARS = _load_env_vars()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or ENV_VARS.get("GEMINI_API_KEY", "")
GOOGLE_EMAIL = os.environ.get("GOOGLE_EMAIL") or ENV_VARS.get("GOOGLE_EMAIL", "")
GOOGLE_PASSWORD = os.environ.get("GOOGLE_PASSWORD") or ENV_VARS.get("GOOGLE_PASSWORD", "")


class ManyaGeminiWebEngine:
    """Orquesta Gemini Web (Playwright) y la cascada Gemini 3.8 Flash para imágenes y textos de Peñarol."""

    @classmethod
    def aplicar_marca_visual_aurinegra(
        cls,
        img: Image.Image,
        opacidad_negro: float = 0.20,
        opacidad_oro: float = 0.20,
        color_oro: tuple = (255, 209, 0),    # #FFD100 Oro Peñarol
        color_negro: tuple = (12, 12, 12),   # #0C0C0C Negro carbón
        angulo_offset: float = 0.10,        # Inclinación diagonal balanceada
        blur_borde: int = 5
    ) -> Image.Image:
        """
        Aplica la marca visual editorial oficial de Manya ServicioTI:
        División diagonal al medio:
        - Izquierda: filtro negro carbón con sutil transparencia (~20%)
        - Derecha: filtro amarillo oro con sutil transparencia (~20%)
        - Línea de corte diagonal con feathering y acento dorado tenue.
        """
        base = img.convert("RGBA")
        w, h = base.size

        # Puntos de corte diagonal (de arriba a la derecha hacia abajo a la izquierda)
        x_top = int(w * (0.5 + angulo_offset))
        x_bottom = int(w * (0.5 - angulo_offset))

        # Crear overlay
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Polígono izquierdo (Negro)
        poly_izq = [(0, 0), (x_top, 0), (x_bottom, h), (0, h)]
        draw.polygon(poly_izq, fill=(color_negro[0], color_negro[1], color_negro[2], int(opacidad_negro * 255)))

        # Polígono derecho (Amarillo Oro)
        poly_der = [(x_top, 0), (w, 0), (w, h), (x_bottom, h)]
        draw.polygon(poly_der, fill=(color_oro[0], color_oro[1], color_oro[2], int(opacidad_oro * 255)))

        if blur_borde > 0:
            overlay = overlay.filter(ImageFilter.GaussianBlur(radius=blur_borde))

        # Componer overlay sobre la base
        comp = Image.alpha_composite(base, overlay)

        # Sutil línea diagonal dorada de acento
        line_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        line_draw = ImageDraw.Draw(line_layer)
        line_draw.line([(x_top, 0), (x_bottom, h)], fill=(color_oro[0], color_oro[1], color_oro[2], 80), width=2)
        comp = Image.alpha_composite(comp, line_layer)

        return comp.convert("RGB")

    @classmethod
    def aplicar_transformacion_cinematografica_local(
        cls,
        input_path: Path,
        output_path: Path,
        titulo: str,
        descripcion: str,
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Transformación visual determinista de respaldo (Grado Editorial Aurinegro):
        - Recorta el 4% de bordes exteriores para eliminar marcos o marcas de agua periféricas.
        - Aplica reencuadre 16:9 cinematográfico inteligente.
        - Aplica la Marca Visual Oficial Aurinegra (división diagonal: negro izquierda, oro derecha).
        - Mejora contraste, nitidez 35mm e inyecta los metadatos SEO EXIF/GPS/XMP completos.
        """
        with Image.open(input_path) as img:
            rgb = img.convert("RGB")
            w, h = rgb.size
            # Recorte sutil del 4% para limpiar bordes periféricos
            crop_x = int(w * 0.04)
            crop_y = int(h * 0.04)
            if w > 300 and h > 300:
                rgb = rgb.crop((crop_x, crop_y, w - crop_x, h - crop_y))
                w, h = rgb.size

            # Reencuadre 16:9 si es necesario
            target_ratio = 16.0 / 9.0
            cur_ratio = w / h
            if abs(cur_ratio - target_ratio) > 0.06:
                if cur_ratio > target_ratio:
                    new_w = int(h * target_ratio)
                    left = (w - new_w) // 2
                    rgb = rgb.crop((left, 0, left + new_w, h))
                else:
                    new_h = int(w / target_ratio)
                    top = (h - new_h) // 2
                    rgb = rgb.crop((0, top, w, top + new_h))

            # Aplicar Marca Visual Aurinegra Oficial (Diagonal Negro / Amarillo Oro)
            rgb = cls.aplicar_marca_visual_aurinegra(rgb)

            # Mejorar contraste, color y nitidez editorial
            rgb = ImageEnhance.Contrast(rgb).enhance(1.08)
            rgb = ImageEnhance.Color(rgb).enhance(1.06)
            rgb = ImageEnhance.Sharpness(rgb).enhance(1.15)
            rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.2, percent=110, threshold=3))

            output_path.parent.mkdir(parents=True, exist_ok=True)
            rgb.save(output_path, format="JPEG", quality=92)

        meta = ManyaSEOMetadataService.blindar_y_optimizar_imagen(
            ruta_imagen=output_path,
            titulo=titulo,
            descripcion=descripcion,
            categoria="Peñarol",
            keywords=keywords,
            transformacion_ia="Marca Visual Aurinegra Oficial (Diagonal Negro/Oro con Transparencia y Nitidez 35mm)"
        )
        return meta

    @classmethod
    async def transformar_imagen_gemini_web_async(
        cls,
        input_image_path: Path,
        output_image_path: Path,
        contexto_titulo: str,
        contexto_caption: str = "",
        keywords: Optional[List[str]] = None,
        headless: bool = True
    ) -> Dict[str, Any]:
        """
        Sube `input_image_path` a Gemini Web (`https://gemini.google.com/app`),
        pide a Gemini que analice la foto, decida automáticamente qué quitar (textos, logos ajenos,
        elementos distractores) y qué agregar/mejorar (atmósfera épica aurinegra en el Estadio Campeón
        del Siglo, iluminación cinematográfica 35mm), y extrae la nueva imagen generada.
        Luego inyecta todos los metadatos SEO EXIF/GPS/XMP.
        """
        from playwright.async_api import async_playwright

        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        output_image_path.parent.mkdir(parents=True, exist_ok=True)

        # Preparar copia ligera de referencia (<400KB) para subida ultrarrápida al chat de Gemini Web
        temp_ref = output_image_path.parent / f"_ref_temp_{input_image_path.stem}.jpg"
        try:
            with Image.open(input_image_path) as im:
                rgb = im.convert("RGB")
                rgb.thumbnail((768, 768), Image.Resampling.LANCZOS)
                rgb.save(temp_ref, format="JPEG", quality=82)
        except Exception:
            temp_ref = input_image_path

        clean_title = re.sub(r"[^\w\sáéíóúÁÉÍÓÚñÑ.,:-]", "", contexto_titulo or "Club Atlético Peñarol")[:110]
        prompt_vision = (
            f"Analiza en detalle la imagen adjunta relacionada con '{clean_title}' del Club Atlético Peñarol (Uruguay). "
            f"Decide automáticamente qué elementos conviene eliminar (como textos sobreimpresos, carteles, marcas de agua, "
            f"logos comerciales o fondos desordenados) y qué elementos visuales conviene potenciar o agregar para lograr "
            f"una fotografía deportiva épica de nivel Champions League (iluminación dramática de estadio nocturno, "
            f"atmósfera aurinegra en tonos amarillo oro #FFD100 y negro carbón profundo, hinchada apasionada desenfocada "
            f"en segundo plano con banderas aurinegras, césped brillante y nitidez de lente teleobjetivo 35mm f/2.8). "
            f"AHORA GENERA UNA IMAGEN NUEVA mejorada en formato horizontal panorámico 16:9 basada en ese análisis. "
            f"REGLA ESTRICTA: Sin textos, sin letras, sin escudos deformados ni marcas de agua."
        )

        generada_ok = False
        try:
            async with async_playwright() as p:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=str(PROFILE_DIR),
                    channel="chrome",
                    headless=headless,
                    accept_downloads=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                )
                try:
                    page = context.pages[0] if context.pages else await context.new_page()
                    await page.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(3)

                    # Adjuntar la imagen de referencia
                    tools_btn = page.locator("button[aria-label*='Subidas y herramientas'], button[aria-label*='Uploads and tools'], button[aria-label*='Añadir']").first
                    if await tools_btn.count() > 0 and await tools_btn.is_visible():
                        await tools_btn.click()
                        await asyncio.sleep(1)
                        subir_opcion = page.locator("[role='menuitem']:has-text('Subir archivos'), button:has-text('Subir archivos'), [role='menuitem']:has-text('Upload')").first
                        async with page.expect_file_chooser(timeout=8000) as fc_info:
                            await subir_opcion.click()
                        fc = await fc_info.value
                        await fc.set_files([str(temp_ref)])
                        await asyncio.sleep(3.5)

                    imgs_antes = await page.evaluate(
                        "() => Array.from(document.querySelectorAll('img')).map(i => i.src).filter(Boolean)"
                    )

                    textbox = page.locator("div[role='textbox'], rich-textarea div[contenteditable='true']").first
                    await textbox.wait_for(state="visible", timeout=15000)
                    await textbox.click()
                    await textbox.fill(prompt_vision)
                    await asyncio.sleep(1)

                    send_btn = page.locator("button[aria-label*='Enviar'], button[aria-label*='Send']").first
                    if await send_btn.count() > 0 and await send_btn.is_visible():
                        await send_btn.click()
                    else:
                        await textbox.press("Enter")

                    logger.info(f"[Gemini Web Vision] Transformando imagen en Gemini Web: '{clean_title[:55]}'...")
                    start_t = time.time()
                    while time.time() - start_t < 75:
                        await asyncio.sleep(3.5)
                        check_res = await page.evaluate('''(urlsAntes) => {
                            const setAntes = new Set(urlsAntes || []);
                            for (let img of document.querySelectorAll("img")) {
                                const src = img.src || "";
                                if (!src || setAntes.has(src)) continue;
                                if (src.includes("default-user") || src.includes("/ogw/") || src.includes("/a/ACg")) continue;
                                if (img.closest("user-query, uploader-file-card, rich-textarea")) continue;
                                const nw = img.naturalWidth || 0;
                                const nh = img.naturalHeight || 0;
                                if (nw >= 550 && nh >= 300) {
                                    return { src, nw, nh };
                                }
                            }
                            return null;
                        }''', imgs_antes)

                        if check_res and check_res.get("src", "").startswith("http"):
                            resp = await page.request.get(check_res["src"], timeout=25000)
                            if resp.status == 200:
                                body = await resp.body()
                                if len(body) > 20000:
                                    with open(output_image_path, "wb") as f:
                                        f.write(body)
                                    generada_ok = True
                                    logger.info(f"[Gemini Web Vision] ✓ Imagen transformada por Gemini Web ({len(body)/1024:.1f} KB)")
                                    break
                finally:
                    await context.close()
        except Exception as e_gw:
            logger.warning(f"[Gemini Web Vision] Conmutando a transformación cinematográfica local para '{clean_title[:40]}': {e_gw}")

        try:
            if temp_ref != input_image_path and temp_ref.exists():
                temp_ref.unlink()
        except Exception:
            pass

        if generada_ok and output_image_path.exists():
            return ManyaSEOMetadataService.blindar_y_optimizar_imagen(
                ruta_imagen=output_image_path,
                titulo=clean_title,
                descripcion=contexto_caption or f"Fotografía editorial transformada con IA de {clean_title} en Manya ServicioTI.",
                categoria="Peñarol",
                keywords=keywords,
                transformacion_ia="Transformación multimodal generativa en Google Gemini Web (Imagen 3) + Blindaje SEO ServicioTI"
            )
        else:
            return cls.aplicar_transformacion_cinematografica_local(
                input_path=input_image_path,
                output_path=output_image_path,
                titulo=clean_title,
                descripcion=contexto_caption or f"Fotografía editorial optimizada de {clean_title} en Manya ServicioTI.",
                keywords=keywords
            )

    @classmethod
    def generar_texto_gflash_38(cls, prompt: str, esperar_json: bool = True) -> Dict[str, Any]:
        """
        Genera contenido editorial de Peñarol priorizando:
        1. Gemini Web (Playwright `~/.gemini_automation_profile` con GFlash 3.8).
        2. Cascada API Google GenAI: `gemini-3.8-flash` -> `gemini-3.5-flash` -> `gemini-3-flash-preview` -> `gemini-2.5-flash`.
        """
        # Intento 1: Usar GeminiWebTextService existente en seo_blogger_automation
        try:
            sys.path.insert(0, str(SCRATCH_DIR / "seo_blogger_automation"))
            from services.gemini_web_text_service import GeminiWebTextService
            logger.info("[Redactor GFlash 3.8] Ejecutando redacción en Gemini Web...")
            if esperar_json:
                return GeminiWebTextService.generar_json(prompt=prompt, headless=True, timeout_seconds=65)
            else:
                txt = GeminiWebTextService.generar_texto(prompt=prompt, headless=True, timeout_seconds=65)
                return {"text": txt}
        except Exception as e_web:
            logger.warning(f"[Redactor GFlash 3.8] Aviso en Gemini Web ({e_web}). Activando cascada API gemini-3.8-flash...")

        # Intento 2: Cascada API encabezada por gemini-3.8-flash
        if GEMINI_API_KEY:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=GEMINI_API_KEY)
            for model_name in ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3-flash-preview", "gemini-2.5-flash"]:
                try:
                    cfg = types.GenerateContentConfig(
                        response_mime_type="application/json" if esperar_json else "text/plain",
                        temperature=0.45
                    )
                    resp = client.models.generate_content(model=model_name, contents=prompt, config=cfg)
                    if resp and resp.text:
                        logger.info(f"[Redactor GFlash 3.8] ✓ Respuesta generada con modelo '{model_name}'.")
                        if esperar_json:
                            clean = re.sub(r"^```(?:json)?|```$", "", resp.text.strip(), flags=re.M).strip()
                            return json.loads(clean)
                        return {"text": resp.text}
                except Exception as e_api:
                    logger.warning(f"[Redactor GFlash 3.8] Modelo {model_name} no disponible ({str(e_api)[:80]}), probando siguiente...")

        return {}
