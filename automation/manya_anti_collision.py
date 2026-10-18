# -*- coding: utf-8 -*-
"""
Módulo Anti-Colisión y Coordinación Central para Manya ServicioTI.
Evita conflictos entre Playwright (perfil de Chrome de Gemini Web),
llamadas simultáneas a Blogger API v3 y cruce de horarios con las
automatizaciones programadas existentes (Clima, POTD, Noticias Uruguay).
"""

import os
import sys
import time
import json
import sqlite3
import psutil
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta, time as dtime
from typing import Optional, Dict, Any

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

logger = logging.getLogger("ManyaAntiCollision")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

BASE_DIR = Path(__file__).resolve().parent.parent
SCRATCH_DIR = BASE_DIR.parent
LOCKS_DIR = SCRATCH_DIR / ".locks"
DATA_DIR = BASE_DIR / "data"

LOCKS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

UY_TZ = timezone(timedelta(hours=-3))


class CentralAutomationLock:
    """
    Controlador de bloqueo entre procesos usando archivos de lock atómicos.
    Protege el perfil de usuario de Chrome (~/.gemini_automation_profile)
    y el acceso a Blogger API v3.
    """

    @classmethod
    def _is_pid_alive(cls, pid: int) -> bool:
        """Verifica si el PID existe y sigue activo."""
        try:
            p = psutil.Process(pid)
            return p.is_running() and p.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
            return False

    @classmethod
    def acquire(cls, lock_name: str, timeout_sec: int = 120, stale_after_sec: int = 900):
        """
        Context manager para adquirir un lock de recurso compartido.
        Uso:
            with CentralAutomationLock.acquire("gemini_web_profile"):
                ...
        """
        return _LockContext(lock_name, timeout_sec, stale_after_sec)


