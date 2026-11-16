# Backend

Layanan FastAPI memvalidasi file churn, menjalankan tiga pipeline dari Data, dan menyediakan ringkasan, prediksi per pelanggan, serta metadata model melalui API.

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

5. Buka [Swagger UI](http://127.0.0.1:8000/docs) untuk melihat dan mencoba endpoint. Tekan `Ctrl+C` di terminal untuk menghentikan server. Jika port 8000 sedang dipakai, tambahkan `--port 8001` ke perintah server dan buka alamat health pada port 8001.

## Memasang file dan model

| Isi | Lokasi bawaan dari root repo | Variabel untuk mengganti lokasi |
| --- | --- | --- |
| CSV churn | `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv` | `RETENSIGHT_DATASET_PATH` |
| Manifest model | `backend/artifacts/manifest.json` | `RETENSIGHT_MODEL_MANIFEST` |
| Hasil analisis | `backend/results/` | `RETENSIGHT_RESULTS_DIR` |

Letakkan ketiga artefak pipeline di folder yang sama dengan manifest. Tim Data dapat menggunakan [contoh paket model](../docs/api.md#paket-model-dari-data) untuk menyiapkan file dan metadata sesuai hasil training. Dependensi Backend memakai daftar versi yang sama dengan folder Data.

Backend memeriksa file sumber saat server mulai dan setiap dua detik setelah pemeriksaan terakhir selesai. Pasangan versi yang sudah memiliki hasil valid dibaca kembali dari JSON lokal. Jika versi berubah, hasil pasangan baru disimpan sebelum API beralih ke `ready`.

Buka [ringkasan dataset](http://127.0.0.1:8000/api/dataset-summary) untuk melihat status. Jika statusnya `failed`, baca `error` dan versi pada respons, lalu periksa log terminal. Perubahan pada CSV, manifest, atau artefak memicu pemeriksaan ulang. Mulai ulang server jika perbaikannya menyangkut pemasangan dependensi atau izin folder hasil. Endpoint health tetap menunjukkan apakah FastAPI merespons.

Untuk menjalankan tes Backend, pasang dependensi pengembangan lalu jalankan pytest dari root repo.

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest backend/tests -q
```

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
