# -*- coding: utf-8 -*-
import sys
import ssl
import json
import re
import urllib.request
from bs4 import BeautifulSoup

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def fetch(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        return r.read().decode("utf-8", errors="ignore")

def inspect_ficha(url):
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    print(f"=== FICHA: {url} ===")
    print("Title:", soup.title.string if soup.title else "")
    
    # Check for images in the ficha
    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        alt = img.get("alt", "")
        if src and not src.startswith("data:"):
            images.append((src, alt))
            
    print(f"\nImages found ({len(images)}):")
    for src, alt in images:
        print(f"  - {src} (alt: {alt})")
        
    # Check for match details: teams, score, date, tournament, referee, lineups, goals, photos/gallery
    print("\nText blocks / match info:")
    for card in soup.find_all(["div", "section"], class_=re.compile(r"(partido|ficha|detalle|alineacion|resumen|datos|galeria|fotos)", re.I)):
        classes = card.get("class", [])
        text = card.get_text(separator=" | ", strip=True)[:250]
        if text:
            print(f"  [{' '.join(classes)}]: {text}")

def inspect_mcp_and_other():
    for path in ["/conector-mcp", "/estadisticas", "/por-el-mundo"]:
        try:
            html = fetch("https://1891.uy" + path)
            soup = BeautifulSoup(html, "html.parser")
            print(f"\n=== PAGE: {path} ===")
            print("Title:", soup.title.string if soup.title else "")
            main_text = soup.get_text(separator=" ", strip=True)[:350]
            print("Sample text:", main_text)
        except Exception as e:
            print(f"Error {path}: {e}")

if __name__ == "__main__":
    inspect_ficha("https://1891.uy/partidos/32170/18-10-2026-penarol-0-1-liverpool")
    inspect_ficha("https://1891.uy/partidos/32168/04-10-2026-penarol-1-0-racing")
    inspect_mcp_and_other()