class _LockContext:
    def __init__(self, lock_name: str, timeout_sec: int, stale_after_sec: int):
        self.lock_name = lock_name
        self.lock_file = LOCKS_DIR / f"{lock_name}.lock"
        self.timeout_sec = timeout_sec
        self.stale_after_sec = stale_after_sec
        self.acquired = False

    def __enter__(self):
        start_time = time.time()
        while time.time() - start_time < self.timeout_sec:
            if not self.lock_file.exists():
                try:
                    # Intento atómico de crear el archivo
                    with open(self.lock_file, "x", encoding="utf-8") as f:
                        payload = {
                            "lock_name": self.lock_name,
                            "pid": os.getpid(),
                            "created_at": datetime.now(UY_TZ).isoformat(),
                            "timestamp": time.time()
                        }
                        json.dump(payload, f)
                    self.acquired = True
                    logger.info(f"[Lock] ✓ Adquirido lock '{self.lock_name}' (PID {os.getpid()})")
                    return self
                except FileExistsError:
                    pass

            # Si ya existe, verificar si quedó huérfano (stale)
            try:
                with open(self.lock_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                owner_pid = data.get("pid")
                lock_time = data.get("timestamp", 0)

                # Si el proceso dueño ya no existe o pasó más del tiempo límite de stale
                if (not CentralAutomationLock._is_pid_alive(owner_pid)) or (time.time() - lock_time > self.stale_after_sec):
                    logger.warning(f"[Lock] Limpiando lock huérfano '{self.lock_name}' de PID {owner_pid}.")
                    try:
                        self.lock_file.unlink()
                        continue
                    except Exception:
                        pass
            except Exception:
                pass

            time.sleep(1.5)

        logger.warning(f"[Lock] No se pudo adquirir el lock '{self.lock_name}' tras {self.timeout_sec}s. Continuando con precaución.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.acquired and self.lock_file.exists():
            try:
                self.lock_file.unlink()
                logger.info(f"[Lock] Liberado lock '{self.lock_name}' (PID {os.getpid()})")
            except Exception as e:
                logger.warning(f"[Lock] Error liberando lock '{self.lock_name}': {e}")


class ScheduleSafety:
    """
    Verifica que las ejecuciones de Peñarol no colisionen con las ventanas
    de tareas programadas existentes de ServicioTI:
      - 05:25 - 05:45: Blogger_Clima_Montevideo_Diario
      - 05:55 - 06:10: Blogger Wikipedia POTD
      - 06:12 - 07:15: Blogger Noticias Uruguay Cronograma Matutino
    """

    BLACKOUT_WINDOWS = [
        (dtime(5, 25), dtime(7, 15), "Ventana Matutina ServicioTI (Clima + POTD + Noticias Uruguay)")
    ]

    @classmethod
    def is_safe_to_publish(cls) -> (bool, str):
        now_time = datetime.now(UY_TZ).time()
        for start_w, end_w, motivo in cls.BLACKOUT_WINDOWS:
            if start_w <= now_time <= end_w:
                return False, f"Horario protegido por {motivo}. Esperar a las {end_w.strftime('%H:%M')} hs."
        return True, "Horario libre y seguro para publicación de Peñarol."


class ManyaBloggerCatalog:
    """
    Catálogo SQLite aislado para llevar registro de todas las publicaciones
    deportivas de Peñarol en Blogger, garantizando control de frecuencia y
    evitando duplicados.
    """

    DB_PATH = DATA_DIR / "manya_blogger_catalog.db"

    @classmethod
    def init_db(cls):
        with sqlite3.connect(cls.DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS manya_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_type TEXT NOT NULL,         -- 'PREVIA', 'CRONICA', 'NOTICIA_DIARIA'
                    match_id TEXT,                  -- ESPN Event ID si aplica (ej. '401929259')
                    match_title TEXT,               -- ej. 'Liverpool vs Peñarol'
                    blogger_post_id TEXT UNIQUE,
                    blogger_url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    published_date TEXT NOT NULL,   -- 'YYYY-MM-DD'
                    published_at TEXT NOT NULL,     -- ISO
                    word_count INTEGER,
                    status TEXT DEFAULT 'PUBLICADO'
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_manya_match ON manya_posts(match_id, post_type);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_manya_date ON manya_posts(published_date, post_type);")
            conn.commit()

    @classmethod
    def can_publish(cls, post_type: str, match_id: Optional[str] = None) -> (bool, str):
        """
        Regla editorial:
          - Para un match_id dado: solo 1 'PREVIA' y solo 1 'CRONICA'.
          - Para 'NOTICIA_DIARIA' (días sin partido): máximo 1 por día.
        """
        cls.init_db()
        today_str = datetime.now(UY_TZ).strftime("%Y-%m-%d")

        with sqlite3.connect(cls.DB_PATH) as conn:
            cursor = conn.cursor()
            if match_id and post_type in ("PREVIA", "CRONICA"):
                cursor.execute(
                    "SELECT blogger_url, title FROM manya_posts WHERE match_id = ? AND post_type = ? LIMIT 1",
                    (str(match_id), post_type)
                )
                row = cursor.fetchone()
                if row:
                    return False, f"Ya existe una publicación de tipo '{post_type}' para el partido {match_id}: {row[0]}"
            else:
                cursor.execute(
                    "SELECT COUNT(*) FROM manya_posts WHERE published_date = ? AND post_type = 'NOTICIA_DIARIA'",
                    (today_str,)
                )
                count = cursor.fetchone()[0]
                if count >= 1:
                    return False, f"Ya se publicó una noticia diaria de Peñarol hoy ({today_str})."

        return True, "Permitido publicar."

    @classmethod
    def register_post(cls, post_type: str, match_id: Optional[str], match_title: str,
                      blogger_post_id: str, blogger_url: str, title: str, word_count: int = 0):
        cls.init_db()
        today_str = datetime.now(UY_TZ).strftime("%Y-%m-%d")
        now_iso = datetime.now(UY_TZ).isoformat()
        with sqlite3.connect(cls.DB_PATH) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO manya_posts 
                (post_type, match_id, match_title, blogger_post_id, blogger_url, title, published_date, published_at, word_count, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PUBLICADO')
            """, (post_type, str(match_id or ""), match_title, blogger_post_id, blogger_url, title, today_str, now_iso, word_count))
            conn.commit()
        logger.info(f"[Catálogo Peñarol] ✓ Registrado post {post_type} en BD: {blogger_url}")


if __name__ == "__main__":
    ManyaBloggerCatalog.init_db()
    safe, msg = ScheduleSafety.is_safe_to_publish()
    print("Safety Check:", safe, "-", msg)
    with CentralAutomationLock.acquire("test_lock", timeout_sec=5):
        print("Lock de prueba exitoso.")
