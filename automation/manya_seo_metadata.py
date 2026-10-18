# -*- coding: utf-8 -*-
"""
MOTOR DE METADATOS SEO, EXIF UNICODE, GPS CAMPEÓN DEL SIGLO Y XMP IPTC (manya_seo_metadata.py)
==============================================================================================
Basado en SEOMetadataService de ServicioTI, calibrado específicamente para `manya.servicioti.com.uy`
y `www.servicioti.com.uy`:
1. Purga cualquier metadato previo o rastro de terceros/IA.
2. Inyecta EXIF con UserComment Unicode, Artist, Copyright y Software.
3. Inyecta coordenadas GPS exactas del Estadio Campeón del Siglo (Ruta 102 Km 23.500, Montevideo:
   34° 47' 49" S, 56° 04' 02" W / -34.7969, -56.0672).
4. Inyecta paquete XMP UTF-8 (Dublin Core, IPTC Core, Google Licensable Images).
5. Genera versión dual JPEG Progresivo + WebP ultraligero para Core Web Vitals (LCP < 1.2s).
"""

import io
import re
import html
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from PIL import Image, ExifTags

logger = logging.getLogger("ManyaSEOMetadata")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

AUTOR_OFICIAL = "Andrés Franchi Ugartemendía"
AUTOR_ASCII = "Andres Franchi Ugartemendia"
ORGANIZACION = "Manya ServicioTI - Portal Aurinegro"
URL_MANYA = "https://manya.servicioti.com.uy"
URL_BLOGGER = "https://www.servicioti.com.uy"
COPYRIGHT_TEXTO = f"Copyright © 2026 {AUTOR_OFICIAL} | {URL_MANYA} - {URL_BLOGGER}"
COPYRIGHT_ASCII = f"Copyright (c) 2026 {AUTOR_ASCII} - {URL_MANYA}"
CREDITO_OFICIAL = f"{AUTOR_OFICIAL} - Manya ServicioTI ({URL_MANYA})"
SOFTWARE_TAG = "Manya ServicioTI Visual & SEO Engine v5.0 (manya.servicioti.com.uy)"

# Coordenadas exactas del Estadio Campeón del Siglo (Montevideo, Uruguay)
CDS_LAT_DEG = (34, 47, 49)   # 34° 47' 49" S (-34.796944)
CDS_LON_DEG = (56, 4, 2)     # 56° 04' 02" W (-56.067222)


