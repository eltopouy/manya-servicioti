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

def check_mcp():
    html = fetch("https://1891.uy/conector-mcp")
    soup = BeautifulSoup(html, "html.parser")
    print("=== MCP CONNECTOR PAGE ===")
    print(soup.get_text(separator="\n", strip=True))

def check_ficha_full():
    html = fetch("https://1891.uy/partidos/32170/18-10-2026-penarol-0-1-liverpool")
    soup = BeautifulSoup(html, "html.parser")
    print("\n=== FULL MATCH FICHA (Liverpool 18-10-2026) ===")
    
    # Extract main info
    main = soup.find("main") or soup.find("article") or soup
    # print text without header/footer
    for tag in soup.find_all(["header", "footer", "nav"]):
        tag.decompose()
        
    print(soup.get_text(separator="\n", strip=True)[:4000])

if __name__ == "__main__":
    check_mcp()
    check_ficha_full()
