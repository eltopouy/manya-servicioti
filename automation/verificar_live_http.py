import urllib.request
import re

url = "https://www.servicioti.com.uy/2026/10/penarol-en-vivo-la-previa-tarde-de.html"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        print("HTTP Status:", resp.status)
        for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', html):
            src = m.group(1)
            alt = m.group(0)
            if "manya" in src or "assets/ig" in src or "blogger_img_proxy" in src:
                print("IMG:", src)
except Exception as e:
    print("Error:", e)