class ManyaSEOMetadataService:
    """Blindaje e inyección de metadatos SEO para todas las imágenes de manya.servicioti.com.uy."""

    @classmethod
    def _build_xmp_packet(
        cls,
        titulo: str,
        descripcion: str,
        categoria: str = "Peñarol",
        keywords: Optional[List[str]] = None,
        transformacion_ia: str = ""
    ) -> str:
        t_esc = html.escape(titulo or "Club Atlético Peñarol - Manya ServicioTI")
        d_esc = html.escape(descripcion or "Actualidad, plantel, historia y estadísticas del Club Atlético Peñarol en Manya ServicioTI.")
        c_esc = html.escape(categoria or "Deportes")

        base_kw = [
            "Peñarol", "Club Atlético Peñarol", "Manya", "Carbonero", "Aurinegro",
            "Campeón del Siglo", "Fútbol Uruguayo", "Copa Libertadores", "Padre y Decano",
            "Montevideo", "Uruguay", "ServicioTI", AUTOR_OFICIAL, c_esc
        ]
        if keywords:
            for k in keywords:
                k_clean = html.escape(str(k).strip())
                if k_clean and k_clean not in base_kw:
                    base_kw.append(k_clean)

        items_kw = "".join(f"<rdf:li>{k}</rdf:li>" for k in base_kw[:28])
        fecha_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S-03:00")
        nota_ia = html.escape(transformacion_ia[:180]) if transformacion_ia else "Curación y optimización visual por Gemini Web para Manya ServicioTI"

        return f"""<?xpacket begin='' id='W5M0MpCehiHzreSzNTczkc9d'?>
<x:xmpmeta xmlns:x='adobe:ns:meta/'>
 <rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>
  <rdf:Description rdf:about=''
    xmlns:dc='http://purl.org/dc/elements/1.1/'
    xmlns:xmp='http://ns.adobe.com/xap/1.0/'
    xmlns:xmpRights='http://ns.adobe.com/xap/1.0/rights/'
    xmlns:photoshop='http://ns.adobe.com/photoshop/1.0/'
    xmlns:Iptc4xmpCore='http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/'
    xmlns:plus='http://ns.useplus.org/ldf/xmp/1.0/'>
   <dc:creator><rdf:Seq><rdf:li>{AUTOR_OFICIAL}</rdf:li></rdf:Seq></dc:creator>
   <dc:title><rdf:Alt><rdf:li xml:lang='x-default'>{t_esc}</rdf:li></rdf:Alt></dc:title>
   <dc:description><rdf:Alt><rdf:li xml:lang='x-default'>{d_esc}</rdf:li></rdf:Alt></dc:description>
   <dc:rights><rdf:Alt><rdf:li xml:lang='x-default'>{COPYRIGHT_TEXTO}</rdf:li></rdf:Alt></dc:rights>
   <dc:subject><rdf:Bag>{items_kw}</rdf:Bag></dc:subject>
   <xmpRights:Marked>True</xmpRights:Marked>
   <xmpRights:WebStatement>{URL_MANYA}</xmpRights:WebStatement>
   <plus:Licensor>
    <rdf:Seq>
     <rdf:li rdf:parseType='Resource'>
      <plus:LicensorName>{ORGANIZACION}</plus:LicensorName>
      <plus:LicensorURL>{URL_MANYA}</plus:LicensorURL>
     </rdf:li>
    </rdf:Seq>
   </plus:Licensor>
   <photoshop:Headline>{t_esc}</photoshop:Headline>
   <photoshop:Credit>{CREDITO_OFICIAL}</photoshop:Credit>
   <photoshop:Source>{URL_MANYA}</photoshop:Source>
   <photoshop:Category>{c_esc}</photoshop:Category>
   <photoshop:City>Montevideo</photoshop:City>
   <photoshop:State>Montevideo</photoshop:State>
   <photoshop:Country>Uruguay</photoshop:Country>
   <photoshop:Instructions>{nota_ia}</photoshop:Instructions>
   <Iptc4xmpCore:Location>Estadio Campeón del Siglo, Ruta 102 Km 23.500</Iptc4xmpCore:Location>
   <photoshop:DateCreated>{fecha_iso}</photoshop:DateCreated>
   <xmp:CreateDate>{fecha_iso}</xmp:CreateDate>
   <xmp:ModifyDate>{fecha_iso}</xmp:ModifyDate>
   <xmp:CreatorTool>{SOFTWARE_TAG}</xmp:CreatorTool>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end='w'?>"""

    @classmethod
    def blindar_y_optimizar_imagen(
        cls,
        ruta_imagen: Path,
        titulo: str,
        descripcion: str = "",
        categoria: str = "Peñarol",
        keywords: Optional[List[str]] = None,
        transformacion_ia: str = "",
        max_width: int = 1280,
        calidad_jpg: int = 86,
        calidad_webp: int = 84
    ) -> Dict[str, Any]:
        """
        1. Crea un lienzo limpio en memoria (eliminando cualquier EXIF/metadato previo inseguro).
        2. Redimensiona proporcionalmente si supera max_width.
        3. Inyecta EXIF limpio + GPS Campeón del Siglo + XMP UTF-8 completo.
        4. Guarda tanto en .jpg progresivo como en .webp ultraligero.
        """
        path = Path(ruta_imagen)
        if not path.exists():
            return {"success": False, "error": f"No existe {path}"}

        try:
            with Image.open(path) as raw_img:
                # Crear copia limpia de píxeles RGB sin metadatos heredados de terceros
                rgb_img = raw_img.convert("RGB")
                w, h = rgb_img.size
                if w > max_width:
                    new_h = int(h * (max_width / w))
                    rgb_img = rgb_img.resize((max_width, new_h), Image.Resampling.LANCZOS)
                    w, h = rgb_img.size

                exif = Image.Exif()
                comentario = f"Autor: {AUTOR_OFICIAL} | {URL_MANYA} | {titulo[:110]}"
                exif[ExifTags.Base.UserComment] = b"UNICODE\x00" + comentario.encode("utf-16le")
                exif[ExifTags.Base.Artist] = AUTOR_ASCII
                exif[ExifTags.Base.Copyright] = COPYRIGHT_ASCII
                exif[ExifTags.Base.Software] = SOFTWARE_TAG
                desc_ascii = re.sub(r"[^\x20-\x7EáéíóúÁÉÍÓÚñÑüÜ¿¡.,;:\-]", " ", descripcion or titulo)[:200]
                exif[ExifTags.Base.ImageDescription] = desc_ascii.encode("latin-1", errors="replace").decode("latin-1")

                ahora_str = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
                exif[ExifTags.Base.DateTime] = ahora_str
                exif[ExifTags.Base.DateTimeOriginal] = ahora_str

                try:
                    gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
                    gps_ifd[ExifTags.GPS.GPSLatitudeRef] = "S"
                    gps_ifd[ExifTags.GPS.GPSLatitude] = CDS_LAT_DEG
                    gps_ifd[ExifTags.GPS.GPSLongitudeRef] = "W"
                    gps_ifd[ExifTags.GPS.GPSLongitude] = CDS_LON_DEG
                    gps_ifd[ExifTags.GPS.GPSAltitudeRef] = 0
                    gps_ifd[ExifTags.GPS.GPSAltitude] = 42
                except Exception:
                    pass

                xmp_bytes = cls._build_xmp_packet(
                    titulo=titulo,
                    descripcion=descripcion,
                    categoria=categoria,
                    keywords=keywords,
                    transformacion_ia=transformacion_ia
                ).encode("utf-8")

                # Guardar JPG Progresivo
                jpg_path = path.with_suffix(".jpg")
                buf_jpg = io.BytesIO()
                rgb_img.save(
                    buf_jpg,
                    format="JPEG",
                    quality=calidad_jpg,
                    optimize=True,
                    progressive=True,
                    subsampling=1,
                    exif=exif,
                    xmp=xmp_bytes
                )
                jpg_bytes = buf_jpg.getvalue()
                with open(jpg_path, "wb") as f:
                    f.write(jpg_bytes)

                # Guardar WebP Ultraligero
                webp_path = path.with_suffix(".webp")
                buf_webp = io.BytesIO()
                rgb_img.save(
                    buf_webp,
                    format="WEBP",
                    quality=calidad_webp,
                    method=6,
                    exif=exif,
                    xmp=xmp_bytes
                )
                webp_bytes = buf_webp.getvalue()
                with open(webp_path, "wb") as f:
                    f.write(webp_bytes)

            logger.info(
                f"[SEO Metadata] ✓ Imagen blindada: {webp_path.name} "
                f"({w}x{h} | WebP: {len(webp_bytes)/1024:.1f} KB | JPG: {len(jpg_bytes)/1024:.1f} KB)"
            )
            return {
                "success": True,
                "jpg_path": str(jpg_path),
                "webp_path": str(webp_path),
                "width": w,
                "height": h,
                "jpg_kb": round(len(jpg_bytes) / 1024, 1),
                "webp_kb": round(len(webp_bytes) / 1024, 1)
            }
        except Exception as e:
            logger.error(f"[SEO Metadata] Error procesando {path}: {e}")
            return {"success": False, "error": str(e)}
