"""
stream_worker.py — Background thread pembaca RTSP kamera dan inferensi AI.

Setiap kamera yang aktif dan memiliki rtsp_url dijalankan dalam thread terpisah.
Thread ini:
1. Membuka koneksi RTSP menggunakan OpenCV VideoCapture.
2. Melakukan frame skip sesuai konfigurasi untuk efisiensi CPU.
3. Mengirimkan setiap frame ke Detector.infer().
4. Jika ada pelanggaran terdeteksi (dan melewati cooldown):
   a. Menyimpan frame snapshot (.jpg) ke disk storage.
   b. Menulis record Violation langsung ke SQL Server via SQLAlchemy.
5. Melakukan reconnect otomatis jika koneksi RTSP terputus.
"""

from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False
    logger.warning("OpenCV tidak tersedia — stream worker berjalan dalam mode dummy.")


class StreamWorker(threading.Thread):
    """
    Thread tunggal untuk satu kamera CCTV.

    Args:
        camera_cfg  : Konfigurasi kamera dari config.yaml (camera_id, model, rtsp_url)
        infer_cfg   : Konfigurasi inferensi (frame_skip, confidence_threshold, imgsz, cooldown)
        label_cfg   : Konfigurasi label kelas (name, class_id, severity)
        weights_dir : Path folder weights/ berisi file .pt
        snapshot_dir: Path folder untuk menyimpan gambar .jpg
        db_factory  : Callable yang mengembalikan SQLAlchemy Session baru
    """

    def __init__(
        self,
        camera_cfg: dict,
        infer_cfg: dict,
        label_cfg: list[dict],
        weights_dir: Path,
        snapshot_dir: Path,
        db_factory,
    ) -> None:
        super().__init__(daemon=True, name=f"StreamWorker-cam{camera_cfg['camera_id']}")
        self.camera_id: int = camera_cfg["camera_id"]
        self.model_key: str = camera_cfg["model"]
        self.rtsp_url: str = camera_cfg["rtsp_url"]
        self.infer_cfg = infer_cfg
        self.label_cfg = label_cfg
        self.weights_dir = weights_dir
        self.snapshot_dir = snapshot_dir
        self.db_factory = db_factory
        self._stop_event = threading.Event()
        self._last_alert_time: float = 0.0

    def stop(self) -> None:
        """Beri sinyal kepada thread untuk berhenti."""
        self._stop_event.set()

    def run(self) -> None:
        logger.info("[%s] Worker mulai. RTSP: %s", self.name, self.rtsp_url)

        # Import here agar tidak crash saat test tanpa torch
        from app.ai.detector import Detector

        detector = Detector.get_or_create(self.model_key, self.weights_dir)
        frame_count = 0
        skip = self.infer_cfg.get("frame_skip", 5)
        conf_thresh = self.infer_cfg.get("confidence_threshold", 0.60)
        imgsz = self.infer_cfg.get("imgsz", 640)
        cooldown = self.infer_cfg.get("cooldown_seconds", 30)

        while not self._stop_event.is_set():
            cap = self._open_capture()
            if cap is None:
                logger.warning("[%s] Gagal membuka RTSP, coba lagi dalam 10 detik...", self.name)
                self._stop_event.wait(10)
                continue

            logger.info("[%s] Koneksi RTSP berhasil.", self.name)

            while not self._stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    logger.warning("[%s] Frame read gagal, reconnect...", self.name)
                    break

                frame_count += 1
                if frame_count % skip != 0:
                    continue

                # ── Inferensi ────────────────────────────────────────────
                detections = detector.infer(frame, self.label_cfg, conf_thresh, imgsz)
                if not detections:
                    continue

                # ── Cek Cooldown ─────────────────────────────────────────
                now = time.time()
                if now - self._last_alert_time < cooldown:
                    continue
                self._last_alert_time = now

                # Ambil deteksi dengan confidence tertinggi sebagai representasi
                top = max(detections, key=lambda d: d.confidence)

                # ── Simpan Snapshot ───────────────────────────────────────
                snapshot_path = self._save_snapshot(frame, top)

                # ── Simpan ke Database ────────────────────────────────────
                self._save_violation(top, snapshot_path)

            cap.release()

        logger.info("[%s] Worker berhenti.", self.name)

    def _open_capture(self):
        """Buka koneksi RTSP dengan OpenCV. Kembalikan None jika gagal."""
        if not _CV2_AVAILABLE:
            return None
        cap = cv2.VideoCapture(self.rtsp_url)
        if not cap.isOpened():
            return None
        return cap

    def _save_snapshot(self, frame, detection) -> str | None:
        """
        Simpan frame yang berisi pelanggaran ke disk sebagai file .jpg.
        Kembalikan path relatif file atau None jika gagal.
        """
        if not _CV2_AVAILABLE:
            return None
        try:
            filename = f"cam{self.camera_id}_{uuid.uuid4().hex[:12]}.jpg"
            filepath = self.snapshot_dir / filename
            # Gambar bounding box pada frame sebelum disimpan
            x1, y1, x2, y2 = detection.box
            annotated = frame.copy()
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(
                annotated, f"{detection.label} ({detection.confidence:.0%})",
                (x1, max(0, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2,
            )
            cv2.imwrite(str(filepath), annotated)
            return filename
        except Exception:
            logger.exception("[%s] Gagal menyimpan snapshot.", self.name)
            return None

    def _save_violation(self, detection, snapshot_filename: str | None) -> None:
        """Tulis record Violation ke SQL Server."""
        from app.models.violation import Violation

        db = self.db_factory()
        try:
            v = Violation(
                camera_id=self.camera_id,
                category=self.model_key,   # 'apd' | 'vehicle'
                label=detection.label,
                severity=detection.severity,
                has_snapshot=snapshot_filename is not None,
                snapshot_path=snapshot_filename,
                is_case=False,
                status="baru",
                created_at=datetime.now(timezone.utc),
            )
            db.add(v)
            db.commit()
            logger.info(
                "[%s] Pelanggaran disimpan: %s (conf=%.0f%%)",
                self.name, detection.label, detection.confidence * 100,
            )
        except Exception:
            db.rollback()
            logger.exception("[%s] Gagal menyimpan violation ke database.", self.name)
        finally:
            db.close()
