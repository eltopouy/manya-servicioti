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

def explore_home():
    html = fetch("https://1891.uy/")
    soup = BeautifulSoup(html, "html.parser")
    print("=== EXPLORING 1891.uy HOME ===")
    print("Title:", soup.title.string if soup.title else "")
    
    # Navigation
    nav = soup.find_all("nav") or soup.find_all("header")
    print("\n-- Nav Links --")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if text and (href.startswith("/") or "1891.uy" in href):
            print(f"{href} -> {text}")
            
    # Check for sections, statistics, highlights
    print("\n-- Headings --")
    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        print(f"<{h.name}> {h.get_text(strip=True)}")

def explore_partidos():
    html = fetch("https://1891.uy/partidos")
    soup = BeautifulSoup(html, "html.parser")
    print("\n=== EXPLORING 1891.uy/partidos ===")
    
    # Look for "fichas", matches, tables, filters, links
    fichas_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if "ficha" in href.lower() or "partido" in href.lower():
            fichas_links.append((href, text))
            
    print(f"Total partido/ficha links found: {len(fichas_links)}")
    for href, text in fichas_links[:25]:
        print(f"{href} -> {text}")

if __name__ == "__main__":
    explore_home()
    explore_partidos()
