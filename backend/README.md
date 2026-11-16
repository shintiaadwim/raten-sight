# Backend

Folder ini berisi scaffold FastAPI dengan `GET /api/health`. Alur Backend yang direncanakan mencakup validasi file churn di server, inference dengan pipeline dari Data, dan penyajian hasil tersimpan melalui API.

## Menjalankan FastAPI dan mengecek health

1. Buka PowerShell dari folder utama repo, yaitu folder yang berisi `backend/`, `data/`, dan `frontend/`. Gunakan Python 3.11 atau 3.12.
2. Untuk setup awal, buat virtual environment dan pasang dependensi.

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
   ```

3. Jalankan server dengan perintah berikut dan biarkan terminal terbuka.

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
   ```

4. Buka [endpoint health](http://127.0.0.1:8000/api/health) di browser. Pada pemeriksaan lokal, `GET /api/health` mengembalikan HTTP 200 dengan respons berikut.

   ```json
   {"status":"ok"}
   ```

5. Buka [Swagger UI](http://127.0.0.1:8000/docs) untuk melihat dan mencoba endpoint scaffold. Tekan `Ctrl+C` di terminal untuk menghentikan server. Jika port 8000 sedang dipakai, tambahkan `--port 8001` ke perintah server dan buka alamat health pada port 8001.

## Tugas pertama

Gunakan [draf kontrak dataset dan API](../docs/api.md) untuk menyepakati lokasi CSV, versi dataset dan model, tipe kolom, dan penanganan data invalid dengan Data. Cocokkan contoh CSV di draf dengan file dan skema fitur yang diserahkan Data.

Bagikan [fixture dashboard](fixtures/dashboard.demo.json) kepada Frontend untuk mencoba kondisi `ready`, `preparing`, dan `failed`. File JSON berisi respons demo yang dapat dipakai Frontend sebagai mock. Bagian [cara memakai fixture](../docs/api.md#cara-memakai-fixture) memetakan contoh ke tiap endpoint.

## Urutan pengerjaan

1. Baca file dari lokasi yang disepakati tim. Periksa versi dataset, identitas pelanggan, kolom, tipe, serta kecocokan input dengan pipeline.
2. Muat pipeline terlatih dan metadata model dari Data. Jalankan inference dengan preprocessing yang tersimpan, lalu terapkan aturan simulasi rekomendasi retensi. Cocokkan hasil dengan `customerID`.
3. Jalankan pemrosesan otomatis saat dataset dan model pertama kali tersedia, lalu proses ulang saat salah satu versinya berubah. Simpan ringkasan dan hasil per pelanggan beserta kedua versi. Sajikan hasil yang sesuai dengan versi aktif setelah pemrosesan berhasil.
4. Sediakan endpoint baca untuk status, ringkasan, hasil per pelanggan, metadata model, dan evaluasi. Atur CORS jika UI dan API memakai origin berbeda.
5. Uji skenario file tersedia, file hilang atau skema tidak sesuai, hasil sedang disiapkan, dan pergantian versi. Ukur waktu pemrosesan batch dan waktu baca hasil tersimpan secara terpisah.

## Hasil serah terima

- API terdokumentasi dengan contoh ringkasan, hasil per pelanggan, status proses, dan respons error.
- Layanan yang memproses file churn otomatis per versi dataset atau model dan menyajikan hasil tersimpan.
- Tes untuk validasi dataset, kecocokan hasil dengan ID pelanggan, dan pemrosesan ulang saat versi berubah.
- Panduan menjalankan server, memasang dataset dan artefak, mengatur CORS, serta memeriksa kesiapan hasil.
