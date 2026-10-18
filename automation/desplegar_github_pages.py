# -*- coding: utf-8 -*-
"""
DESPLEGADOR AUTOMÁTICO DE MANYA.SERVICIOTI.COM.UY EN GITHUB PAGES (desplegar_github_pages.py)
=============================================================================================
1. Obtiene el token de GitHub autenticado en el sistema (Git Credential Manager).
2. Crea automáticamente el repositorio público `eltopouy/manya-servicioti` si no existe.
3. Hace commit y push de toda la PWA, los JSON en `/data/` y las imágenes `.webp`/`.jpg`
   transformadas con Gemini Web y blindadas con metadatos SEO en `/assets/ig/`.
4. Activa GitHub Pages en la rama `main` y configura el dominio `manya.servicioti.com.uy`.
"""

import os
import sys
import json
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_OWNER = "eltopouy"
REPO_NAME = "manya-servicioti"


def get_github_token() -> str:
    try:
        proc = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n\n",
            text=True,
            capture_output=True,
            cwd=str(BASE_DIR.parent / "horarios_servicioti")
        )
        for line in proc.stdout.splitlines():
            if line.startswith("password="):
                return line.split("=", 1)[1].strip()
    except Exception as e:
        print(f"[!] Aviso obteniendo token git credential: {e}")
    return os.environ.get("GITHUB_TOKEN", "")


def github_api_request(method: str, endpoint: str, token: str, payload: dict = None):
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Manya-ServicioTI-Deployer"
    }
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8", errors="ignore")
        return resp.status, (json.loads(body) if body else {})


def ensure_repo_exists(token: str):
    try:
        status, _ = github_api_request("GET", f"/repos/{REPO_OWNER}/{REPO_NAME}", token)
        if status == 200:
            print(f"[*] Repositorio {REPO_OWNER}/{REPO_NAME} ya existe en GitHub.")
            return
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"[~] Aviso verificando repo: {e}")

    print(f"[*] Creando repositorio público {REPO_OWNER}/{REPO_NAME} en GitHub...")
    payload = {
        "name": REPO_NAME,
        "description": "Manya ServicioTI (manya.servicioti.com.uy) — El Portal, Radar en Tiempo Real y Museo 1891 del Glorioso Peñarol",
        "homepage": "https://manya.servicioti.com.uy",
        "private": False,
        "has_issues": True,
        "has_projects": False,
        "has_wiki": False
    }
    status, data = github_api_request("POST", "/user/repos", token, payload)
    print(f"[✓] Repositorio creado exitosamente (HTTP {status}): {data.get('html_url')}")


def push_to_github():
    git_dir = BASE_DIR / ".git"
    remote_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}.git"

    if not git_dir.exists():
        subprocess.run(["git", "init", "-b", "main"], cwd=str(BASE_DIR), check=True)
        subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=str(BASE_DIR), check=True)

    # Crear .gitignore limpio
    gitignore = BASE_DIR / ".gitignore"
    gitignore.write_text("__pycache__/\n*.pyc\n.env\n_ref_temp_*\n_raw_seed_*\n", encoding="utf-8")

    subprocess.run(["git", "add", "-A"], cwd=str(BASE_DIR), check=True)
    status = subprocess.run(["git", "status", "--porcelain"], cwd=str(BASE_DIR), capture_output=True, text=True)
    if status.stdout.strip():
        subprocess.run(
            ["git", "commit", "-m", "feat(manya): deploy Manya ServicioTI PWA + Gemini Web Vision SEO images + GFlash 3.8 data"],
            cwd=str(BASE_DIR),
            check=True
        )
    subprocess.run(["git", "branch", "-M", "main"], cwd=str(BASE_DIR), check=True)
    subprocess.run(["git", "push", "-u", "origin", "main", "--force"], cwd=str(BASE_DIR), check=True)
    print(f"[✓] Código e imágenes empujados exitosamente a {remote_url} (rama main).")


def configure_github_pages(token: str):
    # 1. Intentar activar GitHub Pages en rama main
    try:
        status, data = github_api_request(
            "POST",
            f"/repos/{REPO_OWNER}/{REPO_NAME}/pages",
            token,
            {"source": {"branch": "main", "path": "/"}}
        )
        print(f"[✓] GitHub Pages activado en {REPO_OWNER}/{REPO_NAME} (HTTP {status}).")
    except urllib.error.HTTPError as e:
        if e.code == 409:
            print("[*] GitHub Pages ya estaba activo en el repositorio.")
        else:
            print(f"[~] Aviso activando GitHub Pages ({e.code}): {e.read().decode('utf-8', 'ignore')[:160]}")

    # 2. Configurar custom domain manya.servicioti.com.uy
    try:
        github_api_request(
            "PUT",
            f"/repos/{REPO_OWNER}/{REPO_NAME}/pages",
            token,
            {"cname": "manya.servicioti.com.uy", "source": {"branch": "main", "path": "/"}}
        )
        print("[✓] Custom domain 'manya.servicioti.com.uy' vinculado en GitHub Pages.")
    except urllib.error.HTTPError as e:
        print(f"[*] Nota CNAME GitHub Pages ({e.code}): El archivo CNAME ya está en la raíz del repositorio.")


def main():
    token = get_github_token()
    if not token:
        print("[!] No se encontró token de GitHub.")
        return
    ensure_repo_exists(token)
    push_to_github()
    configure_github_pages(token)


if __name__ == "__main__":
    main()
