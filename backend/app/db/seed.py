"""
Seed data awal untuk Smart CCTV AI — Pertamina EP.

Script ini berjalan otomatis setelah `alembic upgrade head` saat container backend startup.
Data yang disisipkan:
  - 4 user demo (admin, supervisor1, operator1, operator2)
  - 5 kamera sesuai dataset mockup

Jika data sudah ada, script ini aman untuk dijalankan ulang (idempotent).

Cara menjalankan manual:
    python -m app.db.seed
"""

import logging

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Camera, User

logger = logging.getLogger(__name__)

# ── Seed Data ─────────────────────────────────────────────────────────────────

SEED_USERS = [
    {
        "id": "u1",
        "username": "admin",
        "password_hash": hash_password("busDev123!"),
        "first_name": "Rina",
        "last_name": "Kusuma",
        "email": "rina.kusuma@pertamina-ep.local",
        "role": "admin",
        "is_enabled": True,
    },
    {
        "id": "u2",
        "username": "supervisor1",
        "password_hash": hash_password("busDev123!"),
        "first_name": "Agus",
        "last_name": "Wijaya",
        "email": "agus.wijaya@pertamina-ep.local",
        "role": "supervisor",
        "is_enabled": True,
    },
    {
        "id": "u3",
        "username": "operator1",
        "password_hash": hash_password("busDev123!"),
        "first_name": "Budi",
        "last_name": "Santoso",
        "email": "budi.santoso@pertamina-ep.local",
        "role": "operator",
        "is_enabled": True,
    },
    {
        "id": "u4",
        "username": "operator2",
        "password_hash": hash_password("busDev123!"),
        "first_name": "Siti",
        "last_name": "Rahayu",
        "email": "siti.rahayu@pertamina-ep.local",
        "role": "operator",
        "is_enabled": False,  # Disabled by default — sama seperti mockup
    },
]

SEED_CAMERAS = [
    {
        "id": 1,
        "name": "CAM-01 Gerbang Utama",
        "ip_address": "192.168.56.101",
        "location": "Gerbang Utama",
        "category": "apd",
        "stream_path": "cam1",
        "rtsp_url": "rtsp://admin:password@192.168.56.101:554/stream1",
        "is_active": True,
    },
    {
        "id": 2,
        "name": "CAM-02 Area Produksi A",
        "ip_address": "192.168.56.102",
        "location": "Area Produksi A",
        "category": "apd",
        "stream_path": "cam2",
        "rtsp_url": "rtsp://admin:password@192.168.56.102:554/stream1",
        "is_active": True,
    },
    {
        "id": 3,
        "name": "CAM-03 Workshop",
        "ip_address": "192.168.56.103",
        "location": "Workshop",
        "category": "apd",
        "stream_path": None,    # Belum ada stream (sama seperti mockup)
        "rtsp_url": None,
        "is_active": True,
    },
    {
        "id": 4,
        "name": "CAM-04 Pos Satpam",
        "ip_address": "192.168.56.104",
        "location": "Pos Satpam",
        "category": "vehicle",
        "stream_path": "cam4",
        "rtsp_url": "rtsp://admin:password@192.168.56.104:554/stream1",
        "is_active": True,
    },
    {
        "id": 5,
        "name": "CAM-05 Jalan Akses Tambang",
        "ip_address": "192.168.56.105",
        "location": "Jalan Akses Tambang",
        "category": "vehicle",
        "stream_path": "cam5",
        "rtsp_url": "rtsp://admin:password@192.168.56.105:554/stream1",
        "is_active": True,
    },
]


def run_seed(db: Session) -> None:
    """Sisipkan data seed jika belum ada (idempotent berdasarkan ID)."""

    # ── Users ─────────────────────────────────────────────────────────────
    for data in SEED_USERS:
        existing = db.get(User, data["id"])
        if existing is None:
            db.add(User(**data))
            logger.info("Seed: user '%s' ditambahkan.", data["username"])
        else:
            logger.debug("Seed: user '%s' sudah ada, dilewati.", data["username"])

    # ── Cameras ───────────────────────────────────────────────────────────
    for data in SEED_CAMERAS:
        existing = db.get(Camera, data["id"])
        if existing is None:
            db.add(Camera(**data))
            logger.info("Seed: kamera '%s' ditambahkan.", data["name"])
        else:
            logger.debug("Seed: kamera '%s' sudah ada, dilewati.", data["name"])

    db.commit()
    logger.info("Seed selesai.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    db = SessionLocal()
    try:
        run_seed(db)
    finally:
        db.close()
