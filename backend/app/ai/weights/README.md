# Panduan Penempatan File Model AI (.pt)

Folder ini adalah tempat menyimpan file model YOLO/PyTorch yang akan
digunakan oleh AI inference engine yang berjalan di dalam FastAPI backend.

## Nama File yang Diharapkan

| Nama File     | Keterangan |
|---------------|------------|
| `apd.pt`      | Model deteksi APD (Helm, Rompi Safety, Sepatu Safety, dll.) |
| `vehicle.pt`  | Model deteksi pelanggaran kendaraan (Penumpang di bak terbuka, dll.) |

## Cara Menempatkan Model

1. Salin file `.pt` Anda ke dalam folder ini:
   ```
   backend/app/ai/weights/apd.pt
   backend/app/ai/weights/vehicle.pt
   ```

2. File `.pt` di-mount sebagai volume read-only ke dalam container backend:
   ```yaml
   # docker-compose.yml
   volumes:
     - ./backend/app/ai/weights:/app/app/ai/weights:ro
   ```
   **Anda tidak perlu rebuild Docker image** setiap kali mengganti model.
   Cukup ganti file `.pt` dan restart container backend:
   ```bash
   docker compose restart backend
   ```

## Label Kelas (Class Labels)

Sesuaikan konfigurasi label di `backend/app/ai/config.yaml` setelah model ditempatkan.
Label harus sesuai dengan kelas yang dilatih pada model Anda.

## Catatan Keamanan

File `.pt` **tidak akan di-commit ke Git** (sudah dikecualikan di `.gitignore`).
Simpan file model di lokasi yang aman dan sertakan bersama deployment.
