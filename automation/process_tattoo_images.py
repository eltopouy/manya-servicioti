import os
import shutil
from pathlib import Path
from PIL import Image

BRAIN_DIR = Path(r"C:\Users\Andrés\.gemini\antigravity\brain\bd3e4130-a9c5-40bb-ba3d-12b85997db11")
DEST_DIR = Path(r"C:\Users\Andrés\.gemini\antigravity\scratch\manya_servicioti\assets\tattoos")
DEST_DIR.mkdir(parents=True, exist_ok=True)

MAPPINGS = {
    "manya_tattoo_escudo_1891": "manya_tattoo_escudo_1891",
    "manya_tattoo_campeon_del_siglo": "manya_tattoo_campeon_del_siglo",
    "manya_tattoo_idolo_morena": "manya_tattoo_idolo_morena",
    "manya_tattoo_lettering_chicano": "manya_tattoo_lettering_chicano",
    "manya_tattoo_fiera_aguirre_1987": "manya_tattoo_fiera_aguirre_1987",
    "manya_tattoo_minimalista_linea_fina": "manya_tattoo_minimalista_linea_fina",
}

def process_images():
    brain_files = list(BRAIN_DIR.glob("manya_tattoo_*.jpg"))
    processed = 0

    for prefix, target_name in MAPPINGS.items():
        # Find latest file matching prefix
        matches = [f for f in brain_files if f.name.startswith(prefix)]
        if not matches:
            print(f"Waiting for {prefix}...")
            continue
        # Get newest match
        latest_match = max(matches, key=lambda f: f.stat().st_mtime)
        
        target_jpg = DEST_DIR / f"{target_name}.jpg"
        target_webp = DEST_DIR / f"{target_name}.webp"

        # Copy jpg
        shutil.copy2(latest_match, target_jpg)

        # Convert to optimized webp
        try:
            with Image.open(target_jpg) as img:
                # Resize if unnecessarily large (max width 1400)
                if img.width > 1400:
                    ratio = 1400 / img.width
                    new_size = (1400, int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                    img.save(target_jpg, "JPEG", quality=88, optimize=True)
                img.save(target_webp, "WEBP", quality=84, method=6)
            print(f"Processed: {target_name} -> JPG & WEBP")
            processed += 1
        except Exception as e:
            print(f"Error processing {target_name}: {e}")

    return processed

if __name__ == "__main__":
    count = process_images()
    print(f"Total processed: {count}/{len(MAPPINGS)}")
